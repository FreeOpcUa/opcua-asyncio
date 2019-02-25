"""
Internal server implementing opcu-ua interface.
Can be used on server side or to implement binary/https opc-ua servers
"""

from datetime import datetime, timedelta
from copy import copy
from struct import unpack_from
import os
import asyncio
import logging
from enum import Enum
from urllib.parse import urlparse
from typing import Coroutine

from asyncua import ua
from ..common import CallbackType, ServerItemCallback, CallbackDispatcher, Node, create_nonce, ServiceError
from .history import HistoryManager
from .address_space import AddressSpace, AttributeService, ViewService, NodeManagementService, MethodService
from .subscription_service import SubscriptionService
from .standard_address_space import standard_address_space
from .users import User

__all__ = ["InternalServer"]

use_crypto = True
try:
    from asyncua.crypto import uacrypto
except ImportError:
    logging.getLogger(__name__).warning("cryptography is not installed, use of crypto disabled")
    use_crypto = False


class SessionState(Enum):
    Created = 0
    Activated = 1
    Closed = 2


class ServerDesc:
    def __init__(self, serv, cap=None):
        self.Server = serv
        self.Capabilities = cap


class InternalServer:
    def __init__(self, loop):
        self.loop = loop
        self.logger = logging.getLogger(__name__)
        self.server_callback_dispatcher = CallbackDispatcher()
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
        self.subscription_service: SubscriptionService = SubscriptionService(self.loop, self.aspace)
        self.history_manager = HistoryManager(self)

        self.user_manager = default_user_manager  # defined at the end of this file

        # create a session to use on server side
        self.isession = InternalSession(self, self.aspace, self.subscription_service, "Internal", user=User.Admin)
        self.current_time_node = Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))

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
        await ns_node.set_value(uries)

    async def load_standard_address_space(self, shelf_file=None):
        if shelf_file:
            is_file = (await self.loop.run_in_executor(None, os.path.isfile, shelf_file)
                       or await self.loop.run_in_executor(None, os.path.isfile, f'{shelf_file}.db'))
            if is_file:
                # import address space from shelf
                await self.loop.run_in_executor(None, self.aspace.load_aspace_shelf, shelf_file)
                return
        # import address space from code generated from xml
        standard_address_space.fill_address_space(self.node_mgt_service)
        # import address space directly from xml, this has performance impact so disabled
        # importer = xmlimporter.XmlImporter(self.node_mgt_service)
        # importer.import_xml("/path/to/python-asyncua/schemas/Opc.Ua.NodeSet2.xml", self)
        if shelf_file:
            # path was supplied, but file doesn't exist - create one for next start up
            await self.loop.run_in_executor(None, self.aspace.make_aspace_shelf, shelf_file)

    def _address_space_fixes(self) -> Coroutine:
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
        return self.isession.add_references([it, it2])

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
        await Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_State)).set_value(0, ua.VariantType.Int32)
        await Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_StartTime)).set_value(datetime.utcnow())
        if not self.disabled_clock:
            self._set_current_time()

    async def stop(self):
        self.logger.info('stopping internal server')
        await self.isession.close_session()
        await self.history_manager.stop()

    def _set_current_time(self):
        self.loop.create_task(self.current_time_node.set_value(datetime.utcnow()))
        self.loop.call_later(1, self._set_current_time)

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
                if serv_uri[:len(uri)] == uri:
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

    def create_session(self, name, user=User.Anonymous, external=False):
        return InternalSession(self, self.aspace, self.subscription_service, name, user=user, external=external)

    async def enable_history_data_change(self, node, period=timedelta(days=7), count=0):
        """
        Set attribute Historizing of node to True and start storing data for history
        """
        await node.set_attribute(ua.AttributeIds.Historizing, ua.DataValue(True))
        await node.set_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.HistoryRead)
        await node.set_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.HistoryRead)
        await self.history_manager.historize_data_change(node, period, count)

    async def disable_history_data_change(self, node):
        """
        Set attribute Historizing of node to False and stop storing data for history
        """
        await node.set_attribute(ua.AttributeIds.Historizing, ua.DataValue(False))
        await node.unset_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.HistoryRead)
        await node.unset_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.HistoryRead)
        await self.history_manager.dehistorize(node)

    async def enable_history_event(self, source, period=timedelta(days=7), count=0):
        """
        Set attribute History Read of object events to True and start storing data for history
        """
        event_notifier = await source.get_event_notifier()
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
        self.server_callback_dispatcher.addListener(event, handle)

    def unsubscribe_server_callback(self, event, handle):
        """
        Remove a subscription from event to handle
        """
        self.server_callback_dispatcher.removeListener(event, handle)

    def set_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        """
        directly write datavalue to the Attribute, bypasing some checks and structure creation
        so it is a little faster
        """
        self.aspace.set_attribute_value(nodeid, attr, datavalue)

    def set_user_manager(self, user_manager):
        """
        set up a function which that will check for authorize users. Input function takes username
        and password as paramters and returns True of user is allowed access, False otherwise.
        """
        self.user_manager = user_manager

    def check_user_token(self, isession, token):
        """
        unpack the username and password for the benefit of the user defined user manager
        """
        userName = token.UserName
        passwd = token.Password

        # decrypt password is we can
        if str(token.EncryptionAlgorithm) != "None":
            if use_crypto is False:
                return False
            try:
                if token.EncryptionAlgorithm == "http://www.w3.org/2001/04/xmlenc#rsa-1_5":
                    raw_pw = uacrypto.decrypt_rsa15(self.private_key, passwd)
                elif token.EncryptionAlgorithm == "http://www.w3.org/2001/04/xmlenc#rsa-oaep":
                    raw_pw = uacrypto.decrypt_rsa_oaep(self.private_key, passwd)
                else:
                    self.logger.warning("Unknown password encoding %s", token.EncryptionAlgorithm)
                    return False
                length = unpack_from('<I', raw_pw)[0] - len(isession.nonce)
                passwd = raw_pw[4:4 + length]
                passwd = passwd.decode('utf-8')
            except Exception:
                self.logger.exception("Unable to decrypt password")
                return False

        # call user_manager
        return self.user_manager(self, isession, userName, passwd)


