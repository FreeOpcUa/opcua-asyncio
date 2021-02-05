"""
sync API of asyncua
"""
import asyncio
from threading import Thread, Condition
import logging

from asyncua import ua
from asyncua import client
from asyncua import server
from asyncua.common import node
from asyncua.common import subscription, shortcuts

logger = logging.getLogger(__name__)


class ThreadLoopNotRunning(Exception):
    pass


class ThreadLoop(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.loop = None
        self._cond = Condition()

    def start(self):
        with self._cond:
            Thread.start(self)
            self._cond.wait()

    def run(self):
        self.loop = asyncio.new_event_loop()
        logger.debug("Threadloop: %s", self.loop)
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
        if not self.loop or not self.loop.is_running():
            raise ThreadLoopNotRunning(f"could not post {coro}")
        futur = asyncio.run_coroutine_threadsafe(coro, loop=self.loop)
        return futur.result()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_t, exc_v, trace):
        self.stop()


def syncmethod(func):
    def wrapper(self, *args, **kwargs):
        args = list(args)  # FIXME: might be very inefficient...
        for idx, arg in enumerate(args):
            if isinstance(arg, Node):
                args[idx] = arg.aio_obj
        for k, v in kwargs.items():
            if isinstance(v, Node):
                kwargs[k] = v.aio_obj
        aio_func = getattr(self.aio_obj, func.__name__)
        result = self.tloop.post(aio_func(*args, **kwargs))
        if isinstance(result, node.Node):
            return Node(self.tloop, result)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], node.Node):
            return [Node(self.tloop, i) for i in result]
        if isinstance(result, server.event_generator.EventGenerator):
            return EventGenerator(self.tloop, result)
        if isinstance(result, subscription.Subscription):
            return Subscription(self.tloop, result)
        return result

    return wrapper


class _SubHandler:
    def __init__(self, tloop, sync_handler):
        self.tloop = tloop
        self.sync_handler = sync_handler

    def datachange_notification(self, node, val, data):
        self.sync_handler.datachange_notification(Node(self.tloop, node), val, data)

    def event_notification(self, event):
        self.sync_handler.event_notification(event)


class Client:
    def __init__(self, url: str, timeout: int = 4, tloop=None):
        self.tloop = tloop
        self.close_tloop = False
        if not self.tloop:
            self.tloop = ThreadLoop()
            self.tloop.start()
            self.close_tloop = True
        self.aio_obj = client.Client(url, timeout, loop=self.tloop.loop)
        self.nodes = Shortcuts(self.tloop, self.aio_obj.uaclient)

    def __str__(self):
        return "Sync" + self.aio_obj.__str__()
    __repr__ = __str__

    @syncmethod
    def connect(self):
        pass

    def disconnect(self):
        self.tloop.post(self.aio_obj.disconnect())
        if self.close_tloop:
            self.tloop.stop()

    def set_user(self, username: str):
        self.aio_obj.set_user(username)

    def set_password(self, pwd: str):
        self.aio_obj.set_password(pwd)

    @syncmethod
    def load_type_definitions(self, nodes=None):
        pass

    @syncmethod
    def set_security(self):
        pass

    @syncmethod
    def load_enums(self):
        pass

    def create_subscription(self, period, handler):
        coro = self.aio_obj.create_subscription(period, _SubHandler(self.tloop, handler))
        aio_sub = self.tloop.post(coro)
        return Subscription(self.tloop, aio_sub)

    @syncmethod
    def get_namespace_index(self, url):
        pass

    def get_node(self, nodeid):
        return Node(self.tloop, self.aio_obj.get_node(nodeid))

    @syncmethod
    def connect_and_get_server_endpoints(self):
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


class Shortcuts:
    def __init__(self, tloop, aio_server):
        self.tloop = tloop
        self.aio_obj = shortcuts.Shortcuts(aio_server)
        for k, v in self.aio_obj.__dict__.items():
            setattr(self, k, Node(self.tloop, v))


