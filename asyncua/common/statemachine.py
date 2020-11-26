import asyncio, logging

from asyncua import Server, ua, Node
from asyncua.common.instantiate_util import instantiate

class StateMachineTypeClass(object):
    '''
    Implementation of an StateMachineType
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        #if idx = none log parend idx is used
        self._server = server
        self._parent = parent
        self._state_machine_node = None
        self._state_machine_type = ua.NodeId(2299, 0)
        self._name = name
        self._idx = idx

        self._current_state = "None" #Variable
        self._current_state_id = None #Property        
        self._last_transition = "None" #Variable
        self._last_transition_id = None #Property

        self._optionals = False

    async def install(self, optionals=False):
        '''
        setup adressspace and initialize 
        '''
        self._optionals = optionals
        self._state_machine_node = await self._parent.add_object(self._idx, self._name, objecttype=self._state_machine_type, instantiate_optional=optionals)
    
    async def change_state(self, state_name, state, transition_name, transition=None):
        #check types: names = string and others are nodetype
        self._current_state = state #Variable
        self._current_state_id = None #Property  
        if self._optionals:
            self._last_transition = transition #Variable
            self._last_transition_id = None #Property
        #write

class FiniteStateMachineTypeClass(StateMachineTypeClass):
    '''
    Implementation of an FiniteStateMachineType
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        self._state_machine_type = ua.NodeId(2771, 0)
        self._avalible_states = []
        self._avalible_transitions = []

    async def install(self, instantiate_optional=False):
        '''
        setup adressspace and initialize 
        '''
        self._optionals = instantiate_optional
        self._state_machine_node = await self._parent.add_object(self._idx, self._name, objecttype=self._state_machine_type, instantiate_optional=instantiate_optional)

    async def set_avalible_states(self, states):
        self._avalible_states = states

    async def set_avalible_transitions(self, transitions):
        self._avalible_transitions = transitions      

class ExclusiveLimitStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent)
        self._state_machine_type = ua.ObjectIds.ExclusiveLimitStateMachineType
        raise NotImplementedError

class FileTransferStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent)
        self._state_machine_type = ua.ObjectIds.FileTransferStateMachineType
        raise NotImplementedError

class ProgramStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent)
        self._state_machine_type = ua.ObjectIds.ProgramStateMachineType
        self._ready_state = None #State node
        self._halted_state = None #State node
        self._running_state = None #State node
        self._suspended_state = None #State node

        self._halted_to_ready = None #Transition node
        self._ready_to_running = None #Transition node
        self._running_to_halted = None #Transition node
        self._running_to_ready = None #Transition node
        self._running_to_suspended = None #Transition node
        self._suspended_to_running = None #Transition node
        self._suspended_to_halted = None #Transition node
        self._suspended_to_ready = None #Transition node
        self._ready_to_halted = None #Transition node

    async def install(self):
        #setup addressspace
        # instantiate(parent=self._parent, node_type=self._state_machine_type, nodeid=, bname="StateMachine", dname=, idx= , instantiate_optionals=False)
        #maybe better to use create_object()
        self._state_machine_node = None
        #get childnodes:
        self._ready_state = None #State node
        self._halted_state = None #State node
        self._running_state = None #State node
        self._suspended_state = None #State node
        self._halted_to_ready = None #Transition node
        self._ready_to_running = None #Transition node
        self._running_to_halted = None #Transition node
        self._running_to_ready = None #Transition node
        self._running_to_suspended = None #Transition node
        self._suspended_to_running = None #Transition node
        self._suspended_to_halted = None #Transition node
        self._suspended_to_ready = None #Transition node
        self._ready_to_halted = None #Transition node

    #Transition
    async def HaltedToReady(self):
        await self._current_state.write_value(ua.LocalizedText("Ready", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._ready_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("HaltedToReady", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._halted_to_ready.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def ReadyToRunning(self):
        await self._current_state.write_value(ua.LocalizedText("Running", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._running_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("ReadyToRunning", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._ready_to_running.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def RunningToHalted(self):
        await self._current_state.write_value(ua.LocalizedText("Halted", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._halted_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("RunningToHalted", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._running_to_halted.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def RunningToReady(self):
        await self._current_state.write_value(ua.LocalizedText("Ready", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._ready_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("RunningToReady", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._running_to_ready.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def RunningToSuspended(self):
        await self._current_state.write_value(ua.LocalizedText("Suspended", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._suspended_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("RunningToSuspended", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._running_to_suspended.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition 
    async def SuspendedToRunning(self):
        await self._current_state.write_value(ua.LocalizedText("Running", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._running_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("SuspendedToRunning", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._suspended_to_running.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def SuspendedToHalted(self):
        await self._current_state.write_value(ua.LocalizedText("Halted", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._halted_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("SuspendedToHalted", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._suspended_to_halted.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def SuspendedToReady(self):
        await self._current_state.write_value(ua.LocalizedText("Ready", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._ready_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("SuspendedToReady", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._suspended_to_ready.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition 
    async def ReadyToHalted(self):
        await self._current_state.write_value(ua.LocalizedText("Halted", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._current_state_id.write_value(self._halted_state.nodeid, varianttype=ua.VariantType.NodeId)
        await self._last_transition.write_value(ua.LocalizedText("ReadyToHalted", "en-US"), varianttype=ua.VariantType.LocalizedText)
        await self._last_transition_id.write_value(self._ready_to_halted.nodeid, varianttype=ua.VariantType.NodeId)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

class ShelvedStateMachineTypeClass(FiniteStateMachineTypeClass):
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent)
        self._state_machine_type = ua.ObjectIds.ShelvedStateMachineType
        raise NotImplementedError





#Devtests

async def main():
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger('asyncua')

    server = Server()

    await server.init()
    sm = StateMachineTypeClass(server, server.get_objects_node(), 0, "Test1")
    await sm.install()
    fsm = FiniteStateMachineTypeClass(server, server.nodes.objects, 0, "Test2")
    await fsm.install()

    async with server:
        while 1:
            await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
