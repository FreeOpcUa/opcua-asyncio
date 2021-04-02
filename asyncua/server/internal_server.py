"""
Internal server implementing opcu-ua interface.
Can be used on server side or to implement binary/https opc-ua servers
"""

import asyncio
from datetime import datetime, timedelta
from copy import copy
from struct import unpack_from
import os
import logging
from urllib.parse import urlparse
from typing import Coroutine

from asyncua import ua
from .user_managers import PermissiveUserManager, UserManager
from ..common.callback import CallbackService
from ..common.node import Node
from .history import HistoryManager
from .address_space import AddressSpace, AttributeService, ViewService, NodeManagementService, MethodService
from .subscription_service import SubscriptionService
from .standard_address_space import standard_address_space
from .users import User, UserRole
from .internal_session import InternalSession

try:
    from asyncua.crypto import uacrypto
except ImportError:
    logging.getLogger(__name__).warning("cryptography is not installed, use of crypto disabled")
    uacrypto = False

logger = logging.getLogger()


class ServerDesc:
    def __init__(self, serv, cap=None):
        self.Server = serv
        self.Capabilities = cap


class InternalServer:
    """
    There is one `InternalServer` for every `Server`.
    """

    def __init__(self, user_manager: UserManager = None):
        self.logger = logging.getLogger(__name__)
        self.callback_service = CallbackService()
        self.endpoints = []
        self._channel_id_counter = 5
        self.allow_remote_admin = True
        self.disabled_clock = False  # for debugging we may want to disable clock that writes too much in log
        self._known_servers = {}  # used if we are a discovery server
        self.certificate = None
        self.private_key = None
        self.aspace = AddressSpace()
        self.attribute_service = AttributeService(self.aspace)
        self.view_service = ViewService(self.aspace)
        self.method_service = MethodService(self.aspace)
        self.node_mgt_service = NodeManagementService(self.aspace)
        self.asyncio_transports = []
        self.subscription_service: SubscriptionService = SubscriptionService(self.aspace)
        self.history_manager = HistoryManager(self)
        if user_manager is None:
            logger.info("No user manager specified. Using default permissive manager instead.")
            user_manager = PermissiveUserManager()
        self.user_manager = user_manager
        # create a session to use on server side
        self.isession = InternalSession(
            self, self.aspace, self.subscription_service, "Internal", user=User(role=UserRole.Admin)
        )
        self.current_time_node = Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
        self.time_task = None
        self._time_task_stop = False

    async def init(self, shelffile=None):
        await self.load_standard_address_space(shelffile)
        await self._address_space_fixes()
        await self.setup_nodes()
        await self.history_manager.init()

    async def setup_nodes(self):
        """
        Set up some nodes as defined by spec
        """
        uries = ['http://opcfoundation.org/UA/']
        ns_node = Node(self.isession, ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
        await ns_node.write_value(uries)

        params = ua.WriteParameters()
        for nodeid in (
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerRead,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerHistoryReadData,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerHistoryReadEvents,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerWrite,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerHistoryUpdateData,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerHistoryUpdateEvents,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerMethodCall,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerBrowse,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerRegisterNodes,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerTranslateBrowsePathsToNodeIds,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxNodesPerNodeManagement,
            ua.ObjectIds.Server_ServerCapabilities_OperationLimits_MaxMonitoredItemsPerCall,
        ):
            attr = ua.WriteValue()
            attr.NodeId = ua.NodeId(nodeid)
            attr.AttributeId = ua.AttributeIds.Value
            attr.Value = ua.DataValue(
                ua.Variant(10000, ua.VariantType.UInt32),
                StatusCode_=ua.StatusCode(ua.StatusCodes.Good),
                ServerTimestamp=datetime.utcnow(),
            )
            params.NodesToWrite.append(attr)
        result = await self.isession.write(params)
        result[0].check()

    async def load_standard_address_space(self, shelf_file=None):
        if shelf_file:
            is_file = await asyncio.get_running_loop().run_in_executor(
                None, os.path.isfile, shelf_file
            ) or await asyncio.get_running_loop().run_in_executor(None, os.path.isfile, f'{shelf_file}.db')
            if is_file:
                # import address space from shelf
                await asyncio.get_running_loop().run_in_executor(None, self.aspace.load_aspace_shelf, shelf_file)
                return
        # import address space from code generated from xml
        standard_address_space.fill_address_space(self.node_mgt_service)
        # import address space directly from xml, this has performance impact so disabled
        # importer = xmlimporter.XmlImporter(self.node_mgt_service)
        # importer.import_xml("/path/to/python-asyncua/schemas/Opc.Ua.NodeSet2.xml", self)
        if shelf_file:
            # path was supplied, but file doesn't exist - create one for next start up
            await asyncio.get_running_loop().run_in_executor(None, self.aspace.make_aspace_shelf, shelf_file)

    async def _address_space_fixes(self) -> Coroutine:
        """
        Looks like the xml definition of address space has some error. This is a good place to fix them
        """
        it = ua.AddReferencesItem()
        it.SourceNodeId = ua.NodeId(ua.ObjectIds.BaseObjectType)
        it.ReferenceTypeId = ua.NodeId(ua.ObjectIds.Organizes)
        it.IsForward = False
        it.TargetNodeId = ua.NodeId(ua.ObjectIds.ObjectTypesFolder)
        it.TargetNodeClass = ua.NodeClass.Object

        it2 = ua.AddReferencesItem()
        it2.SourceNodeId = ua.NodeId(ua.ObjectIds.BaseDataType)
        it2.ReferenceTypeId = ua.NodeId(ua.ObjectIds.Organizes)
        it2.IsForward = False
        it2.TargetNodeId = ua.NodeId(ua.ObjectIds.DataTypesFolder)
        it2.TargetNodeClass = ua.NodeClass.Object

        results = await self.isession.add_references([it, it2])
        for res in results:
            res.check()

    def load_address_space(self, path):
        """
        Load address space from path
        """
        self.aspace.load(path)

    def dump_address_space(self, path):
        """
        Dump current address space to path
        """
        self.aspace.dump(path)

    async def start(self):
        self.logger.info('starting internal server')
        for edp in self.endpoints:
            self._known_servers[edp.Server.ApplicationUri] = ServerDesc(edp.Server)
        await Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_State)).write_value(
            ua.ServerState.Running, ua.VariantType.Int32
        )
        await Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_StartTime)).write_value(datetime.utcnow())
        if not self.disabled_clock:
            self.time_task = asyncio.create_task(self._set_current_time_loop())

    async def stop(self):
        self.logger.info('stopping internal server')
        if self.time_task:
            self._time_task_stop = True
            await self.time_task
        self.method_service.stop()
        await self.isession.close_session()
        await self.history_manager.stop()

    async def _set_current_time_loop(self):
        while not self._time_task_stop:
            await self.current_time_node.write_value(datetime.utcnow())
            await asyncio.sleep(1)

    def get_new_channel_id(self):
        self._channel_id_counter += 1
        return self._channel_id_counter

    def add_endpoint(self, endpoint):
        self.endpoints.append(endpoint)

    async def get_endpoints(self, params=None, sockname=None):
        self.logger.info('get endpoint')
        if sockname:
            # return to client the ip address it has access to
            edps = []
            for edp in self.endpoints:
                edp1 = copy(edp)
                url = urlparse(edp1.EndpointUrl)
                url = url._replace(netloc=sockname[0] + ':' + str(sockname[1]))
                edp1.EndpointUrl = url.geturl()
                edps.append(edp1)
            return edps
        return self.endpoints[:]

    def find_servers(self, params):
        if not params.ServerUris:
            return [desc.Server for desc in self._known_servers.values()]
        servers = []
        for serv in self._known_servers.values():
            serv_uri = serv.Server.ApplicationUri.split(':')
            for uri in params.ServerUris:
                uri = uri.split(':')
                if serv_uri[: len(uri)] == uri:
                    servers.append(serv.Server)
                    break
        return servers

    def register_server(self, server, conf=None):
        appdesc = ua.ApplicationDescription()
        appdesc.ApplicationUri = server.ServerUri
        appdesc.ProductUri = server.ProductUri
        # FIXME: select name from client locale
        appdesc.ApplicationName = server.ServerNames[0]
        appdesc.ApplicationType = server.ServerType
        appdesc.DiscoveryUrls = server.DiscoveryUrls
        # FIXME: select discovery uri using reachability from client network
        appdesc.GatewayServerUri = server.GatewayServerUri
        self._known_servers[server.ServerUri] = ServerDesc(appdesc, conf)

    def register_server2(self, params):
        return self.register_server(params.Server, params.DiscoveryConfiguration)

    def create_session(self, name, user=User(role=UserRole.Anonymous), external=False):
        return InternalSession(self, self.aspace, self.subscription_service, name, user=user, external=external)

    async def enable_history_data_change(self, node, period=timedelta(days=7), count=0):
        """
        Set attribute Historizing of node to True and start storing data for history
        """
        await node.write_attribute(ua.AttributeIds.Historizing, ua.DataValue(True))
        await node.set_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.HistoryRead)
        await node.set_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.HistoryRead)
        await self.history_manager.historize_data_change(node, period, count)

    async def disable_history_data_change(self, node):
        """
        Set attribute Historizing of node to False and stop storing data for history
        """
        await node.write_attribute(ua.AttributeIds.Historizing, ua.DataValue(False))
        await node.unset_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.HistoryRead)
        await node.unset_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.HistoryRead)
        await self.history_manager.dehistorize(node)

    async def enable_history_event(self, source, period=timedelta(days=7), count=0):
        """
        Set attribute History Read of object events to True and start storing data for history
        """
        event_notifier = await source.read_event_notifier()
        if ua.EventNotifier.SubscribeToEvents not in event_notifier:
            raise ua.UaError('Node does not generate events', event_notifier)
        if ua.EventNotifier.HistoryRead not in event_notifier:
            event_notifier.add(ua.EventNotifier.HistoryRead)
            await source.set_event_notifier(event_notifier)
        await self.history_manager.historize_event(source, period, count)

    async def disable_history_event(self, source):
        """
        Set attribute History Read of node to False and stop storing data for history
        """
        await source.unset_attr_bit(ua.AttributeIds.EventNotifier, ua.EventNotifier.HistoryRead)
        await self.history_manager.dehistorize(source)

    def subscribe_server_callback(self, event, handle):
        """
        Create a subscription from event to handle
        """
        self.callback_service.addListener(event, handle)

    def unsubscribe_server_callback(self, event, handle):
        """
        Remove a subscription from event to handle
        """
        self.callback_service.removeListener(event, handle)

    async def write_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        """
        directly write datavalue to the Attribute, bypassing some checks and structure creation
        so it is a little faster
        """
        await self.aspace.write_attribute_value(nodeid, attr, datavalue)

    def set_user_manager(self, user_manager):
        """
        set up a function which that will check for authorize users. Input function takes username
        and password as parameters and returns True of user is allowed access, False otherwise.
        """
        self.user_manager = user_manager

    def check_user_token(self, isession, token):
        """
        unpack the username and password for the benefit of the user defined user manager
        """
        user_name = token.UserName
        password = token.Password

        # TODO Support all Token Types
        # AnonimousIdentityToken
        # UserIdentityToken
        # UserNameIdentityToken
        # X509IdentityToken
        # IssuedIdentityToken

        # decrypt password if we can
        if str(token.EncryptionAlgorithm) != "None":
            if not uacrypto:
                # raise  # Should I raise a significant exception?
                return False
            try:
                if token.EncryptionAlgorithm == "http://www.w3.org/2001/04/xmlenc#rsa-1_5":
                    raw_pw = uacrypto.decrypt_rsa15(self.private_key, password)
                elif token.EncryptionAlgorithm == "http://www.w3.org/2001/04/xmlenc#rsa-oaep":
                    raw_pw = uacrypto.decrypt_rsa_oaep(self.private_key, password)
                else:
                    self.logger.warning("Unknown password encoding %s", token.EncryptionAlgorithm)
                    # raise  # Should I raise a significant exception?
                    return user_name, password
                length = unpack_from('<I', raw_pw)[0] - len(isession.nonce)
                password = raw_pw[4 : 4 + length]
                password = password.decode('utf-8')
            except Exception:
                self.logger.exception("Unable to decrypt password")
                return False
        elif type(password) == bytes:  # TODO check
            password = password.decode('utf-8')

        return user_name, password
