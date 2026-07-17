"""Tests for the reverse connection client."""

import asyncio
from contextlib import closing

import pytest
from pytest_mock import MockerFixture

from asyncua import ua
from asyncua.client.rc_client import RCClient
from asyncua.client.rc_server import _MAX_ENDPOINT_URL_LENGTH, _MAX_SERVER_URI_LENGTH, RCServer
from asyncua.ua import ua_binary
from tests.conftest import find_free_port


async def test_rc_client_server_start_stop() -> None:
    async with RCServer("127.0.0.1", find_free_port()) as server:
        assert server.is_listening
    assert not server.is_listening


async def test_rc_client_server_wait_for_next_rc_raises_not_listening() -> None:
    server = RCServer("127.0.0.1", find_free_port())
    with pytest.raises(RuntimeError):
        assert not server.is_listening
        await server.wait_for_next_rc()


async def test_rc_client_server_end_to_end_reverse_connection() -> None:
    port = find_free_port()
    async with RCServer("127.0.0.1", port) as server:
        _, writer = await asyncio.open_connection("127.0.0.1", port)
        with closing(writer):
            rh = ua.ReverseHello(ServerUri="urn:e2e:server", EndpointUrl="opc.tcp://127.0.0.1:4840")
            writer.write(ua_binary.uatcp_to_binary(ua.MessageType.ReverseHello, rh))
            await writer.drain()
            rc = await asyncio.wait_for(server.wait_for_next_rc(), timeout=5)
            rc.close()

        assert rc.server_application_uri == "urn:e2e:server"
        assert rc.server_endpoint == "opc.tcp://127.0.0.1:4840"


async def test_rc_client_server_timeout() -> None:
    port = find_free_port()
    timeout = 1
    async with RCServer("127.0.0.1", port, slow_connection_timeout=timeout) as server:
        reader, _ = await asyncio.open_connection("127.0.0.1", port)
        await asyncio.sleep(timeout + 0.5)
        assert reader.at_eof()
        assert (await reader.read()) == b""
        with pytest.raises((TimeoutError, asyncio.TimeoutError)):
            await asyncio.wait_for(server.wait_for_next_rc(), timeout=1)


async def test_rc_client_server_uri_too_long() -> None:
    port = find_free_port()
    async with RCServer("127.0.0.1", port) as server:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        with closing(writer):
            rh = ua.ReverseHello(ServerUri="a" * (_MAX_SERVER_URI_LENGTH + 1), EndpointUrl="opc.tcp://127.0.0.1:4840")
            writer.write(ua_binary.uatcp_to_binary(ua.MessageType.ReverseHello, rh))
            await writer.drain()
            data = await asyncio.wait_for(reader.read(), timeout=5)

            buf = ua.utils.Buffer(data)
            header = ua_binary.header_from_binary(buf)
            assert header.MessageType == ua.MessageType.Error
            error = ua_binary.struct_from_binary(ua.ErrorMessage, buf)
            assert error.Error == ua.StatusCode(ua.StatusCodes.BadServerUriInvalid)

        with pytest.raises((TimeoutError, asyncio.TimeoutError)):
            await asyncio.wait_for(server.wait_for_next_rc(), timeout=1)


async def test_rc_client_server_endpoint_url_too_long() -> None:
    port = find_free_port()
    async with RCServer("127.0.0.1", port) as server:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        with closing(writer):
            rh = ua.ReverseHello(ServerUri="urn:e2e:server", EndpointUrl="a" * (_MAX_ENDPOINT_URL_LENGTH + 1))
            writer.write(ua_binary.uatcp_to_binary(ua.MessageType.ReverseHello, rh))
            await writer.drain()
            data = await asyncio.wait_for(reader.read(), timeout=5)

            buf = ua.utils.Buffer(data)
            header = ua_binary.header_from_binary(buf)
            assert header.MessageType == ua.MessageType.Error
            error = ua_binary.struct_from_binary(ua.ErrorMessage, buf)
            assert error.Error == ua.StatusCode(ua.StatusCodes.BadTcpEndpointUrlInvalid)

        with pytest.raises((TimeoutError, asyncio.TimeoutError)):
            await asyncio.wait_for(server.wait_for_next_rc(), timeout=1)


async def test_rc_client_server_leftover_data() -> None:
    port = find_free_port()
    async with RCServer("127.0.0.1", port) as server:
        _, writer = await asyncio.open_connection("127.0.0.1", port)
        with closing(writer):
            rh = ua.ReverseHello(ServerUri="urn:e2e:server", EndpointUrl="opc.tcp://127.0.0.1:4840")
            extra = b"a" * 1024
            writer.write(ua_binary.uatcp_to_binary(ua.MessageType.ReverseHello, rh))
            writer.write(extra)
            writer.write(extra)
            await writer.drain()
            rc = await asyncio.wait_for(server.wait_for_next_rc(), timeout=5)
            rc.close()

        assert rc.leftover_data == 2 * extra


async def test_rc_client_connect_timeout() -> None:
    server = RCServer("127.0.0.1", find_free_port())
    client = RCClient(server, rc_timeout=0.05)
    with pytest.raises((TimeoutError, asyncio.TimeoutError)):
        await client.connect()
    assert not server.is_listening


async def _wait_and_send_reverse_hello(port: int) -> None:
    for _ in range(50):
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            break
        except ConnectionRefusedError:
            await asyncio.sleep(0.05)
    else:
        raise TimeoutError(f"Could not connect to 127.0.0.1:{port}")

    with closing(writer):
        rh = ua.ReverseHello(ServerUri="urn:e2e:server", EndpointUrl="opc.tcp://127.0.0.1:4840")
        writer.write(ua_binary.uatcp_to_binary(ua.MessageType.ReverseHello, rh))
        await writer.drain()


async def test_rc_client_connect(mocker: MockerFixture) -> None:
    rc_port = find_free_port()
    client = RCClient(RCServer("127.0.0.1", rc_port), rc_timeout=10.0)
    mocker.patch.object(
        client, "_connect_handshake", new=mocker.AsyncMock()
    )  # TODO: replace with an reverse connection server when exists

    sender_task = asyncio.create_task(_wait_and_send_reverse_hello(rc_port))
    async with client:
        await sender_task

    client._connect_handshake.assert_awaited_once()  # type: ignore[attr-defined]
    assert client.server_url.geturl() == "opc.tcp://127.0.0.1:4840"


async def test_rc_client_connect_existing_server(mocker: MockerFixture) -> None:
    port = find_free_port()
    sender_task = asyncio.create_task(_wait_and_send_reverse_hello(port))
    async with RCServer("127.0.0.1", port) as server:
        client = RCClient(server)
        mocker.patch.object(
            client, "_connect_handshake", new=mocker.AsyncMock()
        )  # TODO: replace with an reverse connection server when exists

        assert server.is_listening
        async with client:
            await sender_task
            assert server.is_listening
        assert server.is_listening

    client._connect_handshake.assert_awaited_once()  # type: ignore[attr-defined]
    assert client.server_url.geturl() == "opc.tcp://127.0.0.1:4840"
