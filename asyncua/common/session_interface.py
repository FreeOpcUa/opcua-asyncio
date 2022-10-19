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