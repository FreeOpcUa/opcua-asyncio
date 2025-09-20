import asyncio
import inspect
import logging

from dataclasses import dataclass, field
from enum import IntEnum
from functools import partial
from itertools import chain
from sortedcontainers import SortedDict  # type: ignore
from asyncua import Node, ua, Client
from asyncua.client.ua_client import UASocketProtocol
from asyncua.ua.uaerrors import BadSessionClosed, BadSessionNotActivated
from typing import Dict, List, Set, Tuple, Type, Union
from collections.abc import Generator, Iterable, Sequence

from .reconciliator import Reconciliator
from .common import ClientNotFound, event_wait
from .virtual_subscription import TypeSubHandler, VirtualSubscription
from ...crypto.uacrypto import CertProperties
from ...crypto.security_policies import SecurityPolicy


_logger = logging.getLogger(__name__)


class HaMode(IntEnum):
    # OPC UA Part 4 - 6.6.2.4.5.2 - Cold
    # Only connect to the active_client, failover is managed by
    # promoting another client of the pool to active_client
    COLD = 0
    # OPC UA Part 4 - 6.6.2.4.5.3 - Warm
    # Enable the active client similarly to the cold mode.
    # Secondary clients create the MonitoredItems,
    # but disable sampling and publishing.
    WARM = 1
    # OPC UA Part 4 - 6.6.2.4.5.4 - Hot A
    # Client connects to multiple Servers and establishes
    # subscription(s) in each where only one is Reporting;
    # the others are Sampling only.
    HOT_A = 2
    # OPC UA Part 4 - 6.6.2.4.5.4 - Hot B
    # Client connects to multiple Servers and establishes
    # subscription(s) in each where all subscriptions are Reporting.
    # The Client is responsible for handling/processing
    # multiple subscription streams concurrently.
    HOT_B = 3


class ConnectionStates(IntEnum):
    """
    OPC UA Part 4 - Services Release
    Section 6.6.2.4.2 ServiceLevel
    """

    IN_MAINTENANCE = 0
    NO_DATA = 1
    DEGRADED = 2
    HEALTHY = 200


@dataclass
class ServerInfo:
    url: str
    status: ConnectionStates = ConnectionStates(1)


@dataclass(frozen=True, eq=True)
class HaSecurityConfig:
    policy: Type[SecurityPolicy] | None = None
    certificate: CertProperties | None = None
    private_key: CertProperties | None = None
    server_certificate: CertProperties | None = None
    mode: ua.MessageSecurityMode | None = None


@dataclass(frozen=True, eq=True)
class HaConfig:
    """
    Parameters for the HaClient constructor.
    Timers and timeouts are all in seconds.
    """

    ha_mode: HaMode
    keepalive_timer: int = 15
    manager_timer: int = 15
    reconciliator_timer: int = 15
    session_timeout: int = 60
    request_timeout: int = 30
    secure_channel_timeout: int = 3600
    session_name: str = "HaClient"
    urls: List[str] = field(default_factory=list)


