"""Observation points for code that wants to watch a client at work.

asyncua calls an observer at the few places everything already passes through:
every request, every connection state change, and the subscription lifecycle.
It imports nothing to do so and measures nothing unless an observer is set, so
a client without one behaves exactly as before.

An OpenTelemetry, Prometheus or logging adapter lives outside the library and
implements as much of this protocol as it needs — the default methods do
nothing, so partial implementations are fine::

    class Metrics(ClientObserver):
        def on_request(self, request_type, duration, error):
            REQUESTS.labels(request_type, error is None).observe(duration)

    client.uaclient.observer = Metrics()
"""

from __future__ import annotations

from typing import Protocol


class ClientObserver(Protocol):
    """What a client reports about itself.

    Every method is optional: asyncua looks each one up before calling it, so an
    observer only implements what it cares about.
    """

    def on_request(self, request_type: str, duration: float, error: BaseException | None) -> None:
        """A request finished. ``duration`` is in seconds; ``error`` is None when it succeeded."""

    def on_state_change(self, state: str) -> None:
        """The connection state changed, e.g. ``connected`` or ``reconnecting``."""

    def on_subscription_event(self, event: str, subscription_id: int | None) -> None:
        """A subscription was ``created``, ``recreated`` or ``deleted``."""

    def on_notification(self, subscription_id: int | None, item_count: int) -> None:
        """A publish response arrived carrying ``item_count`` monitored item notifications."""
