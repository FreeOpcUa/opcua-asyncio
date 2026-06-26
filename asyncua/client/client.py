import asyncio
import contextvars
import dataclasses
import json
import logging
import os
import socket
import time
from collections.abc import Awaitable, Callable, Coroutine, Iterable, Sequence
from pathlib import Path
from typing import Any, TypeVar, cast
from urllib.parse import ParseResult, unquote, urlparse

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509.oid import ExtendedKeyUsageOID

import asyncua
from asyncua import ua

from ..common.manage_nodes import delete_nodes
from ..common.node import Node
from ..common.shortcuts import Shortcuts
from ..common.structures import load_enums, load_type_definitions
from ..common.structures104 import load_data_type_definitions
from ..common.subscription import OverflowPolicy, Subscription, SubscriptionHandler
from ..common.ua_utils import copy_dataclass_attr, value_to_datavalue
from ..common.utils import ServiceError, create_nonce
from ..common.xmlexporter import XmlExporter
from ..common.xmlimporter import XmlImporter
from ..crypto import cert_gen, security_policies, uacrypto
from ..crypto.validator import CertificateValidatorMethod
from ..ua.uaerrors import (
    BadCertificateInvalid,
    BadCertificateUntrusted,
    BadSecurityChecksFailed,
    BadSecurityPolicyRejected,
    BadSessionIdInvalid,
)
from .ua_client import StateSubscription, UaClient, UaClientState

_logger = logging.getLogger(__name__)

_T = TypeVar("_T")

# Task-scoped flag: when True, the pre-request hook bypasses its RECONNECTING
# gate. The supervisor sets this around its own teardown/connect-sequence work
# so requests it issues itself don't block waiting for the reconnect we're
# currently performing. Because contextvars are scoped to the running task,
# this does NOT leak into concurrent user requests on other tasks.
_supervisor_owns_requests: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "asyncua.supervisor_owns_requests", default=False
)


def _first_cert_from_chain(der: bytes) -> bytes:
    """Return only the leading certificate's bytes from a (possibly chained) DER blob.

    Servers sometimes hand back the server certificate concatenated with its
    chain; our crypto layer trips on the chained form, so peel off the first
    cert by reading the outer SEQUENCE length (bytes 2:4) and slicing.
    """
    cert_len = int.from_bytes(der[2:4], byteorder="big", signed=False) + 4
    return der[:cert_len]


