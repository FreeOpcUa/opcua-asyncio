import asyncio
from typing import Any, Awaitable, Callable, TypeVar, Union

_T = TypeVar("_T")

async def wait_for(
    fut: Awaitable[_T],
    timeout: Union[int, float, None],
    *,
    loop: asyncio.AbstractEventLoop = None,
    race_handler: Callable[[Union[_T, BaseException], bool], Any] = None,
): ...
