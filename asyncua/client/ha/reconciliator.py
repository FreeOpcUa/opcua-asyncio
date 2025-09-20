import asyncio
import inspect
import logging
import time

from collections import defaultdict
from dataclasses import astuple
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Dict, Set, Union
from sortedcontainers import SortedDict  # type: ignore
from asyncua import ua, Client
from pickle import PicklingError

from .common import batch, event_wait, get_digest
from .virtual_subscription import VirtualSubscription

if TYPE_CHECKING:
    from asyncua.sync import Subscription


_logger = logging.getLogger(__name__)

SubMap = Dict[str, SortedDict]


if TYPE_CHECKING:
    from .ha_client import HaClient


class Method(Enum):
    """
    Map the actions to the lower level object methods
    """

    ADD_SUB = "create_subscription"
    ADD_MI = "subscribe_data_change"
    DEL_SUB = "delete_subscription"
    DEL_MI = "unsubscribe"
    MONITORING = "set_monitoring_mode"
    PUBLISHING = "set_publishing_mode"


class Reconciliator:
    """
    Reconciliator is a side-task of HaClient. It regularly
    applies the HaClient subscription configurations to actual
    OPC-UA objects.

    After a successfull reconciliation and if all the client status
    are >= HEALTHY_STATE, the ideal_map is equal to the real_map.
    """

    BATCH_MI_SIZE = 1000

    def __init__(self, timer: int, ha_client: "HaClient") -> None:
        self.timer = timer
        self.ha_client = ha_client
        self.is_running = False

        # An event loop must be set in the current thread
        self.stop_event = asyncio.Event()

        self.real_map: Dict[str, SortedDict] = {}
        for url in self.ha_client.urls:
            # full type: Dict[str, SortedDict[str, VirtualSubscription]]
            self.real_map[url] = SortedDict()

        self.name_to_subscription = defaultdict(dict)
        self.node_to_handle = defaultdict(dict)
        self.init_hooks()

    def init_hooks(self) -> None:
        """
        Implement hooks for custom actions like collecting metrics
        or triggering external events.
        """
        hook_prefix = "hook_"
        hook_events = ["mi_request", "del_from_map", "add_to_map", "add_to_map_error"]
        hooks = [f"{hook_prefix}{evt}" for evt in hook_events]
        for hook in hooks:
            if getattr(self, hook, None):
                continue
            setattr(self, hook, lambda **kwargs: None)

    async def run(self) -> None:
        _logger.info("Starting Reconciliator loop, checking every %dsec", self.timer)
        self.is_running = True
        while self.is_running:
            start = time.monotonic()
            async with self.ha_client._url_to_reset_lock:
                await self.resubscribe()
            async with self.ha_client._ideal_map_lock:
                await self.reconciliate()
            await self.debug_status()
            stop = time.monotonic() - start
            _logger.info("[TIME] Reconciliation: %.2fsec", stop)

            if await event_wait(self.stop_event, self.timer):
                self.is_running = False
                break

    async def stop(self) -> None:
        self.stop_event.set()

    async def resubscribe(self) -> None:
        """
        Remove all the subscriptions from the real_map.

        Deleting them from the remote server would be
        helpless because they are tied to a deleted session,
        however they should eventually time out.
        """
        _logger.debug("In resubscribe")
        url_to_reset = self.ha_client.url_to_reset
        while url_to_reset:
            url = url_to_reset.pop()
            self.real_map[url].clear()
            if self.name_to_subscription.get(url):
                self.name_to_subscription.pop(url)
            if self.node_to_handle.get(url):
                self.node_to_handle.pop(url)

    async def reconciliate(self) -> None:
        """
        Identify the differences between the ideal and the real_map
        and take actual actions on the underlying OPC-UA objects.

        We only tries to reconciliate healthy clients, since most of the
        unhealthy clients will end up resubscribing and their map
        will be cleared anyway.

        Reconciliator steps are ordered this way:

          1 - Resubscribe newly reconnected clients
          2 - Identify gap with healthy client configurations
          3 - Remove/Add subscription
          4 - Add nodes to subscriptions
          5 - Update publishing/monitoring options
        """

        ideal_map = self.ha_client.ideal_map
        healthy, unhealthy = await self.ha_client.group_clients_by_health()
        async with self.ha_client._client_lock:
            valid_urls = {self.ha_client.clients[h].url for h in healthy}
        real_map = self.real_map
        try:
            targets = set()
            for url in valid_urls:
                digest_ideal = get_digest(ideal_map[url])
                digest_real = get_digest(real_map[url])
                if url not in real_map or digest_ideal != digest_real:
                    targets.add(url)
            if not targets:
                _logger.info("[PASS] No configuration difference for healthy targets: %s", valid_urls)
                return
            _logger.info("[WORK] Configuration difference found for healthy targets: %s", targets)
        except (AttributeError, TypeError, PicklingError) as e:
            _logger.warning("[WORK] Reconciliator performance impacted: %s", e)
            targets = set(valid_urls)
        # add missing and delete unsubscribed subs
        await self.update_subscriptions(real_map, ideal_map, targets)
        # add and remove nodes
        await self.update_nodes(real_map, ideal_map, targets)
        # look for missing options (publish/monitoring) for existing subs
        await self.update_subscription_modes(real_map, ideal_map, targets)

    async def update_subscriptions(self, real_map, ideal_map, targets: Set[str]) -> None:
        _logger.debug("In update_subscriptions")
        tasks = []
        for url in targets:
            tasks.extend(self._subs_to_del(url, real_map, ideal_map))
            tasks.extend(self._subs_to_add(url, real_map, ideal_map))
        await asyncio.gather(*tasks, return_exceptions=True)

    def _subs_to_del(self, url: str, real_map: SubMap, ideal_map: SubMap) -> list[asyncio.Task]:
        to_del: list[asyncio.Task] = []
        sub_to_del = set(real_map[url]) - set(ideal_map[url])
        if sub_to_del:
            _logger.info("Removing %d subscriptions", len(sub_to_del))
        for sub_name in sub_to_del:
            sub_handle = self.name_to_subscription[url][sub_name]
            task = asyncio.create_task(sub_handle.delete())
            task.add_done_callback(partial(self.del_from_map, url, Method.DEL_SUB, sub_name=sub_name))
            to_del.append(task)
        return to_del

    def _subs_to_add(self, url: str, real_map: SubMap, ideal_map: SubMap) -> list[asyncio.Task]:
        to_add: list[asyncio.Task] = []
        sub_to_add = set(ideal_map[url]) - set(real_map[url])
        if sub_to_add:
            _logger.info("Adding %d subscriptions", len(sub_to_add))
        client = self.ha_client.get_client_by_url(url)
        for sub_name in sub_to_add:
            vs = ideal_map[url][sub_name]
            task = asyncio.create_task(client.create_subscription(vs.period, vs.handler, publishing=vs.publishing))
            task.add_done_callback(
                partial(
                    self.add_to_map,
                    url,
                    Method.ADD_SUB,
                    period=vs.period,
                    handler=vs.handler,
                    publishing=vs.publishing,
                    monitoring=vs.monitoring,
                    sub_name=sub_name,
                )
            )
            to_add.append(task)
        return to_add

    async def update_nodes(self, real_map: SubMap, ideal_map: SubMap, targets: Set[str]) -> None:
        _logger.debug("In update_nodes")
        tasks = []
        for url in targets:
            client = self.ha_client.get_client_by_url(url)
            for sub_name in ideal_map[url]:
                real_sub = self.name_to_subscription[url].get(sub_name)
                # in case the previous create_subscription request failed
                if not real_sub:
                    _logger.warning(
                        "Can't create nodes for %s since underlying subscription for %s doesn't exist", url, sub_name
                    )
                    continue
                vs_real = real_map[url][sub_name]
                vs_ideal = ideal_map[url][sub_name]
                tasks.extend(self._nodes_to_del(url, sub_name, vs_real, vs_ideal))
                tasks.extend(self._nodes_to_add(url, sub_name, client, vs_real, vs_ideal))
        await asyncio.gather(*tasks, return_exceptions=True)

    def _nodes_to_add(
        self,
        url: str,
        sub_name: str,
        client: Client,
        vs_real: VirtualSubscription,
        vs_ideal: VirtualSubscription,
    ) -> list[asyncio.Task]:
        tasks: list[asyncio.Task] = []
        real_sub: Subscription = self.name_to_subscription[url].get(sub_name)
        monitoring = vs_real.monitoring
        node_to_add = set(vs_ideal.nodes) - set(vs_real.nodes)
        if node_to_add:
            _logger.info("Adding %d Nodes", len(node_to_add))
        # hack to group subscription by NodeAttributes
        attr_to_nodes = defaultdict(list)
        for node in node_to_add:
            node_attr = vs_ideal.nodes[node]
            node_obj = client.get_node(node)
            attr_to_nodes[node_attr].append(node_obj)
        for node_attr, nodes_obj in attr_to_nodes.items():
            # some servers are sensitive to the number of MI per request
            for batch_nodes_obj in batch(nodes_obj, self.BATCH_MI_SIZE):
                task = asyncio.create_task(
                    real_sub.subscribe_data_change(
                        batch_nodes_obj,
                        *astuple(node_attr),
                        monitoring=monitoring,
                    )
                )
                nodes = [n.nodeid.to_string() for n in batch_nodes_obj]
                task.add_done_callback(
                    partial(
                        self.add_to_map,
                        url,
                        Method.ADD_MI,
                        sub_name=sub_name,
                        nodes=nodes,
                        node_attr=node_attr,
                        monitoring=monitoring,
                    )
                )
                tasks.append(task)
        self.hook_mi_request(url=url, sub_name=sub_name, nodes=node_to_add, action=Method.ADD_MI)
        return tasks

    def _nodes_to_del(
        self,
        url: str,
        sub_name: str,
        vs_real: VirtualSubscription,
        vs_ideal: VirtualSubscription,
    ) -> list[asyncio.Task]:
        to_del: list[asyncio.Task] = []
        node_to_del = set(vs_real.nodes) - set(vs_ideal.nodes)
        real_sub: Subscription = self.name_to_subscription[url].get(sub_name)
        if node_to_del:
            _logger.info("Removing %d Nodes", len(node_to_del))
            for batch_nodes in batch(node_to_del, self.BATCH_MI_SIZE):
                node_handles = [self.node_to_handle[url][node] for node in batch_nodes]
                task = asyncio.create_task(real_sub.unsubscribe(node_handles))
                task.add_done_callback(
                    partial(
                        self.del_from_map,
                        url,
                        Method.DEL_MI,
                        sub_name=sub_name,
                        nodes=batch_nodes,
                    )
                )
                to_del.append(task)
                self.hook_mi_request(url=url, sub_name=sub_name, nodes=node_to_del, action=Method.DEL_MI)
        return to_del

    async def update_subscription_modes(self, real_map: SubMap, ideal_map: SubMap, targets: Set[str]) -> None:
        _logger.debug("In update_subscription_modes")
        modes = [Method.MONITORING, Method.PUBLISHING]
        methods = [n.value for n in modes]
        tasks = []
        for url in targets:
            for sub_name in real_map[url]:
                real_sub = self.name_to_subscription[url].get(sub_name)
                # in case the previous create_subscription request failed
                if not real_sub:
                    _logger.warning(
                        "Can't change modes for %s since underlying subscription for %s doesn't exist", url, sub_name
                    )
                    continue
                vs_real = real_map[url][sub_name]
                vs_ideal = ideal_map[url][sub_name]
                for action, func in zip(modes, methods):
                    attr = action.name.lower()
                    ideal_val = getattr(vs_ideal, attr)
                    real_val = getattr(vs_real, attr)
                    if ideal_val != real_val:
                        _logger.info("Changing %s for %s to %s", attr, sub_name, ideal_val)
                        set_func = getattr(real_sub, func)
                        task = asyncio.create_task(set_func(ideal_val))
                        task.add_done_callback(
                            partial(
                                self.change_mode,
                                url,
                                action,
                                ideal_val,
                                sub_name=sub_name,
                            )
                        )
                        tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

    def change_mode(
        self,
        url: str,
        action: Method,
        val: Union[bool, ua.MonitoringMode],
        fut: asyncio.Task,
        **kwargs,
    ) -> None:
        if fut.exception():
            _logger.warning("Can't %s on %s: %s", action.value, url, fut.exception())
            return
        sub_name = kwargs["sub_name"]
        vs = self.real_map[url][sub_name]
        setattr(vs, action.name.lower(), val)

    def add_to_map(self, url: str, action: Method, fut: asyncio.Task, **kwargs) -> None:
        if fut.exception():
            _logger.warning("Can't %s on %s: %s", action.value, url, fut.exception())
            self.hook_add_to_map_error(url=url, action=action, fut=fut, **kwargs)
            return

        sub_name = kwargs.pop("sub_name")
        if action == Method.ADD_SUB:
            vs = VirtualSubscription(**kwargs)
            self.real_map[url][sub_name] = vs
            self.name_to_subscription[url][sub_name] = fut.result()

        if action == Method.ADD_MI:
            nodes = kwargs["nodes"]
            vs = self.real_map[url][sub_name]
            vs.subscribe_data_change(nodes, *astuple(kwargs["node_attr"]))
            for node, handle in zip(nodes, fut.result()):
                if isinstance(handle, ua.StatusCode):
                    # a StatusCode is returned, the request has failed.
                    vs.unsubscribe([node])
                    _logger.info("Node %s subscription failed: %s", node, handle)
                    # The node is invalid, remove it from both maps
                    if handle.name == "BadNodeIdUnknown":
                        _logger.warning("WARNING: Abandoning %s because it returned %s from %s", node, handle, url)
                        real_vs = self.ha_client.ideal_map[url][sub_name]
                        real_vs.unsubscribe([node])
                    continue
                self.node_to_handle[url][node] = handle
        self.hook_add_to_map(fut=fut, url=url, action=action, **kwargs)

    def del_from_map(self, url: str, action: Method, fut: asyncio.Task, **kwargs) -> None:
        if fut.exception():
            # log exception but continues to delete local resources
            _logger.warning("Can't %s on %s: %s", action.value, url, fut.exception())
        sub_name = kwargs["sub_name"]

        if action == Method.DEL_SUB:
            self.real_map[url].pop(sub_name)
            self.name_to_subscription[url].pop(sub_name)
            _logger.warning("In del_from_map del sub: %s", fut.result())

        if action == Method.DEL_MI:
            nodes = kwargs["nodes"]
            vs = self.real_map[url][sub_name]
            vs.unsubscribe(nodes)
            for node in nodes:
                self.node_to_handle[url].pop(node)
        self.hook_del_from_map(fut=fut, url=url, action=action, **kwargs)

    async def debug_status(self) -> None:
        """
        Return the class attribute for troubleshooting purposes
        """
        for a in inspect.getmembers(self):
            if not a[0].startswith("__") and not inspect.ismethod(a[1]):
                _logger.debug(a)

    def hook_mi_request(self, url: str, sub_name: str, nodes: Set[SortedDict], action: Method):
        """placeholder for easily superclass the HaClient and implement custom logic"""

    def hook_add_to_map_error(self, url: str, action: Method, fut: asyncio.Task, **kwargs):
        """placeholder for easily superclass the HaClient and implement custom logic"""

    def hook_add_to_map(self, fut: asyncio.Task, url: str, action: Method, **kwargs):
        """placeholder for easily superclass the HaClient and implement custom logic"""

    def hook_del_from_map(self, fut: asyncio.Task, url: str, **kwargs):
        """placeholder for easily superclass the HaClient and implement custom logic"""
