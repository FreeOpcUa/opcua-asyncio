import asyncio
import logging
from typing import Union, Coroutine, Optional
from urllib.parse import urlparse

from asyncua import ua
from .ua_client import UaClient
from ..common.xmlimporter import XmlImporter
from ..common.xmlexporter import XmlExporter
from ..common.node import Node
from ..common.manage_nodes import delete_nodes
from ..common.subscription import Subscription
from ..common.shortcuts import Shortcuts
from ..common.structures import load_type_definitions, load_enums
from ..common.structures104 import load_data_type_definitions
from ..common.utils import create_nonce
from ..common.ua_utils import value_to_datavalue
from ..crypto import uacrypto, security_policies

_logger = logging.getLogger(__name__)


class Client:
    """
    High level client to connect to an OPC-UA server.
    This class makes it easy to connect and browse address space.
    It attempts to expose as much functionality as possible
    but if you want more flexibility it is possible and advised to
    use UaClient object, available as self.uaclient
    which offers the raw OPC-UA services interface.
    """
    def __init__(self, url: str, timeout: int = 4, loop=None):
        """
        :param url: url of the server.
            if you are unsure of url, write at least hostname
            and port and call get_endpoints
        :param timeout:
            Each request sent to the server expects an answer within this
            time. The timeout is specified in seconds.
        Some other client parameters can be changed by setting
        attributes on the constructed object:
        See the source code for the exhaustive list.
        """
        self.loop = loop or asyncio.get_event_loop()
        self.server_url = urlparse(url)
        # take initial username and password from the url
        self._username = self.server_url.username
        self._password = self.server_url.password
        self.name = "Pure Python Async. Client"
        self.description = self.name
        self.application_uri = "urn:freeopcua:client"
        self.product_uri = "urn:freeopcua.github.io:client"
        self.security_policy = ua.SecurityPolicy()
        self.secure_channel_id = None
        self.secure_channel_timeout = 3600000  # 1 hour
        self.session_timeout = 3600000  # 1 hour
        self._policy_ids = []
        self.uaclient: UaClient = UaClient(timeout, loop=self.loop)
        self.user_certificate = None
        self.user_private_key = None
        self._server_nonce = None
        self._session_counter = 1
        self.nodes = Shortcuts(self.uaclient)
        self.max_messagesize = 0  # No limits
        self.max_chunkcount = 0  # No limits
        self._renew_channel_task = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    def __str__(self):
        return f"Client({self.server_url.geturl()})"

    __repr__ = __str__

    @staticmethod
    def find_endpoint(endpoints, security_mode, policy_uri):
        """
        Find endpoint with required security mode and policy URI
        """
        _logger.info("find_endpoint %r %r %r", endpoints, security_mode, policy_uri)
        for ep in endpoints:
            if (ep.EndpointUrl.startswith(ua.OPC_TCP_SCHEME) and ep.SecurityMode == security_mode and ep.SecurityPolicyUri == policy_uri):
                return ep
        raise ua.UaError(f"No matching endpoints: {security_mode}, {policy_uri}")

    def set_user(self, username: str):
        """
        Set user name for the connection.
        initial user from the URL will be overwritten
        """
        self._username = username

    def set_password(self, pwd: str):
        """
        Set user password for the connection.
        initial password from the URL will be overwritten
        """
        if not isinstance(pwd, str):
            raise TypeError(f"Password must be a string, got {pwd} of type {type(pwd)}")
        self._password = pwd

    async def set_security_string(self, string: str):
        """
        Set SecureConnection mode.
        :param string: Mode format ``Policy,Mode,certificate,private_key[,server_private_key]``
        where:
        - ``Policy`` is ``Basic128Rsa15``, ``Basic256`` or ``Basic256Sha256``
        - ``Mode`` is ``Sign`` or ``SignAndEncrypt``
        - ``certificate`` and ``server_private_key`` are paths to ``.pem`` or ``.der`` files
        - ``private_key`` may be a path to a ``.pem`` or ``.der`` file or a conjunction of ``path``::``password`` where
          ``password`` is the private key password.
        Call this before connect()
        """
        if not string:
            return
        parts = string.split(",")
        if len(parts) < 4:
            raise ua.UaError(f"Wrong format: `{string}`, expected at least 4 comma-separated values")

        if '::' in parts[3]:  # if the filename contains a colon, assume it's a conjunction and parse it
            parts[3], client_key_password = parts[3].split('::')
        else:
            client_key_password = None

        policy_class = getattr(security_policies, f"SecurityPolicy{parts[0]}")
        mode = getattr(ua.MessageSecurityMode, parts[1])
        return await self.set_security(policy_class, parts[2], parts[3], client_key_password, parts[4] if len(parts) >= 5 else None, mode)

    async def set_security(
        self,
        policy: ua.SecurityPolicy,
        certificate: Union[str, uacrypto.CertProperties],
        private_key: Union[str, uacrypto.CertProperties],
        private_key_password: Optional[Union[str, bytes]] = None,
        server_certificate: Optional[Union[str, uacrypto.CertProperties]] = None,
        mode: ua.MessageSecurityMode = ua.MessageSecurityMode.SignAndEncrypt,
    ):
        """
        Set SecureConnection mode.
        Call this before connect()
        """
        if server_certificate is None:
            # load certificate from server's list of endpoints
            endpoints = await self.connect_and_get_server_endpoints()
            endpoint = Client.find_endpoint(endpoints, mode, policy.URI)
            server_certificate = uacrypto.x509_from_der(endpoint.ServerCertificate)
        elif not isinstance(server_certificate, uacrypto.CertProperties):
            server_certificate = uacrypto.CertProperties(server_certificate)
        if not isinstance(certificate, uacrypto.CertProperties):
            certificate = uacrypto.CertProperties(certificate)
        if not isinstance(private_key, uacrypto.CertProperties):
            private_key = uacrypto.CertProperties(private_key, password=private_key_password)
        return await self._set_security(policy, certificate, private_key, server_certificate, mode)

    async def _set_security(
        self,
        policy: ua.SecurityPolicy,
        certificate: uacrypto.CertProperties,
        private_key: uacrypto.CertProperties,
        server_cert: uacrypto.CertProperties,
        mode: ua.MessageSecurityMode = ua.MessageSecurityMode.SignAndEncrypt,
    ):

        if isinstance(server_cert, uacrypto.CertProperties):
            server_cert = await uacrypto.load_certificate(server_cert.path, server_cert.extension)
        cert = await uacrypto.load_certificate(certificate.path, certificate.extension)
        pk = await uacrypto.load_private_key(
            private_key.path,
            private_key.password,
            private_key.extension,
        )
        self.security_policy = policy(server_cert, cert, pk, mode)
        self.uaclient.set_security(self.security_policy)

    async def load_client_certificate(self, path: str, extension: Optional[str] = None):
        """
        load our certificate from file, either pem or der
        """
        self.user_certificate = await uacrypto.load_certificate(path, extension)

    async def load_private_key(self, path: str, password: Optional[Union[str, bytes]] = None, extension: Optional[str] = None):
        """
        Load user private key. This is used for authenticating using certificate
        """
        self.user_private_key = await uacrypto.load_private_key(path, password, extension)

    async def connect_and_get_server_endpoints(self):
        """
        Connect, ask server for endpoints, and disconnect
        """
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
            endpoints = await self.get_endpoints()
            await self.close_secure_channel()
        finally:
            self.disconnect_socket()
        return endpoints

    async def connect_and_find_servers(self):
        """
        Connect, ask server for a list of known servers, and disconnect
        """
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()  # spec says it should not be necessary to open channel
            servers = await self.find_servers()
            await self.close_secure_channel()
        finally:
            self.disconnect_socket()
        return servers

    async def connect_and_find_servers_on_network(self):
        """
        Connect, ask server for a list of known servers on network, and disconnect
        """
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
            servers = await self.find_servers_on_network()
            await self.close_secure_channel()
        finally:
            self.disconnect_socket()
        return servers

    async def connect(self):
        """
        High level method
        Connect, create and activate session
        """
        _logger.info("connect")
        await self.connect_socket()
        try:
            await self.send_hello()
            await self.open_secure_channel()
            await self.create_session()
        except Exception:
            # clean up open socket
            self.disconnect_socket()
            raise
        await self.activate_session(username=self._username, password=self._password, certificate=self.user_certificate)

    async def disconnect(self):
        """
        High level method
        Close session, secure channel and socket
        """
        _logger.info("disconnect")
        try:
            await self.close_session()
            await self.close_secure_channel()
        finally:
            self.disconnect_socket()

    async def connect_socket(self):
        """
        connect to socket defined in url
        """
        await self.uaclient.connect_socket(self.server_url.hostname, self.server_url.port)

    def disconnect_socket(self):
        self.uaclient.disconnect_socket()

    async def send_hello(self):
        """
        Send OPC-UA hello to server
        """
        ack = await self.uaclient.send_hello(self.server_url.geturl(), self.max_messagesize, self.max_chunkcount)
        if isinstance(ack, ua.UaStatusCodeError):
            raise ack

    async def open_secure_channel(self, renew=False):
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
        params.ClientNonce = create_nonce(self.security_policy.symmetric_key_size)
        result = await self.uaclient.open_secure_channel(params)
        if self.secure_channel_timeout != result.SecurityToken.RevisedLifetime:
            _logger.info("Requested secure channel timeout to be %dms, got %dms instead", self.secure_channel_timeout, result.SecurityToken.RevisedLifetime)
            self.secure_channel_timeout = result.SecurityToken.RevisedLifetime

    async def close_secure_channel(self):
        return await self.uaclient.close_secure_channel()

    async def get_endpoints(self) -> list:
        """Get a list of OPC-UA endpoints."""

        params = ua.GetEndpointsParameters()
        params.EndpointUrl = self.server_url.geturl()
        return await self.uaclient.get_endpoints(params)

    async def register_server(self, server, discovery_configuration=None):
        """
        register a server to discovery server
        if discovery_configuration is provided, the newer register_server2 service call is used
        """
        serv = ua.RegisteredServer()
        serv.ServerUri = server.get_application_uri()
        serv.ProductUri = server.product_uri
        serv.DiscoveryUrls = [server.endpoint.geturl()]
        serv.ServerType = server.application_type
        serv.ServerNames = [ua.LocalizedText(server.name)]
        serv.IsOnline = True
        if discovery_configuration:
            params = ua.RegisterServer2Parameters()
            params.Server = serv
            params.DiscoveryConfiguration = discovery_configuration
            return await self.uaclient.register_server2(params)
        return await self.uaclient.register_server(serv)

    async def find_servers(self, uris=None):
        """
        send a FindServer request to the server. The answer should be a list of
        servers the server knows about
        A list of uris can be provided, only server having matching uris will be returned
        """
        if uris is None:
            uris = []
        params = ua.FindServersParameters()
        params.EndpointUrl = self.server_url.geturl()
        params.ServerUris = uris
        return await self.uaclient.find_servers(params)

    async def find_servers_on_network(self):
        params = ua.FindServersOnNetworkParameters()
        return await self.uaclient.find_servers_on_network(params)

    async def create_session(self):
        """
        send a CreateSessionRequest to server with reasonable parameters.
        If you want o modify settings look at code of this methods
        and make your own
        """
        desc = ua.ApplicationDescription()
        desc.ApplicationUri = self.application_uri
        desc.ProductUri = self.product_uri
        desc.ApplicationName = ua.LocalizedText(self.name)
        desc.ApplicationType = ua.ApplicationType.Client
        params = ua.CreateSessionParameters()
        # at least 32 random bytes for server to prove possession of private key (specs part 4, 5.6.2.2)
        nonce = create_nonce(32)
        params.ClientNonce = nonce
        params.ClientCertificate = self.security_policy.host_certificate
        params.ClientDescription = desc
        params.EndpointUrl = self.server_url.geturl()
        params.SessionName = f"{self.description} Session{self._session_counter}"
        # Requested maximum number of milliseconds that a Session should remain open without activity
        params.RequestedSessionTimeout = self.session_timeout
        params.MaxResponseMessageSize = 0  # means no max size
        response = await self.uaclient.create_session(params)
        if self.security_policy.host_certificate is None:
            data = nonce
        else:
            data = self.security_policy.host_certificate + nonce
        self.security_policy.asymmetric_cryptography.verify(data, response.ServerSignature.Signature)
        self._server_nonce = response.ServerNonce
        if not self.security_policy.peer_certificate:
            self.security_policy.peer_certificate = response.ServerCertificate
        elif self.security_policy.peer_certificate != response.ServerCertificate:
            raise ua.UaError("Server certificate mismatch")
        # remember PolicyId's: we will use them in activate_session()
        ep = Client.find_endpoint(response.ServerEndpoints, self.security_policy.Mode, self.security_policy.URI)
        self._policy_ids = ep.UserIdentityTokens
        #  Actual maximum number of milliseconds that a Session shall remain open without activity
        if self.session_timeout != response.RevisedSessionTimeout:
            _logger.warning("Requested session timeout to be %dms, got %dms instead", self.secure_channel_timeout, response.RevisedSessionTimeout)
            self.session_timeout = response.RevisedSessionTimeout
        self._renew_channel_task = self.loop.create_task(self._renew_channel_loop())
        return response

    async def _renew_channel_loop(self):
        """
        Renew the SecureChannel before the SessionTimeout will happen.
        In theory we could do that only if no session activity
        but it does not cost much..
        """
        try:
            duration = min(self.session_timeout, self.secure_channel_timeout) * 0.7 / 1000
            while True:
                # 0.7 is from spec. 0.001 is because asyncio.sleep expects time in seconds
                await asyncio.sleep(duration)
                _logger.debug("renewing channel")
                await self.open_secure_channel(renew=True)
                val = await self.nodes.server_state.read_value()
                _logger.debug("server state is: %s ", val)
        except asyncio.CancelledError:
            pass
        except Exception:
            _logger.exception("Error while renewing session")
            raise

    def server_policy_id(self, token_type, default):
        """
        Find PolicyId of server's UserTokenPolicy by token_type.
        Return default if there's no matching UserTokenPolicy.
        """
        for policy in self._policy_ids:
            if policy.TokenType == token_type:
                return policy.PolicyId
        return default

    def server_policy_uri(self, token_type):
        """
        Find SecurityPolicyUri of server's UserTokenPolicy by token_type.
        If SecurityPolicyUri is empty, use default SecurityPolicyUri
        of the endpoint
        """
        for policy in self._policy_ids:
            if policy.TokenType == token_type:
                if policy.SecurityPolicyUri:
                    return policy.SecurityPolicyUri
                # empty URI means "use this endpoint's policy URI"
                return self.security_policy.URI
        return self.security_policy.URI

    async def activate_session(self, username: str = None, password: str = None, certificate=None):
        """
        Activate session using either username and password or private_key
        """
        params = ua.ActivateSessionParameters()
        challenge = b""
        if self.security_policy.peer_certificate is not None:
            challenge += self.security_policy.peer_certificate
        if self._server_nonce is not None:
            challenge += self._server_nonce
        if self.security_policy.AsymmetricSignatureURI:
            params.ClientSignature.Algorithm = self.security_policy.AsymmetricSignatureURI
        else:
            params.ClientSignature.Algorithm = (security_policies.SecurityPolicyBasic256.AsymmetricSignatureURI)
        params.ClientSignature.Signature = self.security_policy.asymmetric_cryptography.signature(challenge)
        params.LocaleIds.append("en")
        if not username and not certificate:
            self._add_anonymous_auth(params)
        elif certificate:
            self._add_certificate_auth(params, certificate, challenge)
        else:
            self._add_user_auth(params, username, password)
        return await self.uaclient.activate_session(params)

    def _add_anonymous_auth(self, params):
        params.UserIdentityToken = ua.AnonymousIdentityToken()
        params.UserIdentityToken.PolicyId = self.server_policy_id(ua.UserTokenType.Anonymous, "anonymous")

    def _add_certificate_auth(self, params, certificate, challenge):
        params.UserIdentityToken = ua.X509IdentityToken()
        params.UserIdentityToken.CertificateData = uacrypto.der_from_x509(certificate)
        # specs part 4, 5.6.3.1: the data to sign is created by appending
        # the last serverNonce to the serverCertificate
        params.UserTokenSignature = ua.SignatureData()
        # use signature algorithm that was used for certificate generation
        if certificate.signature_hash_algorithm.name == "sha256":
            params.UserIdentityToken.PolicyId = self.server_policy_id(ua.UserTokenType.Certificate, "certificate_basic256sha256")
            sig = uacrypto.sign_sha256(self.user_private_key, challenge)
            params.UserTokenSignature.Algorithm = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
            params.UserTokenSignature.Signature = sig
        else:
            params.UserIdentityToken.PolicyId = self.server_policy_id(ua.UserTokenType.Certificate, "certificate_basic256")
            sig = uacrypto.sign_sha1(self.user_private_key, challenge)
            params.UserTokenSignature.Algorithm = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
            params.UserTokenSignature.Signature = sig

    def _add_user_auth(self, params, username: str, password: str):
        params.UserIdentityToken = ua.UserNameIdentityToken()
        params.UserIdentityToken.UserName = username
        policy_uri = self.server_policy_uri(ua.UserTokenType.UserName)
        if not policy_uri or policy_uri == security_policies.POLICY_NONE_URI:
            # see specs part 4, 7.36.3: if the token is NOT encrypted,
            # then the password only contains UTF-8 encoded password
            # and EncryptionAlgorithm is null
            if self._password:
                _logger.warning("Sending plain-text password")
                params.UserIdentityToken.Password = password.encode("utf8")
            params.UserIdentityToken.EncryptionAlgorithm = None
        elif self._password:
            data, uri = self._encrypt_password(password, policy_uri)
            params.UserIdentityToken.Password = data
            params.UserIdentityToken.EncryptionAlgorithm = uri
        params.UserIdentityToken.PolicyId = self.server_policy_id(ua.UserTokenType.UserName, "username_basic256")

    def _encrypt_password(self, password: str, policy_uri):
        pubkey = uacrypto.x509_from_der(self.security_policy.peer_certificate).public_key()
        # see specs part 4, 7.36.3: if the token is encrypted, password
        # shall be converted to UTF-8 and serialized with server nonce
        passwd = password.encode("utf8")
        if self._server_nonce is not None:
            passwd += self._server_nonce
        etoken = ua.ua_binary.Primitives.Bytes.pack(passwd)
        data, uri = security_policies.encrypt_asymmetric(pubkey, etoken, policy_uri)
        return data, uri

    async def close_session(self) -> Coroutine:
        """
        Close session
        """
        self._renew_channel_task.cancel()
        try:
            await self._renew_channel_task
        except Exception:
            _logger.exception("Error while closing secure channel loop")
        return await self.uaclient.close_session(True)

    def get_root_node(self):
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.RootFolder))

    def get_objects_node(self):
        _logger.info("get_objects_node")
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.ObjectsFolder))

    def get_server_node(self):
        return self.get_node(ua.FourByteNodeId(ua.ObjectIds.Server))

    def get_node(self, nodeid: Union[ua.NodeId, str]) -> Node:
        """
        Get node using NodeId object or a string representing a NodeId.
        """
        return Node(self.uaclient, nodeid)

    async def create_subscription(self, period, handler, publishing=True):
        """
        Create a subscription.
        Returns a Subscription object which allows to subscribe to events or data changes on server.
        :param period: Either a publishing interval in milliseconds or a `CreateSubscriptionParameters` instance.
            The second option should be used, if the asyncua-server has problems with the default options.
        :param handler: Class instance with data_change and/or event methods (see `SubHandler`
            base class for details). Remember not to block the main event loop inside the handler methods.
        """
        if isinstance(period, ua.CreateSubscriptionParameters):
            params = period
        else:
            params = ua.CreateSubscriptionParameters()
            params.RequestedPublishingInterval = period
            params.RequestedLifetimeCount = 10000
            params.RequestedMaxKeepAliveCount = 3000
            params.MaxNotificationsPerPublish = 10000
            params.PublishingEnabled = publishing
            params.Priority = 0
        subscription = Subscription(self.uaclient, params, handler)
        await subscription.init()
        return subscription

    async def get_namespace_array(self):
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        return await ns_node.read_value()

    async def get_namespace_index(self, uri):
        uries = await self.get_namespace_array()
        _logger.info("get_namespace_index %s %r", type(uries), uries)
        return uries.index(uri)

    async def delete_nodes(self, nodes, recursive=False) -> Coroutine:
        return await delete_nodes(self.uaclient, nodes, recursive)

    async def import_xml(self, path=None, xmlstring=None) -> Coroutine:
        """
        Import nodes defined in xml
        """
        importer = XmlImporter(self)
        return await importer.import_xml(path, xmlstring)

    async def export_xml(self, nodes, path):
        """
        Export defined nodes to xml
        """
        exp = XmlExporter(self)
        await exp.build_etree(nodes)
        await exp.write_xml(path)

    async def register_namespace(self, uri):
        """
        Register a new namespace. Nodes should in custom namespace, not 0.
        This method is mainly implemented for symetry with server
        """
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        uries = await ns_node.read_value()
        if uri in uries:
            return uries.index(uri)
        uries.append(uri)
        await ns_node.write_value(uries)
        return len(uries) - 1

    async def load_type_definitions(self, nodes=None):
        """
        Load custom types (custom structures/extension objects) definition from server
        Generate Python classes for custom structures/extension objects defined in server
        These classes will available in ua module
        WARNING: protocol has changed in 1.04. use load_data_type_definitions()
        """
        _logger.warning("Deprecated since spec 1.04, call load_data_type_definitions")
        return await load_type_definitions(self, nodes)

    async def load_data_type_definitions(self, node=None):
        """
        Load custom types (custom structures/extension objects) definition from server
        Generate Python classes for custom structures/extension objects defined in server
        These classes will be available in ua module
        """
        return await load_data_type_definitions(self, node)

    async def load_enums(self):
        """
        generate Python enums for custom enums on server.
        This enums will be available in ua module
        """
        _logger.warning("Deprecated since spec 1.04, call load_data_type_definitions")
        return await load_enums(self)

    async def register_nodes(self, nodes):
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
        return nodes

    async def unregister_nodes(self, nodes):
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

    async def read_values(self, nodes):
        """
        Read the value of multiple nodes in one ua call.
        """
        nodeids = [node.nodeid for node in nodes]
        results = await self.uaclient.read_attributes(nodeids, ua.AttributeIds.Value)
        return [result.Value.Value for result in results]

    async def write_values(self, nodes, values):
        """
        Write values to multiple nodes in one ua call
        """
        nodeids = [node.nodeid for node in nodes]
        dvs = [value_to_datavalue(val) for val in values]
        results = await self.uaclient.write_attributes(nodeids, dvs, ua.AttributeIds.Value)
        for result in results:
            result.check()

    get_values = read_values  # legacy compatibility
    set_values = write_values  # legacy compatibility
