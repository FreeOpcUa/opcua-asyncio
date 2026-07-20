"""Reverse connection client-side server."""

import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from types import TracebackType

from asyncua import ua
from asyncua.ua import ua_binary, uatypes

_logger = logging.getLogger(__name__)


# limits according to spec Part 6 §7.1.2.6
_MAX_SERVER_URI_LENGTH = 4095
_MAX_ENDPOINT_URL_LENGTH = 4095


@dataclass(frozen=True)
class ReverseConnection:
    """Active reverse connection payload."""

    transport: asyncio.Transport
    server_application_uri: str
    server_endpoint: str
    leftover_data: bytes

    def close(self) -> None:
        self.transport.close()


RCValidateHook = Callable[[ua.ReverseHello], None]


class RCProtocol(asyncio.Protocol):
    """Handle initial reverse hello and yield a connection (Transport)."""

    def __init__(
        self,
        connections: list[asyncio.Transport],
        ready_clients: asyncio.Queue[ReverseConnection],
        *,
        rc_validation_hook: RCValidateHook | None = None,
        slow_connection_timeout: float | None = None,
    ) -> None:
        """
        :param connections: Server connections list.
        :param ready_clients: Queue of ready (accepted) connections.
        :param rc_validation_hook: Hook to extra validate Reverse Hello. Defaults to None.
        :param slow_connection_timeout: Timeout for slow connections. Defaults to None.
        """

        self.rec_buf = bytearray()
        self.transport: asyncio.Transport | None = None
        self.connections = connections
        self.ready_clients = ready_clients
        self.rc_validation_hook = rc_validation_hook
        self.peer: tuple[str, int] | None = None

        self.slow_conn_timeout = slow_connection_timeout
        self.slow_conn_timeout_handle: asyncio.TimerHandle | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        if not isinstance(transport, asyncio.Transport):
            raise TypeError(f"Unexpected transport type: {type(transport)}")
        self.transport = transport
        self.peer = transport.get_extra_info("peername")
        _logger.debug("New connection from %s", self.peer)
        self.connections.append(self.transport)
        if self.slow_conn_timeout:
            self.slow_conn_timeout_handle = asyncio.get_running_loop().call_later(
                delay=self.slow_conn_timeout, callback=self._on_slow_connection_timeout
            )

    def connection_lost(self, exc: Exception | None) -> None:
        if not exc:
            _logger.debug("Connection from %s was closed.", self.peer)
        else:
            _logger.debug("Connection from %s was closed because of the exception.", self.peer, exc_info=exc)
        self._close()

    def data_received(self, data: bytes) -> None:
        if not self.transport:
            return

        self.rec_buf.extend(data)
        buf = ua.utils.Buffer(bytes(self.rec_buf))

        header = self._parse_header(buf)
        if not header:
            return

        reverse_hello = self._parse_rc_hello(header, buf)
        if not reverse_hello:
            return

        if self.rc_validation_hook:
            try:
                self.rc_validation_hook(reverse_hello)
            except Exception as e:
                _logger.warning("Reverse connection from %s did not pass validation - dropping", self.peer, exc_info=e)
                self._close()
                return

        if self.ready_clients.full():
            _logger.warning("RC client queue is full, dropping connection from %s", self.peer)
            self._close()
            return

        self._cancel_slow_connection_timeout()
        self.transport.pause_reading()
        leftover = buf.read(len(buf))
        t, self.transport = self.transport, None
        rc = ReverseConnection(t, reverse_hello.ServerUri, reverse_hello.EndpointUrl, leftover_data=leftover)
        self.connections.remove(rc.transport)
        self.ready_clients.put_nowait(rc)
        _logger.info("Accepted reverse connection %s from %s", rc, self.peer)
        self._close()

    def _parse_header(self, buf: ua.utils.Buffer) -> ua.Header | None:
        try:
            header = ua_binary.header_from_binary(buf)
        except ua.utils.NotEnoughData:
            return None
        if header.MessageType != ua.MessageType.ReverseHello:
            _logger.debug("Received different message than reverse hello from %s - dropping", self.peer)
            self._close()
            return None
        return header

    def _parse_rc_hello(self, header: ua.Header, buf: ua.utils.Buffer) -> ua.ReverseHello | None:
        if len(buf) < header.body_size:
            return None

        try:
            reverse_hello = ua_binary.struct_from_binary(ua.ReverseHello, buf)
        except Exception:
            _logger.debug("Received invalid reverse hello message from %s - dropping", self.peer)
            self._close()
            return None

        error = None
        if len(reverse_hello.ServerUri) > _MAX_SERVER_URI_LENGTH:
            error = ua.ErrorMessage(
                ua.StatusCode(ua.StatusCodes.BadServerUriInvalid), uatypes.String("Server URI is too long")
            )
        elif len(reverse_hello.EndpointUrl) > _MAX_ENDPOINT_URL_LENGTH:
            error = ua.ErrorMessage(
                ua.StatusCode(ua.StatusCodes.BadTcpEndpointUrlInvalid), uatypes.String("Endpoint URL is too long")
            )

        if error:
            if self.transport:
                self.transport.write(ua_binary.uatcp_to_binary(ua.MessageType.Error, error))
            _logger.debug("Received reverse hello message with very long URL/URI from %s - dropping", self.peer)
            self._close()
            return None

        return reverse_hello

    def _close(self) -> None:
        """Close current connection, cancel timeout, reset state, if any."""
        self.rec_buf.clear()
        self._cancel_slow_connection_timeout()
        if self.transport:
            with suppress(ValueError):
                self.connections.remove(self.transport)
            self.transport.close()
            self.transport = None

    def _on_slow_connection_timeout(self) -> None:
        _logger.debug("Dropping a slow connection from %s after timeout of %.1fs", self.peer, self.slow_conn_timeout)
        self._close()

    def _cancel_slow_connection_timeout(self) -> None:
        if self.slow_conn_timeout_handle:
            self.slow_conn_timeout_handle.cancel()
            self.slow_conn_timeout_handle = None


