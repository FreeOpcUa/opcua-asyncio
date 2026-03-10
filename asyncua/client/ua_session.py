"""
OPC-UA Session implementation handling session-specific services and subscriptions.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from asyncua.ua.ua_binary import struct_from_binary
from asyncua.ua.uaprotocol_auto import SubscriptionAcknowledgement

if TYPE_CHECKING:
    from asyncua.client.ua_client import UaClient


class SubscriptionStaleError(ConnectionError):
    """Raised when subscriptions are detected as stale."""

    def __init__(self, subscription_ids: list[int]) -> None:
        self.subscription_ids = subscription_ids
        super().__init__(
            f"Stale subscriptions with no Publish messages: {subscription_ids}"
        )


class SubscriptionDispatchOverflowError(ConnectionError):
    """Raised when subscription dispatch queue overflows."""

    def __init__(self, subscription_id: int, queue_size: int) -> None:
        self.subscription_id = subscription_id
        self.queue_size = queue_size
        super().__init__(
            f"Subscription dispatch queue overflow for subscription "
            f"{subscription_id} at size {queue_size}"
        )


class SubscriptionDispatchOverflowPolicy(str, Enum):
    """Policy for handling subscription dispatch queue overflow."""

    DROP_OLDEST = "drop_oldest"
    WARN = "warn"
    DISCONNECT = "disconnect"


class SessionState(str, Enum):
    IDLE = "idle"
    ESTABLISHING = "establishing"
    READY = "ready"
    SUSPENDED = "suspended"
    RECOVERING = "recovering"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass
class _SubscriptionWatchdogState:
    """Tracks watchdog state for subscription staleness detection."""

    publishing_interval_ms: float
    keepalive_count: int
    last_seen_at: float
    stale_reported: bool = False


@dataclass
class _DispatchSettings:
    """Settings for subscription dispatch behavior."""

    queue_maxsize: int = 1000
    overflow_policy: (
        SubscriptionDispatchOverflowPolicy | str
    ) = SubscriptionDispatchOverflowPolicy.DROP_OLDEST


@dataclass
class _SequenceRecoverySettings:
    """Settings for subscription sequence number recovery."""

    auto_republish_on_gap: bool = True
    max_republish_messages_per_gap: int = 1000


@dataclass
class _WatchdogSettings:
    """Settings for subscription watchdog monitoring."""

    stale_detection_enabled: bool = True
    stale_detection_margin: float = 1.2


@dataclass
class _SubscriptionDispatchRuntime:
    """Runtime state for subscription dispatch worker."""

    queue: asyncio.Queue[ua.PublishResult | None]
    task: asyncio.Task[None] | None = None


def _compute_republish_window(
    expected_sequence: int,
    received_sequence: int,
    max_republish: int,
) -> tuple[int, int] | None:
    """Compute republish window for gap recovery."""
    if received_sequence <= expected_sequence:
        return None
    if max_republish <= 0:
        return None

    missing_count = received_sequence - expected_sequence
    replay_end_exclusive = received_sequence
    if missing_count > max_republish:
        replay_end_exclusive = expected_sequence + max_republish
    return expected_sequence, replay_end_exclusive


def _build_publish_ack(
    subscription_id: int,
    notification_message: ua.NotificationMessage,
) -> SubscriptionAcknowledgement | None:
    """Build subscription acknowledgement from notification message."""
    if not notification_message.NotificationData:
        return None
    ack = ua.SubscriptionAcknowledgement()
    ack.SubscriptionId = subscription_id
    ack.SequenceNumber = notification_message.SequenceNumber
    return ack


async def _invoke_subscription_callback(
    callback: Callable[[ua.PublishResult], Any],
    publish_result: ua.PublishResult,
) -> None:
    """Invoke subscription callback, handling both sync and async."""
    result = callback(publish_result)
    if inspect.isawaitable(result):
        await result


class UaSession(AbstractSession):
    """
    OPC-UA Session managing session-specific operations and subscriptions.

    Handles:
    - Session-scoped services and session closure handling
    - Subscriptions and monitored items
    - Publish/subscription loop with gap recovery
    - Watchdog monitoring for subscription staleness

    Session creation and activation are handled by UaClient.
    """

    def __init__(
        self,
        client: "UaClient",
        session_id: ua.NodeId,
        authentication_token: ua.NodeId,
    ) -> None:
        """Initialize session.

        Args:
            client: Parent UaClient (sessionless component)
            session_id: Session identifier from server
            authentication_token: Token for server authentication
        """
        self.logger = logging.getLogger(f"{__name__}.UaSession")
        self.client = client
        self.session_id = session_id
        self.authentication_token = authentication_token

        # Subscription management
        self._subscription_callbacks: dict[int, Callable[[ua.PublishResult], Any]] = (
            {}
        )
        self._subscription_dispatch_runtime: dict[int, _SubscriptionDispatchRuntime] = (
            {}
        )
        self._last_publish_sequence_numbers: dict[int, int] = {}
        self._subscription_watchdog_states: dict[int, _SubscriptionWatchdogState] = {}

        # Configuration
        self.dispatch_settings = _DispatchSettings()
        self.sequence_recovery_settings = _SequenceRecoverySettings()
        self.watchdog_settings = _WatchdogSettings()

        # Lifecycle
        self._publish_task: asyncio.Task[None] | None = None
        self._closing = False
        self._disconnect_event = asyncio.Event()
        self._ready_event = asyncio.Event()
        self._state: SessionState = SessionState.IDLE

    @property
    def state(self) -> SessionState:
        return self._state

    def _set_state(self, state: SessionState) -> None:
        self._state = state
        if state == SessionState.READY:
            self._ready_event.set()
            return
        self._ready_event.clear()

    async def await_ready(self, timeout: float | None = None) -> None:
        if self._state == SessionState.READY:
            return
        wait_timeout = self.client._timeout if timeout is None else timeout
        try:
            await asyncio.wait_for(self._ready_event.wait(), wait_timeout)
        except (TimeoutError, asyncio.TimeoutError) as ex:
            raise ConnectionError("Session is not ready") from ex

    def on_transport_lost(self) -> None:
        if self._state in (SessionState.CLOSING, SessionState.CLOSED):
            return
        self._set_state(SessionState.SUSPENDED)

    def on_transport_restored(self) -> None:
        if self._state in (SessionState.CLOSING, SessionState.CLOSED):
            return
        self._set_state(SessionState.RECOVERING)

    async def _send_session_request(
        self,
        request: ua.BaseRequest,
        timeout: float | None = None,
        bypass_ready_gate: bool = False,
    ) -> bytes:
        if not bypass_ready_gate:
            await self.await_ready(timeout=timeout)
        return await self.client._send_request(
            request,
            timeout=timeout,
            bypass_ready_gate=bypass_ready_gate,
            authentication_token=self.authentication_token,
        )

    @property
    def subscription_dispatch_queue_maxsize(self) -> int:
        """Get max size for subscription dispatch queue."""
        return self.dispatch_settings.queue_maxsize

    @subscription_dispatch_queue_maxsize.setter
    def subscription_dispatch_queue_maxsize(self, value: int) -> None:
        """Set max size for subscription dispatch queue."""
        self.dispatch_settings.queue_maxsize = int(value)

    @property
    def subscription_dispatch_overflow_policy(
        self,
    ) -> SubscriptionDispatchOverflowPolicy | str:
        """Get policy for dispatch queue overflow handling."""
        return self.dispatch_settings.overflow_policy

    @subscription_dispatch_overflow_policy.setter
    def subscription_dispatch_overflow_policy(
        self, value: SubscriptionDispatchOverflowPolicy | str
    ) -> None:
        """Set policy for dispatch queue overflow handling."""
        self.dispatch_settings.overflow_policy = value

    @property
    def subscription_stale_detection_enabled(self) -> bool:
        """Get whether stale subscription detection is enabled."""
        return self.watchdog_settings.stale_detection_enabled

    @subscription_stale_detection_enabled.setter
    def subscription_stale_detection_enabled(self, value: bool) -> None:
        """Set whether stale subscription detection is enabled."""
        self.watchdog_settings.stale_detection_enabled = bool(value)

    @property
    def subscription_stale_detection_margin(self) -> float:
        """Get margin for stale subscription detection."""
        return self.watchdog_settings.stale_detection_margin

    @subscription_stale_detection_margin.setter
    def subscription_stale_detection_margin(self, value: float) -> None:
        """Set margin for stale subscription detection."""
        self.watchdog_settings.stale_detection_margin = float(value)

    @property
    def auto_republish_on_sequence_gap(self) -> bool:
        """Get whether to auto-republish on sequence gaps."""
        return self.sequence_recovery_settings.auto_republish_on_gap

    @auto_republish_on_sequence_gap.setter
    def auto_republish_on_sequence_gap(self, value: bool) -> None:
        """Set whether to auto-republish on sequence gaps."""
        self.sequence_recovery_settings.auto_republish_on_gap = bool(value)

    @property
    def max_republish_messages_per_gap(self) -> int:
        """Get max messages to republish per gap."""
        return self.sequence_recovery_settings.max_republish_messages_per_gap

    @max_republish_messages_per_gap.setter
    def max_republish_messages_per_gap(self, value: int) -> None:
        """Set max messages to republish per gap."""
        self.sequence_recovery_settings.max_republish_messages_per_gap = int(value)

    # Session Service Set methods (from AbstractSession)

    async def browse(self, parameters: ua.BrowseParameters) -> list[ua.BrowseResult]:
        """Browse node references."""
        self.logger.debug("browse")
        request = ua.BrowseRequest()
        request.Parameters = parameters
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.BrowseResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def browse_next(
        self, parameters: ua.BrowseNextParameters
    ) -> list[ua.BrowseResult]:
        """Browse next set of results."""
        self.logger.debug("browse_next")
        request = ua.BrowseNextRequest()
        request.Parameters = parameters
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.BrowseNextResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def read(self, parameters: ua.ReadParameters) -> list[ua.DataValue]:
        """Read node attributes."""
        self.logger.debug("read")
        request = ua.ReadRequest()
        request.Parameters = parameters
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.ReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def write(self, parameters: ua.WriteParameters) -> list[ua.StatusCode]:
        """Write node attributes."""
        self.logger.debug("write")
        request = ua.WriteRequest()
        request.Parameters = parameters
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.WriteResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def history_read(
        self, params: ua.HistoryReadParameters
    ) -> list[ua.HistoryReadResult]:
        """Read node history."""
        self.logger.debug("history_read")
        request = ua.HistoryReadRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.HistoryReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_nodes(self, params: ua.AddNodesParameters | list[ua.AddNodesItem]) -> list[ua.AddNodesResult]:
        """Add nodes to address space."""
        self.logger.debug("add_nodes")
        request = ua.AddNodesRequest()
        if isinstance(params, list):
            request.Parameters = ua.AddNodesParameters()
            request.Parameters.NodesToAdd = params
        else:
            request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.AddNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_references(
        self, refs: list[ua.AddReferencesItem]
    ) -> list[ua.StatusCode]:
        """Add references to address space."""
        self.logger.debug("add_references")
        request = ua.AddReferencesRequest()
        request.Parameters.ReferencesToAdd = refs
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.AddReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_nodes(
        self, params: ua.DeleteNodesParameters
    ) -> list[ua.StatusCode]:
        """Delete nodes from address space."""
        self.logger.debug("delete_nodes")
        request = ua.DeleteNodesRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.DeleteNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_references(
        self, refs: list[ua.DeleteReferencesItem]
    ) -> list[ua.StatusCode]:
        """Delete references from address space."""
        self.logger.debug("delete_references")
        request = ua.DeleteReferencesRequest()
        request.Parameters.ReferencesToDelete = refs
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.DeleteReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def call(
        self, methodstocall: list[ua.CallMethodRequest]
    ) -> list[ua.CallMethodResult]:
        """Call methods."""
        self.logger.debug("call")
        request = ua.CallRequest()
        request.Parameters.MethodsToCall = methodstocall
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.CallResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def translate_browsepaths_to_nodeids(
        self, browse_paths: list[ua.BrowsePath]
    ) -> list[ua.BrowsePathResult]:
        """Translate browse paths to node IDs."""
        self.logger.debug("translate_browsepath_to_nodeid")
        request = ua.TranslateBrowsePathsToNodeIdsRequest()
        request.Parameters.BrowsePaths = browse_paths
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.TranslateBrowsePathsToNodeIdsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def register_nodes(self, nodes: list[ua.NodeId]) -> list[ua.NodeId]:
        """Register nodes for optimized access."""
        self.logger.debug("register_nodes")
        request = ua.RegisterNodesRequest()
        request.Parameters.NodesToRegister = nodes
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.RegisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.RegisteredNodeIds

    async def unregister_nodes(self, nodes: list[ua.NodeId]) -> list[ua.NodeId]:
        """Unregister nodes."""
        self.logger.debug("unregister_nodes")
        request = ua.UnregisterNodesRequest()
        request.Parameters.NodesToUnregister = nodes
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.UnregisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.UnregisteredNodeIds

    # Subscription Service Set methods

    async def create_subscription(
        self, params: ua.CreateSubscriptionParameters, callback: Callable
    ) -> ua.CreateSubscriptionResult:
        """Create a subscription."""
        self.logger.debug("create_subscription")
        request = ua.CreateSubscriptionRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.CreateSubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        subscription_id = response.Parameters.SubscriptionId
        self._subscription_callbacks[subscription_id] = callback
        
        publishing_interval_ms = float(
            getattr(
                response.Parameters,
                "RevisedPublishingInterval",
                params.RequestedPublishingInterval or 0.0,
            )
            or 0.0
        )
        keepalive_count = int(
            getattr(
                response.Parameters,
                "RevisedMaxKeepAliveCount",
                params.RequestedMaxKeepAliveCount or 1,
            )
            or 1
        )
        self._register_subscription_watchdog(
            subscription_id, publishing_interval_ms, keepalive_count
        )
        self.logger.info("Subscription created: %s", subscription_id)
        self._ensure_subscription_dispatch_worker(subscription_id)
        
        if self._publish_task is None or self._publish_task.done():
            self._publish_task = asyncio.create_task(self._publish_loop())
        
        return response.Parameters

    async def modify_subscription(
        self, params: ua.ModifySubscriptionParameters
    ) -> ua.ModifySubscriptionResult:
        """Modify a subscription."""
        self.logger.debug("modify_subscription")
        request = ua.ModifySubscriptionRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.ModifySubscriptionResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters

    async def delete_subscriptions(
        self, params: ua.DeleteSubscriptionsParameters
    ) -> list[ua.StatusCode]:
        """Delete subscriptions."""
        self.logger.debug("delete_subscriptions")
        request = ua.DeleteSubscriptionsRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.DeleteSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        for subscription_id in params.SubscriptionIds:
            self._stop_subscription_dispatch_worker(subscription_id)
            self._subscription_callbacks.pop(subscription_id, None)
            self._last_publish_sequence_numbers.pop(subscription_id, None)
            self._subscription_watchdog_states.pop(subscription_id, None)
        return response.Results

    async def create_monitored_items(
        self, params: ua.CreateMonitoredItemsParameters
    ) -> list[ua.MonitoredItemCreateResult]:
        """Create monitored items."""
        self.logger.debug("create_monitored_items")
        request = ua.CreateMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.CreateMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def modify_monitored_items(
        self, params: ua.ModifyMonitoredItemsParameters
    ) -> list[ua.MonitoredItemModifyResult]:
        """Modify monitored items."""
        self.logger.debug("modify_monitored_items")
        request = ua.ModifyMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.ModifyMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_monitored_items(
        self, params: ua.DeleteMonitoredItemsParameters
    ) -> list[ua.StatusCode]:
        """Delete monitored items."""
        self.logger.debug("delete_monitored_items")
        request = ua.DeleteMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.DeleteMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def transfer_subscriptions(
        self, params: ua.TransferSubscriptionsParameters
    ) -> list[ua.TransferResult]:
        """Transfer subscriptions to another session."""
        self.logger.debug("transfer_subscriptions")
        request = ua.TransferSubscriptionsRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.TransferSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def set_monitoring_mode(
        self, params: ua.SetMonitoringModeParameters
    ) -> list[ua.StatusCode]:
        """Set monitoring mode for monitored items."""
        self.logger.debug("set_monitoring_mode")
        request = ua.SetMonitoringModeRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.SetMonitoringModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def set_publishing_mode(
        self, params: ua.SetPublishingModeParameters
    ) -> list[ua.StatusCode]:
        """Set publishing mode for subscriptions."""
        self.logger.debug("set_publishing_mode")
        request = ua.SetPublishingModeRequest()
        request.Parameters = params
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.SetPublishingModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    # Subscription dispatch and monitoring infrastructure

    def _ensure_subscription_dispatch_worker(self, subscription_id: int) -> None:
        """Ensure dispatch worker task is running for subscription."""
        if subscription_id not in self._subscription_dispatch_runtime:
            queue: asyncio.Queue[ua.PublishResult | None] = asyncio.Queue(
                maxsize=self.dispatch_settings.queue_maxsize
            )
            task = asyncio.create_task(self._subscription_dispatch_worker(subscription_id))
            self._subscription_dispatch_runtime[subscription_id] = _SubscriptionDispatchRuntime(
                queue=queue, task=task
            )

    def _stop_subscription_dispatch_worker(self, subscription_id: int) -> None:
        """Stop dispatch worker task for subscription."""
        runtime = self._subscription_dispatch_runtime.pop(subscription_id, None)
        if runtime is not None and runtime.task is not None:
            runtime.task.cancel()

    def _get_dispatch_queue(
        self, subscription_id: int
    ) -> asyncio.Queue[ua.PublishResult | None] | None:
        """Get dispatch queue for subscription."""
        runtime = self._subscription_dispatch_runtime.get(subscription_id)
        if runtime is None:
            return None
        return runtime.queue

    def _register_subscription_watchdog(
        self, subscription_id: int, publishing_interval_ms: float, keepalive_count: int
    ) -> None:
        """Register watchdog for subscription."""
        if publishing_interval_ms <= 0:
            self._subscription_watchdog_states.pop(subscription_id, None)
            return
        self._subscription_watchdog_states[subscription_id] = _SubscriptionWatchdogState(
            publishing_interval_ms=publishing_interval_ms,
            keepalive_count=max(int(keepalive_count), 1),
            last_seen_at=time.monotonic(),
        )

    def _mark_subscription_watchdog_activity(self, subscription_id: int) -> None:
        """Mark activity for subscription watchdog."""
        state = self._subscription_watchdog_states.get(subscription_id)
        if state is None:
            return
        state.last_seen_at = time.monotonic()
        state.stale_reported = False

    def _get_stale_subscription_ids(self, now: float) -> list[int]:
        """Get list of stale subscription IDs."""
        if not self.watchdog_settings.stale_detection_enabled:
            return []
        stale_subscription_ids: list[int] = []
        margin = max(self.watchdog_settings.stale_detection_margin, 1.0)
        stale_state_ids_to_prune: list[int] = []
        for subscription_id, state in self._subscription_watchdog_states.items():
            if subscription_id not in self._subscription_callbacks:
                stale_state_ids_to_prune.append(subscription_id)
                continue
            timeout = (
                (state.publishing_interval_ms / 1000.0) * state.keepalive_count * margin
            )
            if timeout <= 0:
                continue
            if (now - state.last_seen_at) <= timeout:
                continue
            if state.stale_reported:
                continue
            state.stale_reported = True
            stale_subscription_ids.append(subscription_id)
        for stale_state_id in stale_state_ids_to_prune:
            self._subscription_watchdog_states.pop(stale_state_id, None)
        return stale_subscription_ids

    def get_next_sequence_number(self, subscription_id: int) -> int:
        """Get next expected sequence number for subscription."""
        last_sequence = self._last_publish_sequence_numbers.get(subscription_id, 0)
        return last_sequence + 1

    def _record_notification_sequence_number(
        self,
        subscription_id: int,
        notification_message: ua.NotificationMessage,
        source: str = "publish",
    ) -> None:
        """Record notification sequence number for gap detection."""
        self._last_publish_sequence_numbers[subscription_id] = (
            notification_message.SequenceNumber
        )

    def get_subscription_ids(self) -> list[int]:
        """Get list of active subscription IDs."""
        return list(self._subscription_callbacks.keys())

    def _enqueue_with_drop_oldest(
        self,
        queue: asyncio.Queue[ua.PublishResult | None],
        subscription_id: int,
        publish_result: ua.PublishResult,
    ) -> bool:
        """Drop oldest item in queue to make room for new one."""
        dropped = False
        try:
            oldest = queue.get_nowait()
            queue.task_done()
            dropped = True
            if oldest is None:
                queue.put_nowait(None)
        except asyncio.QueueEmpty:
            pass
        try:
            queue.put_nowait(publish_result)
        except asyncio.QueueFull:
            self.logger.warning(
                "Subscription %s dispatch queue full after drop; dropping newest",
                subscription_id,
            )
            return False
        if dropped:
            self.logger.warning(
                "Subscription %s dispatch queue overflow; dropped oldest",
                subscription_id,
            )
        return True

    def _enqueue_with_disconnect_policy(
        self,
        queue: asyncio.Queue[ua.PublishResult | None],
        subscription_id: int,
    ) -> bool:
        """Treat overflow as fatal, signal disconnect."""
        overflow_error = SubscriptionDispatchOverflowError(
            subscription_id, queue.qsize()
        )
        self.logger.error("%s", overflow_error)
        self._fail_all_dispatch_workers(overflow_error)
        self._closing = True
        return False

    def _enqueue_with_warn_policy(self, subscription_id: int) -> bool:
        """Log warning and drop newest item."""
        self.logger.warning(
            "Subscription %s dispatch queue overflow; dropping newest",
            subscription_id,
        )
        return False

    def _resolve_overflow_policy(self) -> SubscriptionDispatchOverflowPolicy:
        """Normalize and validate overflow policy setting."""
        policy = self.subscription_dispatch_overflow_policy
        if isinstance(policy, SubscriptionDispatchOverflowPolicy):
            return policy
        if isinstance(policy, str):
            normalized = policy.strip().lower()
            for candidate in SubscriptionDispatchOverflowPolicy:
                if candidate.value == normalized:
                    self.subscription_dispatch_overflow_policy = candidate
                    return candidate
            self.logger.warning(
                "Unknown overflow policy '%s'; fallback to WARN",
                policy,
            )
            self.subscription_dispatch_overflow_policy = (
                SubscriptionDispatchOverflowPolicy.WARN
            )
            return SubscriptionDispatchOverflowPolicy.WARN
        self.logger.warning(
            "Unsupported overflow policy type '%s'; fallback to WARN",
            type(policy).__name__,
        )
        self.subscription_dispatch_overflow_policy = (
            SubscriptionDispatchOverflowPolicy.WARN
        )
        return SubscriptionDispatchOverflowPolicy.WARN

    def _enqueue_when_full(
        self,
        queue: asyncio.Queue[ua.PublishResult | None],
        subscription_id: int,
        publish_result: ua.PublishResult,
    ) -> bool:
        """Enqueue with overflow handling based on configured policy."""
        policy = self._resolve_overflow_policy()
        if policy == SubscriptionDispatchOverflowPolicy.DROP_OLDEST:
            return self._enqueue_with_drop_oldest(queue, subscription_id, publish_result)
        if policy == SubscriptionDispatchOverflowPolicy.DISCONNECT:
            return self._enqueue_with_disconnect_policy(queue, subscription_id)
        if policy == SubscriptionDispatchOverflowPolicy.WARN:
            return self._enqueue_with_warn_policy(subscription_id)
        return self._enqueue_with_warn_policy(subscription_id)

    def _enqueue_publish_result(
        self, subscription_id: int, publish_result: ua.PublishResult
    ) -> bool:
        """Enqueue publish result for subscription, handling overflow."""
        callback = self._subscription_callbacks.get(subscription_id)
        if callback is None:
            self.logger.warning(
                "Publish result for unknown subscription %s",
                subscription_id,
            )
            return False
        queue = self._get_dispatch_queue(subscription_id)
        if queue is None:
            return False
        if not queue.full():
            queue.put_nowait(publish_result)
            return True
        return self._enqueue_when_full(queue, subscription_id, publish_result)

    def _fail_all_dispatch_workers(self, exc: Exception) -> None:
        """Signal all dispatch workers to stop with error."""
        self.logger.error("Stopping all subscription dispatch workers: %s", exc)
        for runtime in self._subscription_dispatch_runtime.values():
            task = runtime.task
            if task is not None and not task.done():
                task.cancel()
        self._subscription_dispatch_runtime.clear()

    async def _subscription_dispatch_worker(
        self, subscription_id: int
    ) -> None:
        """Process queued notifications for subscription."""
        runtime = self._subscription_dispatch_runtime.get(subscription_id)
        if runtime is None:
            return
        queue = runtime.queue
        while True:
            publish_result = await queue.get()
            try:
                if publish_result is None:
                    return
                callback = self._subscription_callbacks.get(subscription_id)
                if callback is None:
                    self.logger.warning(
                        "Queued result for unknown subscription %s",
                        subscription_id,
                    )
                    continue
                await _invoke_subscription_callback(callback, publish_result)
            except Exception:
                self.logger.exception(
                    "Exception in subscription callback"
                )
            finally:
                queue.task_done()

    async def flush_subscription_dispatch(
        self,
        subscription_ids: list[int] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Wait for all queued notifications to be processed."""
        if subscription_ids is None:
            queues = [
                runtime.queue
                for runtime in self._subscription_dispatch_runtime.values()
            ]
        else:
            queues = [
                self._subscription_dispatch_runtime[subscription_id].queue
                for subscription_id in subscription_ids
                if subscription_id in self._subscription_dispatch_runtime
            ]
        if not queues:
            return
        awaitable = asyncio.gather(*(queue.join() for queue in queues))
        if timeout is None:
            await awaitable
        else:
            await asyncio.wait_for(awaitable, timeout)

    async def _recover_sequence_gap(
        self,
        subscription_id: int,
        expected_sequence: int,
        received_sequence: int,
    ) -> None:
        """Republish missing notifications from sequence gap."""
        window = _compute_republish_window(
            expected_sequence,
            received_sequence,
            self.sequence_recovery_settings.max_republish_messages_per_gap,
        )
        if window is None:
            return
        start_sequence, end_sequence = window
        for sequence_number in range(start_sequence, end_sequence):
            try:
                notif_msg = await self.republish(subscription_id, sequence_number)
                await self.dispatch_notification_message(subscription_id, notif_msg)
            except Exception:
                self.logger.exception(
                    "Gap recovery failed for subscription %s sequence %s",
                    subscription_id,
                    sequence_number,
                )
                break

    async def republish(
        self, subscription_id: int, retransmit_sequence_number: int
    ) -> ua.NotificationMessage:
        """Request republish of specific notification."""
        self.logger.debug("republish")
        request = ua.RepublishRequest()
        request.Parameters.SubscriptionId = subscription_id
        request.Parameters.RetransmitSequenceNumber = retransmit_sequence_number
        data = await self._send_session_request(request)
        response = struct_from_binary(ua.RepublishResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        # RepublishResponse can expose NotificationMessage directly (spec-compliant)
        # or behind a Parameters object in older generated protocol code.
        params = getattr(response, "Parameters", None)
        if params is not None:
            return params.NotificationMessage
        return response.NotificationMessage

    async def publish(
        self, acks: list[ua.SubscriptionAcknowledgement]
    ) -> ua.PublishResponse:
        """Send PublishRequest to server."""
        self.logger.debug("publish %r", acks)
        request = ua.PublishRequest()
        request.Parameters.SubscriptionAcknowledgements = acks if acks else []
        await self.await_ready()
        data = await self.client._send_request(
            request,
            timeout=0,
            authentication_token=self.authentication_token,
        )
        protocol = self.client.protocol
        if protocol is None:
            raise ConnectionError("Connection is closed")
        protocol.check_answer(data, "in publish response")
        try:
            response = struct_from_binary(ua.PublishResponse, data)
        except Exception as ex:
            self.logger.exception("Error parsing notification")
            from asyncua.ua.uaerrors import UaStructParsingError
            raise UaStructParsingError from ex
        return response

    async def _read_publish_response(
        self,
        ack: SubscriptionAcknowledgement | None,
    ) -> ua.PublishResponse | None:
        """Read publish response, handling timeouts and errors."""
        from asyncua.ua.uaerrors import BadTimeout, BadNoSubscription
        try:
            return await self.publish([ack] if ack else [])
        except BadTimeout:
            return None
        except BadNoSubscription:
            self.logger.info("BadNoSubscription in publish loop")
            raise
        except Exception:
            self.logger.exception("Unexpected error while reading publish response")
            return None

    async def _maybe_recover_gap(
        self,
        subscription_id: int,
        notification_message: ua.NotificationMessage,
    ) -> None:
        """Check for sequence gaps and recover if enabled."""
        if (
            not self.sequence_recovery_settings.auto_republish_on_gap
            or not notification_message.NotificationData
            or subscription_id not in self._last_publish_sequence_numbers
        ):
            return
        expected_sequence = self.get_next_sequence_number(subscription_id)
        received_sequence = int(notification_message.SequenceNumber)
        if received_sequence > expected_sequence:
            await self._recover_sequence_gap(
                subscription_id, expected_sequence, received_sequence
            )

    async def _handle_publish_response(
        self, response: ua.PublishResponse
    ) -> SubscriptionAcknowledgement | None:
        """Process publish response and dispatch notifications."""
        from asyncua.ua.uaerrors import BadNoSubscription
        subscription_id = response.Parameters.SubscriptionId
        if not subscription_id:
            raise BadNoSubscription()

        self._mark_subscription_watchdog_activity(subscription_id)
        stale_ids = self._get_stale_subscription_ids(time.monotonic())
        if stale_ids:
            raise SubscriptionStaleError(stale_ids)

        notification_message = response.Parameters.NotificationMessage
        await self._maybe_recover_gap(subscription_id, notification_message)
        self._enqueue_publish_result(subscription_id, response.Parameters)
        self._record_notification_sequence_number(
            subscription_id,
            notification_message,
            source="publish",
        )
        return _build_publish_ack(subscription_id, notification_message)

    async def _publish_loop(self) -> None:
        """Main publish loop for subscriptions."""
        from asyncua.ua.uaerrors import BadNoSubscription
        ack: SubscriptionAcknowledgement | None = None
        while not self._closing:
            try:
                response = await self._read_publish_response(ack)
                if response is None:
                    ack = None
                    continue
                ack = await self._handle_publish_response(response)
                await asyncio.sleep(0)
            except BadNoSubscription:
                return
            except SubscriptionStaleError:
                raise
            except Exception:
                ack = None
                self.logger.exception("Unexpected error in publish loop")

    async def dispatch_notification_message(
        self, subscription_id: int, notification_message: ua.NotificationMessage
    ) -> None:
        """Dispatch notification to registered handler."""
        callback = self._subscription_callbacks.get(subscription_id)
        if callback is None:
            return
        publish_result = ua.PublishResult()
        publish_result.SubscriptionId = subscription_id
        publish_result.NotificationMessage = notification_message
        await _invoke_subscription_callback(callback, publish_result)

    async def ensure_publish_loop_running(self) -> None:
        """Start publish loop if not already running."""
        if self._publish_task is None or self._publish_task.done():
            self._publish_task = asyncio.create_task(self._publish_loop())

    async def restart_publish_loop(self) -> None:
        """Restart publish loop after subscription changes."""
        if self._publish_task is not None and not self._publish_task.done():
            self._publish_task.cancel()
            try:
                await self._publish_task
            except asyncio.CancelledError:
                pass
        self._publish_task = None
        await self.ensure_publish_loop_running()

    async def _close_local(self) -> None:
        """Close local session resources without sending CloseSessionRequest."""
        if self._state in (SessionState.CLOSING, SessionState.CLOSED):
            return

        self._set_state(SessionState.CLOSING)
        self._closing = True
        self._disconnect_event.set()

        if self._publish_task is not None and not self._publish_task.done():
            self._publish_task.cancel()
            try:
                await self._publish_task
            except asyncio.CancelledError:
                pass
            except Exception:
                self.logger.exception("Error while stopping publish loop")

        for subscription_id in list(self._subscription_dispatch_runtime.keys()):
            self._stop_subscription_dispatch_worker(subscription_id)

        self._subscription_callbacks.clear()
        self._last_publish_sequence_numbers.clear()
        self._subscription_watchdog_states.clear()

        self._set_state(SessionState.CLOSED)

    async def close(self, delete_subscriptions: bool = True) -> None:
        """Close session and release local and remote resources."""
        await self.client.close_session(
            delete_subscriptions=delete_subscriptions,
            session=self,
        )

    async def inform_subscriptions(self, status: ua.StatusCode) -> None:
        """Inform all subscriptions of status change."""
        status_message = ua.StatusChangeNotification(Status=status)
        notification_message = ua.NotificationMessage(
            NotificationData=[status_message]
        )
        for subid, callback in self._subscription_callbacks.items():
            try:
                parameters = ua.PublishResult(
                    subid, NotificationMessage=notification_message
                )
                await _invoke_subscription_callback(callback, parameters)
            except Exception:
                self.logger.exception("Exception calling user callback")

    @property
    def ready_event(self) -> asyncio.Event:
        """Event signaled when session is ready."""
        return self._ready_event

    async def __aenter__(self) -> UaSession:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit - cleanup."""
        await self.close()
