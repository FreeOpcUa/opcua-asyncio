from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asyncua.client.ua_client import UaClientState

_logger = logging.getLogger(__name__)


class SubscriptionEvent(str, Enum):
    CREATED = "created"
    RECREATED = "recreated"
    DELETED = "deleted"


class Observer:
    """Client observer: every hook is a no-op, subclasses override the ones they care about."""

    def on_request(self, request_type: str, duration: float, error: BaseException | None) -> None: ...

    def on_state_change(self, state: UaClientState) -> None: ...

    def on_subscription_event(self, event: SubscriptionEvent, subscription_id: int | None) -> None: ...

    def on_notification(self, subscription_id: int | None, item_count: int) -> None: ...


NULL_OBSERVER = Observer()


def notify(hook: Callable[..., None], *args: Any) -> None:
    """Call an observer hook, never letting it break the caller."""
    try:
        hook(*args)
    except Exception:
        _logger.exception("observer hook raised")
