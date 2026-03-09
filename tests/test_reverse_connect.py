"""
Tests for OPC UA Reverse Connect (server-side outgoing connections).

Covers:
  - UA protocol type additions (ReverseHello dataclass, MessageType.ReverseHello)
  - Binary serialisation / deserialisation of ReverseHello
  - OPCUAReverseProtocol sends the correct ReverseHello frame
  - ReverseConnectManager dials configured URIs and retries on failure
  - Manager stops cleanly under cancellation
"""
from __future__ import annotations

import asyncio
import socket
import struct
from contextlib import closing

from asyncua import ua
from asyncua.common.connection import TransportLimits
from asyncua.common.utils import Buffer
from asyncua.server.internal_server import InternalServer
from asyncua.server.reverse_connect import (
    OPCUAReverseProtocol,
    ReverseConnectClientEntry,
    ReverseConnectConfig,
    ReverseConnectManager,
)
from asyncua.ua.ua_binary import header_from_binary, struct_from_binary, uatcp_to_binary

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def make_limits() -> TransportLimits:
    return TransportLimits(
        max_recv_buffer=65535,
        max_send_buffer=65535,
        max_chunk_count=100,
        max_message_size=10 * 1024 * 1024,
    )


# ---------------------------------------------------------------------------
# Unit tests - UA type layer
# ---------------------------------------------------------------------------


def test_message_type_reverse_hello():
    """MessageType.ReverseHello must equal the on-wire byte sequence 'RHE'."""
    assert ua.MessageType.ReverseHello == b"RHE"


def test_reverse_hello_dataclass():
    """ReverseHello dataclass has the expected fields with defaults."""
    rhel = ua.ReverseHello()
    assert rhel.ServerUri == ""
    assert rhel.EndpointUrl == ""

    rhel2 = ua.ReverseHello(
        ServerUri="urn:test:server",
        EndpointUrl="opc.tcp://127.0.0.1:4840",
    )
    assert rhel2.ServerUri == "urn:test:server"
    assert rhel2.EndpointUrl == "opc.tcp://127.0.0.1:4840"


def test_reverse_hello_serialise_deserialise():
    """ReverseHello round-trips through uatcp_to_binary / header_from_binary."""
    server_uri = "urn:opcua:testserver"
    endpoint_url = "opc.tcp://localhost:4840/test"

    rhel = ua.ReverseHello(ServerUri=server_uri, EndpointUrl=endpoint_url)
    raw = uatcp_to_binary(ua.MessageType.ReverseHello, rhel)

    # Check the header bytes
    buf = Buffer(raw)
    hdr = header_from_binary(buf)
    assert hdr.MessageType == b"RHE"
    assert hdr.ChunkType == b"F"

    # Decode body
    decoded = struct_from_binary(ua.ReverseHello, buf)
    assert decoded.ServerUri == server_uri
    assert decoded.EndpointUrl == endpoint_url


# ---------------------------------------------------------------------------
# Unit tests - config dataclasses
# ---------------------------------------------------------------------------


def test_reverse_connect_config_defaults():
    cfg = ReverseConnectConfig()
    assert cfg.clients == []
    assert cfg.connect_interval == 15_000
    assert cfg.connect_timeout == 30_000
    assert cfg.reject_timeout == 60_000


def test_reverse_connect_client_entry_defaults():
    entry = ReverseConnectClientEntry(endpoint_url="opc.tcp://host:4840")
    assert entry.enabled is True
    assert entry.max_session_count == 0
    assert entry.timeout == 30_000


# ---------------------------------------------------------------------------
# Integration: OPCUAReverseProtocol sends ReverseHello
# ---------------------------------------------------------------------------


async def _read_reverse_hello(reader: asyncio.StreamReader) -> ua.ReverseHello:
    """Read one OPC UA message frame from *reader* and decode it as ReverseHello."""
    # Read fixed 8-byte header
    header_bytes = await asyncio.wait_for(reader.readexactly(8), timeout=5.0)
    msg_type, chunk_type, packet_size = struct.unpack("<3scI", header_bytes)
    body_size = packet_size - 8
    body_bytes = await asyncio.wait_for(reader.readexactly(body_size), timeout=5.0)

    assert msg_type == b"RHE", f"Expected RHE, got {msg_type!r}"
    assert chunk_type == b"F"

    buf = Buffer(body_bytes)
    return struct_from_binary(ua.ReverseHello, buf)


async def test_protocol_sends_reverse_hello():
    """
    OPCUAReverseProtocol must send a correctly formatted ReverseHello immediately
    after the TCP connection is established.
    """
    port = find_free_port()
    received: list[ua.ReverseHello] = []
    server_ready = asyncio.Event()

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        rhel = await _read_reverse_hello(reader)
        received.append(rhel)
        writer.close()
        await writer.wait_closed()

    srv = await asyncio.start_server(handle_client, "127.0.0.1", port)
    server_ready.set()

    async with srv:
        # Create an InternalServer (minimal, without full init)
        iserver = InternalServer()
        limits = make_limits()

        close_ev = asyncio.Event()

        def factory():
            proto = OPCUAReverseProtocol(
                iserver=iserver,
                policies=[],
                clients=[],
                closing_tasks=[],
                limits=limits,
                server_uri="urn:test:server",
                server_endpoint_url="opc.tcp://127.0.0.1:4840/testserver",
            )
            proto.closed_event = close_ev
            return proto

        loop = asyncio.get_running_loop()
        _transport, _protocol = await loop.create_connection(factory, "127.0.0.1", port)

        # Wait for the server handler to finish reading
        await asyncio.wait_for(close_ev.wait(), timeout=5.0)

    assert len(received) == 1
    assert received[0].ServerUri == "urn:test:server"
    assert received[0].EndpointUrl == "opc.tcp://127.0.0.1:4840/testserver"