class HaClient:
    """
    The HaClient is responsible for managing non-transparent server redundancy.
    The two servers must have:
        - Identical NodeIds
        - Identical browse path and AddressSpace structure
        - Identical Service Level logic
        - However nodes in the server local namespace can differ
        - Time synchronization (e.g NTP)
    It starts the OPC-UA clients and connect to the server that
    fits in the HaMode selected.
    """

    # Override this if your servers require custom ServiceLevels
    # i.e: You're using an OPC-UA proxy
    HEALTHY_STATE = ConnectionStates.HEALTHY

    def __init__(self, config: HaConfig, security: HaSecurityConfig | None = None) -> None:
        self._config: HaConfig = config
        self._keepalive_task: Dict[KeepAlive, asyncio.Task] = {}
        self._manager_task: Dict[HaManager, asyncio.Task] = {}
        self._reconciliator_task: Dict[Reconciliator, asyncio.Task] = {}
        self._gen_sub: Generator[str, None, None] = self.generate_sub_name()

        # An event loop must be set in the current thread
        self._url_to_reset_lock = asyncio.Lock()
        self._ideal_map_lock: asyncio.Lock = asyncio.Lock()
        self._client_lock: asyncio.Lock = asyncio.Lock()

        self.clients: Dict[Client, ServerInfo] = {}
        self.active_client: Client | None = None
        # full type: Dict[str, SortedDict[str, VirtualSubscription]]
        self.ideal_map: Dict[str, SortedDict] = {}
        self.sub_names: Set[str] = set()
        self.url_to_reset: Set[str] = set()
        self.is_running = False

        if config.ha_mode != HaMode.WARM:
            # TODO
            # Check if transparent redundancy support exist for the server (nodeid=2035)
            # and prevent using HaClient with such servers.
            raise NotImplementedError(f"{config.ha_mode} not currently supported by HaClient")

        for url in self.urls:
            c = Client(url, timeout=self._config.request_timeout)
            # timeouts for the session and secure channel are in ms
            c.session_timeout = self._config.session_timeout * 1000
            c.secure_channel_timeout = self._config.secure_channel_timeout * 1000
            c.description = self._config.session_name
            server_info = ServerInfo(url)
            self.clients[c] = server_info
            self.ideal_map[url] = SortedDict()

        # security can also be set via the set_security method
        self.security_config: HaSecurityConfig = security if security else HaSecurityConfig()
        self.manager = HaManager(self, self._config.manager_timer)
        self.reconciliator = Reconciliator(self._config.reconciliator_timer, self)

    async def start(self) -> None:
        for client, server in self.clients.items():
            keepalive = KeepAlive(client, server, self._config.keepalive_timer)
            task = asyncio.create_task(keepalive.run())
            self._keepalive_task[keepalive] = task

        task = asyncio.create_task(self.manager.run())
        self._manager_task[self.manager] = task

        task = asyncio.create_task(self.reconciliator.run())
        self._reconciliator_task[self.reconciliator] = task

        self.is_running = True

    async def stop(self):
        to_stop: Sequence[Union[KeepAlive, HaManager, Reconciliator]] = chain(
            self._keepalive_task, self._manager_task, self._reconciliator_task
        )
        stop = [p.stop() for p in to_stop]

        await asyncio.gather(*stop)
        disco = [c.disconnect() for c in self.clients]
        await asyncio.gather(*disco, return_exceptions=True)

        tasks = list(
            chain(
                self._keepalive_task.values(),
                self._manager_task.values(),
                self._reconciliator_task.values(),
            )
        )

        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.is_running = False

    def set_security(
        self,
        policy: Type[SecurityPolicy],
        certificate: CertProperties,
        private_key: CertProperties,
        server_certificate: CertProperties | None = None,
        mode: ua.MessageSecurityMode = ua.MessageSecurityMode.SignAndEncrypt,
    ) -> None:
        self.security_config = HaSecurityConfig(policy, certificate, private_key, server_certificate, mode)

    async def create_subscription(self, period: int, handler: TypeSubHandler) -> str:
        async with self._ideal_map_lock:
            sub_name = next(self._gen_sub)
            for client in self.clients:
                if client == self.active_client:
                    vs = VirtualSubscription(
                        period=period,
                        handler=handler,
                        publishing=True,
                        monitoring=ua.MonitoringMode.Reporting,
                    )
                else:
                    vs = VirtualSubscription(
                        period=period,
                        handler=handler,
                        publishing=False,
                        monitoring=ua.MonitoringMode.Disabled,
                    )
                url = client.server_url.geturl()
                self.ideal_map[url][sub_name] = vs
            return sub_name

    async def subscribe_data_change(
        self,
        sub_name: str,
        nodes: Union[Iterable[Node], Iterable[str]],
        attr=ua.AttributeIds.Value,
        queuesize=0,
    ) -> None:
        async with self._ideal_map_lock:
            # FIXME: nodeid can be None
            nodes = [n.nodeid.to_string() if isinstance(n, Node) else n for n in nodes]  # type: ignore[union-attr]
            for url in self.urls:
                vs = self.ideal_map[url].get(sub_name)
                if not vs:
                    _logger.warning(
                        "The subscription specified for the data_change: %s doesn't exist in ideal_map", sub_name
                    )
                    return
                vs.subscribe_data_change(nodes, attr, queuesize)
                await self.hook_on_subscribe(nodes=nodes, attr=attr, queuesize=queuesize, url=url)

    async def delete_subscriptions(self, sub_names: List[str]) -> None:
        async with self._ideal_map_lock:
            for sub_name in sub_names:
                for url in self.urls:
                    if self.ideal_map[url].get(sub_name):
                        self.ideal_map[url].pop(sub_name)
                    else:
                        _logger.warning("No subscription named %s in ideal_map", sub_name)
                self.sub_names.remove(sub_name)

    async def reconnect(self, client: Client) -> None:
        """
        Reconnect a client of the HA set and
        add its URL to the reset list.
        """
        async with self._url_to_reset_lock:
            url = client.server_url.geturl()
            self.url_to_reset.add(url)
        try:
            await client.disconnect()
        except Exception:
            pass
        await self.hook_on_reconnect(client=client)
        if self.security_config.policy:
            await client.set_security(**self.security_config.__dict__)
        await client.connect()

    async def unsubscribe(self, nodes: Union[Iterable[Node], Iterable[str]]) -> None:
        async with self._ideal_map_lock:
            sub_to_nodes = {}
            first_url = self.urls[0]
            for sub_name, vs in self.ideal_map[first_url].items():
                # FIXME: nodeid can be None
                node_set = {
                    n.nodeid.to_string() if isinstance(n, Node) else n
                    for n in nodes  # type: ignore[union-attr]
                }
                to_del = node_set & vs.get_nodes()
                if to_del:
                    sub_to_nodes[sub_name] = to_del
            for url in self.urls:
                for sub_name, str_nodes in sub_to_nodes.items():
                    vs = self.ideal_map[url][sub_name]
                    vs.unsubscribe(str_nodes)
                    await self.hook_on_unsubscribe(url=url, nodes=str_nodes)

    async def failover_warm(self, primary: Client | None, secondaries: Iterable[Client]) -> None:
        async with self._ideal_map_lock:
            if primary:
                self._set_monitoring_mode(ua.MonitoringMode.Reporting, clients=[primary])
                self._set_publishing_mode(True, clients=[primary])
            self.active_client = primary
            self._set_monitoring_mode(ua.MonitoringMode.Disabled, clients=secondaries)
            self._set_publishing_mode(False, clients=secondaries)

    def _set_monitoring_mode(self, monitoring: ua.MonitoringMode, clients: Iterable[Client]) -> None:
        for client in clients:
            url = client.server_url.geturl()
            for sub in self.ideal_map[url]:
                vs = self.ideal_map[url][sub]
                vs.monitoring = monitoring

    def _set_publishing_mode(self, publishing: bool, clients: Iterable[Client]) -> None:
        for client in clients:
            url = client.server_url.geturl()
            for sub in self.ideal_map[url]:
                vs = self.ideal_map[url][sub]
                vs.publishing = publishing

    async def group_clients_by_health(self) -> Tuple[List[Client], List[Client]]:
        healthy = []
        unhealthy = []
        async with self._client_lock:
            for client, server in self.clients.items():
                if server.status >= self.HEALTHY_STATE:
                    healthy.append(client)
                else:
                    unhealthy.append(client)
            return healthy, unhealthy

    async def get_serving_client(self, clients: List[Client], serving_client: Client | None) -> Client | None:
        """
        Returns the client with the higher service level.

        The service level reference is taken from the active_client,
        thus we prevent failing over when mutliple clients
        return the same number.
        """
        async with self._client_lock:
            if serving_client:
                max_slevel = self.clients[serving_client].status
            else:
                max_slevel = ConnectionStates.NO_DATA

            for c in clients:
                c_slevel = self.clients[c].status
                if c_slevel > max_slevel:
                    serving_client = c
                    max_slevel = c_slevel
            return serving_client if max_slevel >= self.HEALTHY_STATE else None

    async def debug_status(self):
        """
        Return the class attribute for troubleshooting purposes
        """
        for a in inspect.getmembers(self):
            if not a[0].startswith("__") and not inspect.ismethod(a[1]):
                _logger.debug(a)

    def get_client_warm_mode(self) -> List[Client]:
        return list(self.clients)

    def get_clients(self) -> List[Client]:
        ha_mode = self.ha_mode
        func = f"get_client_{ha_mode}_mode"
        get_clients = getattr(self, func)
        active_clients = get_clients()
        if not isinstance(active_clients, list):
            active_clients = [active_clients]
        return active_clients

    def get_client_by_url(self, url) -> Client:
        for client, srv_info in self.clients.items():
            if srv_info.url == url:
                return client
        raise ClientNotFound(f"{url} not managed by HaClient")

    @property
    def session_timeout(self) -> int:
        return self._config.session_timeout

    @property
    def ha_mode(self) -> str:
        return self._config.ha_mode.name.lower()

    @property
    def urls(self) -> List[str]:
        return self._config.urls

    def generate_sub_name(self) -> Generator[str, None, None]:
        """
        Asyncio unsafe - yield names for subscriptions.
        """
        while True:
            for i in range(9999):
                sub_name = f"sub_{i}"
                if sub_name in self.sub_names:
                    continue
                self.sub_names.add(sub_name)
                yield sub_name

    async def hook_on_reconnect(self, **kwargs):
        pass

    async def hook_on_subscribe(self, **kwargs):
        pass

    async def hook_on_unsubscribe(self, **kwargs):
        pass


