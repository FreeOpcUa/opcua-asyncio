"""
server side implementation of callback event
"""

import inspect
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any


class CallbackType(Enum):
    """
    The possible types of a Callback type.

    :ivar Null:
    :ivar MonitoredItem:

    """

    Null = 0
    ItemSubscriptionCreated = 1
    ItemSubscriptionModified = 2
    ItemSubscriptionDeleted = 3
    PreWrite = 4
    PostWrite = 5
    PreRead = 6
    PostRead = 7


class Callback:
    def __init__(self) -> None:
        self.__name: str | None = None

    def setName(self, name: str | None) -> None:
        self.__name = name

    def getName(self) -> str | None:
        return self.__name


class ServerItemCallback(Callback):
    def __init__(self, request_params: Any, response_params: Any, user: Any = None, is_external: bool = False) -> None:
        super().__init__()
        self.request_params = request_params
        self.response_params = response_params
        self.is_external = is_external
        self.user = user


class CallbackSubscriberInterface:
    def getSubscribedEvents(self) -> dict[str, Any]:
        raise NotImplementedError()


Listener = Callable[[Callback, "CallbackService"], Awaitable[None] | None]


class CallbackService:
    def __init__(self) -> None:
        self._listeners: dict[str, OrderedDict[int, Listener]] = {}

    async def dispatch(self, eventName: str, event: Callback | None = None) -> Callback:
        if event is None:
            event = Callback()
        elif not isinstance(event, Callback):
            raise ValueError("Unexpected event type given")
        event.setName(eventName)
        if eventName not in self._listeners:
            return event
        for listener in self._listeners[eventName].values():
            await self.call_listener(event, listener)

        return event

    async def call_listener(self, event: Callback, listener: Listener) -> None:
        if inspect.iscoroutinefunction(listener):
            await listener(event, self)
        else:
            listener(event, self)

    def addListener(self, eventName: str, listener: Listener, priority: int = 0) -> None:
        if eventName not in self._listeners:
            self._listeners[eventName] = OrderedDict()
        self._listeners[eventName][priority] = listener
        self._listeners[eventName] = OrderedDict(sorted(self._listeners[eventName].items(), key=lambda item: item[0]))

    def removeListener(self, eventName: str, listener: Listener | None = None) -> None:
        if eventName not in self._listeners:
            return
        if not listener:
            del self._listeners[eventName]
        else:
            for name, mylistener in self._listeners[eventName].items():
                if mylistener is listener:
                    self._listeners[eventName].pop(name)
                    return

    def addSubscriber(self, subscriber: CallbackSubscriberInterface) -> None:
        if not isinstance(subscriber, CallbackSubscriberInterface):
            raise ValueError("Unexpected subscriber type given")
        for eventName, params in subscriber.getSubscribedEvents().items():
            if isinstance(params, str):
                self.addListener(eventName, getattr(subscriber, params))
            elif isinstance(params, list):
                if not params:
                    raise ValueError(f'Invalid params "{params!r}" for event "{eventName!s}"')
                if len(params) <= 2 and isinstance(params[0], str):
                    priority = params[1] if len(params) > 1 else 0
                    self.addListener(eventName, getattr(subscriber, params[0]), priority)
                else:
                    for listener in params:
                        priority = listener[1] if len(listener) > 1 else 0
                        self.addListener(eventName, getattr(subscriber, listener[0]), priority)
            else:
                raise ValueError(f'Invalid params for event "{eventName!s}"')
