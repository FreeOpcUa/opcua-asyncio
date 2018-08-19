import asyncio
import logging
from typing import Union, Coroutine
from urllib.parse import urlparse

from opcua import ua
from .ua_client import UaClient
from ..common import XmlImporter, XmlExporter, Node, delete_nodes, Subscription, Shortcuts, load_type_definitions, \
    create_nonce, load_enums
from ..crypto import uacrypto, security_policies

__all__ = ["Client"]
_logger = logging.getLogger(__name__)
asyncio.get_event_loop().set_debug(True)


class Client(object):
    """
    High level client to connect to an OPC-UA server.

    This class makes it easy to connect and browse address space.
    It attempts to expose as much functionality as possible
    but if you want more flexibility it is possible and advised to
    use UaClient object, available as self.uaclient
    which offers the raw OPC-UA services interface.
    """

    def __init__(self, url: str, timeout: int = 4):
        """

        :param url: url of the server.
            if you are unsure of url, write at least hostname
            and port and call get_endpoints

        :param timeout:
            Each request sent to the server expects an answer within this
            time. The timeout is specified in seconds.
        """
        self.logger = logging.getLogger(__name__)
        self.loop = asyncio.get_event_loop()
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
        self.uaclient: UaClient = UaClient(timeout)
        self.user_certificate = None
        self.user_private_key = None
        self._server_nonce = None
        self._session_counter = 1
        self.nodes = Shortcuts(self.uaclient)
        self.max_messagesize = 0  # No limits
        self.max_chunkcount = 0  # No limits

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    @staticmethod
    def find_endpoint(endpoints, security_mode, policy_uri):
        """
        Find endpoint with required security mode and policy URI
        """
        _logger.info("find_endpoint %r %r %r", endpoints, security_mode, policy_uri)
        for ep in endpoints:
            if (ep.EndpointUrl.startswith(ua.OPC_TCP_SCHEME) and
                    ep.SecurityMode == security_mode and
                    ep.SecurityPolicyUri == policy_uri):
                return ep
        raise ua.UaError("No matching endpoints: {0}, {1}".format(security_mode, policy_uri))

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
        if type(pwd) is not str:
            raise TypeError("Password must be a string, got %s", type(pwd))
        self._password = pwd

    async def set_security_string(self, string: str):
        """
        Set SecureConnection mode. String format:
        "<Policy>,<Mode>,<certificate>,<private_key>[,<server_private_key>]"
        where <Policy> is Basic128Rsa15 or Basic256,
        <Mode> is Sign or SignAndEncrypt
        <certificate>, <private_key> and <server_private_key> are paths to .pem or .der files
        Call this before connect()
        """
        if not string:
            return
        parts = string.split(",")
        if len(parts) < 4:
            raise ua.UaError("Wrong format: `{}`, expected at least 4 comma-separated values".format(string))
        policy_class = getattr(security_policies, "SecurityPolicy{}".format(parts[0]))
        mode = getattr(ua.MessageSecurityMode, parts[1])
        return await self.set_security(
            policy_class, parts[2], parts[3], parts[4] if len(parts) >= 5 else None, mode
        )

    async def set_security(self, policy, certificate_path: str, private_key_path: str,
                           server_certificate_path: str = None,
                           mode: ua.MessageSecurityMode = ua.MessageSecurityMode.SignAndEncrypt):
        """
        Set SecureConnection mode.
        Call this before connect()
        """
        if server_certificate_path is None:
            # load certificate from server's list of endpoints
            endpoints = await self.connect_and_get_server_endpoints()
            endpoint = Client.find_endpoint(endpoints, mode, policy.URI)
            server_cert = uacrypto.x509_from_der(endpoint.ServerCertificate)
        else:
            server_cert = await uacrypto.load_certificate(server_certificate_path)
        cert = await uacrypto.load_certificate(certificate_path)
        pk = await uacrypto.load_private_key(private_key_path)
        self.security_policy = policy(server_cert, cert, pk, mode)
        self.uaclient.set_security(self.security_policy)

    async def load_client_certificate(self, path: str):
        """
        load our certificate from file, either pem or der
        """
        self.user_certificate = await uacrypto.load_certificate(path)

    async def load_private_key(self, path: str):
        """
        Load user private key. This is used for authenticating using certificate
        """
        self.user_private_key = await uacrypto.load_private_key(path)

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
        # FIXME check ack

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
        nonce = create_nonce(self.security_policy.symmetric_key_size)
        params.ClientNonce = nonce  # this nonce is used to create a symmetric key
        result = await self.uaclient.open_secure_channel(params)
        self.security_policy.make_symmetric_key(nonce, result.ServerNonce)
        self.secure_channel_timeout = result.SecurityToken.RevisedLifetime

    async def close_secure_channel(self):
        return await self.uaclient.close_secure_channel()

    async def get_endpoints(self) -> list:
        params = ua.GetEndpointsParameters()
        params.EndpointUrl = self.server_url.geturl()
        return await self.uaclient.get_endpoints(params)

    async def register_server(self, server, discovery_configuration=None):
        """
        register a server to discovery server
        if discovery_configuration is provided, the newer register_server2 service call is used
        """
        serv = ua.RegisteredServer()
        serv.ServerUri = server.application_uri
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
        else:
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
        params.ClientCertificate = self.security_policy.client_certificate
        params.ClientDescription = desc
        params.EndpointUrl = self.server_url.geturl()
        params.SessionName = f"{self.description} Session{self._session_counter}"
        # Requested maximum number of milliseconds that a Session should remain open without activity
        params.RequestedSessionTimeout = 60 * 60 * 1000
        params.MaxResponseMessageSize = 0  # means no max size
        response = await self.uaclient.create_session(params)
        if self.security_policy.client_certificate is None:
            data = nonce
        else:
            data = self.security_policy.client_certificate + nonce
        self.security_policy.asymmetric_cryptography.verify(data, response.ServerSignature.Signature)
        self._server_nonce = response.ServerNonce
        if not self.security_policy.server_certificate:
            self.security_policy.server_certificate = response.ServerCertificate
        elif self.security_policy.server_certificate != response.ServerCertificate:
            raise ua.UaError("Server certificate mismatch")
        # remember PolicyId's: we will use them in activate_session()
        ep = Client.find_endpoint(response.ServerEndpoints, self.security_policy.Mode, self.security_policy.URI)
        self._policy_ids = ep.UserIdentityTokens
        #  Actual maximum number of milliseconds that a Session shall remain open without activity
        self.session_timeout = response.RevisedSessionTimeout
        self._schedule_renew_session()
        # ToDo: subscribe to ServerStatus
        """
        The preferred mechanism for a Client to monitor the connection status is through the keep-alive of the
        Subscription. A Client should subscribe for the State Variable in the ServerStatus to detect shutdown or other
        failure states. If no Subscription is created or the Server does not support Subscriptions,
        the connection can be monitored by periodically reading the State Variable
        """
        return response

    def _schedule_renew_session(self, renew_session: bool=False):
        # if the session was intentionally closed `session_timeout` will be None
        if renew_session and self.session_timeout:
            self.loop.create_task(self._renew_session())
        self.loop.call_later(
            # 0.7 is from spec
            min(self.session_timeout, self.secure_channel_timeout) * 0.7,
            self._schedule_renew_session, True
        )

    async def _renew_session(self):
        """
        Renew the SecureChannel before the SessionTimeout will happen.
        ToDo: shouldn't this only be done if there was no session activity?
        """
        server_state = self.get_node(ua.FourByteNodeId(ua.ObjectIds.Server_ServerStatus_State))
        self.logger.debug("renewing channel")
        await self.open_secure_channel(renew=True)
        val = await server_state.get_value()
        self.logger.debug("server state is: %s ", val)

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
                else:  # empty URI means "use this endpoint's policy URI"
                    return self.security_policy.URI
        return self.security_policy.URI

    async def activate_session(self, username: str=None, password: str=None, certificate=None):
        """
        Activate session using either username and password or private_key
        """
        params = ua.ActivateSessionParameters()
        challenge = b""
        if self.security_policy.server_certificate is not None:
            challenge += self.security_policy.server_certificate
        if self._server_nonce is not None:
            challenge += self._server_nonce
        params.ClientSignature.Algorithm = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
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
        params.UserIdentityToken.PolicyId = self.server_policy_id(ua.UserTokenType.Certificate, "certificate_basic256")
        params.UserIdentityToken.CertificateData = uacrypto.der_from_x509(certificate)
        # specs part 4, 5.6.3.1: the data to sign is created by appending
        # the last serverNonce to the serverCertificate
        sig = uacrypto.sign_sha1(self.user_private_key, challenge)
        params.UserTokenSignature = ua.SignatureData()
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
                self.logger.warning("Sending plain-text password")
                params.UserIdentityToken.Password = password.encode("utf8")
            params.UserIdentityToken.EncryptionAlgorithm = None
        elif self._password:
            data, uri = self._encrypt_password(password, policy_uri)
            params.UserIdentityToken.Password = data
            params.UserIdentityToken.EncryptionAlgorithm = uri
        params.UserIdentityToken.PolicyId = self.server_policy_id(ua.UserTokenType.UserName, b"username_basic256")

    def _encrypt_password(self, password: str, policy_uri):
        pubkey = uacrypto.x509_from_der(self.security_policy.server_certificate).public_key()
        # see specs part 4, 7.36.3: if the token is encrypted, password
        # shall be converted to UTF-8 and serialized with server nonce
        passwd = password.encode("utf8")
        if self._server_nonce is not None:
            passwd += self._server_nonce
        etoken = ua.ua_binary.Primitives.Bytes.pack(passwd)
        data, uri = security_policies.encrypt_asymmetric(pubkey, etoken, policy_uri)
        return data, uri

    def close_session(self) -> Coroutine:
        """
        Close session
        """
        self.session_timeout = None
        return self.uaclient.close_session(True)

    def get_root_node(self):
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.RootFolder))

    def get_objects_node(self):
        self.logger.info("get_objects_node")
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.ObjectsFolder))

    def get_server_node(self):
        return self.get_node(ua.FourByteNodeId(ua.ObjectIds.Server))

    def get_node(self, nodeid: Union[ua.NodeId, str]) -> Node:
        """
        Get node using NodeId object or a string representing a NodeId
        """
        return Node(self.uaclient, nodeid)

    async def create_subscription(self, period, handler):
        """
        Create a subscription.
        returns a Subscription object which allow
        to subscribe to events or data on server
        handler argument is a class with data_change and/or event methods.
        period argument is either a publishing interval in milliseconds or a
        CreateSubscriptionParameters instance. The second option should be used,
        if the opcua-server has problems with the default options.
        These methods will be called when notfication from server are received.
        See example-client.py.
        Do not do expensive/slow or network operation from these methods
        since they are called directly from receiving thread. This is a design choice,
        start another thread if you need to do such a thing.
        """

        if isinstance(period, ua.CreateSubscriptionParameters):
            subscription = Subscription(self.uaclient, period, handler)
            await subscription.init()
            return subscription
        params = ua.CreateSubscriptionParameters()
        params.RequestedPublishingInterval = period
        params.RequestedLifetimeCount = 10000
        params.RequestedMaxKeepAliveCount = 3000
        params.MaxNotificationsPerPublish = 10000
        params.PublishingEnabled = True
        params.Priority = 0
        subscription = Subscription(self.uaclient, params, handler)
        await subscription.init()
        return subscription

    def get_namespace_array(self) -> Coroutine:
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        return ns_node.get_value()

    async def get_namespace_index(self, uri):
        uries = await self.get_namespace_array()
        _logger.info("get_namespace_index %s %r", type(uries), uries)
        return uries.index(uri)

    def delete_nodes(self, nodes, recursive=False) -> Coroutine:
        return delete_nodes(self.uaclient, nodes, recursive)

    def import_xml(self, path=None, xmlstring=None) -> Coroutine:
        """
        Import nodes defined in xml
        """
        importer = XmlImporter(self)
        return importer.import_xml(path, xmlstring)

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
        uries = await ns_node.get_value()
        if uri in uries:
            return uries.index(uri)
        uries.append(uri)
        await ns_node.set_value(uries)
        return len(uries) - 1

    def load_type_definitions(self, nodes=None) -> Coroutine:
        """
        Load custom types (custom structures/extension objects) definition from server
        Generate Python classes for custom structures/extension objects defined in server
        These classes will available in ua module
        """
        return load_type_definitions(self, nodes)

    def load_enums(self) -> Coroutine:
        """
        generate Python enums for custom enums on server.
        This enums will be available in ua module
        """
        return load_enums(self)
