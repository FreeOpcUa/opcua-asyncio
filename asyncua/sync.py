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
        aio_func = getattr(self.aio_obj, func.__name__)
        global _tloop
        result = _tloop.post(aio_func(*args, **kwargs))
        if isinstance(result, node.Node):
            return Node(result)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], node.Node):
            return [Node(i) for i in result]
        if isinstance(result, server.event_generator.EventGenerator):
            return EventGenerator(result)
        return result
    return wrapper


class Client:
    def __init__(self, url: str, timeout: int = 4):
        global _tloop
        self.aio_obj = client.Client(url, timeout, loop=_tloop.loop)
        self.nodes = Shortcuts(self.aio_obj.uaclient)

    @syncmethod
    def connect(self):
        pass

    @syncmethod
    def disconnect(self):
        pass

    def get_node(self, nodeid):
        return Node(self.aio_obj.get_node(nodeid))


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
    
    def set_endpoint(self, url):
        return self.aio_obj.set_endpoint(url)
    
    def set_server_name(self, name):
        return self.aio_obj.set_server_name(name)
    
    def set_security_policy(self, security_policy):
        return self.aio_obj.set_security_policy(security_policy)

    @syncmethod
    def register_namespace(self, url):
        return self.aio_obj.register_namespace(url)
    
    @syncmethod
    def start(self):
        pass

    @syncmethod
    def stop(self):
        pass

    @syncmethod
    async def get_event_generator(self, etype=None, emitting_node=ua.ObjectIds.Server):
        pass

    def get_node(self, nodeid):
        return Node(server.Server.get_node(self, nodeid))

    @syncmethod
    def import_xml(self, path=None, xmlstring=None):
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

    @property
    def nodeid(self):
        return self.aio_obj.nodeid
    
    @syncmethod
    def get_browse_name(self):
        pass

    @syncmethod
    def get_children(self):
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

    def __eq__(self, other):
        return self.aio_obj == other.aio_obj


