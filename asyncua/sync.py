"""
sync API of asyncua
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import functools
import sys
from cryptography import x509
from pathlib import Path
from threading import Thread, Condition
import logging
from typing import Any, Dict, List, Set, Tuple, Type, Union, overload
from collections.abc import Callable, Iterable, Sequence

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing import Literal

from asyncua import ua
from asyncua import client
from asyncua import server
from asyncua import common
from asyncua.common import node, subscription, shortcuts, xmlexporter, type_dictionary_builder
from asyncua.common.events import Event

_logger = logging.getLogger(__name__)


class ThreadLoopNotRunning(Exception):
    pass


class ThreadLoop(Thread):
    def __init__(self, timeout: float | None = 120) -> None:
        Thread.__init__(self)
        self.loop = None
        self._cond = Condition()
        self.timeout = timeout

    def start(self):
        with self._cond:
            Thread.start(self)
            self._cond.wait()

    def run(self):
        self.loop = asyncio.new_event_loop()
        _logger.debug("Threadloop: %s", self.loop)
        self.loop.call_soon_threadsafe(self._notify_start)
        self.loop.run_forever()

    def _notify_start(self):
        with self._cond:
            self._cond.notify_all()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.join()
        self.loop.close()

    def post(self, coro):
        if not self.loop or not self.loop.is_running() or not self.is_alive():
            raise ThreadLoopNotRunning(
                f"could not post {coro} since asyncio loop in thread has not been started or has been stopped"
            )
        futur = asyncio.run_coroutine_threadsafe(coro, loop=self.loop)
        return futur.result(self.timeout)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_t, exc_v, trace):
        self.stop()


def _to_async(args, kwargs):
    args = list(args)  # FIXME: might be very inefficient...
    for idx, arg in enumerate(args):
        if isinstance(arg, (SyncNode, Client, Server)):
            args[idx] = arg.aio_obj
        elif isinstance(arg, (list, tuple)):
            args[idx] = _to_async(arg, {})[0]
    for k, v in kwargs.items():
        if isinstance(v, SyncNode):
            kwargs[k] = v.aio_obj
    return args, kwargs


def _to_sync(tloop, result):
    if isinstance(result, node.Node):
        return SyncNode(tloop, result)
    if isinstance(result, (list, tuple)):
        return [_to_sync(tloop, item) for item in result]
    if isinstance(result, server.event_generator.EventGenerator):
        return EventGenerator(tloop, result)
    if isinstance(result, subscription.Subscription):
        return Subscription(tloop, result)
    if isinstance(result, server.Server):
        return Server(tloop, result)
    return result


def syncmethod(func):
    """
    decorator for sync methods
    """

    def wrapper(self, *args, **kwargs):
        args, kwargs = _to_async(args, kwargs)
        aio_func = getattr(self.aio_obj, func.__name__)
        result = self.tloop.post(aio_func(*args, **kwargs))
        return _to_sync(self.tloop, result)

    return wrapper


def sync_wrapper(aio_func):
    def wrapper(*args, **kwargs):
        if not args:
            raise RuntimeError("first argument of function must a ThreadLoop object")
        if isinstance(args[0], ThreadLoop):
            tloop = args[0]
            args = list(args)[1:]
        elif hasattr(args[0], "tloop"):
            tloop = args[0].tloop
        else:
            raise RuntimeError("first argument of function must a ThreadLoop object")
        args, kwargs = _to_async(args, kwargs)
        result = tloop.post(aio_func(*args, **kwargs))
        return _to_sync(tloop, result)

    return wrapper


def syncfunc(aio_func):
    """
    decorator for sync function
    """

    def decorator(func, *args, **kwargs):
        return sync_wrapper(aio_func)

    return decorator


def sync_uaclient_method(aio_func):
    """
    Usage:

    ```python
    from asyncua.client.ua_client import UaClient
    from asyncua.sync import Client

    with Client('otp.tcp://localhost') as client:
        read_attributes = sync_uaclient_method(UaClient.read_attributes)(client)
        results = read_attributes(...)
        ...
    ```
    """

    def sync_method(client: Client):
        uaclient = client.aio_obj.uaclient
        return functools.partial(sync_wrapper(aio_func), client.tloop, uaclient)

    return sync_method


def sync_async_client_method(aio_func):
    """
    Usage:

    ```python
    from asyncua.client import Client as AsyncClient
    from asyncua.sync import Client

    with Client('otp.tcp://localhost') as client:
        read_attributes = sync_async_client_method(AsyncClient.read_attributes)(client)
        results = read_attributes(...)
        ...
    ```
    """

    def sync_method(client: Client):
        return functools.partial(sync_wrapper(aio_func), client.tloop, client)

    return sync_method


@syncfunc(aio_func=common.methods.call_method_full)
def call_method_full(parent, methodid, *args):
    pass


@syncfunc(aio_func=common.ua_utils.data_type_to_variant_type)
def data_type_to_variant_type(dtype_node):
    pass


@syncfunc(aio_func=common.copy_node_util.copy_node)
def copy_node(parent, node, nodeid=None, recursive=True):
    pass


@syncfunc(aio_func=common.instantiate_util.instantiate)
def instantiate(parent, node_type, nodeid=None, bname=None, dname=None, idx=0, instantiate_optional=True):
    pass


class _SubHandler:
    def __init__(self, tloop, sync_handler):
        self.tloop = tloop
        self.sync_handler = sync_handler

    def datachange_notification(self, node, val, data):
        self.sync_handler.datachange_notification(SyncNode(self.tloop, node), val, data)

    def event_notification(self, event):
        self.sync_handler.event_notification(event)

    def status_change_notification(self, status: ua.StatusChangeNotification):
        self.sync_handler.status_change_notification(status)


class Client:
    """
    Sync Client, see doc for async Client
    the sync client has one extra parameter: sync_wrapper_timeout.
    if no ThreadLoop is provided this timeout is used to define how long the sync wrapper
    waits for an async call to return. defualt is 120s and hopefully should fit most applications
    """

    def __init__(
        self,
        url: str,
        timeout: float = 4,
        tloop=None,
        sync_wrapper_timeout: float | None = 120,
        watchdog_intervall: float = 1.0,
    ) -> None:
        self.tloop = tloop
        self.close_tloop = False
        if not self.tloop:
            self.tloop = ThreadLoop(sync_wrapper_timeout)
            self.tloop.start()
            self.close_tloop = True
        self.aio_obj = client.Client(url, timeout, watchdog_intervall)
        self.nodes = Shortcuts(self.tloop, self.aio_obj.uaclient)

    def __str__(self):
        return "Sync" + self.aio_obj.__str__()

    __repr__ = __str__

    @property
    def application_uri(self):
        return self.aio_obj.application_uri

    @application_uri.setter
    def application_uri(self, value):
        self.aio_obj.application_uri = value

    @syncmethod
    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        try:
            self.tloop.post(self.aio_obj.disconnect())
        finally:
            if self.close_tloop:
                self.tloop.stop()

    @syncmethod
    def connect_sessionless(self) -> None:
        pass

    def disconnect_sessionless(self) -> None:
        try:
            self.tloop.post(self.aio_obj.disconnect_sessionless())
        finally:
            if self.close_tloop:
                self.tloop.stop()

    @syncmethod
    def connect_socket(self) -> None:
        pass

    def disconnect_socket(self) -> None:
        try:
            self.aio_obj.disconnect_socket()
        finally:
            if self.close_tloop:
                self.tloop.stop()

    def set_user(self, username: str) -> None:
        self.aio_obj.set_user(username)

    def set_password(self, pwd: str) -> None:
        self.aio_obj.set_password(pwd)

    def set_locale(self, locale: Sequence[str]) -> None:
        self.aio_obj.set_locale(locale)

    @syncmethod
    def load_private_key(
        self, path: str, password: Union[str, bytes] | None = None, extension: str | None = None
    ) -> None:
        pass

    @syncmethod
    def load_client_certificate(self, path: str, extension: str | None = None) -> None:
        pass

    @syncmethod
    def load_type_definitions(self, nodes=None):
        pass

    @syncmethod
    def load_data_type_definitions(  # type: ignore[empty-body]
        self, node: SyncNode | None = None, overwrite_existing: bool = False
    ) -> Dict[str, Type]:
        pass

    @syncmethod
    def get_namespace_array(self) -> List[str]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def set_security(self) -> None:
        pass

    @syncmethod
    def set_security_string(self, string: str) -> None:
        pass

    @syncmethod
    def load_enums(self) -> Dict[str, Type]:  # type: ignore[empty-body]
        pass

    def create_subscription(
        self,
        period: Union[ua.CreateSubscriptionParameters, float],
        handler: subscription.SubscriptionHandler,
        publishing: bool = True,
    ) -> Subscription:
        coro = self.aio_obj.create_subscription(period, _SubHandler(self.tloop, handler), publishing)
        aio_sub = self.tloop.post(coro)
        return Subscription(self.tloop, aio_sub)

    def get_subscription_revised_params(
        self, params: ua.CreateSubscriptionParameters, results: ua.CreateSubscriptionResult
    ) -> ua.ModifySubscriptionParameters | None:  # type: ignore
        return self.aio_obj.get_subscription_revised_params(params, results)

    @syncmethod
    def delete_subscriptions(self, subscription_ids: Iterable[int]) -> List[ua.StatusCode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_namespace_index(self, uri: str) -> int:  # type: ignore[empty-body]
        pass

    def get_node(self, nodeid: Union[SyncNode, ua.NodeId, str, int]) -> SyncNode:
        aio_nodeid = nodeid.aio_obj if isinstance(nodeid, SyncNode) else nodeid
        return SyncNode(self.tloop, self.aio_obj.get_node(aio_nodeid))

    def get_root_node(self) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_root_node())

    def get_objects_node(self) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_objects_node())

    def get_server_node(self) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_server_node())

    @syncmethod
    def connect_and_get_server_endpoints(self) -> List[ua.EndpointDescription]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def connect_and_find_servers(self) -> List[ua.ApplicationDescription]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def connect_and_find_servers_on_network(self) -> List[ua.FindServersOnNetworkResult]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def send_hello(self) -> None:
        pass

    @syncmethod
    def open_secure_channel(self, renew=False) -> None:
        pass

    @syncmethod
    def close_secure_channel(self) -> None:
        pass

    @syncmethod
    def get_endpoints(self) -> List[ua.EndpointDescription]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def register_server(
        self,
        server: Server,
        discovery_configuration: ua.DiscoveryConfiguration | None = None,
    ) -> None:
        pass

    @syncmethod
    def unregister_server(
        self,
        server: Server,
        discovery_configuration: ua.DiscoveryConfiguration | None = None,
    ) -> None:
        pass

    @syncmethod
    def find_servers(self, uris: Iterable[str] | None = None) -> List[ua.ApplicationDescription]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def find_servers_on_network(self) -> List[ua.FindServersOnNetworkResult]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def create_session(self) -> ua.CreateSessionResult:  # type: ignore[empty-body]
        pass

    @syncmethod
    def check_connection(self) -> None:
        pass

    def server_policy(self, token_type: ua.UserTokenType) -> ua.UserTokenPolicy:
        return self.aio_obj.server_policy(token_type)

    @syncmethod
    def activate_session(  # type: ignore[empty-body]
        self,
        username: str | None = None,
        password: str | None = None,
        certificate: x509.Certificate | None = None,
    ) -> ua.ActivateSessionResult:
        pass

    @syncmethod
    def close_session(self) -> None:
        pass

    def get_keepalive_count(self, period: float) -> int:
        return self.aio_obj.get_keepalive_count(period)

    @syncmethod
    def delete_nodes(self, nodes: Iterable[SyncNode], recursive=False) -> Tuple[List[SyncNode], List[ua.StatusCode]]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def import_xml(self, path=None, xmlstring=None, strict_mode=True) -> List[ua.NodeId]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def export_xml(self, nodes, path, export_values: bool = False) -> None:
        pass

    @syncmethod
    def register_namespace(self, uri: str) -> int:  # type: ignore[empty-body]
        pass

    @syncmethod
    def register_nodes(self, nodes: Iterable[SyncNode]) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def unregister_nodes(self, nodes: Iterable[SyncNode]):  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_attributes(  # type: ignore[empty-body]
        self, nodes: Iterable[SyncNode], attr: ua.AttributeIds = ua.AttributeIds.Value
    ) -> List[ua.DataValue]:
        pass

    @syncmethod
    def read_values(self, nodes: Iterable[SyncNode]) -> List[Any]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def write_values(  # type: ignore[empty-body]
        self, nodes: Iterable[SyncNode], values: Iterable[Any], raise_on_partial_error: bool = True
    ) -> List[ua.StatusCode]:
        pass

    @syncmethod
    def browse_nodes(self, nodes: Iterable[SyncNode]) -> List[Tuple[SyncNode, ua.BrowseResult]]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def translate_browsepaths(  # type: ignore[empty-body]
        self, starting_node: ua.NodeId, relative_paths: Iterable[Union[ua.RelativePath, str]]
    ) -> List[ua.BrowsePathResult]:
        pass

    def __enter__(self):
        try:
            self.connect()
        except Exception as ex:
            self.disconnect()
            raise ex
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


class Shortcuts:
    root: SyncNode
    objects: SyncNode
    server: SyncNode
    base_object_type: SyncNode
    base_data_type: SyncNode
    base_event_type: SyncNode
    base_variable_type: SyncNode
    folder_type: SyncNode
    enum_data_type: SyncNode
    option_set_type: SyncNode
    types: SyncNode
    data_types: SyncNode
    event_types: SyncNode
    reference_types: SyncNode
    variable_types: SyncNode
    object_types: SyncNode
    namespace_array: SyncNode
    namespaces: SyncNode
    opc_binary: SyncNode
    base_structure_type: SyncNode
    base_union_type: SyncNode
    server_state: SyncNode
    service_level: SyncNode
    HasComponent: SyncNode
    HasProperty: SyncNode
    Organizes: SyncNode
    HasEncoding: SyncNode

    def __init__(self, tloop, aio_server):
        self.tloop = tloop
        self.aio_obj = shortcuts.Shortcuts(aio_server)
        for k, v in self.aio_obj.__dict__.items():
            setattr(self, k, SyncNode(self.tloop, v))


class Server:
    """
    Sync Server, see doc for async Server
    the sync server has one extra parameter: sync_wrapper_timeout.
    if no ThreadLoop is provided this timeout is used to define how long the sync wrapper
    waits for an async call to return. defualt is 120s and hopefully should fit most applications
    """

    def __init__(
        self,
        shelf_file: Path | None = None,
        tloop=None,
        sync_wrapper_timeout: float | None = 120,
    ):
        self.tloop = tloop
        self.close_tloop = False
        if not self.tloop:
            self.tloop = ThreadLoop(timeout=sync_wrapper_timeout)
            self.tloop.start()
            self.close_tloop = True
        self.aio_obj = server.Server()
        self.tloop.post(self.aio_obj.init(shelf_file))
        self.nodes = Shortcuts(self.tloop, self.aio_obj.iserver.isession)

    def __str__(self):
        return "Sync" + self.aio_obj.__str__()

    __repr__ = __str__

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    @syncmethod
    def load_certificate(self, path: str, format: str = None):
        pass

    @syncmethod
    def load_private_key(self, path, password=None, format=None):
        pass

    def set_endpoint(self, url):
        return self.aio_obj.set_endpoint(url)

    def set_server_name(self, name):
        return self.aio_obj.set_server_name(name)

    def set_security_policy(self, security_policy, permission_ruleset=None):
        return self.aio_obj.set_security_policy(security_policy, permission_ruleset)

    def set_security_IDs(self, policy_ids):
        return self.aio_obj.set_security_IDs(policy_ids)

    def set_identity_tokens(self, tokens):
        return self.aio_obj.set_identity_tokens(tokens)

    def disable_clock(self, val: bool = True):
        return self.aio_obj.disable_clock(val)

    @syncmethod
    def register_namespace(self, url):
        pass

    @syncmethod
    def get_namespace_array(self):
        pass

    @syncmethod
    def start(self):
        pass

    def stop(self):
        self.tloop.post(self.aio_obj.stop())
        if self.close_tloop:
            self.tloop.stop()

    def link_method(self, node, callback):
        return self.aio_obj.link_method(node, callback)

    @syncmethod
    def get_event_generator(self, etype=None, emitting_node=ua.ObjectIds.Server):
        pass

    def get_node(self, nodeid):
        return SyncNode(self.tloop, self.aio_obj.get_node(nodeid))

    @syncmethod
    def import_xml(self, path=None, xmlstring=None, strict_mode=True):
        pass

    @syncmethod
    def get_namespace_index(self, url):
        pass

    @syncmethod
    def load_enums(self):
        pass

    @syncmethod
    def load_type_definitions(self):
        pass

    @syncmethod
    def load_data_type_definitions(self, node=None):
        pass

    @syncmethod
    def write_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        pass

    def set_attribute_value_callback(
        self,
        nodeid: ua.NodeId,
        callback: Callable[[ua.NodeId, ua.AttributeIds], ua.DataValue],
        attr=ua.AttributeIds.Value,
    ) -> None:
        self.aio_obj.set_attribute_value_callback(nodeid, callback, attr)

    def create_subscription(self, period, handler):
        coro = self.aio_obj.create_subscription(period, _SubHandler(self.tloop, handler))
        aio_sub = self.tloop.post(coro)
        return Subscription(self.tloop, aio_sub)


class EventGenerator:
    def __init__(self, tloop, aio_evgen):
        self.aio_obj = aio_evgen
        self.tloop = tloop

    @property
    def event(self):
        return self.aio_obj.event

    def trigger(self, time=None, message=None):
        return self.tloop.post(self.aio_obj.trigger(time, message))


def new_node(sync_node, nodeid):
    """
    given a sync node, create a new SyncNode with the given nodeid
    """
    return SyncNode(sync_node.tloop, node.Node(sync_node.aio_obj.session, nodeid))


class SyncNode:
    def __init__(self, tloop: ThreadLoop, aio_node: node.Node):
        self.aio_obj = aio_node
        self.tloop = tloop

    def __eq__(self, other):
        return other is not None and self.aio_obj == other.aio_obj

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.aio_obj.__str__()

    def __repr__(self):
        return "Sync" + self.aio_obj.__repr__()

    def __hash__(self):
        return self.aio_obj.__hash__()

    def __get_nodeid(self):
        return self.aio_obj.nodeid

    def __set_nodeid(self, value):
        self.aio_obj.nodeid = value

    nodeid: ua.NodeId = property(__get_nodeid, __set_nodeid)

    @syncmethod
    def read_type_definition(self) -> ua.NodeId | None:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_parent(self) -> SyncNode | None:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_node_class(self) -> ua.NodeClass:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_attribute(  # type: ignore[empty-body]
        self,
        attr: ua.AttributeIds,
        indexrange: str | None = None,
        raise_on_bad_status: bool = True,
    ) -> ua.DataValue:
        pass

    @syncmethod
    def write_attribute(
        self,
        attributeid: ua.AttributeIds,
        datavalue: ua.DataValue,
        indexrange: str | None = None,
    ) -> None:
        pass

    @syncmethod
    def read_browse_name(self) -> ua.QualifiedName:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_display_name(self) -> ua.LocalizedText:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_data_type(self) -> ua.NodeId:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_array_dimensions(self) -> List[int]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_value_rank(self) -> int:  # type: ignore[empty-body]
        pass

    @syncmethod
    def delete(self, delete_references: bool = True, recursive: bool = False) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_children(  # type: ignore[empty-body]
        self,
        refs: int = ua.ObjectIds.HierarchicalReferences,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
    ) -> List[SyncNode]:
        pass

    @syncmethod
    def get_properties(self) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_children_descriptions(  # type: ignore[empty-body]
        self,
        refs: int = ua.ObjectIds.HierarchicalReferences,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
        includesubtypes: bool = True,
        result_mask: ua.BrowseResultMask = ua.BrowseResultMask.All,
    ) -> List[ua.ReferenceDescription]:
        pass

    @syncmethod
    def get_user_access_level(self) -> Set[ua.AccessLevel]:  # type: ignore[empty-body]
        pass

    @overload
    def get_child(
        self,
        path: Union[ua.QualifiedName, str, Iterable[Union[ua.QualifiedName, str]]],
        return_all: Literal[False] = False,
    ) -> SyncNode: ...

    @overload
    def get_child(
        self,
        path: Union[ua.QualifiedName, str, Iterable[Union[ua.QualifiedName, str]]],
        return_all: Literal[True] = True,
    ) -> List[SyncNode]: ...

    @syncmethod
    def get_child(  # type: ignore[empty-body]
        self,
        path: Union[ua.QualifiedName, str, Iterable[Union[ua.QualifiedName, str]]],
        return_all: bool = False,
    ) -> Union[SyncNode, List[SyncNode]]:
        pass

    @syncmethod
    def get_children_by_path(  # type: ignore[empty-body]
        self,
        paths: Iterable[Union[ua.QualifiedName, str, Iterable[Union[ua.QualifiedName, str]]]],
        raise_on_partial_error: bool = True,
    ) -> List[List[SyncNode | None]]:
        pass

    @syncmethod
    def read_raw_history(  # type: ignore[empty-body]
        self,
        starttime: datetime | None = None,
        endtime: datetime | None = None,
        numvalues: int = 0,
        return_bounds: bool = True,
    ) -> List[ua.DataValue]:
        pass

    @syncmethod
    def history_read(  # type: ignore[empty-body]
        self,
        details: ua.ReadRawModifiedDetails,
        continuation_point: bytes | None = None,
    ) -> ua.HistoryReadResult:
        pass

    @syncmethod
    def read_event_history(  # type: ignore[empty-body]
        self,
        starttime: datetime = None,
        endtime: datetime = None,
        numvalues: int = 0,
        evtypes: Union[
            SyncNode, ua.NodeId, str, int, Iterable[Union[SyncNode, ua.NodeId, str, int]]
        ] = ua.ObjectIds.BaseEventType,
    ) -> List[Event]:
        pass

    @syncmethod
    def history_read_events(self, details: Iterable[ua.ReadEventDetails]) -> ua.HistoryReadResult:  # type: ignore[empty-body]
        pass

    @syncmethod
    def set_modelling_rule(self, mandatory: bool) -> None:
        pass

    @syncmethod
    def add_variable(  # type: ignore[empty-body]
        self,
        nodeid: Union[ua.NodeId, str],
        bname: Union[ua.QualifiedName, str],
        val: Any,
        varianttype: ua.VariantType | None = None,
        datatype: Union[ua.NodeId, int] | None = None,
    ) -> SyncNode:
        pass

    @syncmethod
    def add_property(  # type: ignore[empty-body]
        self,
        nodeid: Union[ua.NodeId, str],
        bname: Union[ua.QualifiedName, str],
        val: Any,
        varianttype: ua.VariantType | None = None,
        datatype: Union[ua.NodeId, int] | None = None,
    ) -> SyncNode:
        pass

    @syncmethod
    def add_object(  # type: ignore[empty-body]
        self,
        nodeid: Union[ua.NodeId, str],
        bname: Union[ua.QualifiedName, str],
        objecttype: int | None = None,
        instantiate_optional: bool = True,
    ) -> SyncNode:
        pass

    @syncmethod
    def add_object_type(self, nodeid: Union[ua.NodeId, str], bname: Union[ua.QualifiedName, str]) -> SyncNode:  # type: ignore[empty-body]
        pass

    @syncmethod
    def add_variable_type(  # type: ignore[empty-body]
        self, nodeid: Union[ua.NodeId, str], bname: Union[ua.QualifiedName, str], datatype: Union[ua.NodeId, int]
    ) -> SyncNode:
        pass

    @syncmethod
    def add_folder(self, nodeid: Union[ua.NodeId, str], bname: Union[ua.QualifiedName, str]) -> SyncNode:  # type: ignore[empty-body]
        pass

    @syncmethod
    def add_method(self, *args) -> SyncNode:  # type: ignore[empty-body]
        pass

    @syncmethod
    def add_data_type(  # type: ignore[empty-body]
        self, nodeid: Union[ua.NodeId, str], bname: Union[ua.QualifiedName, str], description: str | None = None
    ) -> SyncNode:
        pass

    @syncmethod
    def set_writable(self, writable: bool = True) -> None:
        pass

    @syncmethod
    def write_value(self, value: Any, varianttype: ua.VariantType | None = None) -> None:
        pass

    set_value = write_value  # legacy

    @syncmethod
    def write_params(self, params: ua.WriteParameters) -> List[ua.StatusCode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_params(self, params: ua.ReadParameters) -> List[ua.DataValue]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_value(self) -> Any:
        pass

    get_value = read_value  # legacy

    @syncmethod
    def read_data_value(self, raise_on_bad_status: bool = True) -> ua.DataValue:  # type: ignore[empty-body]
        pass

    get_data_value = read_data_value  # legacy

    @syncmethod
    def read_data_type_as_variant_type(self) -> ua.VariantType:  # type: ignore[empty-body]
        pass

    get_data_type_as_variant_type = read_data_type_as_variant_type  # legacy

    @syncmethod
    def call_method(self, methodid: Union[ua.NodeId, ua.QualifiedName, str], *args) -> Any:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_references(  # type: ignore[empty-body]
        self,
        refs: int = ua.ObjectIds.References,
        direction: ua.BrowseDirection = ua.BrowseDirection.Both,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
        includesubtypes: bool = True,
        result_mask: ua.BrowseResultMask = ua.BrowseResultMask.All,
    ) -> List[ua.ReferenceDescription]:
        pass

    @syncmethod
    def add_reference(
        self,
        target: Union[SyncNode, ua.NodeId, str, int],
        reftype: int,
        forward: bool = True,
        bidirectional: bool = True,
    ) -> None:
        pass

    @syncmethod
    def read_description(self) -> ua.LocalizedText:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_variables(self) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @overload
    def get_path(self, max_length: int = 20, as_string: Literal[False] = False) -> List[SyncNode]: ...

    @overload
    def get_path(self, max_length: int = 20, as_string: Literal[True] = True) -> List[str]: ...

    @syncmethod
    def get_path(self, max_length: int = 20, as_string: bool = False) -> Union[List[SyncNode], List[str]]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_attributes(self, attrs: Iterable[ua.AttributeIds]) -> List[ua.DataValue]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def add_reference_type(  # type: ignore[empty-body]
        self,
        nodeid: Union[ua.NodeId, str],
        bname: Union[ua.QualifiedName, str],
        symmetric: bool = True,
        inversename: str | None = None,
    ) -> SyncNode:
        pass

    @syncmethod
    def delete_reference(  # type: ignore[empty-body]
        self,
        target: Union[SyncNode, ua.NodeId, str, int],
        reftype: int,
        forward: bool = True,
        bidirectional: bool = True,
    ) -> None:
        pass

    @syncmethod
    def get_access_level(self) -> Set[ua.AccessLevel]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_description_refs(self) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_encoding_refs(self) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_methods(self) -> List[SyncNode]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def get_referenced_nodes(  # type: ignore[empty-body]
        self,
        refs: int = ua.ObjectIds.References,
        direction: ua.BrowseDirection = ua.BrowseDirection.Both,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
        includesubtypes: bool = True,
    ) -> List[SyncNode]:
        pass

    @syncmethod
    def read_data_type_definition(self) -> ua.DataTypeDefinition:  # type: ignore[empty-body]
        pass

    @syncmethod
    def read_event_notifier(self) -> Set[ua.EventNotifier]:  # type: ignore[empty-body]
        pass

    @syncmethod
    def register(self) -> None:
        pass

    @syncmethod
    def set_attr_bit(self, attr: ua.AttributeIds, bit: int) -> None:
        pass

    @syncmethod
    def set_event_notifier(self, values) -> None:
        pass

    @syncmethod
    def unregister(self) -> None:
        pass

    @syncmethod
    def unset_attr_bit(self, attr: ua.AttributeIds, bit: int) -> None:
        pass

    @syncmethod
    def write_array_dimensions(self, value: int) -> None:
        pass

    @syncmethod
    def write_data_type_definition(self, sdef: ua.DataTypeDefinition) -> None:
        pass

    @syncmethod
    def write_value_rank(self, value: int) -> None:
        pass


class Subscription:
    def __init__(self, tloop, sub):
        self.tloop = tloop
        self.aio_obj = sub

    @syncmethod
    def subscribe_data_change(
        self,
        nodes,
        attr=ua.AttributeIds.Value,
        queuesize=0,
        monitoring=ua.MonitoringMode.Reporting,
        sampling_interval=0.0,
    ):
        pass

    @syncmethod
    def subscribe_events(
        self,
        sourcenode=ua.ObjectIds.Server,
        evtypes=ua.ObjectIds.BaseEventType,
        evfilter=None,
        queuesize=0,
    ):
        pass

    def _make_monitored_item_request(
        self,
        node: SyncNode,
        attr,
        mfilter,
        queuesize,
        monitoring=ua.MonitoringMode.Reporting,
    ) -> ua.MonitoredItemCreateRequest:
        return self.aio_obj._make_monitored_item_request(node, attr, mfilter, queuesize, monitoring)

    @syncmethod
    def unsubscribe(self, handle):
        pass

    @syncmethod
    def create_monitored_items(self, monitored_items):
        pass

    @syncmethod
    def delete(self):
        pass


class XmlExporter:
    def __init__(self, sync_server):
        self.tloop = sync_server.tloop
        self.aio_obj = xmlexporter.XmlExporter(sync_server.aio_obj)

    @syncmethod
    def build_etree(self, node_list, uris=None):
        pass

    @syncmethod
    def write_xml(self, xmlpath: Path, pretty=True):
        pass


class DataTypeDictionaryBuilder:
    def __init__(self, server, idx, ns_urn, dict_name, dict_node_id=None):
        self.tloop = server.tloop
        self.aio_obj = type_dictionary_builder.DataTypeDictionaryBuilder(
            server.aio_obj, idx, ns_urn, dict_name, dict_node_id
        )
        self.init()

    @property
    def dict_id(self):
        return self.aio_obj.dict_id

    @syncmethod
    def init(self):
        pass

    @syncmethod
    def create_data_type(self, type_name, nodeid=None, init=True):
        pass

    @syncmethod
    def set_dict_byte_string(self):
        pass


def new_struct_field(
    name: str,
    dtype: Union[ua.NodeId, SyncNode, ua.VariantType],
    array: bool = False,
    optional: bool = False,
    description: str = "",
) -> ua.StructureField:
    if isinstance(dtype, SyncNode):
        dtype = dtype.aio_obj
    return common.structures104.new_struct_field(name, dtype, array, optional, description)


@syncfunc(aio_func=common.structures104.new_enum)
def new_enum(  # type: ignore[empty-body]
    server: Union[Server, Client],
    idx: Union[int, ua.NodeId],
    name: Union[int, ua.QualifiedName],
    values: List[str],
    optional: bool = False,
) -> SyncNode:
    pass


@syncfunc(aio_func=common.structures104.new_struct)
def new_struct(  # type: ignore[empty-body]
    server: Union[Server, Client],
    idx: Union[int, ua.NodeId],
    name: Union[int, ua.QualifiedName],
    fields: List[ua.StructureField],
) -> Tuple[SyncNode, List[SyncNode]]:
    pass
