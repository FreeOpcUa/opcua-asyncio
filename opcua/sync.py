"""
sync API of asyncua
"""
import asyncio
from threading import Thread, Condition
import logging

from opcua import client
from opcua import server
from opcua.common import node
from opcua.common import subscription


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
        print("Thread ended")

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def post(self, coro):
        futur = asyncio.run_coroutine_threadsafe(coro, loop=self.loop)
        return futur.result()


#@ipcmethod


_ref_count = 0
_tloop = None



def start_thread_loop():
    print("START")
    global _tloop
    _tloop = ThreadLoop()
    _tloop.start()
    return _tloop


def stop_thread_loop():
    print("STOP")
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
        name = func.__name__
        sup = _get_super(func)
        super_func = getattr(sup, name)
        global _tloop
        result = _tloop.post(super_func(self, *args, **kwargs))
        return result
    return wrapper


class Client(client.Client):
    def __init__(self, url: str, timeout: int = 4):
        global _tloop
        client.Client.__init__(self, url, timeout, loop=_tloop.loop)
    
    @syncmethod
    def connect(self):
        pass

    @syncmethod
    def disconnect(self):
        pass


class Server(server.Server):
    def __init__(self, shelf_file=None):
        global _tloop
        server.Server.__init__(self)
        _tloop.post(self.init(shelf_file))
    
    @syncmethod
    def start(self):
        pass

    @syncmethod
    def stop(self):
        pass


