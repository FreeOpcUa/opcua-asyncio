from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
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
    def observe_request(self, request: Any) -> AbstractContextManager[None]:
        return self._time_request(type(request).__name__)

    @contextmanager
    def _time_request(self, request_type: str) -> Iterator[None]:
        started = time.monotonic()
        error: BaseException | None = None
        try:
            yield
        except BaseException as exc:
            error = exc
            raise
        finally:
            try:
                self.on_request(request_type, time.monotonic() - started, error)
            except Exception:
                _logger.exception("observer on_request raised")

    def on_request(self, request_type: str, duration: float, error: BaseException | None) -> None: ...

    def on_state_change(self, state: UaClientState) -> None: ...

    def on_subscription_event(self, subscription_id: int | None, event: SubscriptionEvent) -> None: ...

    def on_notification(self, subscription_id: int | None, event_count: int) -> None: ...


class _NullObserver(Observer):
    def observe_request(self, request: Any) -> AbstractContextManager[None]:
        return nullcontext()


NULL_OBSERVER: Observer = _NullObserver()
