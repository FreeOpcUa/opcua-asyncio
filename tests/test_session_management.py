"""Set ASYNCUA_MULTI_SESSION_URL to run integration checks against a disposable server.

It must support SecurityPolicy None, admin/reader accounts with password "test",
and an Int32 variable (ASYNCUA_MULTI_SESSION_NODE, default ns=1;s=Counter).
Only admin may write the variable. Validated with open62541 1.4.22.
"""

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from asyncua import Client, ua
from asyncua.client.ua_client import UaClient, UaClientState
from asyncua.client.ua_session import SessionState, UaSession
from asyncua.common.node import Node
from asyncua.common.subscription import DataChangeNotif, Subscription
from asyncua.common.utils import Buffer
from asyncua.ua.ua_binary import nodeid_from_binary, struct_from_binary, struct_to_binary


@pytest.fixture
def managed_client() -> tuple[UaClient, list[tuple[ua.NodeId, ua.RequestHeader]]]:
    client = UaClient()
    protocol = client._make_protocol()
    client._set_state(UaClientState.CHANNEL_OPEN)
    requests: list[tuple[ua.NodeId, ua.RequestHeader]] = []
    responses = {
        ua.ObjectIds.CreateSessionRequest_Encoding_DefaultBinary: ua.CreateSessionResponse,
        ua.ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary: ua.ActivateSessionResponse,
        ua.ObjectIds.ReadRequest_Encoding_DefaultBinary: ua.ReadResponse,
        ua.ObjectIds.CloseSessionRequest_Encoding_DefaultBinary: ua.CloseSessionResponse,
    }
    counter = 0

    def write(packet: bytes) -> None:
        nonlocal counter
        body = Buffer(packet)
        type_id = nodeid_from_binary(body)
        header = struct_from_binary(ua.RequestHeader, body)
        requests.append((type_id, header))
        assert isinstance(type_id.Identifier, int)
        response = responses[type_id.Identifier]()
        if isinstance(response, ua.CreateSessionResponse):
            counter += 1
            response.Parameters.SessionId = ua.NodeId(counter, 1)
            response.Parameters.AuthenticationToken = ua.NodeId(counter + 100, 1)
        protocol._call_callback(protocol._request_id, Buffer(struct_to_binary(response)))

    protocol.transport = Mock(spec=asyncio.Transport)
    protocol.transport.write.side_effect = write
    protocol._connection.message_to_binary = Mock(side_effect=lambda body, **kwargs: body)
    return client, requests


async def test_sessions_are_registered_and_close_independently(managed_client: tuple[UaClient, list]) -> None:
    client, requests = managed_client
    first = await client.create_session_object(ua.CreateSessionParameters())
    second = await client.create_session_object(ua.CreateSessionParameters())
    assert first.session_id is not None
    assert client.get_session(first.session_id) is first
    assert client.sessions == (first, second)
    await first.activate_session(ua.ActivateSessionParameters())
    await second.activate_session(ua.ActivateSessionParameters())
    assert client.state is UaClientState.CONNECTED

    await client.close_session_object(first.session_id)
    assert client.sessions == (second,)
    with pytest.raises(KeyError):
        client.get_session(first.session_id)
    assert client.state is UaClientState.CONNECTED
    assert await second.read(ua.ReadParameters()) == []
    assert requests[-1][1].AuthenticationToken == second.authentication_token
    await second.close_session(True)
    assert client.sessions == ()
    assert client.state is UaClientState.CHANNEL_OPEN


@pytest.mark.parametrize("disconnect", [False, True])
@pytest.mark.parametrize("default", [False, True])
async def test_recreated_session_is_registered_and_cleaned_up(
    managed_client: tuple[UaClient, list], disconnect: bool, default: bool
) -> None:
    client, requests = managed_client
    if default:
        session = client.session
        await client.create_session(ua.CreateSessionParameters())
    else:
        session = await client.create_session_object(ua.CreateSessionParameters())
    old_id = session.session_id
    assert old_id is not None
    await session.close_session(True)
    result = await session.create_session(ua.CreateSessionParameters())
    assert result.SessionId != old_id
    assert client.sessions == (session,)
    assert client.get_session(result.SessionId) is session
    assert client._sessions[result.SessionId] is session
    if default:
        assert client.session is session
        assert client._default_session_id == result.SessionId
    with pytest.raises(KeyError):
        client.get_session(old_id)
    await session.activate_session(ua.ActivateSessionParameters())
    assert client.state is UaClientState.CONNECTED
    await session.read(ua.ReadParameters())
    assert requests[-1][1].AuthenticationToken == result.AuthenticationToken
    if disconnect:
        assert client.protocol is not None
        client.protocol.close_secure_channel = AsyncMock()
        await client.disconnect()
        assert client.protocol is None
    else:
        await client.close_all_sessions()
    assert session.state is SessionState.CLOSED
    assert client.sessions == ()
    with pytest.raises(KeyError):
        client.get_session(result.SessionId)
    if default:
        assert client.session is session


