from abc import (
    ABC,
    abstractmethod
)
from typing import List
from asyncua import ua

class AbstractSession(ABC):
    @abstractmethod
    def browse(self, parameters: ua.BrowseParameters) -> List[ua.BrowseResult]:
        '''

        '''
    
    @abstractmethod
    def browse_next(self, parameters: ua.BrowseNextParameters) -> List[ua.BrowseResult]:
        '''
        
        '''

    @abstractmethod
    def read(self, parameters: ua.ReadParameters) -> List[ua.DataValue]:
        '''

        '''

    @abstractmethod
    def write(self, parameters: ua.WriteParameters) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    def translate_browsepaths_to_nodeids(self, browse_paths: List[ua.BrowsePath]) -> List[ua.BrowsePathResult]:
        '''

        '''

    @abstractmethod
    def history_read(self, params: ua.HistoryReadParameters) -> ua.HistoryReadResult:
        '''

        '''

    @abstractmethod
    def delete_references(self, refs: List[ua.DeleteReferencesItem]) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    def add_references(self, refs: List[ua.AddReferencesItem]) -> List[ua.StatusCode]:
        '''

        '''

    @abstractmethod
    def register_nodes(self, nodes: List[ua.NodeId]) -> List[ua.NodeId]:
        '''

        '''

    @abstractmethod
    def unregister_nodes(self, nodes: List[ua.NodeId]) -> List[ua.NodeId]:
        '''

        '''