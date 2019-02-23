"""
sync API of asyncua
"""
import asyncio
from threading import Thread, Condition
import logging

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


def _get_super(func):
    classname = func.__qualname__.split('.', 1)[0]
    if hasattr(node, classname):
        return getattr(node, classname)
    if hasattr(client, classname):
        return getattr(client, classname)
    if hasattr(server, classname):
        return getattr(server, classname)
    if hasattr(subscription, classname):
        return getattr(subscription, classname)
    return AttributeError(f"Could not find super of parent class for method {func}")


def syncmethod(func):
    def wrapper(self, *args, **kwargs):
        #name = func.__name__
        aio_func = getattr(self.aio_obj, func.__name__)
        #sup = _get_super(func)
        #super_func = getattr(sup, name)
        global _tloop
        print("CALLING", func, func.__name__, args)
        result = _tloop.post(aio_func(*args, **kwargs))
        if isinstance(result, node.Node):
            return Node(result)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], node.Node):
            return [Node(i) for i in result]
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
    
    @syncmethod
    def register_namespace(self, url):
        return self.aio_obj.register_namespace(url)
    
    @syncmethod
    def start(self):
        pass

    @syncmethod
    def stop(self):
        pass

    def get_node(self, nodeid):
        return Node(server.Server.get_node(self, nodeid))


class Node:
    def __init__(self, aio_node):
        self.aio_obj = aio_node
        global _tloop
    
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
    def add_variable(self, ns, name, val):
        pass

    @syncmethod
    def add_object(self, ns, name):
        pass

    @syncmethod
    def set_writable(self, writable=True):
        pass

    @syncmethod
    def set_value(self, val):
        pass

    def __eq__(self, other):
        return self.aio_obj == other.aio_obj