class Client:
    """
    High level client to connect to an OPC-UA server.
    This class makes it easy to connect and browse address space.
    It attempts to expose as much functionality as possible
    but if you want more flexibility it is possible and advised to
    use UaClient object, available as self.uaclient
    which offers the raw OPC-UA services interface.
    """

    def __init__(
        self,
        url: str,
        timeout: float = 4,
        watchdog_intervall: float = 1.0,
        auto_reconnect: bool = False,
        reconnect_max_delay: float = 30.0,
        reconnect_request_timeout: float = 60.0,
    ) -> None:
        """
        :param url: url of the server.
            if you are unsure of url, write at least hostname
            and port and call get_endpoints
        :param timeout:
            Each request sent to the server expects an answer within this
            time. The timeout is specified in seconds.
        :param watchdog_intervall:
            The time between checking if the server is still alive. The timeout is specified in seconds.
        :param auto_reconnect: when True, a supervisor task is started that
            monitors transport health and re-establishes the connection
            (including re-creating all live subscriptions) on loss.
        :param reconnect_max_delay: exponential backoff cap for reconnect attempts (seconds).
        :param reconnect_request_timeout: how long requests block waiting for the
            connection to become ready while the supervisor is reconnecting.

        Some other client parameters can be changed by setting
        attributes on the constructed object:
        See the source code for the exhaustive list.
        """
        self._username: str | None = None
        self._password: str | None = None
        self.strip_url_credentials: bool = True
        self._server_url = urlparse(url)
        userinfo, have_info, _ = self._server_url.netloc.rpartition("@")
        if have_info:
            username, have_password, password = userinfo.partition(":")
            self._username = unquote(username)
            if have_password:
                self._password = unquote(password)

        self.name = "Pure Python Async Client"
        self.description = self.name
        self.application_uri = "urn:example.org:FreeOpcUa:opcua-asyncio"
        self.product_uri = "urn:freeopcua.github.io:client"
        self.server_uri: str | None = None
        self.security_policy = security_policies.SecurityPolicyNone()
        self.secure_channel_id = None
        self.secure_channel_timeout = 3600000  # 1 hour
        self.session_timeout = 3600000  # 1 hour
        self.connection_lost_callback: Callable[[Exception], Coroutine[Any, Any, None]] | None = None
        self._policy_ids: list[ua.UserTokenPolicy] = []
        self.uaclient: UaClient = UaClient(timeout)
        self.uaclient.pre_request_hook = self._wait_until_ready
        self.user_certificate: x509.Certificate | None = None
        self.user_private_key: PrivateKeyTypes | None = None
        self.user_certificate_chain: list[x509.Certificate] = []
        self._server_nonce = None
        self._session_counter = 1
        self.nodes: Shortcuts = Shortcuts(self.uaclient.session)
        self.max_messagesize = 0  # No limits
        self.max_chunkcount = 0  # No limits
        self._renew_channel_task: asyncio.Task[None] | None = None
        self._supervisor_task: asyncio.Task[None] | None = None
        self._stale_watchdog_task: asyncio.Task[None] | None = None
        self._locale = ["en"]
        self._watchdog_intervall = watchdog_intervall
        # Tracked so the auto-reconnect supervisor can re-create them; delete()
        # flips Subscription.is_deleted and the supervisor skips those.
        self._subscriptions: list[Subscription] = []
        self._auto_reconnect: bool = auto_reconnect
        self._reconnect_max_delay: float = reconnect_max_delay
        self._reconnect_request_timeout: float = reconnect_request_timeout
        self._stale_check_margin: float = 1.5
        self._stale_check_interval: float = 0.5
        self.certificate_validator: CertificateValidatorMethod | None = None
        """hook to validate a certificate, raises a ServiceError when not valid"""
        # Set before connect() to let a fresh client process resume the existing
        # server-side session via ActivateSession instead of creating a new one
        # (spec Part 4 §6.7) — useful after a client crash.
        self.session_state_path: Path | None = None

    async def __aenter__(self) -> "Client":
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Any
    ) -> None:
        await self.disconnect()

    def __str__(self) -> str:
        return f"Client({self.server_url.geturl()})"

    __repr__ = __str__

    @property
    def state(self) -> UaClientState:
        """Current connection state. Mirrors `self.uaclient.state`."""
        return self.uaclient.state

    def subscribe_state(self) -> StateSubscription:
        """Subscribe to state transitions; see `UaClient.subscribe_state`."""
        return self.uaclient.subscribe_state()

    @property
    def server_url(self) -> ParseResult:
        """Return the server URL with stripped credentials

        if self.strip_url_credentials is True.  Disabling this
        is not recommended for security reasons.
        """
        url = self._server_url
        _userinfo, have_info, hostinfo = url.netloc.rpartition("@")
        if have_info:
            if self.strip_url_credentials:
                url = url.__class__(url[0], hostinfo, *url[2:])
        return url

    @staticmethod
    def find_endpoint(
        endpoints: Iterable[ua.EndpointDescription], security_mode: ua.MessageSecurityMode, policy_uri: str
    ) -> ua.EndpointDescription:
        """
        Find endpoint with required security mode and policy URI
        """
        _logger.info("find_endpoint %r %r %r", endpoints, security_mode, policy_uri)
        for ep in endpoints:
            if (
                ep.EndpointUrl.startswith(ua.OPC_TCP_SCHEME)
                and ep.SecurityMode == security_mode
                and ep.SecurityPolicyUri == policy_uri
            ):
                return ep
        raise ua.UaError(f"No matching endpoints: {security_mode}, {policy_uri}")

    def set_user(self, username: str) -> None:
        """
        Set user name for the connection.
        initial user from the URL will be overwritten
        """
        if not isinstance(username, str):
            raise TypeError(f"Username must be a string, got {username} of type {type(username)}")
        self._username = username

    def set_password(self, pwd: str) -> None:
        """
        Set user password for the connection.
        initial password from the URL will be overwritten
        """
        if not isinstance(pwd, str):
            raise TypeError(f"Password must be a string, got {pwd} of type {type(pwd)}")
        self._password = pwd

    def set_locale(self, locale: Sequence[str]) -> None:
        """
        Sets the preferred locales of the client, the server chooses which locale he can provide.
        Normally the first matching locale in the list will be chosen, by the server.
        Call this before connect()
        """
        self._locale = locale

    async def set_security_string(self, string: str) -> None:
        """
        Set SecureConnection mode.
        :param string: Mode format ``Policy,Mode,certificate,private_key[,server_certificate]``
        where:
        - ``Policy`` is ``Basic256Sha256``, ``Aes128Sha256RsaOaep`` or ``Aes256Sha256RsaPss``
        - ``Mode`` is ``Sign`` or ``SignAndEncrypt``
        - ``certificate`` and ``server_certificate`` are paths to ``.pem`` or ``.der`` files
        - ``private_key`` may be a path to a ``.pem`` or ``.der`` file or a conjunction of ``path``::``password`` where
          ``password`` is the private key password.
        Call this before connect()
        """
        if not string:
            return None
        parts = string.split(",")
        if len(parts) < 4:
            raise ua.UaError(f"Wrong format: `{string}`, expected at least 4 comma-separated values")

        if "::" in parts[3]:
            parts[3], client_key_password = parts[3].split("::", 1)
        else:
            client_key_password = None

        policy_class = getattr(security_policies, f"SecurityPolicy{parts[0]}")
        mode = getattr(ua.MessageSecurityMode, parts[1])
        return await self.set_security(
            policy_class, parts[2], parts[3], client_key_password, parts[4] if len(parts) >= 5 else None, mode
        )

    async def set_security(
        self,
        policy: type[security_policies.SecurityPolicy],
        certificate: str | uacrypto.CertProperties | bytes | Path,
        private_key: str | uacrypto.CertProperties | bytes | Path,
        private_key_password: str | bytes | None = None,
        server_certificate: str | uacrypto.CertProperties | bytes | None = None,
        mode: ua.MessageSecurityMode = ua.MessageSecurityMode.SignAndEncrypt,
        certificate_chain: Sequence[str | uacrypto.CertProperties | bytes | Path] | None = None,
    ) -> None:
        """
        Set SecureConnection mode.
        Call this before connect()
        """
        if server_certificate is None:
            # Force unencrypted/unsigned SecureChannel to list the endpoints
            new_policy = security_policies.SecurityPolicyNone()
            self.security_policy = new_policy
            self.uaclient.security_policy = new_policy
            endpoints = await self.connect_and_get_server_endpoints()
            endpoint = Client.find_endpoint(endpoints, mode, policy.URI)
            server_certificate = uacrypto.x509_from_der(_first_cert_from_chain(endpoint.ServerCertificate))
        elif not isinstance(server_certificate, uacrypto.CertProperties):
            server_certificate = uacrypto.CertProperties(server_certificate)
        if not isinstance(certificate, uacrypto.CertProperties):
            certificate = uacrypto.CertProperties(certificate)
        certificate_chain = certificate_chain or []
        chain = [
            cert if isinstance(cert, uacrypto.CertProperties) else uacrypto.CertProperties(cert)
            for cert in certificate_chain
        ]
        if not isinstance(private_key, uacrypto.CertProperties):
            private_key = uacrypto.CertProperties(private_key, password=private_key_password)
        return await self._set_security(policy, certificate, private_key, server_certificate, mode, chain)

    async def _set_security(
        self,
        policy: type[security_policies.SecurityPolicy],
        certificate: uacrypto.CertProperties,
        private_key: uacrypto.CertProperties,
        server_cert: uacrypto.CertProperties,
        mode: ua.MessageSecurityMode = ua.MessageSecurityMode.SignAndEncrypt,
        certificate_chain: Sequence[uacrypto.CertProperties] | None = None,
    ) -> None:
        if isinstance(server_cert, uacrypto.CertProperties):
            server_cert = await uacrypto.load_certificate(server_cert.path_or_content, server_cert.extension)
        cert = await uacrypto.load_certificate(certificate.path_or_content, certificate.extension)
        certificate_chain = certificate_chain or []
        chain = await asyncio.gather(
            *(uacrypto.load_certificate(c.path_or_content, c.extension) for c in certificate_chain)
        )
        pk = await uacrypto.load_private_key(
            private_key.path_or_content,
            private_key.password,
            private_key.extension,
        )
        uacrypto.check_certificate(cert, self.application_uri, socket.gethostname())
        self.security_policy = policy(server_cert, cert, pk, mode, host_cert_chain=chain)
        self.uaclient.set_security(self.security_policy)

    async def load_client_certificate(self, path: str, extension: str | None = None) -> None:
        """
        Load user certificate from file, either pem or der
        """
        self.user_certificate = await uacrypto.load_certificate(path, extension)

    async def load_client_chain(self, certs: Iterable[uacrypto.CertProperties]) -> None:
        """
        Load user intermediate chain certificates, either pem or der
        """
        self.user_certificate_chain = await asyncio.gather(
            *(uacrypto.load_certificate(cert.path_or_content, cert.extension) for cert in certs)
        )

    async def load_private_key(
        self, path: Path, password: str | bytes | None = None, extension: str | None = None
    ) -> None:
        """
        Load user private key. This is used for authenticating using certificate
        """
        self.user_private_key = await uacrypto.load_private_key(path, password, extension)

    async def setup_self_signed_certificate(
        self,
        key_file: Path,
        cert_file: Path,
        subject_attrs: dict[str, str] | None = None,
        extended: list[x509.ObjectIdentifier] | None = None,
        host_name: str | None = None,
    ) -> tuple[Path, Path]:
        """Generate a self-signed application instance certificate and private key at the
        given paths when they are missing or invalid, using this client's application_uri.

        Nothing is regenerated when both files already exist and the certificate is still
        valid (matching application_uri / host_name and not expired); otherwise the missing
        or invalid artifact is rebuilt. Parent directories are created as needed. The pair is
        left on disk for the caller to load through set_security; the client's own security
        state is not modified.

        :param key_file: Path to the RSA private key, in PEM (PKCS8) format. Loaded and reused
            if present; otherwise a fresh 2048-bit key is generated and written here. A
            regenerated key always forces the certificate to be regenerated too.
        :param cert_file: Path to the certificate, in DER format. Regenerated when missing,
            when the key was just regenerated, or when the existing certificate fails
            validation. Generated certificates are valid for 365 days.
        :param subject_attrs: Extra subject Distinguished Name fields as
            ``{attribute_name: value}``, e.g.
            ``{"countryName": "DE", "organizationName": "ACME"}``. The common name (CN) is set
            automatically from this client's ``application_uri``. Keys must be X.509 attribute
            names known to ``cryptography`` (see ``asyncua.crypto.cert_gen.OID_NAME_MAP`` for the
            accepted set). Defaults to no extra fields.
        :param extended: Extended Key Usage OIDs declaring how the certificate may be used.
            ``None`` or an empty list defaults to ``[ExtendedKeyUsageOID.CLIENT_AUTH]``; pass
            ``[ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH]`` for a pair
            usable as both client and server.
        :param host_name: Host name embedded as a DNS SubjectAltName and checked when validating
            an existing certificate. Defaults to the local machine's hostname
            (``socket.gethostname()``). The ``application_uri`` is always added as a URI SAN.
        :return: ``(cert_file, key_file)`` as ``Path`` objects, for convenient passing to
            ``set_security``.
        """
        key_file, cert_file = Path(key_file), Path(cert_file)
        key_file.parent.mkdir(parents=True, exist_ok=True)
        cert_file.parent.mkdir(parents=True, exist_ok=True)
        await cert_gen.setup_self_signed_certificate(
            key_file,
            cert_file,
            self.application_uri,
            host_name or socket.gethostname(),
            extended or [ExtendedKeyUsageOID.CLIENT_AUTH],
            subject_attrs or {},
        )
        return cert_file, key_file

    async def _with_temp_channel(self, op: Callable[[], Awaitable[_T]]) -> _T:
        """Open a transient socket + SecureChannel, run op, tear it down on exit."""
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
            try:
                return await op()
            finally:
                await self.close_secure_channel()
        finally:
            self.disconnect_socket()

    async def connect_and_get_server_endpoints(self) -> list[ua.EndpointDescription]:
        """
        Connect, ask server for endpoints, and disconnect
        """
        return await self._with_temp_channel(self.get_endpoints)

    async def connect_and_find_servers(self) -> list[ua.ApplicationDescription]:
        """
        Connect, ask server for a list of known servers, and disconnect
        """
        return await self._with_temp_channel(self.find_servers)

    async def connect_and_find_servers_on_network(self) -> ua.FindServersOnNetworkResult:
        """
        Connect, ask server for a list of known servers on network, and disconnect
        """
        return await self._with_temp_channel(self.find_servers_on_network)

    async def connect(
        self,
        *,
        auto_reconnect: bool | None = None,
        reconnect_max_delay: float | None = None,
        reconnect_request_timeout: float | None = None,
    ) -> None:
        """
        High level method: connect, create and activate session.

        :param auto_reconnect: when True, a supervisor task is started that
            monitors transport health and re-establishes the connection
            (including re-creating all live subscriptions) on loss.
        :param reconnect_max_delay: exponential backoff cap for reconnect attempts (seconds).
        :param reconnect_request_timeout: how long requests block waiting for the
            connection to become ready while the supervisor is reconnecting.
        """
        _logger.info("connect (auto_reconnect=%s)", auto_reconnect)
        if auto_reconnect is not None:
            self._auto_reconnect = auto_reconnect
        if reconnect_max_delay is not None:
            self._reconnect_max_delay = reconnect_max_delay
        if reconnect_request_timeout is not None:
            self._reconnect_request_timeout = reconnect_request_timeout
        self.uaclient.clear_disconnect_request()
        await self._connect_sequence()
        self._supervisor_task = asyncio.create_task(self._connection_supervisor())
        self._stale_watchdog_task = asyncio.create_task(self._stale_watchdog_loop())

    async def _connect_sequence(self) -> None:
        """Run the full connect sequence: socket, hello, channel, session, activate.

        If `session_state_path` is set and a persisted session is found, attempt
        ActivateSession on the existing authentication_token first (spec Part 4
        §6.7). Fall back to CreateSession + ActivateSession when no state is
        persisted or the server has expired the session.
        """
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
            if await self._try_resume_persisted_session():
                return
            await self._create_and_activate_session()
            self._save_session_state()
            self._start_renew_loop()
        except Exception:
            self.disconnect_socket()
            raise

    async def _activate_with_credentials(self) -> ua.ActivateSessionResult:
        return await self.activate_session(
            username=self._username, password=self._password, certificate=self.user_certificate
        )

    async def _create_and_activate_session(self) -> None:
        """CreateSession + ActivateSession, unwinding the session then the channel on failure."""
        try:
            await self.create_session()
            try:
                await self._activate_with_credentials()
            except Exception:
                await self._close_session_quiet()
                raise
        except Exception:
            await self._close_secure_channel_quiet()
            raise

    async def _try_resume_persisted_session(self) -> bool:
        """ActivateSession on a persisted token if one is on disk (spec Part 4 §6.7).

        Returns True when the session resumed; on failure clears the stale state and
        returns False so the caller falls back to CreateSession + ActivateSession.
        """
        if not self._try_load_persisted_session():
            return False
        try:
            await self._activate_with_credentials()
        except Exception as exc:
            if isinstance(exc, BadSessionIdInvalid):
                _logger.info("Persisted session expired on server; creating fresh one")
            else:
                _logger.warning("Failed to resume persisted session; creating fresh one", exc_info=True)
            self._clear_persisted_session()
            self.uaclient.session.reset_authentication_token()
            self._server_nonce = None
            return False
        _logger.info("Resumed persisted session %s", self.uaclient.session.authentication_token)
        self._save_session_state()
        self._start_renew_loop()
        return True

    async def connect_sessionless(self) -> None:
        """
        High level method
        Connect without a session
        """
        _logger.info("connect")
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
        except Exception:
            self.disconnect_socket()
            raise

    async def disconnect(self) -> None:
        """
        High level method
        Close session, secure channel and socket
        """
        _logger.info("disconnect")
        try:
            await self.close_session()
        except Exception:
            _logger.exception("close_session raised during disconnect; continuing teardown")
        try:
            await self.close_secure_channel()
        except Exception:
            _logger.exception("close_secure_channel raised during disconnect; continuing teardown")
        self.disconnect_socket()
        self._clear_persisted_session()

    def _try_load_persisted_session(self) -> bool:
        """Load `authentication_token` + `server_nonce` from disk into the live session.

        Returns True when a session is loaded and worth attempting ActivateSession on.
        Returns False (and silently) when no state path is set, the file is missing,
        or the recorded session is older than `session_timeout` (server would have
        expired it already).
        """
        if self.session_state_path is None:
            return False
        try:
            raw = self.session_state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return False
        except OSError as exc:
            _logger.warning("Could not read session state at %s: %s", self.session_state_path, exc)
            return False
        try:
            state = json.loads(raw)
            token = ua.NodeId.from_string(state["authentication_token"])
            nonce = bytes.fromhex(state["server_nonce"]) if state.get("server_nonce") else None
            saved_at = float(state.get("saved_at", 0))
        except (KeyError, ValueError, TypeError) as exc:
            _logger.warning("Persisted session state at %s is malformed: %s", self.session_state_path, exc)
            self._clear_persisted_session()
            return False
        age = time.time() - saved_at
        if age > self.session_timeout / 1000:
            _logger.info(
                "Persisted session at %s is %.0fs old (>%.0fms timeout); skipping",
                self.session_state_path,
                age,
                self.session_timeout,
            )
            self._clear_persisted_session()
            return False
        self.uaclient.session.restore_authentication_token(token)
        self._server_nonce = nonce
        return True

    def _save_session_state(self) -> None:
        """Persist the current session's auth_token + server_nonce atomically with 0o600."""
        if self.session_state_path is None:
            return
        token = self.uaclient.session.authentication_token
        if token.is_null():
            return
        state = {
            "authentication_token": token.to_string(),
            "server_nonce": self._server_nonce.hex() if self._server_nonce else None,
            "saved_at": time.time(),
        }
        path = self.session_state_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            data = json.dumps(state)
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(fd, data.encode("utf-8"))
            finally:
                os.close(fd)
            os.replace(tmp, path)
        except OSError as exc:
            _logger.warning("Could not save session state to %s: %s", path, exc)

    def _clear_persisted_session(self) -> None:
        if self.session_state_path is None:
            return
        try:
            self.session_state_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            _logger.warning("Could not delete session state at %s: %s", self.session_state_path, exc)

    async def disconnect_sessionless(self) -> None:
        """
        High level method
        Close secure channel and socket
        """
        _logger.info("disconnect")
        try:
            await self.close_secure_channel()
        finally:
            self.disconnect_socket()

    async def connect_socket(self) -> None:
        """
        connect to socket defined in url
        """

        await self.uaclient.connect_socket(self.server_url.hostname, self.server_url.port)

    def disconnect_socket(self) -> None:
        if self.uaclient:
            self.uaclient.disconnect_socket()

    async def send_hello(self) -> None:
        """
        Send OPC-UA hello to server
        """
        await self.uaclient.send_hello(self.server_url.geturl(), self.max_messagesize, self.max_chunkcount)

    async def open_secure_channel(self, renew: bool = False) -> None:
        """
        Open secure channel, if renew is True, renew channel
        """
        params = ua.OpenSecureChannelParameters()
        params.ClientProtocolVersion = 0
        params.RequestType = ua.SecurityTokenRequestType.Issue
        if renew:
            params.RequestType = ua.SecurityTokenRequestType.Renew
        params.SecurityMode = self.security_policy.Mode
        params.RequestedLifetime = self.secure_channel_timeout
        # length should be equal to the length of key of symmetric encryption
        params.ClientNonce = create_nonce(self.security_policy.secure_channel_nonce_length)
        result = await self.uaclient.open_secure_channel(params)
        if self.secure_channel_timeout != result.SecurityToken.RevisedLifetime:
            _logger.info(
                "Requested secure channel timeout to be %dms, got %dms instead",
                self.secure_channel_timeout,
                result.SecurityToken.RevisedLifetime,
            )
            self.secure_channel_timeout = result.SecurityToken.RevisedLifetime

    async def close_secure_channel(self) -> None:
        return await self.uaclient.close_secure_channel()

    async def get_endpoints(self) -> list[ua.EndpointDescription]:
        """Get a list of OPC-UA endpoints."""

        params = ua.GetEndpointsParameters()
        params.EndpointUrl = self.server_url.geturl()
        return await self.uaclient.get_endpoints(params)

    async def register_server(
        self, server: "asyncua.server.Server", discovery_configuration: ua.DiscoveryConfiguration | None = None
    ) -> None:
        """
        register a server to discovery server
        if discovery_configuration is provided, the newer register_server2 service call is used
        """
        serv = ua.RegisteredServer()
        serv.ServerUri = server.get_application_uri()
        serv.ProductUri = server.product_uri
        serv.DiscoveryUrls = [cast(ua.String, server.endpoint.geturl())]
        serv.ServerType = server.application_type
        serv.ServerNames = [ua.LocalizedText(server.name)]
        serv.IsOnline = True
        if discovery_configuration:
            params = ua.RegisterServer2Parameters()
            params.Server = serv
            params.DiscoveryConfiguration = discovery_configuration
            await self.uaclient.register_server2(params)
        await self.uaclient.register_server(serv)

    async def unregister_server(
        self, server: "asyncua.server.Server", discovery_configuration: ua.DiscoveryConfiguration | None = None
    ) -> None:
        """
        register a server to discovery server
        if discovery_configuration is provided, the newer register_server2 service call is used
        """
        serv = ua.RegisteredServer()
        serv.ServerUri = server.get_application_uri()
        serv.ProductUri = server.product_uri
        serv.DiscoveryUrls = [cast(ua.String, server.endpoint.geturl())]
        serv.ServerType = server.application_type
        serv.ServerNames = [ua.LocalizedText(server.name)]
        serv.IsOnline = False
        if discovery_configuration:
            params = ua.RegisterServer2Parameters()
            params.Server = serv
            params.DiscoveryConfiguration = discovery_configuration
            await self.uaclient.unregister_server2(params)
        await self.uaclient.unregister_server(serv)

    async def find_servers(self, uris: Iterable[str] | None = None) -> list[ua.ApplicationDescription]:
        """
        send a FindServer request to the server. The answer should be a list of
        servers the server knows about
        A list of uris can be provided, only server having matching uris will be returned
        """
        if uris is None:
            uris = []
        params = ua.FindServersParameters()
        params.EndpointUrl = self.server_url.geturl()
        params.ServerUris = list(uris)
        return await self.uaclient.find_servers(params)

    async def find_servers_on_network(self) -> ua.FindServersOnNetworkResult:
        params = ua.FindServersOnNetworkParameters()
        return await self.uaclient.find_servers_on_network(params)

    async def create_session(self) -> ua.CreateSessionResult:
        """
        send a CreateSessionRequest to server with reasonable parameters.
        If you want to modify settings look at code of these methods
        and make your own
        """
        desc = ua.ApplicationDescription()
        desc.ApplicationUri = self.application_uri
        desc.ProductUri = self.product_uri
        desc.ApplicationName = ua.LocalizedText(self.name)
        desc.ApplicationType = ua.ApplicationType.Client
        params = ua.CreateSessionParameters()
        params.ServerUri = self.server_uri
        # at least 32 random bytes for server to prove possession of private key (specs part 4, 5.6.2.2)
        nonce = create_nonce(32)
        params.ClientNonce = nonce
        if self.security_policy.host_certificate:
            params.ClientCertificate = self.security_policy.host_certificate
        elif self.user_certificate:
            params.ClientCertificate = uacrypto.der_from_x509(self.user_certificate)
        else:
            params.ClientCertificate = None
        params.ClientDescription = desc
        params.EndpointUrl = self.server_url.geturl()
        params.SessionName = f"{self.description} Session{self._session_counter}"
        params.RequestedSessionTimeout = self.session_timeout
        params.MaxResponseMessageSize = 0  # means no max size
        response = await self.uaclient.create_session(params)
        if self.security_policy.host_certificate is None:
            data = nonce
        else:
            data = self.security_policy.host_certificate + nonce
        self.security_policy.asymmetric_cryptography.verify(data, response.ServerSignature.Signature)
        self._server_nonce = response.ServerNonce
        server_certificate = None
        if response.ServerCertificate is not None:
            server_certificate = _first_cert_from_chain(response.ServerCertificate)
        if not self.security_policy.peer_certificate:
            self.security_policy.peer_certificate = server_certificate
        elif self.security_policy.peer_certificate != server_certificate:
            raise ua.UaError("Server certificate mismatch")
        ep = Client.find_endpoint(response.ServerEndpoints, self.security_policy.Mode, self.security_policy.URI)

        if self.certificate_validator and server_certificate:
            try:
                await self.certificate_validator(x509.load_der_x509_certificate(server_certificate), ep.Server)
            except ServiceError as exp:
                status = ua.StatusCode(exp.code)
                _logger.error("create_session fault response: %s (%s)", status.doc, status.name)
                raise ua.UaStatusCodeError(exp.code) from exp

        self._policy_ids = ep.UserIdentityTokens
        if self.session_timeout != response.RevisedSessionTimeout:
            _logger.warning(
                "Requested session timeout to be %dms, got %dms instead",
                self.secure_channel_timeout,
                response.RevisedSessionTimeout,
            )
            self.session_timeout = response.RevisedSessionTimeout
        return response

    def _start_renew_loop(self) -> None:
        if self._renew_channel_task is not None and not self._renew_channel_task.done():
            return
        self._renew_channel_task = asyncio.create_task(self._renew_channel_loop())

    async def _wait_until_ready(self) -> None:
        """Pre-request hook: block while the supervisor is reconnecting, fail fast otherwise.

        Only RECONNECTING is gated: during initial connect (CONNECTING / SOCKET_OPEN /
        CHANNEL_OPEN) the session-establishment requests themselves must pass through.
        DISCONNECTED / DISCONNECTING raise immediately so callers see ConnectionError
        instead of silently sending to a dead transport.

        We deliberately do NOT raise on `is_disconnect_requested` alone: in-flight
        requests started before the user called `disconnect()` should be allowed
        to either complete or fail at the transport layer, not get short-circuited
        here mid-teardown.

        Requests originating from the supervisor's own reconnect work
        (CloseSession during teardown, recreate-subscription, etc.) bypass the
        gate via the `_supervisor_owns_requests` contextvar so they don't
        deadlock waiting for the very transition they're performing.
        """
        if _supervisor_owns_requests.get():
            return
        state = self.uaclient.state
        if state is UaClientState.DISCONNECTED:
            raise ConnectionError("client is disconnected")
        if state is UaClientState.DISCONNECTING:
            raise ConnectionError("client is disconnecting")
        if state is not UaClientState.RECONNECTING:
            return
        async with self.uaclient.subscribe_state() as sub:
            try:
                await sub.wait_for_state(UaClientState.CONNECTED, timeout=self._reconnect_request_timeout)
            except asyncio.TimeoutError:
                raise ConnectionError(
                    f"Timed out waiting for client to reconnect (state={self.uaclient.state.value})"
                ) from None

    # Kept as a back-compat alias for any external callers; the harness no longer registers it.
    check_connection = _wait_until_ready

    async def _connection_supervisor(self) -> None:
        """
        Single supervisor task driving health-check and reconnect.

        Started by `connect()` after the initial connect succeeds. The loop:
          1. waits for either a periodic health-tick or a state change away from CONNECTED,
          2. on each tick, probes server_state to detect dead-but-not-closed connections,
          3. on any failure, fires `connection_lost_callback` and (if auto_reconnect)
             transitions to RECONNECTING and runs `_reconnect_with_backoff`.

        Exits when `is_disconnect_requested` is set or `auto_reconnect=False` and a loss is detected.
        """
        try:
            while not self.uaclient.is_disconnect_requested:
                try:
                    exc = await self._detect_connection_loss()
                    if exc is None:
                        continue
                    if self.uaclient.is_disconnect_requested:
                        return
                    if not await self._handle_connection_loss(exc):
                        return
                except Exception:
                    _logger.exception("Connection supervisor iteration crashed; retrying in 1s")
                    await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass

    async def _detect_connection_loss(self) -> Exception | None:
        """Wait for the next health signal; return the triggering exception on a
        detected loss, or None while the connection still looks healthy."""
        try:
            await self._wait_for_health_signal()
            if self.uaclient.state is not UaClientState.CONNECTED:
                raise ConnectionError("transport lost")
        except (ConnectionError, OSError, asyncio.TimeoutError, ua.UaStatusCodeError) as exc:
            return exc
        return None

    async def _handle_connection_loss(self, exc: Exception) -> bool:
        """React to a detected loss. Returns False to stop the supervisor, True to keep going."""
        _logger.info("Supervisor detected connection issue: %r", exc)
        await self._fire_connection_lost_callback(exc)
        if not self._auto_reconnect:
            await self._inform_subscriptions_lost()
            self.uaclient.mark_disconnected()
            return False
        self.uaclient.enter_reconnecting()
        return await self._reconnect_with_backoff()

    async def _inform_subscriptions_lost(self) -> None:
        try:
            await self.uaclient.inform_subscriptions(ua.StatusCode(ua.StatusCodes.BadShutdown))
        except Exception:
            _logger.debug("inform_subscriptions raised during loss handling", exc_info=True)

    async def _stale_watchdog_loop(self) -> None:
        try:
            while not self.uaclient.is_disconnect_requested:
                await asyncio.sleep(self._stale_check_interval)
                if self.uaclient.state is not UaClientState.CONNECTED:
                    continue
                for sub in list(self._subscriptions):
                    if not sub.is_stale(self._stale_check_margin):
                        continue
                    _logger.warning("Subscription %s is stale; recreating", sub.subscription_id)
                    try:
                        await sub.recreate()
                    except Exception:
                        _logger.exception(
                            "Subscription %s recreate failed; escalating to reconnect", sub.subscription_id
                        )
                        self.uaclient.notify_transport_lost()
                        return
        except asyncio.CancelledError:
            pass
        except Exception:
            _logger.exception("Stale subscription watchdog crashed")

    async def _wait_for_health_signal(self) -> None:
        """Wait for either a state change (transport loss / supervisor work) or the next tick.

        On a tick with state still CONNECTED, probe server_state to detect a
        dead-but-not-closed connection. Raises on probe failure.
        """
        async with self.uaclient.subscribe_state() as sub:
            try:
                await sub.next_change(self._watchdog_intervall)
            except asyncio.TimeoutError:
                pass
        if self.uaclient.state is UaClientState.CONNECTED:
            probe_timeout = min(self.session_timeout / 1000 / 2, self._watchdog_intervall)
            await asyncio.wait_for(self.nodes.server_state.read_value(), timeout=probe_timeout)

    async def _fire_connection_lost_callback(self, exc: Exception) -> None:
        if self.connection_lost_callback is None:
            return
        try:
            await self.connection_lost_callback(exc)
        except Exception:
            _logger.exception("Error calling connection_lost_callback")

    async def _reconnect_with_backoff(self) -> bool:
        """Retry the connect sequence with exponential backoff. Returns True on success."""
        token = _supervisor_owns_requests.set(True)
        try:
            delay = 1.0
            while not self.uaclient.is_disconnect_requested:
                await self._teardown_transport_only()
                try:
                    reused = await self._try_reactivate_existing_session()
                except (
                    BadCertificateInvalid,
                    BadCertificateUntrusted,
                    BadSecurityChecksFailed,
                    BadSecurityPolicyRejected,
                ) as exc:
                    _logger.warning("Reconnect failed with security error %r; refreshing endpoints", exc)
                    await self._refresh_endpoints_quiet()
                except Exception as exc:
                    _logger.warning("Reconnect attempt failed: %r; retrying in %.1fs", exc, delay)
                else:
                    await self._finalize_reconnect(reused)
                    return True
                self.uaclient.enter_reconnecting()
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._reconnect_max_delay)
            return False
        finally:
            _supervisor_owns_requests.reset(token)

    async def _finalize_reconnect(self, reused: bool) -> None:
        self._subscriptions = [s for s in self._subscriptions if not s.is_deleted]
        try:
            await self._recreate_subscriptions()
        except Exception:
            _logger.exception("Subscription recreation failed; continuing")
        _logger.info("Reconnected successfully (session %s)", "reused" if reused else "recreated")

    async def _try_reactivate_existing_session(self) -> bool:
        """Open new socket+channel; try to re-activate the existing session.

        Returns True if the existing session was reactivated (subscriptions still
        alive on the server). Returns False if a fresh session had to be created.
        Raises on transport/channel-level failures so the outer loop can retry.
        """
        had_session = self.uaclient.has_session
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
            if had_session and await self._reactivate_session():
                return True
            await self._create_and_activate_session()
            self._start_renew_loop()
        except Exception:
            self.disconnect_socket()
            raise
        return False

    async def _reactivate_session(self) -> bool:
        """Bind the existing token to the new channel and try ActivateSession.

        Returns True if the server still held the session; False (after closing it)
        when a fresh CreateSession is needed.
        """
        self.uaclient.session.rebind_authentication_token()
        try:
            await self._activate_with_credentials()
        except BadSessionIdInvalid:
            _logger.info("Server forgot session; falling back to create+activate")
        except Exception:
            _logger.info("Re-activate failed; falling back to create+activate", exc_info=True)
        else:
            self.uaclient.ensure_publish_loop()
            self._start_renew_loop()
            return True
        await self._close_session_quiet()
        return False

    async def _refresh_endpoints_quiet(self) -> None:
        try:
            await self.connect_and_get_server_endpoints()
        except Exception:
            _logger.debug("GetEndpoints refresh during reconnect failed", exc_info=True)

    async def _teardown_transport_only(self) -> None:
        """Cancel the channel-renew loop and drop the socket; leave the session intact.

        We deliberately do NOT call close_session here: spec Part 4 §6.7 reconnect
        keeps the session alive server-side so ActivateSession on a new channel can
        reuse it. close_session only runs in the fallback path when the server
        rejects the reactivate.
        """
        await self._cancel_task(self._renew_channel_task)
        self._renew_channel_task = None
        if self.uaclient.has_transport:
            self.uaclient.disconnect_socket()

    async def _recreate_subscriptions(self) -> None:
        live = [s for s in self._subscriptions if not s.is_deleted]
        self._subscriptions = live
        for sub in live:
            try:
                await sub.restore()
            except Exception:
                _logger.exception("Failed to restore subscription")

    async def _close_session_quiet(self) -> None:
        # Goes through UaClient, not Client.close_session, so it does NOT cancel the
        # supervisor task; safe to call from inside the reconnect retry loop.
        try:
            await self.uaclient.close_session(False)
        except Exception:
            _logger.debug("close_session during cleanup raised", exc_info=True)

    async def _close_secure_channel_quiet(self) -> None:
        try:
            await self.uaclient.close_secure_channel()
        except Exception:
            _logger.debug("close_secure_channel during cleanup raised", exc_info=True)

    async def _renew_channel_loop(self) -> None:
        """
        Renew the SecureChannel before the SecureChannelTimeout will happen.
        In theory, we could do that only if no session activity,
        but it does not cost much.
        """
        try:
            # Part4 5.5.2.1:
            # Clients should request a new SecurityToken after 75 % of its lifetime has elapsed
            duration = self.secure_channel_timeout * 0.75 / 1000
            while not self.uaclient.is_disconnect_requested:
                await asyncio.sleep(duration)
                _logger.debug("renewing channel")
                await self.open_secure_channel(renew=True)
                self.uaclient.revolve_security_token()
        except ConnectionError as e:
            _logger.info("connection error  in watchdog loop %s", e, exc_info=True)
            raise
        except Exception:
            _logger.exception("Error while renewing session")
            raise

    def server_policy(self, token_type: ua.UserTokenType) -> ua.UserTokenPolicy:
        """
        Find UserTokenPolicy by token_type.
        If SecurityPolicyUri is empty, use default SecurityPolicyUri
        of the endpoint
        """
        for policy in self._policy_ids:
            if policy.TokenType == token_type:
                if policy.SecurityPolicyUri:
                    return policy
                # empty URI means "use this endpoint's policy URI"
                return dataclasses.replace(policy, SecurityPolicyUri=self.security_policy.URI)
        return ua.UserTokenPolicy(TokenType=token_type, SecurityPolicyUri=self.security_policy.URI)

    async def activate_session(
        self,
        username: str | None = None,
        password: str | None = None,
        certificate: x509.Certificate | None = None,
    ) -> ua.ActivateSessionResult:
        """
        Activate session using either username and password or private_key
        """
        user_certificate = certificate
        params = ua.ActivateSessionParameters()
        challenge = b""
        if self.security_policy.peer_certificate is not None:
            challenge += self.security_policy.peer_certificate
        if self._server_nonce is not None:
            challenge += self._server_nonce
        if self.security_policy.AsymmetricSignatureURI:
            params.ClientSignature.Algorithm = self.security_policy.AsymmetricSignatureURI
        else:
            params.ClientSignature.Algorithm = security_policies.SecurityPolicyBasic256Sha256.AsymmetricSignatureURI
        params.ClientSignature.Signature = self.security_policy.asymmetric_cryptography.signature(challenge)
        params.LocaleIds = self._locale
        if not username and not (user_certificate and self.user_private_key):
            self._add_anonymous_auth(params)
        elif user_certificate:
            self._add_certificate_auth(params, user_certificate, challenge, self.user_certificate_chain)
        else:
            self._add_user_auth(params, username, password)
        res = await self.uaclient.activate_session(params)
        self._server_nonce = res.ServerNonce
        return res

    def _add_anonymous_auth(self, params: ua.ActivateSessionParameters) -> None:
        params.UserIdentityToken = ua.AnonymousIdentityToken()
        params.UserIdentityToken.PolicyId = self.server_policy(ua.UserTokenType.Anonymous).PolicyId

    def _add_certificate_auth(
        self,
        params: ua.ActivateSessionParameters,
        certificate: x509.Certificate,
        challenge: bytes,
        certificate_chain: list[x509.Certificate] | None = None,
    ) -> None:
        params.UserIdentityToken = ua.X509IdentityToken()
        params.UserIdentityToken.CertificateData = uacrypto.der_from_x509(certificate)
        certificate_chain = certificate_chain or []
        for cert in certificate_chain:
            params.UserIdentityToken.CertificateData += uacrypto.der_from_x509(cert)
        # specs part 4, 5.6.3.1: the data to sign is created by appending
        # the last serverNonce to the serverCertificate
        policy = self.server_policy(ua.UserTokenType.Certificate)
        sig, alg = security_policies.sign_asymmetric(self.user_private_key, challenge, policy.SecurityPolicyUri)
        params.UserIdentityToken.PolicyId = policy.PolicyId
        params.UserTokenSignature.Algorithm = alg
        params.UserTokenSignature.Signature = sig

    def _add_user_auth(self, params: ua.ActivateSessionParameters, username: str | None, password: str | None) -> None:
        params.UserIdentityToken = ua.UserNameIdentityToken()
        params.UserIdentityToken.UserName = username
        policy = self.server_policy(ua.UserTokenType.UserName)
        if not policy.SecurityPolicyUri or policy.SecurityPolicyUri == security_policies.SecurityPolicyNone.URI:
            # see specs part 4, 7.36.3: if the token is NOT encrypted,
            # then the password only contains UTF-8 encoded password
            # and EncryptionAlgorithm is null
            if password:
                if self.security_policy.Mode != ua.MessageSecurityMode.SignAndEncrypt:
                    _logger.warning("Sending plain-text password")
                params.UserIdentityToken.Password = password.encode("utf8")
            params.UserIdentityToken.EncryptionAlgorithm = None
        elif password:
            data, uri = self._encrypt_password(password, policy.SecurityPolicyUri)
            params.UserIdentityToken.Password = data
            params.UserIdentityToken.EncryptionAlgorithm = uri
        params.UserIdentityToken.PolicyId = policy.PolicyId

    def _encrypt_password(self, password: str, policy_uri: str) -> tuple[bytes, str]:
        pubkey = uacrypto.x509_from_der(self.security_policy.peer_certificate).public_key()
        # see specs part 4, 7.36.3: if the token is encrypted, password
        # shall be converted to UTF-8 and serialized with server nonce
        passwd = password.encode("utf8")
        if self._server_nonce is not None:
            passwd += self._server_nonce
        etoken = ua.ua_binary.Primitives.Bytes.pack(passwd)
        data, uri = security_policies.encrypt_asymmetric(pubkey, etoken, policy_uri)
        return data, uri

    async def close_session(self) -> None:
        """
        Close session
        """
        self.uaclient.request_disconnect()
        await self._cancel_task(self._stale_watchdog_task)
        self._stale_watchdog_task = None
        await self._cancel_task(self._supervisor_task)
        self._supervisor_task = None
        # Disable the pre-request hook for the close path so it doesn't block.
        self.uaclient.pre_request_hook = None
        await self._cancel_task(self._renew_channel_task)
        self._renew_channel_task = None
        return await self.uaclient.close_session(True)

    @staticmethod
    async def _cancel_task(task: asyncio.Task[Any] | None) -> None:
        """Cancel a task, await its exit, and swallow CancelledError / shutdown noise."""
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    def get_root_node(self) -> Node:
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.RootFolder))

    def get_objects_node(self) -> Node:
        _logger.info("get_objects_node")
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.ObjectsFolder))

    def get_server_node(self) -> Node:
        return self.get_node(ua.FourByteNodeId(ua.ObjectIds.Server))

    def get_node(self, nodeid: Node | ua.NodeId | str | int) -> Node:
        """
        Get node using NodeId object or a string representing a NodeId.
        """
        return Node(self.uaclient.session, nodeid)

    async def create_subscription(
        self,
        period: ua.CreateSubscriptionParameters | float,
        handler: SubscriptionHandler | None = None,
        publishing: bool = True,
        *,
        queue_maxsize: int = 1000,
        overflow: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> Subscription:
        """
        Create a subscription.

        Returns a Subscription object which can be used either:
        - **Callback mode** (legacy): pass a `handler` and implement
          `datachange_notification` / `event_notification` /
          `status_change_notification`. The handler is invoked from a task
          so the publish loop never awaits user code.
        - **Iterator mode**: pass `handler=None` and use the subscription as
          an async context manager + async iterator:

              async with sub:
                  await sub.subscribe_data_change(node)
                  async for ev in sub:
                      ...

          `queue_maxsize` bounds the internal buffer; `overflow` selects what
          happens when the consumer falls behind.

        :param period: Either a publishing interval in milliseconds or a
            `CreateSubscriptionParameters` instance.
        :param handler: Optional callback handler. If None, iterator mode.
        :param queue_maxsize: Iterator-mode queue bound (default 1000).
        :param overflow: Iterator-mode overflow policy (default DROP_OLDEST).
        """
        if isinstance(period, ua.CreateSubscriptionParameters):
            params = period
        else:
            params = ua.CreateSubscriptionParameters()
            params.RequestedPublishingInterval = period
            params.RequestedLifetimeCount = 10000
            params.RequestedMaxKeepAliveCount = self.get_keepalive_count(period)
            params.MaxNotificationsPerPublish = 10000
            params.PublishingEnabled = publishing
            params.Priority = 0
        subscription = Subscription(
            self.uaclient.session,
            params,
            handler,
            queue_maxsize=queue_maxsize,
            overflow=overflow,
        )
        # Wire the DISCONNECT overflow policy to the supervisor's reconnect path.
        subscription.set_overflow_disconnect_handler(self.uaclient.notify_transport_lost)
        results = await subscription.init()
        new_params = self.get_subscription_revised_params(params, results)
        if new_params:
            results = await subscription.update(new_params)
            _logger.info("Result from subscription update: %s", results)
        self._subscriptions.append(subscription)
        return subscription

    def get_subscription_revised_params(
        self,
        params: ua.CreateSubscriptionParameters,
        results: ua.CreateSubscriptionResult,
    ) -> ua.ModifySubscriptionParameters | None:
        if (
            results.RevisedPublishingInterval == params.RequestedPublishingInterval
            and results.RevisedLifetimeCount == params.RequestedLifetimeCount
            and results.RevisedMaxKeepAliveCount == params.RequestedMaxKeepAliveCount
        ):
            return None
        _logger.warning("Revised values returned differ from subscription values: %s", results)
        revised_interval = results.RevisedPublishingInterval
        new_keepalive_count = self.get_keepalive_count(revised_interval)
        if (
            revised_interval != params.RequestedPublishingInterval
            and new_keepalive_count != params.RequestedMaxKeepAliveCount
        ):
            _logger.info(
                "KeepAliveCount will be updated to %s for consistency with RevisedPublishInterval",
                new_keepalive_count,
            )
            modified_params = ua.ModifySubscriptionParameters()
            copy_dataclass_attr(params, modified_params)
            modified_params.RequestedMaxKeepAliveCount = new_keepalive_count
            modified_params.SubscriptionId = results.SubscriptionId
            modified_params.RequestedPublishingInterval = results.RevisedPublishingInterval
            modified_params.RequestedLifetimeCount = results.RevisedLifetimeCount
            return modified_params
        return None

    async def delete_subscriptions(self, subscription_ids: Iterable[int]) -> list[ua.StatusCode]:
        """
        Deletes the provided list of subscription_ids
        """
        return await self.uaclient.delete_subscriptions(subscription_ids)

    def get_keepalive_count(self, period: float) -> int:
        """
        We request the server to send a Keepalive notification when
        no notification has been received for 75% of the session lifetime.
        This is especially useful to keep the session up
        when self.session_timeout < self.secure_channel_timeout.

        Part4 5.13.2: If the requested value is 0, the Server
        shall revise with the smallest supported keep-alive count.
        """
        if not period:
            return 0
        return int((self.session_timeout / period) * 0.75)

    async def get_namespace_array(self) -> list[str]:
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        return await ns_node.read_value()

    async def get_namespace_index(self, uri: str) -> int:
        uries = await self.get_namespace_array()
        _logger.info("get_namespace_index %s %r", type(uries), uries)
        return uries.index(uri)

    async def delete_nodes(
        self, nodes: Iterable[Node], recursive: bool = False
    ) -> tuple[list[Node], list[ua.StatusCode]]:
        return await delete_nodes(self.uaclient.session, nodes, recursive)

    async def import_xml(
        self,
        path: str | None = None,
        xmlstring: str | None = None,
        strict_mode: bool = True,
        auto_load_definitions: bool = True,
    ) -> list[ua.NodeId]:
        """
        Import nodes defined in xml
        """
        importer = XmlImporter(self, strict_mode=strict_mode, auto_load_definitions=auto_load_definitions)
        return await importer.import_xml(path, xmlstring)

    async def export_xml(self, nodes: Iterable[Node], path: str, export_values: bool = False) -> None:
        """
        Export defined nodes to xml
        :param export_values: exports values from variants
        """
        exp = XmlExporter(self, export_values=export_values)
        await exp.build_etree(nodes)
        await exp.write_xml(path)

    async def register_namespace(self, uri: str) -> int:
        """
        Register a new namespace. Nodes should in custom namespace, not 0.
        This method is mainly implemented for symmetry with server
        """
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        uries = await ns_node.read_value()
        if uri in uries:
            return uries.index(uri)
        uries.append(uri)
        await ns_node.write_value(uries)
        return len(uries) - 1

    async def load_type_definitions(self, nodes: Iterable[Node] | None = None) -> Any:
        """
        Load custom types (custom structures/extension objects) definition from server
        Generate Python classes for custom structures/extension objects defined in server
        These classes will available in ua module
        WARNING: protocol has changed in 1.04. use load_data_type_definitions()
        """
        _logger.warning("Deprecated since spec 1.04, call load_data_type_definitions")
        return await load_type_definitions(self, nodes)

    async def load_data_type_definitions(
        self, node: Node | None = None, overwrite_existing: bool = False
    ) -> dict[str, type]:
        """
        Load custom types (custom structures/extension objects) definition from server
        Generate Python classes for custom structures/extension objects defined in server
        These classes will be available in ua module
        """
        return await load_data_type_definitions(self, node, overwrite_existing=overwrite_existing)

    async def load_enums(self) -> dict[str, type]:
        """
        generate Python enums for custom enums on server.
        This enums will be available in ua module
        """
        _logger.warning("Deprecated since spec 1.04, call load_data_type_definitions")
        return await load_enums(self)

    async def register_nodes(self, nodes: Iterable[Node]) -> list[Node]:
        """
        Register nodes for faster read and write access (if supported by server)
        Rmw: This call modifies the nodeid of the nodes, the original nodeid is
        available as node.basenodeid
        """
        nodeids = [node.nodeid for node in nodes]
        nodeids = await self.uaclient.register_nodes(nodeids)
        for node, nodeid in zip(nodes, nodeids):
            node.basenodeid = node.nodeid
            node.nodeid = nodeid
        return list(nodes)

    async def unregister_nodes(self, nodes: Iterable[Node]) -> None:
        """
        Unregister nodes
        """
        nodeids = [node.nodeid for node in nodes]
        await self.uaclient.unregister_nodes(nodeids)
        for node in nodes:
            if not node.basenodeid:
                continue
            node.nodeid = node.basenodeid
            node.basenodeid = None

    async def read_attributes(
        self, nodes: Iterable[Node], attr: ua.AttributeIds = ua.AttributeIds.Value
    ) -> list[ua.DataValue]:
        """
        Read the attributes of multiple nodes.
        """
        nodeids = [node.nodeid for node in nodes]
        return await self.uaclient.read_attributes(nodeids, attr)

    async def read_values(self, nodes: Iterable[Node]) -> list[Any]:
        """
        Read the value of multiple nodes in one ua call.
        """
        res = await self.read_attributes(nodes, attr=ua.AttributeIds.Value)
        return [r.Value.Value if r.Value is not None else None for r in res]

    async def write_values(
        self, nodes: Iterable[Node], values: Iterable[Any], raise_on_partial_error: bool = True
    ) -> list[ua.StatusCode]:
        """
        Write values to multiple nodes in one ua call
        """
        nodeids = [node.nodeid for node in nodes]
        dvs = [value_to_datavalue(val) for val in values]
        results = await self.uaclient.write_attributes(nodeids, dvs, ua.AttributeIds.Value)
        if raise_on_partial_error:
            for result in results:
                result.check()
        return results

    get_values = read_values  # legacy compatibility
    set_values = write_values  # legacy compatibility

    async def browse_nodes(self, nodes: Iterable[Node]) -> list[tuple[Node, ua.BrowseResult]]:
        """
        Browses multiple nodes in one ua call
        returns a List of Tuples(Node, BrowseResult)
        """
        nodestobrowse = []
        for node in nodes:
            desc = ua.BrowseDescription()
            desc.NodeId = node.nodeid
            desc.ResultMask = ua.BrowseResultMask.All
            nodestobrowse.append(desc)
        parameters = ua.BrowseParameters()
        parameters.View = ua.ViewDescription()
        parameters.RequestedMaxReferencesPerNode = 0
        parameters.NodesToBrowse = nodestobrowse
        results = await self.uaclient.browse(parameters)
        return list(zip(nodes, results))

    async def translate_browsepaths(
        self, starting_node: ua.NodeId, relative_paths: Iterable[ua.RelativePath | str]
    ) -> list[ua.BrowsePathResult]:
        bpaths = []
        for p in relative_paths:
            try:
                rpath = ua.RelativePath.from_string(p) if isinstance(p, str) else p
            except ValueError as e:
                raise ua.UaStringParsingError(f"Failed to parse one of RelativePath: {p}") from e
            bpath = ua.BrowsePath()
            bpath.StartingNode = starting_node
            bpath.RelativePath = rpath
            bpaths.append(bpath)

        return await self.uaclient.translate_browsepaths_to_nodeids(bpaths)
