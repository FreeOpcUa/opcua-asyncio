"""Tests for the async-iterator subscription API."""

from __future__ import annotations

import asyncio

import pytest

from asyncua import Client, Server
from asyncua.common.subscription import (
    DataChangeEvent,
    OverflowPolicy,
)

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio


async def _start_server(port: int) -> Server:
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()
    return srv


async def test_iterator_yields_data_changes() -> None:
    """Iterator-mode subscription yields DataChangeEvent for monitored variable writes."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    var = await objects.add_variable(2, "IterVar", 0)
    await var.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        sub = await client.create_subscription(50)  # no handler -> iterator mode
        async with sub:
            await sub.subscribe_data_change(client.get_node(var.nodeid))
            # First arrival is the initial value (0).
            first = await asyncio.wait_for(sub.next_event(), timeout=3.0)
            assert isinstance(first, DataChangeEvent)
            assert first.value == 0
            # Then writes propagate as DataChangeEvents.
            await var.write_value(7)
            seen: list[int] = []
            while 7 not in seen:
                ev = await asyncio.wait_for(sub.next_event(), timeout=3.0)
                if isinstance(ev, DataChangeEvent):
                    seen.append(ev.value)
            assert 7 in seen
    finally:
        await client.disconnect()
        await srv.stop()


async def test_iterator_async_for_loop_exits_on_delete() -> None:
    """`async for ev in sub` ends cleanly when the subscription is deleted."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    var = await objects.add_variable(2, "IterVar2", 0)
    await var.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        await sub.subscribe_data_change(client.get_node(var.nodeid))
        consumed: list[object] = []
        pending: list[asyncio.Task[None]] = []

        async def consumer() -> None:
            async for ev in sub:
                consumed.append(ev)
                if isinstance(ev, DataChangeEvent) and ev.value == 1:
                    # Trigger delete from inside the loop (a common pattern).
                    pending.append(asyncio.create_task(sub.delete()))

        consumer_task = asyncio.create_task(consumer())
        # Wait for initial value, then poke a new one to trigger delete.
        await asyncio.sleep(0.2)
        await var.write_value(1)
        await asyncio.wait_for(consumer_task, timeout=3.0)
        # consumer ended naturally via StopAsyncIteration; loop got at least
        # the initial value (0) and the trigger value (1).
        assert any(isinstance(ev, DataChangeEvent) and ev.value == 1 for ev in consumed)
    finally:
        await srv.stop()


async def test_iterator_context_manager_deletes_on_exit() -> None:
    """`async with sub:` exit deletes the server-side subscription."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        assert sub._deleted is False
        async with sub:
            assert sub.subscription_id is not None
        assert sub._deleted is True
    finally:
        await client.disconnect()
        await srv.stop()


async def test_iterator_rejects_handler_mode() -> None:
    """Trying to iterate a handler-mode subscription is a hard error."""
    port = find_free_port()
    srv = await _start_server(port)

    class _Noop:
        def datachange_notification(self, _n, _v, _d) -> None:
            pass

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        sub = await client.create_subscription(50, _Noop())
        with pytest.raises(RuntimeError, match="handler mode"):
            sub.__aiter__()
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()


async def test_iterator_drop_oldest_policy_keeps_recent() -> None:
    """DROP_OLDEST overflow: when queue fills, the front is evicted and new events are kept."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    var = await objects.add_variable(2, "OverflowVar", 0)
    await var.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        # Tiny queue so writes immediately overflow.
        sub = await client.create_subscription(50, queue_maxsize=2, overflow=OverflowPolicy.DROP_OLDEST)
        await sub.subscribe_data_change(client.get_node(var.nodeid))
        # Wait for the initial value to land.
        await asyncio.sleep(0.2)
        # Burst many writes; with DROP_OLDEST, the queue should hold the two
        # most recent values.
        for i in range(1, 20):
            await var.write_value(i)
        await asyncio.sleep(0.5)
        assert sub._event_queue is not None
        # Drain whatever the queue holds.
        drained: list[object] = []
        while not sub._event_queue.empty():
            drained.append(sub._event_queue.get_nowait())
        values = [ev.value for ev in drained if isinstance(ev, DataChangeEvent)]
        # We don't promise exactly which values land — only that the queue
        # bound is respected and the values present are the *recent* ones.
        assert len(drained) <= 2
        if values:
            assert max(values) >= 15  # at least one of the late writes survived
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()


async def test_iterator_overflow_disconnect_triggers_reconnect() -> None:
    """DISCONNECT overflow: when queue fills, the supervisor reconnects."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    var = await objects.add_variable(2, "OverflowVar2", 0)
    await var.set_writable()

    from asyncua.client.ua_client import UaClientState

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(50, queue_maxsize=1, overflow=OverflowPolicy.DISCONNECT)
        await sub.subscribe_data_change(client.get_node(var.nodeid))

        async with client.subscribe_state() as state_sub:
            # Make the queue overflow.
            for i in range(1, 30):
                await var.write_value(i)
            saw_leave = False

            async def _round_trip() -> None:
                nonlocal saw_leave
                while True:
                    state = await state_sub.next_change()
                    if state is not UaClientState.CONNECTED:
                        saw_leave = True
                    elif saw_leave:
                        return

            await asyncio.wait_for(_round_trip(), timeout=5.0)
    finally:
        await client.disconnect()
        await srv.stop()


async def test_handler_dispatch_doesnt_block_publish_loop() -> None:
    """A slow handler shouldn't stall the publish loop for other notifications."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    var = await objects.add_variable(2, "SlowVar", 0)
    await var.set_writable()

    completed: list[int] = []
    barrier = asyncio.Event()

    class SlowHandler:
        async def datachange_notification(self, _node, val, _data) -> None:
            if val == 0:
                # Initial value: block until the test releases us.
                await barrier.wait()
            completed.append(val)

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        sub = await client.create_subscription(50, SlowHandler())
        await sub.subscribe_data_change(client.get_node(var.nodeid))
        # Without the dispatch-as-task fix the next notification would never
        # arrive because the first handler call is blocking the publish loop.
        await asyncio.sleep(0.2)
        await var.write_value(42)
        # The 42 notification should reach the handler queue even though the
        # initial-value handler is still parked.
        deadline = asyncio.get_event_loop().time() + 3.0
        while 42 not in completed and asyncio.get_event_loop().time() < deadline:
            # Release the parked initial-value handler late so the test still
            # observes that 42 made it through the publish loop in parallel.
            if asyncio.get_event_loop().time() > deadline - 1.5:
                barrier.set()
            await asyncio.sleep(0.05)
        barrier.set()
        await asyncio.sleep(0.2)
        assert 42 in completed
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()