class Server:
    def __init__(self, shelf_file=None, tloop=None):
        self.tloop = tloop
        self.close_tloop = False
        if not self.tloop:
            self.tloop = ThreadLoop()
            self.tloop.start()
            self.close_tloop = True
        self.aio_obj = server.Server(loop=self.tloop.loop)
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

    def set_endpoint(self, url):
        return self.aio_obj.set_endpoint(url)

    def set_server_name(self, name):
        return self.aio_obj.set_server_name(name)

    def set_security_policy(self, security_policy):
        return self.aio_obj.set_security_policy(security_policy)

    def disable_clock(self, boolean):
        return self.aio_obj.disable_clock(boolean)

    @syncmethod
    def register_namespace(self, url):
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
        return Node(self.tloop, self.aio_obj.get_node(nodeid))

    @syncmethod
    def import_xml(self, path=None, xmlstring=None):
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
    def write_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        pass


class EventGenerator:
    def __init__(self, tloop, aio_evgen):
        self.aio_obj = aio_evgen
        self.tloop = tloop

    @property
    def event(self):
        return self.aio_obj.event

    def trigger(self, time=None, message=None):
        return self.tloop.post(self.aio_obj.trigger(time, message))


class Node:
    def __init__(self, tloop, aio_node):
        self.aio_obj = aio_node
        self.tloop = tloop

    def __eq__(self, other):
        return other != None and self.aio_obj == other.aio_obj

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

    nodeid = property(__get_nodeid, __set_nodeid)

    @syncmethod
    def read_browse_name(self):
        pass

    @syncmethod
    def read_display_name(self):
        pass

    get_display_name = read_display_name  # legacy

    @syncmethod
    def get_children(
        self, refs=ua.ObjectIds.HierarchicalReferences, nodeclassmask=ua.NodeClass.Unspecified
    ):
        pass

    @syncmethod
    def get_properties(self):
        pass

    @syncmethod
    def get_children_descriptions(
        self,
        refs=ua.ObjectIds.HierarchicalReferences,
        nodeclassmask=ua.NodeClass.Unspecified,
        includesubtypes=True,
    ):
        pass

    @syncmethod
    def get_user_access_level(self):
        pass

    @syncmethod
    def get_child(self, path):
        pass

    @syncmethod
    def set_modelling_rule(self, mandatory: bool):
        pass

    @syncmethod
    def add_variable(self, ns, name, val):
        pass

    @syncmethod
    def add_property(self, ns, name, val):
        pass

    @syncmethod
    def add_object(self, ns, name):
        pass

    @syncmethod
    def add_object_type(self, ns, name):
        pass

    @syncmethod
    def add_folder(self, ns, name):
        pass

    @syncmethod
    def add_method(self, *args):
        pass

    @syncmethod
    def set_writable(self, writable=True):
        pass

    @syncmethod
    def write_value(self, val):
        pass

    set_value = write_value  # legacy

    @syncmethod
    def write_params(self, params):
        pass

    @syncmethod
    def read_params(self, params):
        pass

    @syncmethod
    def read_value(self):
        pass

    get_value = read_value  # legacy

    @syncmethod
    def read_data_type_as_variant_type(self):
        pass

    get_data_type_as_variant_type = read_data_type_as_variant_type #legacy

    @syncmethod
    def call_method(self, methodid, *args):
        pass

    @syncmethod
    def get_references(
        self,
        refs=ua.ObjectIds.References,
        direction=ua.BrowseDirection.Both,
        nodeclassmask=ua.NodeClass.Unspecified,
        includesubtypes=True,
    ):
        pass

    @syncmethod
    def read_description(self):
        pass

    @syncmethod
    def get_variables(self):
        pass

    @syncmethod
    def get_path(self):
        pass

    @syncmethod
    def read_node_class(self):
        pass

    @syncmethod
    def read_attributes(self):
        pass


class Subscription:
    def __init__(self, tloop, sub):
        self.tloop = tloop
        self.aio_obj = sub

    @syncmethod
    def subscribe_data_change(self, nodes, attr=ua.AttributeIds.Value, queuesize=0):
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

    def _make_monitored_item_request(self, node: Node, attr, mfilter, queuesize) -> ua.MonitoredItemCreateRequest:
        return self.aio_obj._make_monitored_item_request(node, attr, mfilter, queuesize)

    @syncmethod
    def unsubscribe(self, handle):
        pass

    @syncmethod
    async def create_monitored_items(self, monitored_items):
        pass

    @syncmethod
    def delete(self):
        pass
