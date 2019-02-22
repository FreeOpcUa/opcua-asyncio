"""
sync API of asyncua
"""
import asyncio
import inspect
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


def get_thread_loop():
    global _tloop
    if _tloop is None:
        _tloop = ThreadLoop()
        _tloop.start()
    global _ref_count
    _ref_count += 1
    print("RETURNING", _tloop, _ref_count)
    return _tloop


def release_thread_loop():
    global _tloop
    if _tloop is None:
        return
    global _ref_count
    if _ref_count == 0:
        _ref_count -= 1
    print("STOPPING", _tloop, _ref_count)
    _tloop.stop()
    _tloop.join()


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
        return _tloop.post(super_func(self, *args, **kwargs))
    return wrapper


class Client(client.Client):
    def __init__(self, url: str, timeout: int = 4):
        self._tloop = get_thread_loop()
        client.Client.__init__(self, url, timeout, loop=self._tloop.loop)
    
    @syncmethod
    def connect(self):
        print("NOT HEERE")
        pass

    @syncmethod
    def disconnect(self):
        pass



