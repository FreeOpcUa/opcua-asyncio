'''
    Protocols which are used to decople components from pubsub
'''
from asyncua.ua.uatypes import Byte, ExtensionObject, String, UInt16, UInt32, UInt64
from asyncua import ua
from .uadp import UadpNetworkMessage
from typing import List, Optional, Union
from .dataset import DataSetMeta, DataSetValue, PublishedDataSet

try:
    from typing import Protocol
except ImportError:
    # Protocol is only supported in Python >= 3.8
    # if mypy support is needed we should add typing extension as requirement
    class Protocol:
        pass


class PubSubSender(Protocol):
    '''
    Implements sending Messages
    '''
    def send_uadp(self, msgs: List[UadpNetworkMessage]):
        '''
        Sends a UadpMessage if supported!
        '''
        pass

    def get_publisher_id(self) -> Union[Byte, UInt16, UInt32, UInt64, String]:
        '''
        Returns the publisher id for creating messages
        '''
        pass


class IPubSub(Protocol):
    '''
    Interface to glue PublishedDataSet and Connection together
    '''
    def get_published_dataset(self, name: String) -> Optional[PublishedDataSet]:
        pass


class PubSubReciver(Protocol):
    '''
    Reciver for Pubsub Messages
    '''
    async def got_uadp(self, msg: UadpNetworkMessage):
        ''' Called when a msg is recived '''
        pass


class SubscripedDataSet(Protocol):
    ''' Reciver for subscriped datasets '''

    async def on_dataset_recived(self, meta: DataSetMeta, fields: List[DataSetValue]):
        ''' Called when a published dataset recived an update '''
        pass

    async def on_state_change(self, meta: DataSetMeta, state: ua.PubSubState):
        ''' Called when a DataSet state changes '''
        pass

    def get_subscribed_dataset(self) -> ExtensionObject:
        '''
            Returns the ExtensionObject
        '''
        pass
