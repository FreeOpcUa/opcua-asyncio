"""
High level interface to pure python OPC-UA server
"""

import asyncio
import logging
from datetime import timedelta, datetime
from urllib.parse import urlparse
from typing import Coroutine, Optional

from asyncua import ua
from .binary_server_asyncio import BinaryServer
from .internal_server import InternalServer
from .event_generator import EventGenerator
from ..client import Client
from ..common.node import Node
from ..common.subscription import Subscription
from ..common.xmlimporter import XmlImporter
from ..common.xmlexporter import XmlExporter
from ..common.manage_nodes import delete_nodes
from ..common.event_objects import BaseEvent
from ..common.shortcuts import Shortcuts
from ..common.structures import load_type_definitions, load_enums
from ..common.ua_utils import get_nodes_of_namespace

from ..crypto import security_policies, uacrypto

_logger = logging.getLogger(__name__)


def _get_node(isession, whatever):
    if isinstance(whatever, Node):
        return whatever
    if isinstance(whatever, ua.NodeId):
        return Node(isession, whatever)
    return Node(isession, ua.NodeId(whatever))


class Server:
    """
    High level Server class

    This class creates an asyncua server with default values

    Create your own namespace and then populate your server address space
    using use the get_root() or get_objects() to get Node objects.
    and get_event_object() to fire events.
    Then start server. See example_server.py
    All methods are threadsafe

    If you need more flexibility you call directly the Ua Service methods
    on the iserver  or iserver.isession object members.

    During startup the standard address space will be constructed, which may be
    time-consuming when running a server on a less powerful device (e.g. a
    Raspberry Pi). In order to improve startup performance, a optional path to a
    cache file can be passed to the server constructor.
    If the parameter is defined, the address space will be loaded from the
    cache file or the file will be created if it does not exist yet.
    As a result the first startup will be even slower due to the cache file
    generation but all further start ups will be significantly faster.
    ┌────────┐
    │ Server │ ── BinaryServer ── OPCUAProtocol ── UaProcessor
    │        │ ── InternalServer ── InternalSession
    └────────┘                   ── SubscriptionService

    :ivar product_uri:
    :ivar name:
    :ivar default_timeout: timeout in milliseconds for sessions and secure channel
    :ivar iserver: `InternalServer` instance
    :ivar bserver: binary protocol server `BinaryServer`
    :ivar nodes: shortcuts to common nodes - `Shortcuts` instance
    """

    def __init__(self, iserver: InternalServer = None, loop: asyncio.AbstractEventLoop = None):
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.logger = logging.getLogger(__name__)
        self.endpoint = urlparse("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self._application_uri = "urn:freeopcua:python:server"
        self.product_uri = "urn:freeopcua.github.io:python:server"
        self.name: str = "FreeOpcUa Python Server"
        self.manufacturer_name = "FreeOpcUa"
        self.application_type = ua.ApplicationType.ClientAndServer
        self.default_timeout: int = 60 * 60 * 1000
        self.iserver = iserver if iserver else InternalServer(self.loop)
        self.bserver: Optional[BinaryServer] = None
        self._discovery_clients = {}
        self._discovery_period = 60
        self._policies = []
        self.nodes = Shortcuts(self.iserver.isession)
        # enable all endpoints by default
        self._security_policy = [
            ua.SecurityPolicyType.NoSecurity, ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign
        ]
        self._policyIDs = ["Anonymous", "Basic256Sha256", "Username"]
        self.certificate = None

    async def init(self, shelf_file=None):
        await self.iserver.init(shelf_file)
        # setup some expected values
        await self.set_application_uri(self._application_uri)
        sa_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_ServerArray))
        await sa_node.set_value([self._application_uri])
        status_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus))
        build_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_BuildInfo))
        status = ua.ServerStatusDataType()
        status.BuildInfo.ProductUri = self.product_uri
        status.BuildInfo.ManufacturerName = self.manufacturer_name
        status.BuildInfo.ProductName = self.name
        status.BuildInfo.SoftwareVersion = "1.0pre"
        status.BuildInfo.BuildNumber = "0"
        status.BuildInfo.BuildDate = datetime.now()
        status.SecondsTillShutdown = 0
        await status_node.set_value(status)
        await build_node.set_value(status.BuildInfo)

    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.stop()

    def __str__(self):
        return f"OPC UA Server()"
    __repr__ = __str__

    async def load_certificate(self, path: str):
        """
        load server certificate from file, either pem or der
        """
        self.certificate = await uacrypto.load_certificate(path)

    async def load_private_key(self, path):
        self.iserver.private_key = await uacrypto.load_private_key(path)

    def disable_clock(self, val: bool = True):
        """
        for debugging you may want to disable clock that write every second
        to address space
        """
        self.iserver.disabled_clock = val

    def get_application_uri(self):
        return self._application_uri

    async def set_application_uri(self, uri: str):
        """
        Set application/server URI.
        This uri is supposed to be unique. If you intent to register
        your server to a discovery server, it really should be unique in
        your system!
        default is : "urn:freeopcua:python:server"
        """
        self._application_uri = uri
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        uries = await ns_node.get_value()
        if len(uries) > 1:
            uries[1] = uri  # application uri is always namespace 1
        else:
            uries.append(uri)
        await ns_node.set_value(uries)

    async def find_servers(self, uris=None):
        """
        find_servers. mainly implemented for symmetry with client
        """
        if uris is None:
            uris = []
        params = ua.FindServersParameters()
        params.EndpointUrl = self.endpoint.geturl()
        params.ServerUris = uris
        return self.iserver.find_servers(params)

    async def register_to_discovery(self, url: str = "opc.tcp://localhost:4840", period: int = 60):
        """
        Register to an OPC-UA Discovery server. Registering must be renewed at
        least every 10 minutes, so this method will use our asyncio thread to
        re-register every period seconds
        if period is 0 registration is not automatically renewed
        """
        # FIXME: have a period per discovery
        if url in self._discovery_clients:
            await self._discovery_clients[url].disconnect()
        self._discovery_clients[url] = Client(url)
        await self._discovery_clients[url].connect()
        await self._discovery_clients[url].register_server(self)
        self._discovery_period = period
        if period:
            self.loop.call_soon(self._schedule_renew_registration)

    def unregister_to_discovery(self, url: str = "opc.tcp://localhost:4840"):
        """
        stop registration thread
        """
        # FIXME: is there really no way to deregister?
        self._discovery_clients[url].disconnect()

    def _schedule_renew_registration(self):
        self.loop.create_task(self._renew_registration())
        self.loop.call_later(self._discovery_period, self._schedule_renew_registration)

    async def _renew_registration(self):
        for client in self._discovery_clients.values():
            await client.register_server(self)

    def allow_remote_admin(self, allow):
        """
        Enable or disable the builtin Admin user from network clients
        """
        self.iserver.allow_remote_admin = allow

    def set_endpoint(self, url):
        self.endpoint = urlparse(url)

    def get_endpoints(self) -> Coroutine:
        return self.iserver.get_endpoints()

    def set_security_policy(self, security_policy):
        """
        Method setting up the security policies for connections
        to the server, where security_policy is a list of integers.
        During server initialization, all endpoints are enabled:

                security_policy = [
                            ua.SecurityPolicyType.NoSecurity,
                            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                            ua.SecurityPolicyType.Basic256Sha256_Sign
                                ]

        E.g. to limit the number of endpoints and disable no encryption:

                set_security_policy([
                            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])

        """
        self._security_policy = security_policy

    def set_security_IDs(self, policy_ids):
        """
            Method setting up the security endpoints for identification
            of clients. During server object initialization, all possible
            endpoints are enabled:

            self._policyIDs = ["Anonymous", "Basic256Sha256", "Username"]

            E.g. to limit the number of IDs and disable anonymous clients:

                set_security_policy(["Basic256Sha256"])

        (Implementation for ID check is currently not finalized...)
        """
        self._policyIDs = policy_ids

    async def _setup_server_nodes(self):
        # to be called just before starting server since it needs all parameters to be setup
        if ua.SecurityPolicyType.NoSecurity in self._security_policy:
            self._set_endpoints()
            self._policies = [ua.SecurityPolicyFactory()]

        if self._security_policy != [ua.SecurityPolicyType.NoSecurity]:
            if not (self.certificate and self.iserver.private_key):
                self.logger.warning("Endpoints other than open requested but private key and certificate are not set.")
                return

            if ua.SecurityPolicyType.NoSecurity in self._security_policy:
                self.logger.warning(
                    "Creating an open endpoint to the server, although encrypted endpoints are enabled.")

            if ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt in self._security_policy:
                self._set_endpoints(security_policies.SecurityPolicyBasic256Sha256,
                                    ua.MessageSecurityMode.SignAndEncrypt)
                self._policies.append(
                    ua.SecurityPolicyFactory(security_policies.SecurityPolicyBasic256Sha256,
                                             ua.MessageSecurityMode.SignAndEncrypt, self.certificate,
                                             self.iserver.private_key))
            if ua.SecurityPolicyType.Basic256Sha256_Sign in self._security_policy:
                self._set_endpoints(security_policies.SecurityPolicyBasic256Sha256, ua.MessageSecurityMode.Sign)
                self._policies.append(
                    ua.SecurityPolicyFactory(security_policies.SecurityPolicyBasic256Sha256,
                                             ua.MessageSecurityMode.Sign, self.certificate, self.iserver.private_key))

    def _set_endpoints(self, policy=ua.SecurityPolicy, mode=ua.MessageSecurityMode.None_):
        idtokens = []
        if "Anonymous" in self._policyIDs:
            idtoken = ua.UserTokenPolicy()
            idtoken.PolicyId = "anonymous"
            idtoken.TokenType = ua.UserTokenType.Anonymous
            idtokens.append(idtoken)

        if "Basic256Sha256" in self._policyIDs:
            idtoken = ua.UserTokenPolicy()
            idtoken.PolicyId = 'certificate_basic256sha256'
            idtoken.TokenType = ua.UserTokenType.Certificate
            idtokens.append(idtoken)

        if "Username" in self._policyIDs:
            idtoken = ua.UserTokenPolicy()
            idtoken.PolicyId = "username"
            idtoken.TokenType = ua.UserTokenType.UserName
            idtokens.append(idtoken)

        appdesc = ua.ApplicationDescription()
        appdesc.ApplicationName = ua.LocalizedText(self.name)
        appdesc.ApplicationUri = self._application_uri
        appdesc.ApplicationType = self.application_type
        appdesc.ProductUri = self.product_uri
        appdesc.DiscoveryUrls.append(self.endpoint.geturl())

        edp = ua.EndpointDescription()
        edp.EndpointUrl = self.endpoint.geturl()
        edp.Server = appdesc
        if self.certificate:
            edp.ServerCertificate = uacrypto.der_from_x509(self.certificate)
        edp.SecurityMode = mode
        edp.SecurityPolicyUri = policy.URI
        edp.UserIdentityTokens = idtokens
        edp.TransportProfileUri = "http://opcfoundation.org/UA-Profile/Transport/uatcp-uasc-uabinary"
        edp.SecurityLevel = 0
        self.iserver.add_endpoint(edp)

    def set_server_name(self, name):
        self.name = name

    async def start(self):
        """
        Start to listen on network
        """
        await self._setup_server_nodes()
        await self.iserver.start()
        try:
            self.bserver = BinaryServer(self.iserver, self.endpoint.hostname, self.endpoint.port)
            self.bserver.set_policies(self._policies)
            await self.bserver.start()
        except Exception as exp:
            await self.iserver.stop()
            raise exp

    async def stop(self):
        """
        Stop server
        """
        if self._discovery_clients:
            await asyncio.wait([client.disconnect() for client in self._discovery_clients.values()])
        await self.bserver.stop()
        await self.iserver.stop()

    def get_root_node(self):
        """
        Get Root node of server. Returns a Node object.
        """
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.RootFolder))

    def get_objects_node(self):
        """
        Get Objects node of server. Returns a Node object.
        """
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.ObjectsFolder))

    def get_server_node(self):
        """
        Get Server node of server. Returns a Node object.
        """
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.Server))

    def get_node(self, nodeid):
        """
        Get a specific node using NodeId object or a string representing a NodeId
        """
        return Node(self.iserver.isession, nodeid)

    async def create_subscription(self, period, handler):
        """
        Create a subscription.
        Returns a Subscription object which allow to subscribe to events or data changes on server
        :param period: Period in milliseconds
        :param handler: A class instance - see `SubHandler` base class for details
        """
        params = ua.CreateSubscriptionParameters()
        params.RequestedPublishingInterval = period
        params.RequestedLifetimeCount = 3000
        params.RequestedMaxKeepAliveCount = 10000
        params.MaxNotificationsPerPublish = 0
        params.PublishingEnabled = True
        params.Priority = 0
        subscription = Subscription(self.iserver.isession, params, handler)
        await subscription.init()
        return subscription

    def get_namespace_array(self) -> Coroutine:
        """
        get all namespace defined in server
        """
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        return ns_node.get_value()

    async def register_namespace(self, uri) -> int:
        """
        Register a new namespace. Nodes should in custom namespace, not 0.
        """
        ns_node = self.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        uries = await ns_node.get_value()
        if uri in uries:
            return uries.index(uri)
        uries.append(uri)
        await ns_node.set_value(uries)
        return len(uries) - 1

    async def get_namespace_index(self, uri):
        """
        get index of a namespace using its uri
        """
        uries = await self.get_namespace_array()
        return uries.index(uri)

    async def get_event_generator(self, etype=None, emitting_node=ua.ObjectIds.Server):
        """
        Returns an event object using an event type from address space.
        Use this object to fire events
        """
        if not etype:
            etype = BaseEvent()
        ev_gen = EventGenerator(self.iserver.isession)
        await ev_gen.init(etype, emitting_node=emitting_node)
        return ev_gen

    async def create_custom_data_type(self, idx, name, basetype=ua.ObjectIds.BaseDataType, properties=None, description=None) -> Coroutine:
        if properties is None:
            properties = []
        base_t = _get_node(self.iserver.isession, basetype)

        custom_t = await base_t.add_data_type(idx, name, description)
        for prop in properties:
            datatype = None
            if len(prop) > 2:
                datatype = prop[2]
            await custom_t.add_property(idx, prop[0], ua.get_default_value(prop[1]), varianttype=prop[1], datatype=datatype)
        return custom_t

    async def create_custom_event_type(self, idx, name, basetype=ua.ObjectIds.BaseEventType, properties=None) -> Coroutine:
        if properties is None:
            properties = []
        return await self._create_custom_type(idx, name, basetype, properties, [], [])

    async def create_custom_object_type(self,
                                  idx,
                                  name,
                                  basetype=ua.ObjectIds.BaseObjectType,
                                  properties=None,
                                  variables=None,
                                  methods=None) -> Coroutine:
        if properties is None:
            properties = []
        if variables is None:
            variables = []
        if methods is None:
            methods = []
        return await self._create_custom_type(idx, name, basetype, properties, variables, methods)

    # def create_custom_reference_type(self, idx, name, basetype=ua.ObjectIds.BaseReferenceType, properties=[]):
    # return self._create_custom_type(idx, name, basetype, properties)

    async def create_custom_variable_type(self,
                                    idx,
                                    name,
                                    basetype=ua.ObjectIds.BaseVariableType,
                                    properties=None,
                                    variables=None,
                                    methods=None) -> Coroutine:
        if properties is None:
            properties = []
        if variables is None:
            variables = []
        if methods is None:
            methods = []
        return await self._create_custom_type(idx, name, basetype, properties, variables, methods)

    async def _create_custom_type(self, idx, name, basetype, properties, variables, methods):
        base_t = _get_node(self.iserver.isession, basetype)
        custom_t = await base_t.add_object_type(idx, name)
        for prop in properties:
            datatype = None
            if len(prop) > 2:
                datatype = prop[2]
            await custom_t.add_property(
                idx, prop[0], ua.get_default_value(prop[1]), varianttype=prop[1], datatype=datatype)
        for variable in variables:
            datatype = None
            if len(variable) > 2:
                datatype = variable[2]
            await custom_t.add_variable(
                idx, variable[0], ua.get_default_value(variable[1]), varianttype=variable[1], datatype=datatype)
        for method in methods:
            await custom_t.add_method(idx, method[0], method[1], method[2], method[3])
        return custom_t

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

    async def export_xml_by_ns(self, path: str, namespaces: list = None):
        """
        Export nodes of one or more namespaces to an XML file.
        Namespaces used by nodes are always exported for consistency.
        :param path: name of the xml file to write
        :param namespaces: list of string uris or int indexes of the namespace to export, if not provide all ns are used except 0
        """
        if namespaces is None:
            namespaces = []
        nodes = await get_nodes_of_namespace(self, namespaces)
        await self.export_xml(nodes, path)

    def delete_nodes(self, nodes, recursive=False) -> Coroutine:
        return delete_nodes(self.iserver.isession, nodes, recursive)

    async def historize_node_data_change(self, node, period=timedelta(days=7), count=0):
        """
        Start historizing supplied nodes; see history module
        :param node: node or list of nodes that can be historized (variables/properties)
        :param period: time delta to store the history; older data will be deleted from the storage
        :param count: number of changes to store in the history
        """
        nodes = node if isinstance(node, (list, tuple)) else [node]
        for n in nodes:
            await self.iserver.enable_history_data_change(n, period, count)

    async def dehistorize_node_data_change(self, node):
        """
        Stop historizing supplied nodes; see history module
        :param node: node or list of nodes that can be historized (UA variables/properties)
        """
        nodes = node if isinstance(node, (list, tuple)) else [node]
        for n in nodes:
            await self.iserver.disable_history_data_change(n)

    async def historize_node_event(self, node, period=timedelta(days=7), count: int = 0):
        """
        Start historizing events from node (typically a UA object); see history module
        :param node: node or list of nodes that can be historized (UA objects)
        :param period: time delta to store the history; older data will be deleted from the storage
        :param count: number of events to store in the history
        """
        nodes = node if isinstance(node, (list, tuple)) else [node]
        for n in nodes:
            await self.iserver.enable_history_event(n, period, count)

    async def dehistorize_node_event(self, node):
        """
        Stop historizing events from node (typically a UA object); see history module
        :param node: node or list of nodes that can be historized (UA objects)
        """
        nodes = node if isinstance(node, (list, tuple)) else [node]
        for n in nodes:
            await self.iserver.disable_history_event(n)

    def subscribe_server_callback(self, event, handle):
        self.iserver.subscribe_server_callback(event, handle)

    def unsubscribe_server_callback(self, event, handle):
        self.iserver.unsubscribe_server_callback(event, handle)

    def link_method(self, node, callback):
        """
        Link a python function to a UA method in the address space; required when a UA method has been imported
        to the address space via XML; the python executable must be linked manually
        :param node: UA method node
        :param callback: python function that the UA method will call
        """
        self.iserver.isession.add_method_callback(node.nodeid, callback)

    def load_type_definitions(self, nodes=None) -> Coroutine:
        """
        load custom structures from our server.
        Server side this can be used to create python objects from custom structures
        imported through xml into server
        """
        return load_type_definitions(self, nodes)

    def load_enums(self) -> Coroutine:
        """
        load UA structures and generate python Enums in ua module for custom enums in server
        """
        return load_enums(self)

    def set_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        """
        directly write datavalue to the Attribute, bypasing some checks and structure creation
        so it is a little faster
        """
        return self.iserver.set_attribute_value(nodeid, datavalue, attr)
