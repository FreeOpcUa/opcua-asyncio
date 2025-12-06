import asyncio
import hashlib
import logging
import pickle
from itertools import chain, islice

from asyncua.common.utils import wait_for

_logger = logging.getLogger(__name__)


class ClientNotFound(Exception):
    pass


async def event_wait(evt, timeout) -> bool:
    try:
        await wait_for(evt.wait(), timeout)
    except asyncio.TimeoutError:
        pass
    return evt.is_set()


def get_digest(conf) -> str:
    return hashlib.md5(pickle.dumps(conf)).hexdigest()


def batch(iterable, size):
    iterator = iter(iterable)
    while True:
        try:
            batchiter = islice(iterator, size)
            yield list(chain([next(batchiter)], batchiter))
        except StopIteration:
            break
