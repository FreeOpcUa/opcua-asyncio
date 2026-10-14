"""Tests for the async-iterator subscription API."""

from __future__ import annotations

import asyncio

import pytest

from asyncua import Client, Server
from asyncua.common.subscription import (
    DataChangeEvent,
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
        assert sub.is_deleted is False
        async with sub:
            assert sub.subscription_id is not None
        assert sub.is_deleted is True
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
