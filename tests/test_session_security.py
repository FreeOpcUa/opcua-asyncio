from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from asyncua import Client, Server, ua
from asyncua.common.utils import ServiceError
from asyncua.crypto.permission_rules import User, UserRole
from asyncua.server.user_managers import UserManager

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio

EXAMPLE_PATH = Path(__file__).parent.parent / "examples"
SERVER_CERT = EXAMPLE_PATH / "certificate-example.der"
SERVER_KEY = EXAMPLE_PATH / "private-key-example.pem"
PEER_1 = (
    EXAMPLE_PATH / "certificates" / "peer-certificate-example-1.der",
    EXAMPLE_PATH / "certificates" / "peer-private-key-example-1.pem",
)
PEER_2 = (
    EXAMPLE_PATH / "certificates" / "peer-certificate-example-2.der",
    EXAMPLE_PATH / "certificates" / "peer-private-key-example-2.pem",
)


class PasswordUserManager(UserManager):
    def get_user(
        self, iserver: Any, username: str | None = None, password: str | None = None, certificate: Any = None
    ) -> User | None:
        if username == "operator" and password == "secret":
            return User(role=UserRole.Admin, name="operator")
        if username is None:
            return User(role=UserRole.User)
        return None


async def _start_server(secure: bool) -> tuple[Server, str]:
    url = f"opc.tcp://127.0.0.1:{find_free_port()}"
    srv = Server(user_manager=PasswordUserManager())
    await srv.init()
    srv.set_endpoint(url)
    if secure:
        srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
        await srv.load_certificate(SERVER_CERT)
        await srv.load_private_key(SERVER_KEY)
    else:
        srv.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    await srv.start()
    return srv, url


@pytest.fixture
async def open_server() -> AsyncIterator[tuple[Server, str]]:
    srv, url = await _start_server(secure=False)
    yield srv, url
    await srv.stop()


@pytest.fixture
async def secure_server() -> AsyncIterator[tuple[Server, str]]:
    srv, url = await _start_server(secure=True)
    yield srv, url
    await srv.stop()


async def _secure_client(url: str, peer: tuple[Path, Path]) -> Client:
    client = Client(url)
    await client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{peer[0]},{peer[1]}")
    return client


async def _open_channel(client: Client) -> None:
    await client.connect_socket()
    await client.send_hello()
    await client.open_secure_channel()


async def _activate_with_token(client: Client, token: ua.NodeId) -> None:
    client.uaclient.session.restore_authentication_token(token)
    params = ua.ActivateSessionParameters()
    params.UserIdentityToken = ua.AnonymousIdentityToken(PolicyId="anonymous")
    params.ClientSignature = ua.SignatureData()
    await client.uaclient.activate_session(params)


async def _read_server_state(client: Client) -> bool:
    params = ua.ReadParameters()
    params.NodesToRead = [
        ua.ReadValueId(NodeId=ua.NodeId(ua.ObjectIds.Server_ServerStatus_State), AttributeId=ua.AttributeIds.Value)
    ]
    status = (await client.uaclient.read(params))[0].StatusCode
    return status is not None and status.is_good()


async def test_authentication_tokens_are_random_bytestrings(open_server: tuple[Server, str]) -> None:
    _srv, url = open_server
    async with Client(url) as first, Client(url) as second:
        tokens = [first.uaclient.session.authentication_token, second.uaclient.session.authentication_token]
    assert all(token.NodeIdType == ua.NodeIdType.ByteString for token in tokens)
    assert all(len(token.Identifier) == 32 for token in tokens)
    assert tokens[0] != tokens[1]


async def test_failed_activation_on_new_channel_does_not_bind_session(open_server: tuple[Server, str]) -> None:
    srv, url = open_server
    victim = Client(url)
    victim.set_user("operator")
    victim.set_password("secret")
    async with victim:
        attacker = Client(url)
        await _open_channel(attacker)
        try:
            with pytest.raises(ua.uaerrors.BadIdentityTokenRejected):
                await _activate_with_token(attacker, victim.uaclient.session.authentication_token)
            with pytest.raises(ua.UaStatusCodeError):
                await _read_server_state(attacker)
            node = await srv.nodes.objects.add_variable(2, "Setpoint", 1.0)
            await node.set_writable()
            with pytest.raises(ua.UaStatusCodeError):
                await attacker.get_node(node.nodeid).write_value(666.0)
            assert await node.read_value() == 1.0
            assert await _read_server_state(victim)
        finally:
            attacker.disconnect_socket()


async def test_session_cannot_move_to_channel_with_other_certificate(secure_server: tuple[Server, str]) -> None:
    _srv, url = secure_server
    victim = await _secure_client(url, PEER_1)
    async with victim:
        attacker = await _secure_client(url, PEER_2)
        await _open_channel(attacker)
        try:
            with pytest.raises(ua.uaerrors.BadSecurityChecksFailed):
                await _activate_with_token(attacker, victim.uaclient.session.authentication_token)
            with pytest.raises(ua.UaStatusCodeError):
                await _read_server_state(attacker)
            assert await _read_server_state(victim)
        finally:
            attacker.disconnect_socket()


async def test_moved_session_rejects_requests_on_old_channel(open_server: tuple[Server, str]) -> None:
    _srv, url = open_server
    async with Client(url) as original:
        token = original.uaclient.session.authentication_token
        replacement = Client(url)
        await _open_channel(replacement)
        try:
            await _activate_with_token(replacement, token)
            assert await _read_server_state(replacement)
            with pytest.raises(ua.uaerrors.BadSecureChannelIdInvalid):
                await _read_server_state(original)
        finally:
            replacement.disconnect_socket()


@pytest.mark.parametrize("client_certificate", [None, PEER_2[0].read_bytes()], ids=["missing", "other"])
async def test_create_session_certificate_must_match_channel(
    secure_server: tuple[Server, str], client_certificate: bytes | None
) -> None:
    srv, url = secure_server
    validated = []

    async def reject_unknown(certificate: Any, app_description: Any) -> None:
        validated.append(certificate)
        raise ServiceError(ua.StatusCodes.BadCertificateUntrusted)

    srv.set_certificate_validator(reject_unknown)
    client = await _secure_client(url, PEER_1)
    create_session = client.uaclient.create_session

    async def create_session_with_other_certificate(params: ua.CreateSessionParameters) -> ua.CreateSessionResult:
        params.ClientCertificate = client_certificate
        return await create_session(params)

    client.uaclient.create_session = create_session_with_other_certificate
    with pytest.raises(ua.uaerrors.BadSecurityChecksFailed):
        await client.connect()
    await client.disconnect()
    assert validated == []