class RCServer:
    """Reverse connection client-side server.

    RC server accepts reverse connections, processes the rc-specific part of the handshake and hands out the
    connection to be handle as a regular UA connection.
    """

    def __init__(
        self,
        host: str,
        port: int,
        *,
        rc_validation_hook: RCValidateHook | None = None,
        slow_connection_timeout: float | None = None,
        reuse_address: bool | None = None,
    ) -> None:
        """Init Self.

        :param host: Host.
        :param port: Port.
        :param rc_validation_hook: Hook to check the Server URI/Endpoint URL in
            Reverse Hello message. Defaults to None.
        :param slow_connection_timeout: Deadline for Reverse Hello to be processed since connection
            initiated, to mitigate slow clients. Defaults to None.
        :param reuse_address: Whether to reuse address (see asyncio loop.create_server()). Defaults to None.
        """
        self.host = host
        self.port = port
        self.slow_connection_timeout = slow_connection_timeout
        self.reuse_address = reuse_address

        self._server: asyncio.Server | None = None
        self._connections: list[asyncio.Transport] = []
        self._ready_clients = asyncio.Queue[ReverseConnection]()
        self._rc_validation_hook = rc_validation_hook

    @property
    def is_listening(self) -> bool:
        """Whether server is currently listening."""
        return self._server is not None

    async def start(self) -> None:
        """Start listening for incoming reverse connections."""
        self._server = await asyncio.get_running_loop().create_server(
            lambda: RCProtocol(
                self._connections,
                self._ready_clients,
                rc_validation_hook=self._rc_validation_hook,
                slow_connection_timeout=self.slow_connection_timeout,
            ),
            self.host,
            self.port,
            reuse_address=self.reuse_address,
            start_serving=True,
        )

    async def stop(self) -> None:
        """Stop listening for new reverse connections and cancel all waiting or being-processed connections."""
        server, self._server = self._server, None
        if server is not None:
            server.close()
        connections, self._connections = self._connections, []
        for c in connections:
            c.close()
        ready_clients, self._ready_clients = self._ready_clients, asyncio.Queue()
        while not ready_clients.empty():
            client = ready_clients.get_nowait()
            client.close()

    async def next_rc(self) -> ReverseConnection:
        """Get the next reverse connection, blocking until it comes in (server must be listening)."""
        if not self.is_listening:
            raise RuntimeError("Can not wait for reverse connections when server is not listening")
        return await self._ready_clients.get()

    async def __aenter__(self) -> "RCServer":
        await self.start()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        await self.stop()
