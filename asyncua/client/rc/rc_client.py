"""Reverse connection client."""

import asyncio
from contextlib import nullcontext
from urllib.parse import urlparse

from asyncua.client.client import Client
from asyncua.client.rc.rc_server import RCServer, ReverseConnection


class RCClient(Client):
    """Reverse connection client.

    When setting security on the RC client, make sure to pass the server certificate!
    Otherwise client will try to dial the server to retrieve the certificate and
    will fail as the server address is unknown.

    The source of the reverse connections for the client is a RC server.
    If you just want to get a single RC client, give the not-listening RC server to the client and it will manage
    the server lifecycle itself.
    Otherwise, if you want to reuse the server for same/other RC clients, start the server before you give it out
    to any of the clients.
    """

    def __init__(
        self,
        rc_server: RCServer,
        *,
        rc_timeout: float | None = 30.0,
        timeout: float = 4,
        watchdog_intervall: float = 1.0,
    ) -> None:
        """
        :param rc_server: RC server to provide incoming reverse connections. If the server is not listening, the client
            will take 'ownership' of the server and will start and stop it for each `self.connect()` call.
        :param rc_timeout: Timeout to wait for an incoming reverse connection. If `None`, wait is indefinite.
            Defaults to 30.0 seconds.
        :param timeout: See `Client.timeout`.
        :param watchdog_intervall: See `Client.watchdog_intervall`.
        """
        super().__init__("", timeout, watchdog_intervall, auto_reconnect=False)
        self._rc_server_ctx = rc_server if not rc_server.is_listening else nullcontext(rc_server)
        self.rc_timeout = rc_timeout
        self._auto_reconnect = False

    async def _connect_sequence(self) -> None:
        """Run the connect handshake: reverse hello, channel, session, activate."""
        async with self._rc_server_ctx as server:
            conn: ReverseConnection = await asyncio.wait_for(server.next_rc(), timeout=self.rc_timeout)
        self.uaclient.attach_socket(conn.transport, leftover_data=conn.leftover_data)
        self._server_url = urlparse(conn.server_endpoint)
        await self._connect_handshake()