@pytest.mark.parametrize("close_default_first", [False, True])
async def test_legacy_default_session_api_is_preserved(
    managed_client: tuple[UaClient, list], close_default_first: bool
) -> None:
    client, _ = managed_client
    result = await client.create_session(ua.CreateSessionParameters())
    assert isinstance(result, ua.CreateSessionResult)
    assert client.get_session(result.SessionId) is client.session
    assert client._sessions[result.SessionId] is client.session
    await client.activate_session(ua.ActivateSessionParameters())
    other = await client.create_session_object(ua.CreateSessionParameters())
    await other.activate_session(ua.ActivateSessionParameters())

    if close_default_first:
        await client.close_session(True)
        assert client.state is UaClientState.CONNECTED
        assert not client._is_session_closing()
        assert await other.read(ua.ReadParameters()) == []
    await client.close_all_sessions()
    assert client.sessions == ()
    assert client.session.state is other.state is SessionState.CLOSED


async def test_failed_creation_does_not_register_session(managed_client: tuple[UaClient, list]) -> None:
    client, _ = managed_client
    assert client.protocol is not None
    client.protocol._connection.message_to_binary = Mock(side_effect=ConnectionError("transport lost"))
    with pytest.raises(ConnectionError):
        await client.create_session_object(ua.CreateSessionParameters())
    assert client.sessions == ()


async def test_close_all_continues_after_failure_and_drains_tasks(managed_client: tuple[UaClient, list]) -> None:
    client, _ = managed_client
    first = await client.create_session_object(ua.CreateSessionParameters())
    second = await client.create_session_object(ua.CreateSessionParameters())
    first._send_request = AsyncMock(side_effect=ConnectionError("transport lost"))
    second._publish_task = asyncio.create_task(asyncio.Event().wait())
    with pytest.raises(ConnectionError):
        await client.close_all_sessions()
    assert client.sessions == ()
    assert first.state is second.state is SessionState.CLOSED
    assert second._publish_task.cancelled()


async def test_disconnect_cleans_transport_even_if_session_close_fails(managed_client: tuple[UaClient, list]) -> None:
    client, _ = managed_client
    first = await client.create_session_object(ua.CreateSessionParameters())
    first._send_request = AsyncMock(side_effect=ConnectionError("transport lost"))
    assert client.protocol is not None
    protocol = client.protocol
    protocol.close_secure_channel = AsyncMock()
    with pytest.raises(ConnectionError):
        await client.disconnect()
    protocol.close_secure_channel.assert_awaited_once()
    assert isinstance(protocol.transport, Mock)
    protocol.transport.close.assert_called_once()
    assert client.protocol is None
    assert client.state is UaClientState.DISCONNECTED


async def test_channel_close_stops_publishing_without_destroying_sessions(
    managed_client: tuple[UaClient, list],
) -> None:
    client, _ = managed_client
    first = await client.create_session_object(ua.CreateSessionParameters())
    await first.activate_session(ua.ActivateSessionParameters())
    assert client.protocol is not None
    client.protocol.close_secure_channel = AsyncMock()
    first._publish_task = asyncio.create_task(asyncio.Event().wait())
    await client.close_secure_channel()
    assert client.state is UaClientState.SOCKET_OPEN
    assert first._publish_task.cancelled()
    assert first.has_session
    assert client.sessions == (first,)
    await client.close_all_sessions()


async def test_concurrent_close_sends_one_request(managed_client: tuple[UaClient, list]) -> None:
    client, requests = managed_client
    session = await client.create_session_object(ua.CreateSessionParameters())
    assert session.create_session_result is not None
    assert session.create_session_result.SessionId == session.session_id
    session._publish_task = asyncio.create_task(asyncio.Event().wait())
    await asyncio.gather(session.close_session(True), session.close_session(True))
    closes = [
        kind for kind, _ in requests if kind.Identifier == ua.ObjectIds.CloseSessionRequest_Encoding_DefaultBinary
    ]
    assert len(closes) == 1
    assert client.sessions == ()


@pytest.mark.parametrize("fail_default_close", [False, True])
async def test_high_level_disconnect_closes_additional_sessions(
    managed_client: tuple[UaClient, list], fail_default_close: bool
) -> None:
    low, _ = managed_client
    extra = await low.create_session_object(ua.CreateSessionParameters())
    await extra.activate_session(ua.ActivateSessionParameters())
    extra._publish_task = asyncio.create_task(asyncio.Event().wait())
    assert low.protocol is not None
    low.protocol.close_secure_channel = AsyncMock()
    high = Client("opc.tcp://localhost:4840")
    high.uaclient = low
    if fail_default_close:
        high.close_session = AsyncMock(side_effect=ConnectionError("default close failed"))
    await high.disconnect()
    assert low.sessions == ()
    assert extra.state is SessionState.CLOSED
    assert extra._publish_task.cancelled()
    assert low.protocol is None