class InternalSession:
    _counter = 10
    _auth_counter = 1000

    def __init__(self, internal_server, aspace, submgr, name, user=User.Anonymous, external=False):
        self.logger = logging.getLogger(__name__)
        self.iserver = internal_server
        self.external = external  # define if session is external, we need to copy some objects if it is internal
        self.aspace = aspace
        self.subscription_service = submgr
        self.name = name
        self.user = user
        self.nonce = None
        self.state = SessionState.Created
        self.session_id = ua.NodeId(self._counter)
        InternalSession._counter += 1
        self.authentication_token = ua.NodeId(self._auth_counter)
        InternalSession._auth_counter += 1
        self.logger.info('Created internal session %s', self.name)

    def __str__(self):
        return 'InternalSession(name:{0}, user:{1}, id:{2}, auth_token:{3})'.format(
            self.name, self.user, self.session_id, self.authentication_token)

    async def get_endpoints(self, params=None, sockname=None):
        return await self.iserver.get_endpoints(params, sockname)

    async def create_session(self, params, sockname=None):
        self.logger.info('Create session request')

        result = ua.CreateSessionResult()
        result.SessionId = self.session_id
        result.AuthenticationToken = self.authentication_token
        result.RevisedSessionTimeout = params.RequestedSessionTimeout
        result.MaxRequestMessageSize = 65536
        self.nonce = create_nonce(32)
        result.ServerNonce = self.nonce
        result.ServerEndpoints = await self.get_endpoints(sockname=sockname)

        return result

    async def close_session(self, delete_subs=True):
        self.logger.info('close session %s')
        self.state = SessionState.Closed
        await self.delete_subscriptions(list(self.subscription_service.subscriptions.keys()))

    def activate_session(self, params):
        self.logger.info('activate session')
        result = ua.ActivateSessionResult()
        if self.state != SessionState.Created:
            raise ServiceError(ua.StatusCodes.BadSessionIdInvalid)
        self.nonce = create_nonce(32)
        result.ServerNonce = self.nonce
        for _ in params.ClientSoftwareCertificates:
            result.Results.append(ua.StatusCode())
        self.state = SessionState.Activated
        id_token = params.UserIdentityToken
        if isinstance(id_token, ua.UserNameIdentityToken):
            if self.iserver.check_user_token(self, id_token) is False:
                raise ServiceError(ua.StatusCodes.BadUserAccessDenied)
        self.logger.info("Activated internal session %s for user %s", self.name, self.user)
        return result

    async def read(self, params):
        results = self.iserver.attribute_service.read(params)
        return results

    def history_read(self, params) -> Coroutine:
        return self.iserver.history_manager.read_history(params)

    async def write(self, params):
        return self.iserver.attribute_service.write(params, self.user)

    async def browse(self, params):
        return self.iserver.view_service.browse(params)

    async def translate_browsepaths_to_nodeids(self, params):
        return self.iserver.view_service.translate_browsepaths_to_nodeids(params)

    async def add_nodes(self, params):
        return self.iserver.node_mgt_service.add_nodes(params, self.user)

    async def delete_nodes(self, params):
        return self.iserver.node_mgt_service.delete_nodes(params, self.user)

    async def add_references(self, params):
        return self.iserver.node_mgt_service.add_references(params, self.user)

    async def delete_references(self, params):
        return self.iserver.node_mgt_service.delete_references(params, self.user)

    async def add_method_callback(self, methodid, callback):
        return self.aspace.add_method_callback(methodid, callback)

    def call(self, params):
        """COROUTINE"""
        return self.iserver.method_service.call(params)

    async def create_subscription(self, params, callback):
        result = await self.subscription_service.create_subscription(params, callback)
        return result

    async def create_monitored_items(self, params):
        """Returns Future"""
        subscription_result = await self.subscription_service.create_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(CallbackType.ItemSubscriptionCreated,
                                                         ServerItemCallback(params, subscription_result))
        return subscription_result

    def modify_monitored_items(self, params):
        subscription_result = self.subscription_service.modify_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(CallbackType.ItemSubscriptionModified,
                                                         ServerItemCallback(params, subscription_result))
        return subscription_result

    def republish(self, params):
        return self.subscription_service.republish(params)

    async def delete_subscriptions(self, ids):
        # This is an async method, dues to symetry with client code
        return await self.subscription_service.delete_subscriptions(ids)

    async def delete_monitored_items(self, params):
        # This is an async method, dues to symetry with client code
        subscription_result = self.subscription_service.delete_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(CallbackType.ItemSubscriptionDeleted,
                                                         ServerItemCallback(params, subscription_result))
        return subscription_result

    async def publish(self, acks=None):
        # This is an async method, dues to symetry with client code
        if acks is None:
            acks = []
        return self.subscription_service.publish(acks)


def default_user_manager(iserver, isession, username, password):
    """
    Default user_manager, does nothing much but check for admin
    """
    if iserver.allow_remote_admin and username in ("admin", "Admin"):
        isession.user = User.Admin
    return True
