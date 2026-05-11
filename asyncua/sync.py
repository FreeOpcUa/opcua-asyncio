# mypy: disable-error-code="empty-body"
"""
sync API of asyncua
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine, Iterable, Sequence
from datetime import datetime
from pathlib import Path
from threading import Condition, Thread
from types import TracebackType
from typing import Any, Literal, TypeVar, overload

from cryptography import x509

from asyncua import client, common, server, ua
from asyncua.common import node, shortcuts, subscription, type_dictionary_builder, xmlexporter
from asyncua.common.events import Event
from asyncua.crypto import uacrypto

_logger = logging.getLogger(__name__)

_T = TypeVar("_T")


class ThreadLoopNotRunning(Exception): ...


class ThreadLoop(Thread):
    def __init__(self, timeout: float | None = 120) -> None:
        Thread.__init__(self)
        self.loop: asyncio.AbstractEventLoop | None = None
        self._cond: Condition = Condition()
        self.timeout: float | None = timeout

    def start(self) -> None:
        with self._cond:
            Thread.start(self)
            self._cond.wait()

    def run(self) -> None:
        self.loop = asyncio.new_event_loop()
        _logger.debug("Threadloop: %s", self.loop)
        self.loop.call_soon_threadsafe(self._notify_start)
        self.loop.run_forever()

    def _notify_start(self) -> None:
        with self._cond:
            self._cond.notify_all()

    def stop(self) -> None:
        if self.loop is None:
            return
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.join()
        self.loop.close()

    def post(self, coro: Coroutine[Any, Any, _T]) -> _T:
        if not self.loop or not self.loop.is_running() or not self.is_alive():
            raise ThreadLoopNotRunning(
                f"could not post {coro} since asyncio loop in thread has not been started or has been stopped"
            )
        futur = asyncio.run_coroutine_threadsafe(coro, loop=self.loop)
        return futur.result(self.timeout)

    def __enter__(self) -> ThreadLoop:
        self.start()
        return self

    def __exit__(
        self, exc_t: type[BaseException] | None, exc_v: BaseException | None, trace: TracebackType | None
    ) -> None:
        self.stop()


def _to_async(args: tuple[Any, ...] | list[Any], kwargs: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    args = list(args)  # FIXME: might be very inefficient...
    for idx, arg in enumerate(args):
        if isinstance(arg, SyncNode | Client | Server):
            args[idx] = arg.aio_obj
        elif isinstance(arg, list | tuple):
            args[idx] = _to_async(arg, {})[0]
    for k, v in kwargs.items():
        if isinstance(v, SyncNode):
            kwargs[k] = v.aio_obj
    return args, kwargs


def _to_sync(tloop: ThreadLoop, result: Any) -> Any:
    if isinstance(result, node.Node):
        return SyncNode(tloop, result)
    if isinstance(result, list | tuple):
        return [_to_sync(tloop, item) for item in result]
    if isinstance(result, server.event_generator.EventGenerator):
        return EventGenerator(tloop, result)
    if isinstance(result, subscription.Subscription):
        return Subscription(tloop, result)
    if isinstance(result, server.Server):
        return Server(tloop, result)
    return result


def syncmethod(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    decorator for sync methods
    """

    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        args, kwargs = _to_async(args, kwargs)
        aio_func = getattr(self.aio_obj, func.__name__)
        result = self.tloop.post(aio_func(*args, **kwargs))
        return _to_sync(self.tloop, result)

    return wrapper