async def _activate_external_session(client: Client, username: str) -> UaSession:
    params = ua.CreateSessionParameters()
    params.ClientDescription.ApplicationUri = "urn:asyncua:session-management-test"
    params.EndpointUrl = client.server_url.geturl()
    params.SessionName = username
    params.ClientNonce = os.urandom(32)
    params.RequestedSessionTimeout = 60000
    session = await client.uaclient.create_session_object(params)
    result = session.create_session_result
    assert result is not None
    policy = next(
        token
        for endpoint in result.ServerEndpoints
        if endpoint.SecurityMode == ua.MessageSecurityMode.None_
        for token in endpoint.UserIdentityTokens
        if token.TokenType == ua.UserTokenType.UserName
        and token.SecurityPolicyUri in (None, "", "http://opcfoundation.org/UA/SecurityPolicy#None")
    )
    activation = ua.ActivateSessionParameters()
    activation.UserIdentityToken = ua.UserNameIdentityToken(
        PolicyId=policy.PolicyId, UserName=username, Password=b"test"
    )
    await session.activate_session(activation)
    return session


class _ValueHandler:
    def __init__(self) -> None:
        self.values: asyncio.Queue[Any] = asyncio.Queue()

    def datachange_notification(self, node: Node, value: Any, data: DataChangeNotif) -> None:
        self.values.put_nowait(value)

    async def wait_for_value(self, expected: int) -> None:
        async def receive() -> None:
            while await self.values.get() != expected:
                pass

        await asyncio.wait_for(receive(), timeout=5)


@pytest.mark.skipif(not os.getenv("ASYNCUA_MULTI_SESSION_URL"), reason="requires an external multi-session server")
@pytest.mark.parametrize("close_first", [0, 1])
async def test_external_sessions_permissions_and_subscriptions(close_first: int) -> None:
    """Use a disposable SecurityPolicy None server with admin/reader:test and a writable Int32 Counter."""
    url = os.environ["ASYNCUA_MULTI_SESSION_URL"]
    node_id = os.getenv("ASYNCUA_MULTI_SESSION_NODE", "ns=1;s=Counter")
    client = Client(url)
    writer = Client(url)
    writer.set_user("admin")
    writer.set_password("test")
    await client.connect_sessionless()
    try:
        sessions = [await _activate_external_session(client, name) for name in ("admin", "reader")]
        protocol = client.uaclient.protocol
        assert sessions[0].authentication_token != sessions[1].authentication_token
        nodes = [Node(session, node_id) for session in sessions]
        handlers = [_ValueHandler(), _ValueHandler()]
        params = ua.CreateSubscriptionParameters(
            RequestedPublishingInterval=100,
            RequestedLifetimeCount=100,
            RequestedMaxKeepAliveCount=10,
            PublishingEnabled=True,
            MaxNotificationsPerPublish=100,
        )
        for session, node, handler in zip(sessions, nodes, handlers, strict=True):
            subscription = Subscription(session, params, handler)
            await subscription.init()
            await subscription.subscribe_data_change(node)
        await nodes[0].write_value(ua.DataValue(ua.Variant(101, ua.VariantType.Int32), StatusCode=None))
        assert await nodes[1].read_value() == 101
        with pytest.raises(ua.UaStatusCodeError) as denied:
            await nodes[1].write_value(ua.DataValue(ua.Variant(999, ua.VariantType.Int32), StatusCode=None))
        assert denied.value.code in (ua.StatusCodes.BadUserAccessDenied, ua.StatusCodes.BadNotWritable)
        await asyncio.gather(*(handler.wait_for_value(101) for handler in handlers))
        await sessions[close_first].close_session(True)
        assert client.uaclient.protocol is protocol
        closed_task = sessions[close_first]._publish_task
        live_task = sessions[1 - close_first]._publish_task
        assert closed_task is not None and live_task is not None
        assert closed_task.done()
        assert not live_task.done()
        async with writer:
            await writer.get_node(node_id).write_value(
                ua.DataValue(ua.Variant(202, ua.VariantType.Int32), StatusCode=None)
            )
        await handlers[1 - close_first].wait_for_value(202)
        assert await nodes[1 - close_first].read_value() == 202
    finally:
        await client.disconnect()
    assert client.uaclient.sessions == ()
    assert client.uaclient.protocol is None
    assert all(session._publish_task is not None and session._publish_task.done() for session in sessions)
