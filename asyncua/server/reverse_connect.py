"""
OPC UA Reverse Connect support for the asyncua server.

Implements the server-side of OPC UA Reverse Connect as specified in
OPC UA Part 6 §7.1.3 and Part 2 §6.14.

In Reverse Connect the *server* dials an outgoing TCP connection to a
pre-configured client URI, then immediately sends a ``ReverseHello``
message.  The client uses that message to identify the connecting server
and, if desired, drives the rest of the OPC UA handshake exactly as if
*it* had connected (OpenSecureChannel → CreateSession → ActivateSession).

Usage example::

    from asyncua import Server
    from asyncua.server.reverse_connect import ReverseConnectConfig, ReverseConnectClientEntry

    server = Server()
    await server.init()
    server.reverse_connect = ReverseConnectConfig(
        clients=[
            ReverseConnectClientEntry(endpoint_url="opc.tcp://192.168.1.10:4840"),
        ],
        connect_interval=15_000,   # retry every 15 s
    )
    async with server:
        await asyncio.sleep(3600)
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from asyncua import ua
from asyncua.ua.ua_binary import uatcp_to_binary

from ..common.connection import TransportLimits
from ..common.utils import Buffer, NotEnoughData
from ..ua.ua_binary import header_from_binary
from .internal_server import InternalServer
from .uaprocessor import UaProcessor

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ReverseConnectClientEntry:
    """Configuration for a single reverse-connect target (one client endpoint)."""

    endpoint_url: str
    """OPC UA endpoint URL of the client listener, e.g. ``opc.tcp://host:4840``."""

    timeout: int = 30_000
    """Connection timeout in milliseconds (per-attempt)."""

    max_session_count: int = 0
    """Maximum simultaneous sessions over this reverse connection (0 = unlimited)."""

    enabled: bool = True
    """Set to ``False`` to disable this entry without removing it from the config."""


@dataclass
class ReverseConnectConfig:
    """Server-side Reverse Connect configuration."""

    clients: list[ReverseConnectClientEntry] = field(default_factory=list)
    """Ordered list of client endpoints the server should dial."""

    connect_interval: int = 15_000
    """Milliseconds to wait between connection attempts (or between retries on failure)."""

    connect_timeout: int = 30_000
    """Milliseconds to wait for the TCP connect+ReverseHello to succeed."""

    reject_timeout: int = 60_000
    """Milliseconds to wait before retrying after the remote actively refused the connection."""


# ---------------------------------------------------------------------------
# Protocol for outgoing reverse connections
# ---------------------------------------------------------------------------


