import asyncio
from contextlib import nullcontext
from urllib.parse import urlparse

from asyncua.client.client import Client
from asyncua.client.rc_server import RCServer, ReverseConnection


class RCClient(Client):
    def __init__(
        self,
        rc_server: RCServer,
        *,
        rc_timeout: float | None = 30.0,
        timeout: float = 4,
        watchdog_intervall: float = 1.0,
    ) -> None:
        super().__init__("", timeout, watchdog_intervall, auto_reconnect=False)
        self._rc_server = rc_server
        self.rc_timeout = rc_timeout
        self._auto_reconnect = False

    async def _connect_sequence(self) -> None:
        """Run the connect handshake: reverse hello, channel, session, activate."""
        server_ctx = self._rc_server if not self._rc_server.is_listening else nullcontext(self._rc_server)
        async with server_ctx as server:
            conn: ReverseConnection = await asyncio.wait_for(server.wait_for_next_rc(), timeout=self.rc_timeout)
        self.uaclient.attach_socket(conn.transport, leftover_data=conn.leftover_data)
        self._server_url = urlparse(conn.server_endpoint)
        await self._connect_handshake()
