from abc import (
    ABC,
    abstractmethod
)
from typing import List
from asyncua import ua

class AbstractSession(ABC):
    @abstractmethod
    async def browse(self, parameters: ua.BrowseParameters) -> List[ua.BrowseResult]:
        '''

        '''
    
    @abstractmethod
    async def browse_next(self, parameters: ua.BrowseNextParameters) -> List[ua.BrowseResult]:
        '''
        
        '''

    @abstractmethod
    async def read(self, parameters: ua.ReadParameters) -> List[ua.DataValue]:
        '''

        '''

    @abstractmethod
    async def write(self, parameters: ua.WriteParameters) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    async def translate_browsepaths_to_nodeids(self, browse_paths: List[ua.BrowsePath]) -> List[ua.BrowsePathResult]:
        '''

        '''

    @abstractmethod
    async def history_read(self, params: ua.HistoryReadParameters) -> ua.HistoryReadResult:
        '''

        '''

    @abstractmethod
    async def delete_references(self, refs: List[ua.DeleteReferencesItem]) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    async def add_references(self, refs: List[ua.AddReferencesItem]) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    async def register_nodes(self, nodes: List[ua.NodeId]) -> List[ua.NodeId]:
        '''

        '''

    @abstractmethod
    async def unregister_nodes(self, nodes: List[ua.NodeId]) -> List[ua.NodeId]:
        '''

        '''

    @abstractmethod
    async def add_nodes(self, params: ua.AddNodesParameters) -> List[ua.AddNodesResult]:
        '''

        '''

    @abstractmethod
    async def delete_nodes(self, params: ua.DeleteNodesParameters) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    async def call(self, methodstocall: List[ua.CallMethodRequest]) -> ua.CallMethodResult:
        '''

        '''

    @abstractmethod
    async def create_subscription(self, params: ua.CreateSubscriptionParameters) -> ua.CreateSubscriptionResult:
        '''

        '''

    @abstractmethod
    async def modify_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        '''

        '''

    @abstractmethod
    async def delete_subscriptions(self, params: ua.DeleteSubscriptionsParameters) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    async def create_monitored_items(self, params: ua.CreateMonitoredItemsParameters) -> List[ua.MonitoredItemCreateResult]:
        '''

        '''

    @abstractmethod
    async def modify_monitored_items(self, params: ua.ModifyMonitoredItemsParameters) -> List[ua.MonitoredItemModifyResult]:
        '''

        '''

    @abstractmethod
    async def delete_monitored_items(self, params: ua.DeleteMonitoredItemsParameters) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    async def transfer_subscription(self, params: ua.TransferSubscriptionsParameters) -> ua.TransferResult:
        '''

        '''
