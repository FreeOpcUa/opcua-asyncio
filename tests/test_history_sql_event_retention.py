import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest

from asyncua import Server, ua
from asyncua.server.history_sql import HistorySQLite

from .conftest import find_free_port


@pytest.fixture
async def sqlite_server() -> AsyncIterator[Server]:
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{find_free_port()}")
    history = HistorySQLite(":memory:")
    await history.init()
    srv.iserver.history_manager.set_storage(history)
    async with srv:
        yield srv


async def test_events_older_than_the_period_are_deleted(sqlite_server: Server) -> None:
    server_node = sqlite_server.get_node(ua.ObjectIds.Server)
    await server_node.add_reference(ua.ObjectIds.BaseEventType, ua.ObjectIds.GeneratesEvent)
    await sqlite_server.historize_node_event(server_node, period=timedelta(seconds=1))
    gen = await sqlite_server.get_event_generator()

    gen.event.Severity = 1
    await gen.trigger(message="old")
    await asyncio.sleep(1.5)
    gen.event.Severity = 2
    await gen.trigger(message="new")
    await asyncio.sleep(0.5)

    end = datetime.now(UTC) + timedelta(days=1)
    events = await server_node.read_event_history(datetime.now(UTC) - timedelta(days=1), end, 0)
    assert [getattr(e, "Severity") for e in events] == [2]
