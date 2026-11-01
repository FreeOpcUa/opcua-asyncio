import asyncio
from collections.abc import Callable
from unittest.mock import AsyncMock, Mock

import pytest

from asyncua import ua
from asyncua.client.ua_client import UaClient
from asyncua.client.ua_session import UaSession
from asyncua.common.utils import Buffer
from asyncua.ua.ua_binary import nodeid_from_binary, struct_from_binary, struct_to_binary


@pytest.fixture
def transport_client() -> tuple[UaClient, list[ua.RequestHeader]]:
    client = UaClient()
    protocol = client._make_protocol()
    headers: list[ua.RequestHeader] = []

    def write(packet: bytes) -> None:
        body = Buffer(packet)
        nodeid_from_binary(body)
        headers.append(struct_from_binary(ua.RequestHeader, body))
        response = ua.ReadResponse()
        protocol._call_callback(protocol._request_id, Buffer(struct_to_binary(response)))

    protocol.transport = Mock(spec=asyncio.Transport)
    protocol.transport.write.side_effect = write
    protocol._connection.message_to_binary = Mock(side_effect=lambda body, **kwargs: body)
    return client, headers


@pytest.mark.parametrize(
    "request_type",
    [ua.ActivateSessionRequest, ua.ReadRequest, ua.WriteRequest, ua.PublishRequest, ua.CloseSessionRequest],
)
async def test_interleaved_sessions_send_their_own_tokens(
    transport_client: tuple[UaClient, list[ua.RequestHeader]],
    request_type: Callable[[], object],
) -> None:
    client, headers = transport_client
    session_a = client.session
    session_b = UaSession(client)
    session_a.restore_authentication_token(ua.NodeId(101, 1))
    session_b.restore_authentication_token(ua.NodeId(202, 1))

    await asyncio.gather(
        session_a._send_request(request_type()),
        session_b._send_request(request_type()),
        session_a._send_request(request_type()),
    )

    assert [header.AuthenticationToken for header in headers] == [
        session_a.authentication_token,
        session_b.authentication_token,
        session_a.authentication_token,
    ]
    assert [header.RequestHandle for header in headers] == [1, 2, 3]


async def test_explicit_null_token_does_not_inherit_session_token(
    transport_client: tuple[UaClient, list[ua.RequestHeader]],
) -> None:
    client, headers = transport_client
    client.session.restore_authentication_token(ua.NodeId(101, 1))
    await client.session._send_request(ua.ReadRequest())
    request = ua.GetEndpointsRequest()
    request.RequestHeader.AuthenticationToken = client.session.authentication_token

    assert client.protocol is not None
    await client.protocol.send_request(request, authentication_token=ua.NodeId())

    assert headers[0].AuthenticationToken == client.session.authentication_token
    assert headers[1].AuthenticationToken.is_null()


async def test_request_uses_latest_session_token_and_transport_after_reconnect(
    transport_client: tuple[UaClient, list[ua.RequestHeader]],
) -> None:
    client, headers = transport_client
    client.session.restore_authentication_token(ua.NodeId(101, 1))
    replacement_protocol = client.protocol
    entered_hook = asyncio.Event()
    resume = asyncio.Event()

    async def wait_for_reconnect() -> None:
        entered_hook.set()
        await resume.wait()

    client.pre_request_hook = wait_for_reconnect
    client.protocol = None
    session = UaSession(client)
    pending = asyncio.create_task(session._send_request(ua.ReadRequest()))
    await asyncio.wait_for(entered_hook.wait(), timeout=1)
    session.restore_authentication_token(ua.NodeId(202, 1))
    client.protocol = replacement_protocol
    resume.set()
    await asyncio.wait_for(pending, timeout=1)

    assert headers[0].AuthenticationToken == ua.NodeId(202, 1)


@pytest.mark.parametrize("entry_point", ["client", "session", "protocol"])
async def test_protocol_hook_runs_once_before_token_selection(
    transport_client: tuple[UaClient, list[ua.RequestHeader]], entry_point: str
) -> None:
    client, headers = transport_client
    client.session.restore_authentication_token(ua.NodeId(101, 1))
    assert client.protocol is not None

    async def refresh_token() -> None:
        client.session.restore_authentication_token(ua.NodeId(202, 1))

    hook = AsyncMock(side_effect=refresh_token)
    client.protocol.pre_request_hook = hook

    if entry_point == "client":
        await client._send_request(ua.ReadRequest())
    elif entry_point == "session":
        await client.session._send_request(ua.ReadRequest())
    else:
        await client.protocol.send_request(ua.ReadRequest())

    hook.assert_awaited_once_with()
    assert headers[0].AuthenticationToken == ua.NodeId(202, 1)


async def test_default_session_supports_old_protocol_overrides(
    transport_client: tuple[UaClient, list[ua.RequestHeader]], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, headers = transport_client
    protocol = client.protocol
    assert protocol is not None
    original_send = protocol.send_request
    original_send_sync = protocol._send_request
    original_header = protocol._setup_request_header

    async def send(
        request: object, timeout: float | None = None, message_type: ua.MessageType = ua.MessageType.SecureMessage
    ) -> Buffer:
        return await original_send(request, timeout, message_type)

    def send_sync(
        request: object, timeout: float = 1, message_type: ua.MessageType = ua.MessageType.SecureMessage
    ) -> asyncio.Future:
        return original_send_sync(request, timeout, message_type)

    def setup_header(header: ua.RequestHeader, timeout: float = 1) -> None:
        original_header(header, timeout)

    monkeypatch.setattr(protocol, "send_request", send)
    monkeypatch.setattr(protocol, "_send_request", send_sync)
    monkeypatch.setattr(protocol, "_setup_request_header", setup_header)
    client.session.restore_authentication_token(ua.NodeId(101, 1))
    await client.session._send_request(ua.ReadRequest())
    client.session.restore_authentication_token(ua.NodeId(202, 1))
    await client.session._send_request(ua.ReadRequest())
    assert [header.AuthenticationToken for header in headers] == [ua.NodeId(101, 1), ua.NodeId(202, 1)]