class OPCUAReverseProtocol(asyncio.Protocol):
    """
    asyncio Protocol used for *outgoing* reverse-connect TCP connections.

    Behaviour is nearly identical to :class:`OPCUAProtocol` (the inbound
    server protocol), with two differences:

    1. In ``connection_made`` the protocol immediately writes a
       ``ReverseHello`` message so the remote client can identify the
       server.
    2. ``connection_lost`` sets an internal ``asyncio.Event`` that the
       owning :class:`ReverseConnectManager` task awaits to know when to
       schedule a reconnect.
    """

    def __init__(
        self,
        iserver: InternalServer,
        policies: list,
        clients: list,
        closing_tasks: list,
        limits: TransportLimits,
        server_uri: str,
        server_endpoint_url: str,
    ) -> None:
        self.peer_name = None
        self.transport: asyncio.Transport | None = None
        self.processor: UaProcessor | None = None
        self._buffer = b""
        self.iserver: InternalServer = iserver
        self.policies = policies
        self.clients = clients
        self.closing_tasks = closing_tasks
        self.messages: asyncio.Queue = asyncio.Queue()
        self.limits = limits
        self.server_uri = server_uri
        self.server_endpoint_url = server_endpoint_url
        # Signal fired in connection_lost so the manager loop can reschedule.
        self.closed_event: asyncio.Event = asyncio.Event()
        self._task: asyncio.Task | None = None

    def __str__(self) -> str:
        return f"OPCUAReverseProtocol({self.peer_name})"

    __repr__ = __str__

    def connection_made(self, transport: asyncio.Transport) -> None:  # type: ignore[override]
        self.peer_name = transport.get_extra_info("peername")
        _logger.info("Reverse connection established to %s", self.peer_name)
        self.transport = transport
        self.processor = UaProcessor(self.iserver, self.transport, self.limits)
        self.processor.set_policies(self.policies)
        self.iserver.asyncio_transports.append(transport)
        self.clients.append(self)
        self._task = asyncio.create_task(self._process_received_message_loop())

        # --- Send ReverseHello immediately --------------------------------
        rhel = ua.ReverseHello()
        rhel.ServerUri = self.server_uri
        rhel.EndpointUrl = self.server_endpoint_url
        transport.write(uatcp_to_binary(ua.MessageType.ReverseHello, rhel))
        _logger.debug(
            "Sent ReverseHello(ServerUri=%s, EndpointUrl=%s) to %s",
            self.server_uri,
            self.server_endpoint_url,
            self.peer_name,
        )

    def connection_lost(self, exc: Exception | None) -> None:
        _logger.info("Reverse connection to %s closed (%s)", self.peer_name, exc)
        self.transport.close()
        if self.transport in self.iserver.asyncio_transports:
            self.iserver.asyncio_transports.remove(self.transport)
        closing_task = asyncio.create_task(self.processor.close())
        self.closing_tasks.append(closing_task)
        if self in self.clients:
            self.clients.remove(self)
        self.messages.put_nowait((None, None))
        if self._task is not None:
            self._task.cancel()
        self.closed_event.set()

    def data_received(self, data: bytes) -> None:
        self._buffer += data
        while self._buffer:
            try:
                buf = Buffer(self._buffer)
                try:
                    header = header_from_binary(buf)
                except NotEnoughData:
                    return
                if header.header_size + header.body_size <= header.header_size:
                    _logger.error("Got malformed header %s from %s", header, self.peer_name)
                    self.transport.close()
                    return
                if len(buf) < header.body_size:
                    _logger.debug(
                        "Not enough data from %s: need %s, got %s",
                        self.peer_name,
                        header.body_size,
                        len(buf),
                    )
                    return
                self.messages.put_nowait((header, buf))
                self._buffer = self._buffer[(header.header_size + header.body_size) :]
            except Exception:
                _logger.exception("Exception while parsing message from %s", self.peer_name)
                return

    async def _process_received_message_loop(self) -> None:
        while True:
            header, buf = await self.messages.get()
            if header is None and buf is None:
                break
            try:
                await self._process_one_msg(header, buf)
            except Exception:
                _logger.exception("Exception while processing message from %s", self.peer_name)

    async def _process_one_msg(self, header, buf) -> None:
        _logger.debug("_process_received_message %s %s", header.body_size, len(buf))
        ret = await self.processor.process(header, buf)
        if not ret:
            _logger.info("Processor returned False; closing reverse connection to %s", self.peer_name)
            self.transport.close()


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class ReverseConnectManager:
    """
    Manages outgoing reverse-connect TCP connections on behalf of the server.

    For each enabled :class:`ReverseConnectClientEntry` a long-running
    asyncio task is created that:

    * dials the target URI,
    * sends a ``ReverseHello``,
    * waits until the connection closes,
    * then sleeps for ``connect_interval`` ms before retrying.

    The manager is started/stopped by :class:`~asyncua.server.Server`.
    """

    def __init__(
        self,
        iserver: InternalServer,
        policies: list,
        closing_tasks: list,
        limits: TransportLimits,
        server_uri: str,
        server_endpoint_url: str,
        config: ReverseConnectConfig,
    ) -> None:
        self.iserver = iserver
        self.policies = policies
        self.closing_tasks = closing_tasks
        self.limits = limits
        self.server_uri = server_uri
        self.server_endpoint_url = server_endpoint_url
        self.config = config
        self._clients: list = []
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start one reconnect loop per enabled client entry."""
        for entry in self.config.clients:
            if not entry.enabled:
                _logger.info("ReverseConnect: skipping disabled entry %s", entry.endpoint_url)
                continue
            task = asyncio.create_task(
                self._connect_loop(entry),
                name=f"rc-{entry.endpoint_url}",
            )
            self._tasks.append(task)
            _logger.info("ReverseConnect: started loop for %s", entry.endpoint_url)

    async def stop(self) -> None:
        """Cancel all reconnect tasks and wait for them to finish."""
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        _logger.info("ReverseConnect: all loops stopped")

    async def _connect_loop(self, entry: ReverseConnectClientEntry) -> None:
        """
        Infinite retry loop for a single reverse-connect target.

        The loop:
        1. Resolves host/port from the entry URL.
        2. Dials the client.
        3. Waits for the connection to close.
        4. Sleeps ``connect_interval`` ms and goes back to 1.
        """
        from urllib.parse import urlparse

        url = urlparse(entry.endpoint_url)
        host = url.hostname
        port = url.port or 4840
        connect_timeout_s = (entry.timeout or self.config.connect_timeout) / 1000.0
        interval_s = self.config.connect_interval / 1000.0
        reject_timeout_s = self.config.reject_timeout / 1000.0

        while True:
            try:
                _logger.info("ReverseConnect: attempting connection to %s:%s", host, port)
                loop = asyncio.get_running_loop()

                closed_event = asyncio.Event()

                def protocol_factory():
                    proto = OPCUAReverseProtocol(
                        iserver=self.iserver,
                        policies=self.policies,
                        clients=self._clients,
                        closing_tasks=self.closing_tasks,
                        limits=self.limits,
                        server_uri=self.server_uri,
                        server_endpoint_url=self.server_endpoint_url,
                    )
                    # Bind the event so we can await it below.
                    closed_event.__setattr__  # access to check it's there
                    proto.closed_event = closed_event
                    return proto

                _transport, _protocol = await asyncio.wait_for(
                    loop.create_connection(protocol_factory, host, port),
                    timeout=connect_timeout_s,
                )
                _logger.info("ReverseConnect: connected to %s:%s - waiting for session to end", host, port)
                # Wait until the protocol's connection_lost fires.
                await closed_event.wait()
                _logger.info("ReverseConnect: connection to %s:%s ended; will retry in %.1f s", host, port, interval_s)

            except asyncio.CancelledError:
                _logger.debug("ReverseConnect: loop for %s cancelled", entry.endpoint_url)
                return

            except ConnectionRefusedError:
                _logger.warning(
                    "ReverseConnect: connection to %s:%s was refused; retrying in %.1f s",
                    host,
                    port,
                    reject_timeout_s,
                )
                try:
                    await asyncio.sleep(reject_timeout_s)
                except asyncio.CancelledError:
                    return
                continue

            except (OSError, asyncio.TimeoutError) as exc:
                _logger.warning(
                    "ReverseConnect: could not connect to %s:%s (%s); retrying in %.1f s",
                    host,
                    port,
                    exc,
                    interval_s,
                )

            try:
                await asyncio.sleep(interval_s)
            except asyncio.CancelledError:
                return
