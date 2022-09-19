"""
Socket server forwarding request to internal server
"""
import logging
import asyncio
import math
from typing import Optional

from asyncua.common.connection import TransportLimits

from ..ua.ua_binary import header_from_binary
from ..common.utils import Buffer, NotEnoughData
from .uaprocessor import UaProcessor
from .internal_server import InternalServer

logger = logging.getLogger(__name__)


class OPCUAProtocol(asyncio.Protocol):
    """
    Instantiated for every connection.
    """

    def __init__(self, iserver: InternalServer, policies, clients, closing_tasks, limits: TransportLimits):
        self.peer_name = None
        self.transport = None
        self.processor = None
        self._buffer = b''
        self.iserver: InternalServer = iserver
        self.policies = policies
        self.clients = clients
        self.closing_tasks = closing_tasks
        self.messages = asyncio.Queue()
        self.limits = limits
        self._task = None

    def __str__(self):
        return f'OPCUAProtocol({self.peer_name}, {self.processor.session})'

    __repr__ = __str__

    def connection_made(self, transport):
        self.peer_name = transport.get_extra_info('peername')
        logger.info('New connection from %s', self.peer_name)
        self.transport = transport
        self.processor = UaProcessor(self.iserver, self.transport, self.limits)
        self.processor.set_policies(self.policies)
        self.iserver.asyncio_transports.append(transport)
        self.clients.append(self)
        self._task = asyncio.create_task(self._process_received_message_loop())

    def connection_lost(self, ex):
        logger.info('Lost connection from %s, %s', self.peer_name, ex)
        self.transport.close()
        self.iserver.asyncio_transports.remove(self.transport)
        closing_task = asyncio.create_task(self.processor.close())
        self.closing_tasks.append(closing_task)
        if self in self.clients:
            self.clients.remove(self)
        self.messages.put_nowait((None, None))
        self._task.cancel()

    def data_received(self, data):
        self._buffer += data
        # try to parse the incoming data
        while self._buffer:
            try:
                buf = Buffer(self._buffer)
                try:
                    header = header_from_binary(buf)
                except NotEnoughData:
                    # a packet should at least contain a header otherwise it is malformed (8 or 12 bytes)
                    logger.debug('Not enough data while parsing header from client, empty the buffer')
                    self.transport.close()
                    return
                if header.header_size + header.body_size <= header.header_size:
                    # malformed header prevent invalid access of your buffer
                    logger.error(f'Got malformed header {header}')
                    self.transport.close()
                else:
                    if len(buf) < header.body_size:
                        logger.debug('We did not receive enough data from client. Need %s got %s', header.body_size,
                                    len(buf))
                        return
                    # we have a complete message
                    self.messages.put_nowait((header, buf))
                    self._buffer = self._buffer[(header.header_size + header.body_size):]
            except Exception:
                logger.exception('Exception raised while parsing message from client')
                return

    async def _process_received_message_loop(self):
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
                logger.exception('Exception raised while processing message from client')

    async def _process_one_msg(self, header, buf):
        logger.debug('_process_received_message %s %s', header.body_size, len(buf))
        ret = await self.processor.process(header, buf)
        if not ret:
            logger.info('processor returned False, we close connection from %s', self.peer_name)
            self.transport.close()
            return


class BinaryServer:
    def __init__(self, internal_server: InternalServer, hostname, port):
        self.logger = logging.getLogger(__name__)
        self.hostname = hostname
        self.port = port
        self.iserver: InternalServer = internal_server
        self._server: Optional[asyncio.AbstractServer] = None
        self._policies = []
        self.clients = []
        self.closing_tasks = []
        self.cleanup_task = None
        # Use accectable limits
        buffer_sz = 65535
        max_msg_sz = 16 * 1024 * 1024  # 16mb simular to the opc ua c stack so this is a good default
        self.limits = TransportLimits(
            max_recv_buffer=buffer_sz,
            max_send_buffer=buffer_sz,
            max_chunk_count=math.ceil(buffer_sz / max_msg_sz),  # Round up to allow max msg size
            max_message_size=max_msg_sz
        )

    def set_policies(self, policies):
        self._policies = policies

    def _make_protocol(self):
        """Protocol Factory"""
        return OPCUAProtocol(
            iserver=self.iserver,
            policies=self._policies,
            clients=self.clients,
            closing_tasks=self.closing_tasks,
            limits=self.limits
        )

    async def start(self):
        self._server = await asyncio.get_running_loop().create_server(self._make_protocol, self.hostname, self.port)
        # get the port and the hostname from the created server socket
        # only relevant for dynamic port asignment (when self.port == 0)
        if self.port == 0 and len(self._server.sockets) == 1:
            # will work for AF_INET and AF_INET6 socket names
            # these are to only families supported by the create_server call
            sockname = self._server.sockets[0].getsockname()
            self.hostname = sockname[0]
            self.port = sockname[1]
        self.logger.info('Listening on %s:%s', self.hostname, self.port)
        self.cleanup_task = asyncio.create_task(self._close_task_loop())

    async def stop(self):
        self.logger.info('Closing asyncio socket server')
        for transport in self.iserver.asyncio_transports:
            transport.close()

        # stop cleanup process and run it a last time
        self.cleanup_task.cancel()
        try:
            await self.cleanup_task
        except asyncio.CancelledError:
            pass
        await self._close_tasks()

        if self._server:
            asyncio.get_running_loop().call_soon(self._server.close)
            await self._server.wait_closed()

    async def _close_task_loop(self):
        while True:
            await self._close_tasks()
            await asyncio.sleep(10)

    async def _close_tasks(self):
        while self.closing_tasks:
            task = self.closing_tasks.pop()
            try:
                await task
            except asyncio.CancelledError:
                # this means a stop request has been sent, it should not be catched
                raise
            except Exception:
                logger.exception("Unexpected crash in BinaryServer._close_tasks")
