import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

import pytest

from asyncua import Server, ua

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("field", ["StartTime", "CurrentTime"])
async def test_server_status_timestamps_match_components(opc: Any, field: str) -> None:
    status_node = opc.opc.get_node(ua.ObjectIds.Server_ServerStatus)
    component = await status_node.get_child(f"0:{field}")
    for _ in range(30):
        value = await status_node.read_data_value()
        assert value.StatusCode.is_good()
        assert value.Value is not None
        status = value.Value.Value
        assert value.SourceTimestamp >= status.CurrentTime
        component_value = await component.read_value()
        if getattr(status, field) == component_value:
            break
        await asyncio.sleep(0.1)
    assert getattr(status, field) == component_value


async def test_server_status_clock_updates_preserve_fields(server: Server) -> None:
    status_node = server.get_node(ua.ObjectIds.Server_ServerStatus)
    await server.set_build_info("urn:test", "Manufacturer", "Product", "2.0", "42", datetime.now(timezone.utc))
    before = deepcopy(await status_node.read_value())
    for _ in range(30):
        current = await status_node.read_value()
        if current.CurrentTime > before.CurrentTime:
            break
        await asyncio.sleep(0.1)
    assert current.CurrentTime > before.CurrentTime
    assert current.StartTime == before.StartTime
    assert current.BuildInfo == before.BuildInfo
    assert current.State == before.State
    assert current.SecondsTillShutdown == before.SecondsTillShutdown
    assert current.ShutdownReason == before.ShutdownReason


@pytest.mark.parametrize("disabled_clock", [False, True])
async def test_server_status_start_time_and_clock_shutdown(disabled_clock: bool) -> None:
    server = Server()
    await server.init()
    server.iserver.disabled_clock = disabled_clock
    before = datetime.now(timezone.utc)
    await server.iserver.start()
    try:
        status = await server.get_node(ua.ObjectIds.Server_ServerStatus).read_value()
        start = await server.get_node(ua.ObjectIds.Server_ServerStatus_StartTime).read_value()
        assert before <= status.StartTime <= datetime.now(timezone.utc)
        assert status.StartTime == start
        assert (server.iserver.time_task is None) == disabled_clock
    finally:
        await server.iserver.stop()
    if server.iserver.time_task is not None:
        assert server.iserver.time_task.done()


async def test_server_status_subscription_receives_clock_updates(opc: Any) -> None:
    values: asyncio.Queue[ua.ServerStatusDataType] = asyncio.Queue()

    class Handler:
        def datachange_notification(self, node: Any, value: ua.ServerStatusDataType, data: Any) -> None:
            values.put_nowait(deepcopy(value))

    subscription = await opc.opc.create_subscription(20, Handler())
    try:
        await subscription.subscribe_data_change(opc.opc.get_node(ua.ObjectIds.Server_ServerStatus))
        before = await asyncio.wait_for(values.get(), 3)
        after = await asyncio.wait_for(values.get(), 3)
        assert after.CurrentTime > before.CurrentTime
        assert after.StartTime == before.StartTime
        assert after.BuildInfo == before.BuildInfo
    finally:
        await subscription.delete()
