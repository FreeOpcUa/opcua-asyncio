import logging
from enum import Enum
from typing import Coroutine, Iterable, Optional

from asyncua import ua
from ..common.callback import CallbackType, ServerItemCallback
from ..common.utils import create_nonce, ServiceError
from .address_space import AddressSpace
from .users import User
from .subscription_service import SubscriptionService


class SessionState(Enum):
    Created = 0
    Activated = 1
    Closed = 2


class InternalSession:
    """

    """
    max_connections = 1000
    _current_connections = 0
    _counter = 10
    _auth_counter = 1000

    def __init__(self, internal_server, aspace: AddressSpace, submgr: SubscriptionService, name, user=User.Anonymous, external=False):
        self.logger = logging.getLogger(__name__)
        self.iserver = internal_server
        # define if session is external, we need to copy some objects if it is internal
        self.external = external
        self.aspace: AddressSpace = aspace
        self.subscription_service: SubscriptionService = submgr
        self.name = name
        self.user = user
        self.nonce = None
        self.state = SessionState.Created
        self.session_id = ua.NodeId(self._counter)
        InternalSession._counter += 1
        self.subscriptions = []
        self.auth_token = ua.NodeId(self._auth_counter)
        InternalSession._auth_counter += 1
        self.logger.info('Created internal session %s', self.name)

    def __str__(self):
        return f'InternalSession(name:{self.name}, user:{self.user}, id:{self.session_id}, auth_token:{self.auth_token})'


    async def get_endpoints(self, params=None, sockname=None):
        return await self.iserver.get_endpoints(params, sockname)

    async def create_session(self, params, sockname=None):
        self.logger.info('Create session request')
        result = ua.CreateSessionResult()
        result.SessionId = self.session_id
        result.AuthenticationToken = self.auth_token
        result.RevisedSessionTimeout = params.RequestedSessionTimeout
        result.MaxRequestMessageSize = 65536
        self.nonce = create_nonce(32)
        result.ServerNonce = self.nonce
        result.ServerEndpoints = await self.get_endpoints(sockname=sockname)

        return result

    async def close_session(self, delete_subs=True):
        self.logger.info('close session %s', self.name)
        if self.state == SessionState.Activated:
            InternalSession._current_connections -= 1
        if InternalSession._current_connections < 0:
            InternalSession._current_connections = 0
        self.state = SessionState.Closed
        await self.delete_subscriptions(self.subscriptions)

    def activate_session(self, params):
        self.logger.info('activate session')
        result = ua.ActivateSessionResult()
        if self.state != SessionState.Created:
            raise ServiceError(ua.StatusCodes.BadSessionIdInvalid)
        if InternalSession._current_connections >= InternalSession.max_connections:
            raise ServiceError(ua.StatusCodes.BadMaxConnectionsReached)
        self.nonce = create_nonce(32)
        result.ServerNonce = self.nonce
        for _ in params.ClientSoftwareCertificates:
            result.Results.append(ua.StatusCode())
        self.state = SessionState.Activated
        InternalSession._current_connections += 1
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

    def add_method_callback(self, methodid, callback):
        return self.aspace.add_method_callback(methodid, callback)

    def call(self, params):
        """COROUTINE"""
        return self.iserver.method_service.call(params)

    async def create_subscription(self, params, callback=None):
        result = await self.subscription_service.create_subscription(params, callback, external=self.external)
        self.subscriptions.append(result.SubscriptionId)
        return result

    async def create_monitored_items(self, params: ua.CreateMonitoredItemsParameters):
        """Returns Future"""
        subscription_result = await self.subscription_service.create_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(CallbackType.ItemSubscriptionCreated,
            ServerItemCallback(params, subscription_result))
        return subscription_result

    async def modify_monitored_items(self, params):
        subscription_result = self.subscription_service.modify_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(CallbackType.ItemSubscriptionModified,
            ServerItemCallback(params, subscription_result))
        return subscription_result

    def republish(self, params):
        return self.subscription_service.republish(params)

    async def delete_subscriptions(self, ids):
        # This is an async method, dues to symmetry with client code
        return await self.subscription_service.delete_subscriptions(ids)

    async def delete_monitored_items(self, params):
        # This is an async method, dues to symmetry with client code
        subscription_result = self.subscription_service.delete_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(CallbackType.ItemSubscriptionDeleted,
            ServerItemCallback(params, subscription_result))
        return subscription_result

    def publish(self, acks: Optional[Iterable[ua.SubscriptionAcknowledgement]] = None):
        return self.subscription_service.publish(acks or [])