class KeepAlive:
    """
    Ping the server status regularly to check its health
    """

    def __init__(self, client, server, timer) -> None:
        self.client: Client = client
        self.server: ServerInfo = server
        self.timer: int = timer
        self.stop_event: asyncio.locks.Event = asyncio.Event()
        self.is_running: bool = False

    async def stop(self) -> None:
        self.stop_event.set()

    async def run(self) -> None:
        status_node = self.client.nodes.server_state
        slevel_node = self.client.nodes.service_level
        server_info = self.server
        client = self.client
        # wait for HaManager to connect clients
        await asyncio.sleep(3)
        self.is_running = True
        _logger.info("Starting keepalive loop for %s, checking every %dsec", server_info.url, self.timer)
        while self.is_running:
            if client.uaclient.protocol is None:
                server_info.status = ConnectionStates.NO_DATA
                _logger.info("No active client")
            else:
                try:
                    status, slevel = await client.read_values([status_node, slevel_node])
                    if status != ua.ServerState.Running:
                        _logger.info("ServerState is not running")
                        server_info.status = ConnectionStates.NO_DATA
                    else:
                        server_info.status = slevel
                except BadSessionNotActivated:
                    _logger.warning("Session is not yet activated.")
                    server_info.status = ConnectionStates.NO_DATA
                except BadSessionClosed:
                    _logger.warning("Session is closed.")
                    server_info.status = ConnectionStates.NO_DATA
                except ConnectionError:
                    _logger.warning("No connection.")
                    server_info.status = ConnectionStates.NO_DATA
                except asyncio.TimeoutError:
                    _logger.warning("Timeout when fetching state")
                    server_info.status = ConnectionStates.NO_DATA
                except asyncio.CancelledError:
                    _logger.warning("CancelledError, this means we should shutdown")
                    server_info.status = ConnectionStates.NO_DATA
                    # FIXME: It cannot be correct to catch CancelledError here, we should re-raise
                except Exception:
                    _logger.exception("Unknown exception during keepalive liveness check")
                    server_info.status = ConnectionStates.NO_DATA

            _logger.info("ServiceLevel for %s: %s", server_info.url, server_info.status)
            if await event_wait(self.stop_event, self.timer):
                self.is_running = False
                break


