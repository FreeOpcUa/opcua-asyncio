from unittest.mock import AsyncMock

import pytest

from asyncua import ua
from asyncua.client.ua_client import UaClient
from asyncua.client.ua_session import UaSession
from asyncua.common.node import Node

pytestmark = pytest.mark.asyncio


async def test_node_history_update_sends_details_and_returns_result():
    details = ua.UpdateDataDetails()
    result = ua.HistoryUpdateResult()
    session = AsyncMock()
    session.history_update.return_value = [result]
    node = Node(session, ua.NodeId(1234, 2))

    returned = await node.history_update(details)

    assert returned is result
    session.history_update.assert_awaited_once()
    params = session.history_update.await_args.args[0]
    assert params.HistoryUpdateDetails == [details]


async def test_node_history_update_raises_for_bad_status():
    details = ua.UpdateDataDetails()
    result = ua.HistoryUpdateResult()
    result.StatusCode = ua.StatusCode(ua.StatusCodes.BadNotWritable)
    session = AsyncMock()
    session.history_update.return_value = [result]
    node = Node(session, ua.NodeId(1234, 2))

    with pytest.raises(ua.UaStatusCodeError):
        await node.history_update(details)


async def test_ua_client_history_update_delegates_to_session():
    client = UaClient()
    expected = [ua.HistoryUpdateResult()]
    client.session.history_update = AsyncMock(return_value=expected)

    result = await client.history_update(ua.HistoryUpdateParameters())

    assert result == expected
    client.session.history_update.assert_awaited_once()


async def test_ua_session_history_update_builds_request(monkeypatch):
    client = AsyncMock()
    session = UaSession(client)
    params = ua.HistoryUpdateParameters()
    details = ua.UpdateDataDetails()
    params.HistoryUpdateDetails.append(details)
    response = ua.HistoryUpdateResponse()
    response.Results = [ua.HistoryUpdateResult()]
    session._send_request = AsyncMock(return_value=b"response")
    monkeypatch.setattr("asyncua.client.ua_session.struct_from_binary", lambda _type, _data: response)

    result = await session.history_update(params)

    assert result == response.Results
    request = session._send_request.await_args.args[0]
    assert isinstance(request, ua.HistoryUpdateRequest)
    assert request.Parameters is params
