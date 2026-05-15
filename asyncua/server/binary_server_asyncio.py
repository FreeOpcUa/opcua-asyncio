"""
Socket server forwarding request to internal server
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..common.connection import TransportLimits
from ..common.utils import Buffer, NotEnoughData
from ..ua.ua_binary import header_from_binary
from .internal_server import InternalServer
from .uaprocessor import UaProcessor

_logger = logging.getLogger(__name__)


class OPCUAProtocol(asyncio.Protocol):
    """
    Instantiated for every connection.
    """

    def __init__(
        self,
        iserver: InternalServer,
        policies: list[Any],
        clients: list[OPCUAProtocol],
        closing_tasks: list[asyncio.Task[Any]],
        limits: TransportLimits,
    ) -> None:
        self.peer_name: Any = None
        self.transport: asyncio.Transport | None = None
        self.processor: UaProcessor | None = None
        self._buffer = b""
        self.iserver: InternalServer = iserver
        self.policies = policies
        self.clients = clients
        self.closing_tasks = closing_tasks
        self.messages: asyncio.Queue[tuple[Any, Any]] = asyncio.Queue()
        self.limits = limits
        self._task: asyncio.Task[Any] | None = None

    def __str__(self) -> str:
        return f"OPCUAProtocol({self.peer_name}, {self.processor.session})"  # type: ignore[union-attr]

    __repr__ = __str__

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.peer_name = transport.get_extra_info("peername")
        _logger.info("New connection from %s", self.peer_name)
        self.transport = transport  # type: ignore[assignment]
        self.processor = UaProcessor(self.iserver, self.transport, self.limits)
        self.processor.set_policies(self.policies)
        self.iserver.asyncio_transports.append(transport)
        self.clients.append(self)
        self._task = asyncio.create_task(self._process_received_message_loop())

    def connection_lost(self, ex: BaseException | None) -> None:
        _logger.info("Lost connection from %s, %s", self.peer_name, ex)
        if self.transport is not None:
            self.transport.close()
            self.iserver.asyncio_transports.remove(self.transport)
        if self.processor is not None:
            closing_task = asyncio.create_task(self.processor.close())
            self.closing_tasks.append(closing_task)
        if self in self.clients:
            self.clients.remove(self)
        self.messages.put_nowait((None, None))
        if self._task is not None:
            self._task.cancel()

    def data_received(self, data: bytes) -> None:
        self._buffer += data
        # try to parse the incoming data
        while self._buffer:
            try:
                buf = Buffer(self._buffer)
                try:
                    header = header_from_binary(buf)
                except NotEnoughData:
                    # we jsut wait for more data, that happens.
                    # worst case recv will go in timeout or it hangs and it should be fine too
                    return
                if header.header_size + header.body_size <= header.header_size:
                    # malformed header prevent invalid access of your buffer
                    _logger.error("Got malformed header %s", header)
                    if self.transport is not None:
                        self.transport.close()
                    return
                if len(buf) < header.body_size:
                    _logger.debug(
                        "We did not receive enough data from client. Need %s got %s", header.body_size, len(buf)
                    )
                    return
                # we have a complete message
                self.messages.put_nowait((header, buf))
                self._buffer = self._buffer[(header.header_size + header.body_size) :]
            except Exception:
                _logger.exception("Exception raised while parsing message from client")
                return

    async def _process_received_message_loop(self) -> None:
        """
        Take message from the queue and try to process it.
        """
        while True:
            header, buf = await self.messages.get()
            if header is None and buf is None:
                # Connection was closed, end task
                break
            try:
                await self._process_one_msg(header, buf)
            except Exception:
                _logger.exception("Exception raised while processing message from client")

    async def _process_one_msg(self, header: Any, buf: Buffer) -> None:
        _logger.debug("_process_received_message %s %s", header.body_size, len(buf))
        if self.processor is None:
            return
        ret = await self.processor.process(header, buf)
        if not ret:
            _logger.info("processor returned False, we close connection from %s", self.peer_name)
            if self.transport is not None:
                self.transport.close()
            return


class BinaryServer:
    def __init__(
        self,
        internal_server: InternalServer,
        hostname: str,
        port: int,
        limits: TransportLimits,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.hostname = hostname
        self.port = port
        self.iserver: InternalServer = internal_server
        self._server: asyncio.AbstractServer | None = None
        self._policies: list[Any] = []
        self.clients: list[OPCUAProtocol] = []
        self.closing_tasks: list[asyncio.Task[Any]] = []
        self.cleanup_task: asyncio.Task[Any] | None = None
        self.limits = limits

    def set_policies(self, policies: list[Any]) -> None:
        self._policies = policies

    def _make_protocol(self) -> OPCUAProtocol:
        """Protocol Factory"""
        return OPCUAProtocol(
            iserver=self.iserver,
            policies=self._policies,
            clients=self.clients,
            closing_tasks=self.closing_tasks,
            limits=self.limits,
        )

    async def start(self) -> None:
        self._server = await asyncio.get_running_loop().create_server(self._make_protocol, self.hostname, self.port)
        # get the port and the hostname from the created server socket
        # only relevant for dynamic port asignment (when self.port == 0)
        if self.port == 0 and len(self._server.sockets) == 1:
            # will work for AF_INET and AF_INET6 socket names
            # these are to only families supported by the create_server call
            sockname = self._server.sockets[0].getsockname()
            self.hostname = sockname[0]
            self.port = sockname[1]
        self.logger.info("Listening on %s:%s", self.hostname, self.port)
        self.cleanup_task = asyncio.create_task(self._close_task_loop())

    async def stop(self) -> None:
        self.logger.info("Closing asyncio socket server")
        for transport in self.iserver.asyncio_transports:
            transport.close()

        # stop cleanup process and run it a last time
        if self.cleanup_task is not None:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        await self._close_tasks()

        if self._server:
            asyncio.get_running_loop().call_soon(self._server.close)
            await self._server.wait_closed()

    async def _close_task_loop(self) -> None:
        while True:
            await self._close_tasks()
            await asyncio.sleep(10)

    async def _close_tasks(self) -> None:
        while self.closing_tasks:
            task = self.closing_tasks.pop()
            try:
                await task
            except Exception:
                _logger.exception("Unexpected crash in BinaryServer._close_tasks")
