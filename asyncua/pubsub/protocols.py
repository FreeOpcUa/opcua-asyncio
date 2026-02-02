"""
Protocols which are used to decouple components from pubsub
"""

from typing import Protocol

from ..ua.uaprotocol_auto import PubSubState
from ..ua.uatypes import Byte, ExtensionObject, String, UInt16, UInt32, UInt64
from .dataset import DataSetMeta, DataSetValue, PublishedDataSet
from .uadp import UadpNetworkMessage


class PubSubSender(Protocol):
    """
    Implements sending Messages
    """

    def send_uadp(self, msgs: list[UadpNetworkMessage]):
        """
        Sends a UadpMessage if supported!
        """
        raise NotImplementedError

    def get_publisher_id(self) -> Byte | UInt16 | UInt32 | UInt64 | String:
        """
        Returns the publisher id for creating messages
        """
        raise NotImplementedError


class IPubSub(Protocol):
    """
    Interface to glue PublishedDataSet and Connection together
    """

    def get_published_dataset(self, name: String) -> PublishedDataSet | None:
        raise NotImplementedError


class PubSubReceiver(Protocol):
    """
    Receiver for Pubsub Messages
    """

    async def got_uadp(self, msg: UadpNetworkMessage):
        """Called when a msg is received"""
        raise NotImplementedError


class SubscribedDataSet(Protocol):
    """Receiver for subscribed datasets"""

    async def on_dataset_received(self, meta: DataSetMeta, fields: list[DataSetValue]):
        """Called when a published dataset received an update"""
        raise NotImplementedError

    async def on_state_change(self, meta: DataSetMeta, state: PubSubState):
        """Called when a DataSet state changes"""
        raise NotImplementedError

    def get_subscribed_dataset(self) -> ExtensionObject:
        """
        Returns the ExtensionObject
        """
        raise NotImplementedError
