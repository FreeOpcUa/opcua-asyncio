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
        with self._cond:
            self._cond.notify_all()
        self.loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def post(self, coro):
        futur = asyncio.run_coroutine_threadsafe(coro, loop=self.loop)
        return futur.result()

    def __enter__(self):
        self.start()
        global _tloop
        _tloop = self
        return self

    def __exit__(self, exc_t, exc_v, trace):
        self.stop()
        self.join()

#@ipcmethod

_ref_count = 0
_tloop = None


def start_thread_loop():
    global _tloop
    _tloop = ThreadLoop()
    _tloop.start()
    return _tloop


def stop_thread_loop():
    global _tloop
    _tloop.stop()
    _tloop.join()


def get_thread_loop():
    global _tloop
    if _tloop is None:
        start_thread_loop()
    global _ref_count
    _ref_count += 1
    return _tloop


def release_thread_loop():
    global _tloop
    if _tloop is None:
        return
    global _ref_count
    if _ref_count == 0:
        _ref_count -= 1
    stop_thread_loop()


def syncmethod(func):
    def wrapper(self, *args, **kwargs):
        args = list(args)  #FIXME: might be very inefficient...
        for idx, arg in enumerate(args):
            if isinstance(arg, Node):
                args[idx] = arg.aio_obj
        for k, v in kwargs.items():
            if isinstance(v, Node):
                kwargs[k] = v.aio_obj
        aio_func = getattr(self.aio_obj, func.__name__)
        global _tloop
        result = _tloop.post(aio_func(*args, **kwargs))
        if isinstance(result, node.Node):
            return Node(result)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], node.Node):
            return [Node(i) for i in result]
        if isinstance(result, server.event_generator.EventGenerator):
            return EventGenerator(result)
        if isinstance(result, subscription.Subscription):
            return Subscription(result)
        return result

    return wrapper


class _SubHandler:
    def __init__(self, sync_handler):
        self.sync_handler = sync_handler

    def datachange_notification(self, node, val, data):
        self.sync_handler.datachange_notification(Node(node), val, data)

    def event_notification(self, event):
        self.sync_handler.event_notification(event)


class Client:
    def __init__(self, url: str, timeout: int = 4):
        global _tloop
        self.aio_obj = client.Client(url, timeout, loop=_tloop.loop)
        self.nodes = Shortcuts(self.aio_obj.uaclient)

    def __str__(self):
        return "Sync" + self.aio_obj.__str__()
    __repr__ = __str__

    @syncmethod
    def connect(self):
        pass

    @syncmethod
    def disconnect(self):
        pass

    @syncmethod
    def load_type_definitions(self, nodes=None):
        pass

    def create_subscription(self, period, handler):
        coro = self.aio_obj.create_subscription(period, _SubHandler(handler))
        aio_sub = _tloop.post(coro)
        return Subscription(aio_sub)

    @syncmethod
    def get_namespace_index(self, url):
        pass

    def get_node(self, nodeid):
        return Node(self.aio_obj.get_node(nodeid))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


class Shortcuts:
    def __init__(self, aio_server):
        self.aio_obj = shortcuts.Shortcuts(aio_server)
        for k, v in self.aio_obj.__dict__.items():
            setattr(self, k, Node(v))


class Server:
    def __init__(self, shelf_file=None):
        global _tloop
        self.aio_obj = server.Server(loop=_tloop.loop)
        _tloop.post(self.aio_obj.init(shelf_file))
        self.nodes = Shortcuts(self.aio_obj.iserver.isession)

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
        return self.aio_obj.register_namespace(url)

    @syncmethod
    def start(self):
        pass

    @syncmethod
    def stop(self):
        pass

    def link_method(self, node, callback):
        return self.aio_obj.link_method(node, callback)

    @syncmethod
    def get_event_generator(self, etype=None, emitting_node=ua.ObjectIds.Server):
        pass

    def get_node(self, nodeid):
        return Node(server.Server.get_node(self, nodeid))

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

    def set_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        return self.aio_obj.set_attribute_value(nodeid, datavalue, attr)


class EventGenerator:
    def __init__(self, aio_evgen):
        self.aio_obj = aio_evgen

    @property
    def event(self):
        return self.aio_obj.event

    def trigger(self, time=None, message=None):
        return self.aio_obj.trigger(time, message)


class Node:
    def __init__(self, aio_node):
        self.aio_obj = aio_node
        global _tloop

    def __hash__(self):
        return self.aio_obj.__hash__()

    def __str__(self):
        return "Sync" + self.aio_obj.__str__()
    __repr__ = __str__

    @property
    def nodeid(self):
        return self.aio_obj.nodeid

    @syncmethod
    def get_browse_name(self):
        pass

    @syncmethod
    def get_children(self, refs=ua.ObjectIds.HierarchicalReferences, nodeclassmask=ua.NodeClass.Unspecified):
        pass

    @syncmethod
    def get_children_descriptions(self,
                                  refs=ua.ObjectIds.HierarchicalReferences,
                                  nodeclassmask=ua.NodeClass.Unspecified,
                                  includesubtypes=True):
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
    def set_value(self, val):
        pass

    @syncmethod
    def get_value(self, val):
        pass

    @syncmethod
    def call_method(self, methodid, *args):
        pass

    def __eq__(self, other):
        return self.aio_obj == other.aio_obj


class Subscription:
    def __init__(self, sub):
        self.aio_obj = sub

    @syncmethod
    def subscribe_data_change(self, nodes, attr=ua.AttributeIds.Value, queuesize=0):
        pass

    @syncmethod
    def subscribe_events(self,
                         sourcenode=ua.ObjectIds.Server,
                         evtypes=ua.ObjectIds.BaseEventType,
                         evfilter=None,
                         queuesize=0):
        pass

    @syncmethod
    def unsubscribe(self, handle):
        pass

    @syncmethod
    async def create_monitored_items(self, monitored_items):
        pass

    @syncmethod
    def delete(self):
        pass