def sync_wrapper(aio_func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def syncfunc(aio_func: Callable[..., Any]) -> Callable[..., Callable[..., Any]]:
    """
    decorator for sync function
    """

    def decorator(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
        return sync_wrapper(aio_func)

    return decorator


def sync_uaclient_method(aio_func: Callable[..., Any]) -> Callable[[Client], functools.partial[Any]]:
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

    def sync_method(client: Client) -> functools.partial[Any]:
        uaclient = client.aio_obj.uaclient
        return functools.partial(sync_wrapper(aio_func), client.tloop, uaclient)

    return sync_method


def sync_async_client_method(aio_func: Callable[..., Any]) -> Callable[[Client], functools.partial[Any]]:
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

    def sync_method(client: Client) -> functools.partial[Any]:
        return functools.partial(sync_wrapper(aio_func), client.tloop, client)

    return sync_method


@syncfunc(aio_func=common.methods.call_method_full)
def call_method_full(
    parent: SyncNode, methodid: ua.NodeId | ua.QualifiedName | str, *args: Any
) -> ua.CallMethodResult: ...


@syncfunc(aio_func=common.ua_utils.data_type_to_variant_type)
def data_type_to_variant_type(dtype_node: SyncNode) -> ua.VariantType: ...


@syncfunc(aio_func=common.copy_node_util.copy_node)
def copy_node(
    parent: SyncNode, node: SyncNode, nodeid: ua.NodeId | None = None, recursive: bool = True
) -> list[SyncNode]: ...


@syncfunc(aio_func=common.instantiate_util.instantiate)
def instantiate(
    parent: SyncNode,
    node_type: SyncNode,
    nodeid: ua.NodeId | None = None,
    bname: ua.QualifiedName | None = None,
    dname: ua.LocalizedText | None = None,
    idx: int = 0,
    instantiate_optional: bool = True,
) -> list[SyncNode]: ...


class _SubHandler:
    def __init__(self, tloop: ThreadLoop, sync_handler: Any) -> None:
        self.tloop: ThreadLoop = tloop
        self.sync_handler: Any = sync_handler

    def datachange_notification(self, node: node.Node, val: Any, data: Any) -> None:
        self.sync_handler.datachange_notification(SyncNode(self.tloop, node), val, data)

    def event_notification(self, event: Event) -> None:
        self.sync_handler.event_notification(event)

    def status_change_notification(self, status: ua.StatusChangeNotification) -> None:
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
        tloop: ThreadLoop | None = None,
        sync_wrapper_timeout: float | None = 120,
        watchdog_intervall: float = 1.0,
    ) -> None:
        self.tloop: ThreadLoop = tloop  # type: ignore[assignment]
        self.close_tloop: bool = False
        if not self.tloop:
            self.tloop = ThreadLoop(sync_wrapper_timeout)
            self.tloop.start()
            self.close_tloop = True
        self.aio_obj: client.Client = client.Client(url, timeout, watchdog_intervall)
        self.nodes: Shortcuts = Shortcuts(self.tloop, self.aio_obj.uaclient)

    def __str__(self) -> str:
        return "Sync" + self.aio_obj.__str__()

    __repr__ = __str__

    @property
    def application_uri(self) -> str:
        return self.aio_obj.application_uri

    @application_uri.setter
    def application_uri(self, value: str) -> None:
        self.aio_obj.application_uri = value

    @syncmethod
    def connect(self) -> None: ...

    def disconnect(self) -> None:
        try:
            self.tloop.post(self.aio_obj.disconnect())
        finally:
            if self.close_tloop:
                self.tloop.stop()

    @syncmethod
    def connect_sessionless(self) -> None: ...

    def disconnect_sessionless(self) -> None:
        try:
            self.tloop.post(self.aio_obj.disconnect_sessionless())
        finally:
            if self.close_tloop:
                self.tloop.stop()

    @syncmethod
    def connect_socket(self) -> None: ...

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
        self, path: str, password: str | bytes | None = None, extension: str | None = None
    ) -> None: ...

    @syncmethod
    def load_client_certificate(self, path: str, extension: str | None = None) -> None: ...

    @syncmethod
    def load_client_chain(self, certs: Iterable[uacrypto.CertProperties]) -> None: ...

    @syncmethod
    def load_type_definitions(self, nodes: Iterable[SyncNode] | None = None) -> dict[str, type]: ...

    @syncmethod
    def load_data_type_definitions(
        self, node: SyncNode | None = None, overwrite_existing: bool = False
    ) -> dict[str, type]: ...

    @syncmethod
    def get_namespace_array(self) -> list[str]: ...

    @syncmethod
    def set_security(self) -> None: ...

    @syncmethod
    def set_security_string(self, string: str) -> None: ...

    @syncmethod
    def load_enums(self) -> dict[str, type]: ...

    def create_subscription(
        self,
        period: ua.CreateSubscriptionParameters | float,
        handler: Any = None,
        publishing: bool = True,
    ) -> Subscription:
        wrapped = _SubHandler(self.tloop, handler) if handler is not None else None
        coro = self.aio_obj.create_subscription(period, wrapped, publishing)
        aio_sub = self.tloop.post(coro)
        return Subscription(self.tloop, aio_sub)

    def get_subscription_revised_params(
        self, params: ua.CreateSubscriptionParameters, results: ua.CreateSubscriptionResult
    ) -> ua.ModifySubscriptionParameters | None:  # type: ignore
        return self.aio_obj.get_subscription_revised_params(params, results)

    @syncmethod
    def delete_subscriptions(self, subscription_ids: Iterable[int]) -> list[ua.StatusCode]: ...

    @syncmethod
    def get_namespace_index(self, uri: str) -> int: ...

    def get_node(self, nodeid: SyncNode | ua.NodeId | str | int) -> SyncNode:
        aio_nodeid = nodeid.aio_obj if isinstance(nodeid, SyncNode) else nodeid
        return SyncNode(self.tloop, self.aio_obj.get_node(aio_nodeid))

    def get_root_node(self) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_root_node())

    def get_objects_node(self) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_objects_node())

    def get_server_node(self) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_server_node())

    @syncmethod
    def connect_and_get_server_endpoints(self) -> list[ua.EndpointDescription]: ...

    @syncmethod
    def connect_and_find_servers(self) -> list[ua.ApplicationDescription]: ...

    @syncmethod
    def connect_and_find_servers_on_network(self) -> list[ua.FindServersOnNetworkResult]: ...

    @syncmethod
    def send_hello(self) -> None: ...

    @syncmethod
    def open_secure_channel(self, renew: bool = False) -> None: ...

    @syncmethod
    def close_secure_channel(self) -> None: ...

    @syncmethod
    def get_endpoints(self) -> list[ua.EndpointDescription]: ...

    @syncmethod
    def register_server(
        self,
        server: Server,
        discovery_configuration: ua.DiscoveryConfiguration | None = None,
    ) -> None: ...

    @syncmethod
    def unregister_server(
        self,
        server: Server,
        discovery_configuration: ua.DiscoveryConfiguration | None = None,
    ) -> None: ...

    @syncmethod
    def find_servers(self, uris: Iterable[str] | None = None) -> list[ua.ApplicationDescription]: ...

    @syncmethod
    def find_servers_on_network(self) -> list[ua.FindServersOnNetworkResult]: ...

    @syncmethod
    def create_session(self) -> ua.CreateSessionResult: ...

    @syncmethod
    def check_connection(self) -> None: ...

    def server_policy(self, token_type: ua.UserTokenType) -> ua.UserTokenPolicy:
        return self.aio_obj.server_policy(token_type)

    @syncmethod
    def activate_session(
        self,
        username: str | None = None,
        password: str | None = None,
        certificate: x509.Certificate | None = None,
    ) -> ua.ActivateSessionResult: ...

    @syncmethod
    def close_session(self) -> None: ...

    def get_keepalive_count(self, period: float) -> int:
        return self.aio_obj.get_keepalive_count(period)

    @syncmethod
    def delete_nodes(
        self, nodes: Iterable[SyncNode], recursive: bool = False
    ) -> tuple[list[SyncNode], list[ua.StatusCode]]: ...

    @syncmethod
    def import_xml(
        self, path: str | None = None, xmlstring: str | None = None, strict_mode: bool = True
    ) -> list[ua.NodeId]: ...

    @syncmethod
    def export_xml(self, nodes: Iterable[SyncNode], path: str, export_values: bool = False) -> None: ...

    @syncmethod
    def register_namespace(self, uri: str) -> int: ...

    @syncmethod
    def register_nodes(self, nodes: Iterable[SyncNode]) -> list[SyncNode]: ...

    @syncmethod
    def unregister_nodes(self, nodes: Iterable[SyncNode]) -> None: ...

    @syncmethod
    def read_attributes(
        self, nodes: Iterable[SyncNode], attr: ua.AttributeIds = ua.AttributeIds.Value
    ) -> list[ua.DataValue]: ...

    @syncmethod
    def read_values(self, nodes: Iterable[SyncNode]) -> list[Any]: ...

    @syncmethod
    def write_values(
        self, nodes: Iterable[SyncNode], values: Iterable[Any], raise_on_partial_error: bool = True
    ) -> list[ua.StatusCode]: ...

    @syncmethod
    def browse_nodes(self, nodes: Iterable[SyncNode]) -> list[tuple[SyncNode, ua.BrowseResult]]: ...

    @syncmethod
    def translate_browsepaths(
        self, starting_node: ua.NodeId, relative_paths: Iterable[ua.RelativePath | str]
    ) -> list[ua.BrowsePathResult]: ...

    def __enter__(self) -> Client:
        try:
            self.connect()
        except Exception as ex:
            self.disconnect()
            raise ex
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
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

    def __init__(self, tloop: ThreadLoop, aio_server: Any) -> None:
        self.tloop: ThreadLoop = tloop
        self.aio_obj: shortcuts.Shortcuts = shortcuts.Shortcuts(aio_server)
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
        tloop: ThreadLoop | None = None,
        sync_wrapper_timeout: float | None = 120,
    ) -> None:
        self.tloop: ThreadLoop = tloop  # type: ignore[assignment]
        self.close_tloop: bool = False
        if not self.tloop:
            self.tloop = ThreadLoop(timeout=sync_wrapper_timeout)
            self.tloop.start()
            self.close_tloop = True
        self.aio_obj: server.Server = server.Server()
        self.tloop.post(self.aio_obj.init(shelf_file))
        self.nodes: Shortcuts = Shortcuts(self.tloop, self.aio_obj.iserver.isession)

    def __str__(self) -> str:
        return "Sync" + self.aio_obj.__str__()

    __repr__ = __str__

    def __enter__(self) -> Server:
        self.start()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.stop()

    @syncmethod
    def load_certificate(self, path: str, format: str | None = None) -> None: ...

    @syncmethod
    def load_private_key(
        self, path: str | Path | bytes, password: str | bytes | None = None, format: str | None = None
    ) -> None: ...

    def set_endpoint(self, url: str) -> None:
        return self.aio_obj.set_endpoint(url)

    def set_server_name(self, name: str) -> None:
        return self.aio_obj.set_server_name(name)

    def set_security_policy(
        self, security_policy: list[ua.SecurityPolicyType], permission_ruleset: Any | None = None
    ) -> None:
        return self.aio_obj.set_security_policy(security_policy, permission_ruleset)

    def set_security_IDs(self, policy_ids: list[str]) -> None:
        return self.aio_obj.set_security_IDs(policy_ids)

    def set_identity_tokens(self, tokens: list[type]) -> None:
        return self.aio_obj.set_identity_tokens(tokens)

    def disable_clock(self, val: bool = True) -> None:
        return self.aio_obj.disable_clock(val)

    @syncmethod
    def register_namespace(self, url: str) -> int: ...

    @syncmethod
    def get_namespace_array(self) -> list[str]: ...

    @syncmethod
    def start(self) -> None: ...

    def stop(self) -> None:
        self.tloop.post(self.aio_obj.stop())
        if self.close_tloop:
            self.tloop.stop()

    def link_method(self, node: SyncNode, callback: Callable[..., Any]) -> None:
        return self.aio_obj.link_method(node, callback)

    @syncmethod
    def get_event_generator(
        self, etype: Any | None = None, emitting_node: ua.NodeId | int = ua.ObjectIds.Server
    ) -> EventGenerator: ...

    def get_node(self, nodeid: SyncNode | ua.NodeId | str | int) -> SyncNode:
        return SyncNode(self.tloop, self.aio_obj.get_node(nodeid))

    @syncmethod
    def import_xml(
        self, path: str | None = None, xmlstring: str | None = None, strict_mode: bool = True
    ) -> list[ua.NodeId]: ...

    @syncmethod
    def get_namespace_index(self, url: str) -> int: ...

    @syncmethod
    def load_enums(self) -> dict[str, type]: ...

    @syncmethod
    def load_type_definitions(self) -> dict[str, type]: ...

    @syncmethod
    def load_data_type_definitions(self, node: SyncNode | None = None) -> dict[str, type]: ...

    @syncmethod
    def write_attribute_value(
        self, nodeid: ua.NodeId, datavalue: ua.DataValue, attr: ua.AttributeIds = ua.AttributeIds.Value
    ) -> None: ...

    def set_attribute_value_callback(
        self,
        nodeid: ua.NodeId,
        callback: Callable[[ua.NodeId, ua.AttributeIds], ua.DataValue],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> None:
        self.aio_obj.set_attribute_value_callback(nodeid, callback, attr)

    def create_subscription(
        self,
        period: ua.CreateSubscriptionParameters | float,
        handler: Any = None,
    ) -> Subscription:
        wrapped = _SubHandler(self.tloop, handler) if handler is not None else None
        coro = self.aio_obj.create_subscription(period, wrapped)
        aio_sub = self.tloop.post(coro)
        return Subscription(self.tloop, aio_sub)


class EventGenerator:
    def __init__(self, tloop: ThreadLoop, aio_evgen: server.event_generator.EventGenerator) -> None:
        self.aio_obj: server.event_generator.EventGenerator = aio_evgen
        self.tloop: ThreadLoop = tloop

    @property
    def event(self) -> Event:
        return self.aio_obj.event

    def trigger(self, time: datetime | None = None, message: str | None = None) -> None:
        return self.tloop.post(self.aio_obj.trigger(time, message))


def new_node(sync_node: SyncNode, nodeid: ua.NodeId | str | int) -> SyncNode:
    """
    given a sync node, create a new SyncNode with the given nodeid
    """
    return SyncNode(sync_node.tloop, node.Node(sync_node.aio_obj.session, nodeid))


class SyncNode:
    def __init__(self, tloop: ThreadLoop, aio_node: node.Node) -> None:
        self.aio_obj: node.Node = aio_node
        self.tloop: ThreadLoop = tloop

    def __eq__(self, other: object) -> bool:
        return other is not None and isinstance(other, SyncNode) and self.aio_obj == other.aio_obj

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return self.aio_obj.__str__()

    def __repr__(self) -> str:
        return "Sync" + self.aio_obj.__repr__()

    def __hash__(self) -> int:
        return self.aio_obj.__hash__()

    def __get_nodeid(self) -> ua.NodeId:
        return self.aio_obj.nodeid

    def __set_nodeid(self, value: ua.NodeId) -> None:
        self.aio_obj.nodeid = value

    nodeid: ua.NodeId = property(__get_nodeid, __set_nodeid)

    @syncmethod
    def read_type_definition(self) -> ua.NodeId | None: ...

    @syncmethod
    def get_parent(self) -> SyncNode | None: ...

    @syncmethod
    def read_node_class(self) -> ua.NodeClass: ...

    @syncmethod
    def read_attribute(
        self,
        attr: ua.AttributeIds,
        indexrange: str | None = None,
        raise_on_bad_status: bool = True,
    ) -> ua.DataValue: ...

    @syncmethod
    def write_attribute(
        self,
        attributeid: ua.AttributeIds,
        datavalue: ua.DataValue,
        indexrange: str | None = None,
    ) -> None: ...

    @syncmethod
    def read_browse_name(self) -> ua.QualifiedName: ...

    @syncmethod
    def read_display_name(self) -> ua.LocalizedText: ...

    @syncmethod
    def read_data_type(self) -> ua.NodeId: ...

    @syncmethod
    def read_array_dimensions(self) -> list[int]: ...

    @syncmethod
    def read_value_rank(self) -> int: ...

    @syncmethod
    def delete(self, delete_references: bool = True, recursive: bool = False) -> list[SyncNode]: ...

    @syncmethod
    def get_children(
        self,
        refs: SyncNode | ua.NodeId | str | int = ua.ObjectIds.HierarchicalReferences,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
    ) -> list[SyncNode]: ...

    @syncmethod
    def get_properties(self) -> list[SyncNode]: ...

    @syncmethod
    def get_children_descriptions(
        self,
        refs: int = ua.ObjectIds.HierarchicalReferences,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
        includesubtypes: bool = True,
        result_mask: ua.BrowseResultMask = ua.BrowseResultMask.All,
    ) -> list[ua.ReferenceDescription]: ...

    @syncmethod
    def get_user_access_level(self) -> set[ua.AccessLevel]: ...

    @overload
    def get_child(
        self,
        path: ua.QualifiedName | str | Iterable[ua.QualifiedName | str],
        return_all: Literal[False] = False,
    ) -> SyncNode: ...

    @overload
    def get_child(
        self,
        path: ua.QualifiedName | str | Iterable[ua.QualifiedName | str],
        return_all: Literal[True] = True,
    ) -> list[SyncNode]: ...

    @syncmethod
    def get_child(
        self,
        path: ua.QualifiedName | str | Iterable[ua.QualifiedName | str],
        return_all: bool = False,
    ) -> SyncNode | list[SyncNode]: ...

    @syncmethod
    def get_children_by_path(
        self,
        paths: Iterable[ua.QualifiedName | str | Iterable[ua.QualifiedName | str]],
        raise_on_partial_error: bool = True,
    ) -> list[list[SyncNode | None]]: ...

    @syncmethod
    def read_raw_history(
        self,
        starttime: datetime | None = None,
        endtime: datetime | None = None,
        numvalues: int = 0,
        return_bounds: bool = True,
    ) -> list[ua.DataValue]: ...

    @syncmethod
    def history_read(
        self,
        details: ua.ReadRawModifiedDetails,
        continuation_point: bytes | None = None,
    ) -> ua.HistoryReadResult: ...

    @syncmethod
    def read_event_history(
        self,
        starttime: datetime | None = None,
        endtime: datetime | None = None,
        numvalues: int = 0,
        evtypes: SyncNode
        | ua.NodeId
        | str
        | int
        | Iterable[SyncNode | ua.NodeId | str | int] = ua.ObjectIds.BaseEventType,
    ) -> list[Event]: ...

    @syncmethod
    def history_read_events(self, details: Iterable[ua.ReadEventDetails]) -> ua.HistoryReadResult: ...

    @syncmethod
    def set_modelling_rule(self, mandatory: bool) -> None: ...

    @syncmethod
    def add_variable(
        self,
        nodeid: ua.NodeId | str,
        bname: ua.QualifiedName | str,
        val: Any,
        varianttype: ua.VariantType | None = None,
        datatype: ua.NodeId | int | None = None,
    ) -> SyncNode: ...

    @syncmethod
    def add_property(
        self,
        nodeid: ua.NodeId | str,
        bname: ua.QualifiedName | str,
        val: Any,
        varianttype: ua.VariantType | None = None,
        datatype: ua.NodeId | int | None = None,
    ) -> SyncNode: ...

    @syncmethod
    def add_object(
        self,
        nodeid: ua.NodeId | str,
        bname: ua.QualifiedName | str,
        objecttype: int | None = None,
        instantiate_optional: bool = True,
    ) -> SyncNode: ...

    @syncmethod
    def add_object_type(self, nodeid: ua.NodeId | str, bname: ua.QualifiedName | str) -> SyncNode: ...

    @syncmethod
    def add_variable_type(
        self, nodeid: ua.NodeId | str, bname: ua.QualifiedName | str, datatype: ua.NodeId | int
    ) -> SyncNode: ...

    @syncmethod
    def add_folder(self, nodeid: ua.NodeId | str, bname: ua.QualifiedName | str) -> SyncNode: ...

    @syncmethod
    def add_method(self, *args: Any) -> SyncNode: ...

    @syncmethod
    def add_data_type(
        self, nodeid: ua.NodeId | str, bname: ua.QualifiedName | str, description: str | None = None
    ) -> SyncNode: ...

    @syncmethod
    def set_writable(self, writable: bool = True) -> None: ...

    @syncmethod
    def write_value(self, value: Any, varianttype: ua.VariantType | None = None) -> None: ...

    set_value = write_value  # legacy

    @syncmethod
    def write_params(self, params: ua.WriteParameters) -> list[ua.StatusCode]: ...

    @syncmethod
    def read_params(self, params: ua.ReadParameters) -> list[ua.DataValue]: ...

    @syncmethod
    def read_value(self) -> Any: ...

    get_value = read_value  # legacy

    @syncmethod
    def read_data_value(self, raise_on_bad_status: bool = True) -> ua.DataValue: ...

    get_data_value = read_data_value  # legacy

    @syncmethod
    def read_data_type_as_variant_type(self) -> ua.VariantType: ...

    get_data_type_as_variant_type = read_data_type_as_variant_type  # legacy

    @syncmethod
    def call_method(self, methodid: ua.NodeId | ua.QualifiedName | str, *args: Any) -> Any: ...

    @syncmethod
    def get_references(
        self,
        refs: SyncNode | ua.NodeId | str | int = ua.ObjectIds.References,
        direction: ua.BrowseDirection = ua.BrowseDirection.Both,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
        includesubtypes: bool = True,
        result_mask: ua.BrowseResultMask = ua.BrowseResultMask.All,
    ) -> list[ua.ReferenceDescription]: ...

    @syncmethod
    def add_reference(
        self,
        target: SyncNode | ua.NodeId | str | int,
        reftype: SyncNode | ua.NodeId | str | int,
        forward: bool = True,
        bidirectional: bool = True,
    ) -> None: ...

    @syncmethod
    def read_description(self) -> ua.LocalizedText: ...

    @syncmethod
    def get_variables(self) -> list[SyncNode]: ...

    @overload
    def get_path(self, max_length: int = 20, as_string: Literal[False] = False) -> list[SyncNode]: ...

    @overload
    def get_path(self, max_length: int = 20, as_string: Literal[True] = True) -> list[str]: ...

    @syncmethod
    def get_path(self, max_length: int = 20, as_string: bool = False) -> list[SyncNode] | list[str]: ...

    @syncmethod
    def read_attributes(self, attrs: Iterable[ua.AttributeIds]) -> list[ua.DataValue]: ...

    @syncmethod
    def add_reference_type(
        self,
        nodeid: ua.NodeId | str,
        bname: ua.QualifiedName | str,
        symmetric: bool = True,
        inversename: str | None = None,
    ) -> SyncNode: ...

    @syncmethod
    def delete_reference(
        self,
        target: SyncNode | ua.NodeId | str | int,
        reftype: SyncNode | ua.NodeId | str | int,
        forward: bool = True,
        bidirectional: bool = True,
    ) -> None: ...

    @syncmethod
    def get_access_level(self) -> set[ua.AccessLevel]: ...

    @syncmethod
    def get_description_refs(self) -> list[SyncNode]: ...

    @syncmethod
    def get_encoding_refs(self) -> list[SyncNode]: ...

    @syncmethod
    def get_methods(self) -> list[SyncNode]: ...

    @syncmethod
    def get_referenced_nodes(
        self,
        refs: SyncNode | ua.NodeId | str | int = ua.ObjectIds.References,
        direction: ua.BrowseDirection = ua.BrowseDirection.Both,
        nodeclassmask: ua.NodeClass = ua.NodeClass.Unspecified,
        includesubtypes: bool = True,
    ) -> list[SyncNode]: ...

    @syncmethod
    def read_data_type_definition(self) -> ua.DataTypeDefinition: ...

    @syncmethod
    def read_event_notifier(self) -> set[ua.EventNotifier]: ...

    @syncmethod
    def register(self) -> None: ...

    @syncmethod
    def set_attr_bit(self, attr: ua.AttributeIds, bit: int) -> None: ...

    @syncmethod
    def set_event_notifier(self, values: Iterable[ua.EventNotifier]) -> None: ...

    @syncmethod
    def unregister(self) -> None: ...

    @syncmethod
    def unset_attr_bit(self, attr: ua.AttributeIds, bit: int) -> None: ...

    @syncmethod
    def write_array_dimensions(self, value: int) -> None: ...

    @syncmethod
    def write_data_type_definition(self, sdef: ua.DataTypeDefinition) -> None: ...

    @syncmethod
    def write_value_rank(self, value: int) -> None: ...


class Subscription:
    def __init__(self, tloop: ThreadLoop, sub: subscription.Subscription) -> None:
        self.tloop: ThreadLoop = tloop
        self.aio_obj: subscription.Subscription = sub

    def __enter__(self) -> Subscription:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, tb: Any) -> None:
        self.delete()

    def __iter__(self) -> Subscription:
        return self

    def __next__(self) -> subscription.SubEvent:
        try:
            return self._wrap_event(self.tloop.post(self.aio_obj.__anext__()))
        except StopAsyncIteration:
            raise StopIteration from None

    def next_event(self, timeout: float | None = None) -> subscription.SubEvent | None:
        event = self.tloop.post(self.aio_obj.next_event(timeout=timeout))
        return self._wrap_event(event) if event is not None else None

    def _wrap_event(self, event: subscription.SubEvent) -> subscription.SubEvent:
        if isinstance(event, subscription.DataChangeEvent):
            return subscription.DataChangeEvent(
                node=SyncNode(self.tloop, event.node),  # type: ignore[arg-type]
                value=event.value,
                data=event.data,
            )
        return event

    @syncmethod
    def subscribe_data_change(
        self,
        nodes: SyncNode | Iterable[SyncNode],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: float = 0.0,
    ) -> int | list[int | ua.StatusCode]: ...

    @syncmethod
    def subscribe_events(
        self,
        sourcenode: SyncNode | ua.NodeId | str | int = ua.ObjectIds.Server,
        evtypes: SyncNode
        | ua.NodeId
        | str
        | int
        | Iterable[SyncNode | ua.NodeId | str | int] = ua.ObjectIds.BaseEventType,
        evfilter: ua.EventFilter | None = None,
        queuesize: int = 0,
    ) -> int: ...

    def _make_monitored_item_request(
        self,
        node: SyncNode,
        attr: ua.AttributeIds,
        mfilter: ua.MonitoringFilter | None,
        queuesize: int,
        monitoring: ua.MonitoringMode,
        sampling_interval: ua.Duration,
    ) -> ua.MonitoredItemCreateRequest:
        return self.aio_obj._make_monitored_item_request(node, attr, mfilter, queuesize, monitoring, sampling_interval)

    @syncmethod
    def unsubscribe(self, handle: int | Iterable[int]) -> None: ...

    @syncmethod
    def create_monitored_items(
        self, monitored_items: Iterable[ua.MonitoredItemCreateRequest]
    ) -> list[int | ua.StatusCode]: ...

    @syncmethod
    def delete(self) -> None: ...


