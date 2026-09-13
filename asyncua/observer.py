from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asyncua.client.ua_client import UaClientState

_NULL_CONTEXT: AbstractContextManager[None] = nullcontext()


class SubscriptionEvent(str, Enum):
    CREATED = "created"
    RECREATED = "recreated"
    DELETED = "deleted"


class Observer:
    """Client observer: every hook does nothing, subclasses override the ones they care about.

    `observe_request` wraps the request and therefore owns its timing, making it a natural
    place to open a tracing span; the `on_*` hooks report events that already happened.

    Hooks run inline on the client's event loop and their exceptions are not caught: an
    implementation must be quick and must not raise. Queue the observation and let another
    task or thread carry it forward.
    """

    def observe_request(self, request: Any) -> AbstractContextManager[None]:
        return _NULL_CONTEXT

    def on_state_change(self, state: UaClientState) -> None: ...

    def on_subscription_event(self, event: SubscriptionEvent, subscription_id: int | None) -> None: ...

    def on_notification(self, subscription_id: int | None, item_count: int) -> None: ...


NULL_OBSERVER = Observer()
