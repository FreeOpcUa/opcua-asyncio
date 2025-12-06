"""
server side implementation of callback event
"""

import asyncio
from collections import OrderedDict
from enum import Enum


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
    def __init__(self):
        self.__name = None

    def setName(self, name):
        self.__name = name

    def getName(self):
        return self.__name


class ServerItemCallback(Callback):
    def __init__(self, request_params, response_params, user=None, is_external=False):
        self.request_params = request_params
        self.response_params = response_params
        self.is_external = is_external
        self.user = user


class CallbackSubscriberInterface:
    def getSubscribedEvents(self):
        raise NotImplementedError()


class CallbackService:
    def __init__(self):
        self._listeners = {}

    async def dispatch(self, eventName, event=None):
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

    async def call_listener(self, event, listener):
        if asyncio.iscoroutinefunction(listener):
            await listener(event, self)
        else:
            listener(event, self)

    def addListener(self, eventName, listener, priority=0):
        if eventName not in self._listeners:
            self._listeners[eventName] = {}
        self._listeners[eventName][priority] = listener
        self._listeners[eventName] = OrderedDict(sorted(self._listeners[eventName].items(), key=lambda item: item[0]))

    def removeListener(self, eventName, listener=None):
        if eventName not in self._listeners:
            return
        if not listener:
            del self._listeners[eventName]
        else:
            for name, mylistener in self._listeners[eventName].items():
                if mylistener is listener:
                    self._listeners[eventName].pop(name)
                    return

    def addSubscriber(self, subscriber):
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