# ---------------------------------------------------------------------------
# Integration: ReverseConnectManager dials out and retries
# ---------------------------------------------------------------------------


async def test_manager_dials_and_sends_reverse_hello():
    """
    ReverseConnectManager must dial the configured URI and send ReverseHello.
    """
    port = find_free_port()
    received: list[ua.ReverseHello] = []
    first_connection_ev = asyncio.Event()

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            rhel = await _read_reverse_hello(reader)
            received.append(rhel)
        finally:
            first_connection_ev.set()
            writer.close()

    srv = await asyncio.start_server(handle_client, "127.0.0.1", port)
    async with srv:
        iserver = InternalServer()
        config = ReverseConnectConfig(
            clients=[ReverseConnectClientEntry(endpoint_url=f"opc.tcp://127.0.0.1:{port}")],
            connect_interval=2_000,
        )
        manager = ReverseConnectManager(
            iserver=iserver,
            policies=[],
            closing_tasks=[],
            limits=make_limits(),
            server_uri="urn:myserver",
            server_endpoint_url="opc.tcp://127.0.0.1:4840",
            config=config,
        )
        await manager.start()
        try:
            await asyncio.wait_for(first_connection_ev.wait(), timeout=5.0)
        finally:
            await manager.stop()

    assert len(received) >= 1
    assert received[0].ServerUri == "urn:myserver"


async def test_manager_retries_on_refused():
    """
    When the target is not reachable, the manager should retry after reject_timeout
    and eventually connect when the listener comes up.
    """
    port = find_free_port()
    connected_ev = asyncio.Event()

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        await _read_reverse_hello(reader)
        connected_ev.set()
        writer.close()

    iserver = InternalServer()
    config = ReverseConnectConfig(
        clients=[ReverseConnectClientEntry(endpoint_url=f"opc.tcp://127.0.0.1:{port}")],
        connect_interval=200,   # quick retry for tests
        reject_timeout=200,
        connect_timeout=1_000,
    )
    manager = ReverseConnectManager(
        iserver=iserver,
        policies=[],
        closing_tasks=[],
        limits=make_limits(),
        server_uri="urn:retry:server",
        server_endpoint_url="opc.tcp://127.0.0.1:4840",
        config=config,
    )
    await manager.start()

    # Give manager a moment to fail a couple of times (port not yet open)
    await asyncio.sleep(0.5)

    # Now open the listener - manager should connect on its next retry
    srv = await asyncio.start_server(handle_client, "127.0.0.1", port)
    async with srv:
        try:
            await asyncio.wait_for(connected_ev.wait(), timeout=5.0)
        finally:
            await manager.stop()

    assert connected_ev.is_set()


async def test_manager_disabled_entry():
    """Disabled entries must never cause a connection attempt."""
    port = find_free_port()
    connection_count = 0

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        nonlocal connection_count
        connection_count += 1
        writer.close()

    srv = await asyncio.start_server(handle_client, "127.0.0.1", port)
    async with srv:
        iserver = InternalServer()
        config = ReverseConnectConfig(
            clients=[
                ReverseConnectClientEntry(
                    endpoint_url=f"opc.tcp://127.0.0.1:{port}",
                    enabled=False,
                )
            ],
        )
        manager = ReverseConnectManager(
            iserver=iserver,
            policies=[],
            closing_tasks=[],
            limits=make_limits(),
            server_uri="urn:disabled:server",
            server_endpoint_url="opc.tcp://127.0.0.1:4840",
            config=config,
        )
        await manager.start()
        await asyncio.sleep(0.3)
        await manager.stop()

    assert connection_count == 0, "Disabled entry should not have connected"


async def test_manager_stop_cancels_tasks():
    """ReverseConnectManager.stop() must complete without hanging."""
    port = find_free_port()  # nothing listening on this port

    iserver = InternalServer()
    config = ReverseConnectConfig(
        clients=[ReverseConnectClientEntry(endpoint_url=f"opc.tcp://127.0.0.1:{port}")],
        connect_interval=60_000,
        reject_timeout=60_000,
        connect_timeout=10_000,
    )
    manager = ReverseConnectManager(
        iserver=iserver,
        policies=[],
        closing_tasks=[],
        limits=make_limits(),
        server_uri="urn:stop:server",
        server_endpoint_url="opc.tcp://127.0.0.1:4840",
        config=config,
    )
    await manager.start()
    # Should return quickly even though connect_interval is huge
    await asyncio.wait_for(manager.stop(), timeout=3.0)