class HaManager:
    """
    The manager handles individual client connections
    according to the selected HaMode
    """

    def __init__(self, ha_client: HaClient, timer: int | None = None) -> None:
        self.ha_client = ha_client
        self.timer = self.set_loop_timer(timer)
        self.stop_event = asyncio.Event()
        self.is_running = False

    def set_loop_timer(self, timer: int | None):
        return timer if timer else int(self.ha_client.session_timeout)

    async def run(self) -> None:
        ha_mode = self.ha_client.ha_mode
        update_func = f"update_state_{ha_mode}"
        update_state = getattr(self, update_func)
        reco_func = f"reconnect_{ha_mode}"
        reconnect = getattr(self, reco_func)
        self.is_running = True

        _logger.info("Starting HaManager loop, checking every %dsec", self.timer)
        while self.is_running:
            # failover happens here
            await update_state()
            await reconnect()
            await self.ha_client.debug_status()

            if await event_wait(self.stop_event, self.timer):
                self.is_running = False
                break

    async def stop(self) -> None:
        self.stop_event.set()

    async def update_state_warm(self) -> None:
        active_client = self.ha_client.active_client
        clients = self.ha_client.get_clients()
        primary_client = await self.ha_client.get_serving_client(list(self.ha_client.clients), active_client)
        if primary_client != active_client:
            # disable monitoring and reporting when the service_level goes below 200
            _logger.info("Failing over active client from %s to %s", active_client, primary_client)
            secondaries = set(clients) - {primary_client} if primary_client else set(clients)
            await self.ha_client.failover_warm(primary=primary_client, secondaries=secondaries)

    async def reconnect_warm(self) -> None:
        """
        Reconnect disconnected clients
        """
        healthy, unhealthy = await self.ha_client.group_clients_by_health()

        async def reco_resub(client: Client, force: bool):
            if (
                force
                or not client.uaclient.protocol
                or client.uaclient.protocol
                and client.uaclient.protocol.state == UASocketProtocol.CLOSED
            ):
                _logger.info("Virtually reconnecting and resubscribing %s", client)
                await self.ha_client.reconnect(client=client)

        def log_exception(client: Client, fut: asyncio.Task):
            if fut.exception():
                _logger.warning("Error when reconnecting %s: %s", client, fut.exception())

        tasks = []
        for client in healthy:
            task = asyncio.create_task(reco_resub(client, force=False))
            task.add_done_callback(partial(log_exception, client))
            tasks.append(task)
        for client in unhealthy:
            task = asyncio.create_task(reco_resub(client, force=True))
            task.add_done_callback(partial(log_exception, client))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
