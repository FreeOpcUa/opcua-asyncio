"""
server side implementation of callback event 
"""

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
    WritePerformed = 4


class Callback(object):
    def __init__(self):
        self.__name = None

    def setName(self, name):
        self.__name = name

    def getName(self):
        return self.__name


class ServerItemCallback(Callback):
    def __init__(self, request_params, response_params, user=None):
        self.request_params = request_params
        self.response_params = response_params
        self.user = user


class CallbackSubscriberInterface(object):
    def getSubscribedEvents(self):
        raise NotImplementedError()


class CallbackDispatcher(object):
    def __init__(self):
        self._listeners = {}

    def dispatch(self, eventName, event=None):
        if event is None:
            event = Callback()
        elif not isinstance(event, Callback):
            raise ValueError('Unexpected event type given')
        event.setName(eventName)
        if eventName not in self._listeners:
            return event
        for listener in self._listeners[eventName].values():
            listener(event, self)
        return event

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
            for p, l in self._listeners[eventName].items():
                if l is listener:
                    self._listeners[eventName].pop(p)
                    return

    def addSubscriber(self, subscriber):
        if not isinstance(subscriber, CallbackSubscriberInterface):
            raise ValueError('Unexpected subscriber type given')
        for eventName, params in subscriber.getSubscribedEvents().items():
            if isinstance(params, str):
                self.addListener(eventName, getattr(subscriber, params))
            elif isinstance(params, list):
                if not params:
                    raise ValueError('Invalid params "{0!r}" for event "{1!s}"'.format(params, eventName))
                if len(params) <= 2 and isinstance(params[0], str):
                    priority = params[1] if len(params) > 1 else 0
                    self.addListener(eventName, getattr(subscriber, params[0]), priority)
                else:
                    for listener in params:
                        priority = listener[1] if len(listener) > 1 else 0
                        self.addListener(eventName, getattr(subscriber, listener[0]), priority)
            else:
                raise ValueError('Invalid params for event "{0!s}"'.format(eventName))
