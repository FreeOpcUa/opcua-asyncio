import asyncio

from asyncua import Server, ua, Node
from asyncua.common.instantiate_util import instantiate

class StateMachineTypeClass(object):
    def __init__(self, server=None, parent=None):
        self._server = server
        self._parent = parent
        raise NotImplementedError

class FiniteStateMachineTypeClass(StateMachineTypeClass):
    def __init__(self, server=None, parent=None):
        super().__init__(server, parent)  
        raise NotImplementedError

class ExclusiveLimitStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None):
        super().__init__(server, parent)
        raise NotImplementedError

class FileTransferStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None):
        super().__init__(server, parent)
        raise NotImplementedError

class ProgramStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None):
        super().__init__(server, parent)
        raise NotImplementedError

class ShelvedStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None):
        super().__init__(server, parent)
        raise NotImplementedError
