from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Iterable
from enum import Enum
from typing import TYPE_CHECKING, Any

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from asyncua.crypto.permission_rules import User, UserRole

from ..common.callback import CallbackType, ServerItemCallback
from ..common.utils import ServiceError, create_nonce
from ..crypto.uacrypto import x509
from .address_space import AddressSpace
from .subscription_service import SubscriptionService

if TYPE_CHECKING:
    from .internal_server import InternalServer


class SessionState(Enum):
    Created = 0
    Activated = 1
    Closed = 2


class InternalSession(AbstractSession):
    """ """

    max_connections = 1000
    _current_connections = 0
    _counter = 10
    _auth_counter = 1000

    def __init__(
        self,
        internal_server: InternalServer,
        aspace: AddressSpace,
        submgr: SubscriptionService,
        name: str,
        user: User = User(role=UserRole.Anonymous),
        external: bool = False,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.iserver: InternalServer = internal_server
        # define if session is external, we need to copy some objects if it is internal
        self.external = external
        self.aspace: AddressSpace = aspace
        self.subscription_service: SubscriptionService = submgr
        self.name: str = name
        self.user: User = user
        self.nonce: bytes | None = None
        self.state = SessionState.Created
        self.session_id = ua.NodeId(self._counter)
        InternalSession._counter += 1
        self.auth_token = ua.NodeId(self._auth_counter)
        InternalSession._auth_counter += 1
        self.logger.info("Created internal session %s", self.name)
        self.session_timeout: float | None = None
        self._last_activity: float = time.monotonic()
        self._timeout_task: asyncio.Task[None] | None = None
        if self.external:
            self.iserver.register_external_session(self)

    def __str__(self) -> str:
        return (
            f"InternalSession(name:{self.name}, user:{self.user}, id:{self.session_id}, auth_token:{self.auth_token})"
        )

    async def get_endpoints(
        self, params: ua.GetEndpointsParameters | None = None, sockname: tuple[str, int] | None = None
    ) -> list[ua.EndpointDescription]:
        return await self.iserver.get_endpoints(params, sockname)

    def is_activated(self) -> bool:
        return self.state == SessionState.Activated

    async def create_session(
        self, params: ua.CreateSessionParameters, sockname: tuple[str, int] | None = None
    ) -> ua.CreateSessionResult:
        self.logger.info("Create session request")
        result = ua.CreateSessionResult()
        result.SessionId = self.session_id
        result.AuthenticationToken = self.auth_token
        requested_timeout_ms = float(params.RequestedSessionTimeout or 0)
        revised_ms = min(
            max(requested_timeout_ms, self.iserver.min_session_timeout_ms),
            self.iserver.max_session_timeout_ms,
        )
        if revised_ms != requested_timeout_ms:
            self.logger.info(
                "Clamping RequestedSessionTimeout %.0fms to %.0fms", requested_timeout_ms, revised_ms
            )
        result.RevisedSessionTimeout = revised_ms
        result.MaxRequestMessageSize = 65536
        self.session_timeout = result.RevisedSessionTimeout / 1000

        if self.iserver.certificate_validator and params.ClientCertificate:
            await self.iserver.certificate_validator(
                x509.load_der_x509_certificate(params.ClientCertificate), params.ClientDescription
            )

        self.nonce = create_nonce(32)
        result.ServerNonce = self.nonce

        ep_params = ua.GetEndpointsParameters()
        ep_params.EndpointUrl = params.EndpointUrl
        result.ServerEndpoints = await self.get_endpoints(params=ep_params, sockname=sockname)
        return result

    async def close_session(self, delete_subs: bool = True) -> None:
        self.logger.info("close session %s", self.name)
        if self.state == SessionState.Closed:
            return
        if self.state == SessionState.Activated:
            InternalSession._current_connections -= 1
        if InternalSession._current_connections < 0:
            InternalSession._current_connections = 0
        self.state = SessionState.Closed
        if self._timeout_task is not None and self._timeout_task is not asyncio.current_task():
            self._timeout_task.cancel()
        if self.external:
            self.iserver.unregister_external_session(self)
        if delete_subs:
            await self.delete_subscriptions(
                [id for id, sub in self.subscription_service.subscriptions.items() if sub.session_id == self.session_id]
            )

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    def _start_timeout_watchdog(self) -> None:
        if self.session_timeout is None or self.session_timeout <= 0:
            return
        if self._timeout_task is not None and not self._timeout_task.done():
            return
        self._timeout_task = asyncio.create_task(self._timeout_loop())

    async def _timeout_loop(self) -> None:
        try:
            while self.state is not SessionState.Closed:
                timeout = self.session_timeout or 0
                idle = time.monotonic() - self._last_activity
                remaining = timeout - idle
                if remaining <= 0:
                    self.logger.info("Session %s idle past %ss; closing", self.name, timeout)
                    await self.close_session(True)
                    return
                await asyncio.sleep(min(remaining, max(timeout / 4, 0.1)))
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("Session timeout watchdog crashed")

    def activate_session(
        self, params: ua.ActivateSessionParameters, peer_certificate: bytes | None
    ) -> ua.ActivateSessionResult:
        self.logger.info("activate session")
        result = ua.ActivateSessionResult()
        if self.state == SessionState.Closed:
            raise ServiceError(ua.StatusCodes.BadSessionIdInvalid)
        first_activation = self.state == SessionState.Created
        if first_activation and InternalSession._current_connections >= InternalSession.max_connections:
            raise ServiceError(ua.StatusCodes.BadMaxConnectionsReached)
        for _ in params.ClientSoftwareCertificates:
            result.Results.append(ua.StatusCode())
        id_token = params.UserIdentityToken
        if isinstance(id_token, ua.ExtensionObject) and id_token.TypeId == ua.NodeId(ua.ObjectIds.Null):
            # https://reference.opcfoundation.org/Core/Part4/v104/docs/5.6.3
            # Null or empty user token shall always be interpreted as anonymous.
            id_token = ua.AnonymousIdentityToken()
        # Check if security policy is supported
        if not isinstance(id_token, self.iserver.supported_tokens):
            self.logger.error("Rejected active session UserIdentityToken not supported")
            raise ServiceError(ua.StatusCodes.BadIdentityTokenRejected)
        if self.iserver.user_manager is not None:
            try:
                if isinstance(id_token, ua.UserNameIdentityToken):
                    username, password = self.iserver.decrypt_user_token(self, id_token)
                elif isinstance(id_token, ua.X509IdentityToken):
                    peer_certificate = self.iserver.verify_x509_token(self, id_token, params.UserTokenSignature)
                    username, password = None, None
                else:
                    username, password = None, None
            except (ServiceError, ua.uaerrors.UaStatusCodeError):
                raise
            except Exception:
                raise ServiceError(ua.StatusCodes.BadIdentityTokenInvalid)

            user = self.iserver.user_manager.get_user(
                self.iserver, username=username, password=password, certificate=peer_certificate
            )
            if user is None:
                raise ServiceError(ua.StatusCodes.BadUserAccessDenied)
            self.user = user
        self.nonce = create_nonce(32)
        result.ServerNonce = self.nonce
        self.state = SessionState.Activated
        if first_activation:
            InternalSession._current_connections += 1
        self.touch()
        self._start_timeout_watchdog()
        self.logger.info("Activated internal session %s for user %s", self.name, self.user)
        return result

    async def read(self, params: ua.ReadParameters) -> list[ua.DataValue]:
        if self.user is None:
            user = User()
        else:
            user = self.user
        await self.iserver.callback_service.dispatch(
            CallbackType.PreRead, ServerItemCallback(params, None, user, self.external)
        )
        results = self.iserver.attribute_service.read(params)
        await self.iserver.callback_service.dispatch(
            CallbackType.PostRead, ServerItemCallback(params, results, user, self.external)
        )
        return results

    async def history_read(self, params: ua.HistoryReadParameters) -> list[ua.HistoryReadResult]:
        return await self.iserver.history_manager.read_history(params)

    async def write(self, params: ua.WriteParameters) -> list[ua.StatusCode]:
        if self.user is None:
            user = User()
        else:
            user = self.user
        await self.iserver.callback_service.dispatch(
            CallbackType.PreWrite, ServerItemCallback(params, None, user, self.external)
        )
        write_result = await self.iserver.attribute_service.write(params, user=user)
        await self.iserver.callback_service.dispatch(
            CallbackType.PostWrite, ServerItemCallback(params, write_result, user, self.external)
        )
        return write_result

    async def browse(self, params: ua.BrowseParameters) -> list[ua.BrowseResult]:
        return self.iserver.view_service.browse(params)

    async def browse_next(self, parameters: ua.BrowseNextParameters) -> list[ua.BrowseResult]:
        # TODO
        # ContinuationPoint: https://reference.opcfoundation.org/v104/Core/docs/Part4/7.6/
        # Add "ContinuationPoints" and some form of management for them to current sessionimplementation
        # BrowseNext: https://reference.opcfoundation.org/Core/Part4/v104/5.8.3/
        raise NotImplementedError

    async def register_nodes(self, nodes: list[ua.NodeId]) -> list[ua.NodeId]:
        self.logger.info("Node registration not implemented")
        return nodes

    async def unregister_nodes(self, nodes: list[ua.NodeId]) -> None:
        self.logger.info("Node registration not implemented")

    async def translate_browsepaths_to_nodeids(
        self, params: list[ua.BrowsePath]
    ) -> list[ua.BrowsePathResult]:
        return self.iserver.view_service.translate_browsepaths_to_nodeids(params)

    async def add_nodes(self, params: list[ua.AddNodesItem]) -> list[ua.AddNodesResult]:
        return self.iserver.node_mgt_service.add_nodes(params, self.user)

    async def delete_nodes(self, params: ua.DeleteNodesParameters) -> list[ua.StatusCode]:
        return self.iserver.node_mgt_service.delete_nodes(params, self.user)

    async def add_references(self, params: list[ua.AddReferencesItem]) -> list[ua.StatusCode]:
        return self.iserver.node_mgt_service.add_references(params, self.user)

    async def delete_references(self, params: list[ua.DeleteReferencesItem]) -> list[ua.StatusCode]:
        return self.iserver.node_mgt_service.delete_references(params, self.user)

    def add_method_callback(self, methodid: ua.NodeId, callback: Callable[..., Any]) -> ua.StatusCode:
        return self.aspace.add_method_callback(methodid, callback)

    async def call(self, params: list[ua.CallMethodRequest]) -> list[ua.CallMethodResult]:
        """COROUTINE"""
        return await self.iserver.method_service.call(params)

    async def create_subscription(
        self,
        params: ua.CreateSubscriptionParameters,
        callback: Callable[..., Any],
        request_callback: Callable[..., Any] | None = None,
    ) -> ua.CreateSubscriptionResult:
        result = await self.subscription_service.create_subscription(
            params, callback, self.session_id, request_callback=request_callback
        )
        return result

    async def create_monitored_items(
        self, params: ua.CreateMonitoredItemsParameters
    ) -> list[ua.MonitoredItemCreateResult]:
        """Returns Future"""
        subscription_result = await self.subscription_service.create_monitored_items(params)
        await self.iserver.callback_service.dispatch(
            CallbackType.ItemSubscriptionCreated, ServerItemCallback(params, subscription_result, None, self.external)
        )
        return subscription_result

    async def modify_monitored_items(
        self, params: ua.ModifyMonitoredItemsParameters
    ) -> list[ua.MonitoredItemModifyResult]:
        subscription_result = self.subscription_service.modify_monitored_items(params)
        await self.iserver.callback_service.dispatch(
            CallbackType.ItemSubscriptionModified, ServerItemCallback(params, subscription_result, None, self.external)
        )
        return subscription_result

    def republish(self, params: ua.RepublishParameters) -> ua.NotificationMessage:
        return self.subscription_service.republish(params)

    async def delete_subscriptions(self, ids: list[int]) -> list[ua.StatusCode]:
        return await self.subscription_service.delete_subscriptions(ids)

    async def delete_monitored_items(
        self, params: ua.DeleteMonitoredItemsParameters
    ) -> list[ua.StatusCode]:
        # This is an async method, dues to symmetry with client code
        subscription_result = self.subscription_service.delete_monitored_items(params)
        await self.iserver.callback_service.dispatch(
            CallbackType.ItemSubscriptionDeleted, ServerItemCallback(params, subscription_result, None, self.external)
        )

        return subscription_result

    def publish(self, acks: Iterable[ua.SubscriptionAcknowledgement] | None = None) -> None:
        return self.subscription_service.publish(acks or [])

    def modify_subscription(
        self, params: ua.ModifySubscriptionParameters
    ) -> ua.ModifySubscriptionResult:
        # Sync because the underlying service is sync; the client-side UaSession
        # is async (RPC). Not part of AbstractSession because the shapes diverge.
        return self.subscription_service.modify_subscription(params)

    # The server-side override takes an extra `callback` (the per-connection
    # publish-response callback owned by the UaProcessor handling the transfer
    # request) so the rebound InternalSubscription delivers future publishes
    # to the new connection's socket. The client-side override has no such
    # need, hence the signature divergence.
    async def transfer_subscriptions(  # type: ignore[override]
        self, params: ua.TransferSubscriptionsParameters, callback: Callable[..., Any]
    ) -> list[ua.TransferResult]:
        return await self.subscription_service.transfer_subscriptions(params, self.session_id, callback)
