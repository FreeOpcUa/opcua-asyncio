import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from asyncua import ua
from asyncua.client.client import Client
from asyncua.client.ua_client import UaClient
from asyncua.common.utils import Buffer


def test_request_limit_has_a_high_default() -> None:
    assert UaClient._max_concurrent_requests == 100


@pytest.mark.asyncio
async def test_request_limit_caps_in_flight_requests() -> None:
    client = Client("opc.tcp://localhost:4840")
    client.set_max_concurrent_requests(2)
    release = asyncio.Event()
    limit_reached = asyncio.Event()
    active = 0
    peak = 0

    async def send_request(
        request: Any,
        timeout: float | None = None,
        message_type: ua.MessageType = ua.MessageType.SecureMessage,
    ) -> Buffer:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2:
            limit_reached.set()
        await release.wait()
        active -= 1
        return Buffer(b"")

    protocol = AsyncMock()
    protocol.send_request.side_effect = send_request
    client.uaclient.protocol = protocol

    requests = [asyncio.create_task(client.uaclient._send_request(ua.ReadRequest())) for _ in range(3)]
    await asyncio.wait_for(limit_reached.wait(), timeout=1)
    await asyncio.sleep(0)

    assert client.uaclient._max_concurrent_requests == 2
    assert active == 2
    assert peak == 2

    release.set()
    await asyncio.gather(*requests)