class XmlExporter:
    def __init__(self, sync_server: Server) -> None:
        self.tloop: ThreadLoop = sync_server.tloop
        self.aio_obj: xmlexporter.XmlExporter = xmlexporter.XmlExporter(sync_server.aio_obj)

    @syncmethod
    def build_etree(self, node_list: Iterable[SyncNode], uris: list[str] | None = None) -> None: ...

    @syncmethod
    def write_xml(self, xmlpath: Path, pretty: bool = True) -> None: ...


class DataTypeDictionaryBuilder:
    def __init__(
        self, server: Server, idx: int, ns_urn: str, dict_name: str, dict_node_id: ua.NodeId | None = None
    ) -> None:
        self.tloop: ThreadLoop = server.tloop
        self.aio_obj: type_dictionary_builder.DataTypeDictionaryBuilder = (
            type_dictionary_builder.DataTypeDictionaryBuilder(server.aio_obj, idx, ns_urn, dict_name, dict_node_id)
        )
        self.init()

    @property
    def dict_id(self) -> ua.NodeId | None:
        return self.aio_obj.dict_id

    @syncmethod
    def init(self) -> None: ...

    @syncmethod
    def create_data_type(self, type_name: str, nodeid: ua.NodeId | None = None, init: bool = True) -> Any: ...

    @syncmethod
    def set_dict_byte_string(self) -> None: ...


def new_struct_field(
    name: str,
    dtype: ua.NodeId | SyncNode | ua.VariantType,
    array: bool = False,
    optional: bool = False,
    description: str = "",
) -> ua.StructureField:
    if isinstance(dtype, SyncNode):
        dtype = dtype.aio_obj
    return common.structures104.new_struct_field(name, dtype, array, optional, description)


@syncfunc(aio_func=common.structures104.new_enum)
def new_enum(
    server: Server | Client,
    idx: int | ua.NodeId,
    name: str | ua.QualifiedName,
    values: list[str],
    optional: bool = False,
) -> SyncNode: ...


@syncfunc(aio_func=common.structures104.new_struct)
def new_struct(
    server: Server | Client,
    idx: int | ua.NodeId,
    name: int | ua.QualifiedName,
    fields: list[ua.StructureField],
) -> tuple[SyncNode, list[SyncNode]]: ...
