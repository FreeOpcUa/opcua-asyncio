'''
https://reference.opcfoundation.org/v104/Core/docs/Part10/
https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.1/

Basic statemachines described in OPC UA Spec.:
StateMachineType
FiniteStateMachineType
ExclusiveLimitStateMachineType
FileTransferStateMachineType
ProgramStateMachineType
ShelvedStateMachineType

Relevant information:
Overview - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.3/#5.2.3.1
States - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.3/#5.2.3.2
Transitions - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.3/#5.2.3.3
Events - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.5/
'''
import asyncio, logging

#FIXME 
# -change to relativ imports!
# -remove unused imports
from asyncua import Server, ua, Node
from asyncua.common.event_objects import TransitionEvent, ProgramTransitionEvent

_logger = logging.getLogger(__name__)

class StateTypeClass(object):
    _count = 0
    def __init__(self, name, node=None, auto_id=True):
        self.name = name
        self.node = node
        if auto_id:
            self._id = type(self)._count + 1 #according to the specs a unique number for each state
            type(self)._count = self._id
            return
        self._id = 0
    
    def set_id(self, id):
        self._id = id

class TransitionTypeClass(object):
    _count = 0
    def __init__(self, name, node=None, auto_id=True):
        self.name = name
        self.node = node
        if auto_id:
            self._id = type(self)._count + 1  #according to the specs a unique number for each transition
            type(self)._count = self._id
            return
        self._id = 0
    
    def set_id(self, id):
        self._id = id

class StateMachineTypeClass(object):
    '''
    Implementation of an StateMachineType (most basic type)
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        if not isinstance(server, Server): 
            raise ValueError
        if not isinstance(parent, Node): 
            raise ValueError
        if idx == None:
            idx = parent.nodeid.NamespaceIndex
        if name == None:
            name = "StateMachine"
        self.locale = "en-US"
        self._server = server
        self._parent = parent
        self._state_machine_node = None
        self._state_machine_type = ua.NodeId(2299, 0) #StateMachineType
        self._name = name
        self._idx = idx
        self._optionals = False
        self._current_state_node = None
        self._current_state_id_node = None
        self._last_transition_node = None
        self._last_transition_id_node = None
        self._evgen = None
        self.evtype = TransitionEvent()

    async def install(self, optionals=False):
        '''
        setup adressspace
        '''
        self._optionals = optionals
        self._state_machine_node = await self._parent.add_object(
            self._idx, 
            self._name, 
            objecttype=self._state_machine_type, 
            instantiate_optional=optionals
            )
        await self.init(self._state_machine_node)
    
    async def init(self, statemachine):
        '''
        initialize subnodes
        '''
        #FIXME check for childrens typdefinitions which matches statemachine
        self._current_state_node = await statemachine.get_child(["CurrentState"])
        self._current_state_id_node = await statemachine.get_child(["CurrentState","Id"])
        if self._optionals:
            self._last_transition_node = await statemachine.get_child(["LastTransition"])
            self._last_transition_id_node = await statemachine.get_child(["LastTransition","Id"])
        self._evgen = await self._server.get_event_generator(self.evtype, self._state_machine_node)

    async def change_state(
        self, 
        state, 
        transition=None, 
        event_msg=None,
        severity=500
        ):
        '''
        method to change the state of the statemachine
        state (type StateTypeClass mandatory)
        transition (type TransitionTypeClass optional)
        event_msg (type string optional)
        severity (type Int optional)
        '''
        #FIXME check StateType exist
        #FIXME check TransitionTypeType exist
        await self._write_state(state)
        if transition:
            await self._write_transition(transition)
        if event_msg:
            if isinstance(event_msg, (type(""))):
                event_msg = ua.LocalizedText(event_msg, self.locale)
            self._evgen.event.Message = event_msg
            self._evgen.event.Severity = severity
            await self._evgen.trigger()

    async def _write_state(self, state):
        await self._current_state_node.write_value(ua.LocalizedText(state.name, self.locale))
        if state.node:
            await self._current_state_id_node.write_value(state.node.nodeid)

    async def _write_transition(self, transition):
        await self._last_transition_node.write_value(ua.LocalizedText(transition.name, self.locale))
        if transition.node:
            await self._last_transition_id_node.write_value(transition.node.nodeid)
    
    async def add_state(self, state, state_type=ua.NodeId(2307, 0), optionals=False):
        '''
        state: StateTypeClass
        InitialStateType: ua.NodeId(2309, 0)
        StateType: ua.NodeId(2307, 0)
        ChoiceStateType: ua.NodeId(15109,0)
        '''
        if not isinstance(state, StateTypeClass):
            raise ValueError
        state.node = await self._state_machine_node.add_object(
            self._idx, 
            state.name, 
            objecttype=state_type, 
            instantiate_optional=optionals
            )
        state_number = await state.node.get_child(["StateNumber"])
        await state_number.write_value(state._id, ua.VariantType.UInt32)
        return state.node

    async def add_transition(self, transition, transition_type=ua.NodeId(2310, 0), optionals=False):
        '''
        transition: TransitionTypeClass
        transition_type: ua.NodeId(2310, 0)
        '''
        if not isinstance(transition, TransitionTypeClass):
            raise ValueError
        transition.node = await self._state_machine_node.add_object(
            self._idx, 
            transition.name, 
            objecttype=transition_type, 
            instantiate_optional=optionals
            )
        transition_number = await transition.node.get_child(["TransitionNumber"])
        await transition_number.write_value(transition._id, ua.VariantType.UInt32)
        return transition.node

    async def remove(self, nodes):
        #FIXME
        raise NotImplementedError

class FiniteStateMachineTypeClass(StateMachineTypeClass):
    '''
    Implementation of an FiniteStateMachineType a little more advanced than the basic one
    if you need to know the avalible states and transition from clientside
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "FiniteStateMachine"
        self._state_machine_type = ua.NodeId(2771, 0)
        self._avalible_states_node = None
        self._avalible_transitions_node = None

    async def install(self, optionals=False):
        '''
        setup adressspace and initialize 
        '''
        self._optionals = optionals
        self._state_machine_node = await self._parent.add_object(
            self._idx, 
            self._name, 
            objecttype=self._state_machine_type, 
            instantiate_optional=optionals
            )

    async def init(self, avalible_states, avalible_transitions, ):
        #FIXME get children and map children
        #await self.find_all_states()
        await self.set_avalible_states(avalible_states)
        #await self.find_all_transitions()
        await self.set_avalible_transitions(avalible_transitions)

    async def set_avalible_states(self, states):
        #check if its list
        await self._avalible_states_node.write_value(states, varianttype=ua.VariantType.NodeId)

    async def set_avalible_transitions(self, transitions):
        #check if its list
        await self._avalible_transitions_node.write_value(transitions, varianttype=ua.VariantType.NodeId)

    async def find_all_states(self):
        return NotImplementedError
    
    async def find_all_transitions(self):
        return NotImplementedError

class ExclusiveLimitStateMachineTypeClass(FiniteStateMachineTypeClass):
    '''
    NOT IMPLEMENTED "ExclusiveLimitStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "ExclusiveLimitStateMachine"
        self._state_machine_type = ua.NodeId(9318, 0)
        raise NotImplementedError

class FileTransferStateMachineTypeClass(FiniteStateMachineTypeClass):
    '''
    NOT IMPLEMENTED "FileTransferStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "FileTransferStateMachine"
        self._state_machine_type = ua.NodeId(15803, 0)
        raise NotImplementedError

class ProgramStateMachineTypeClass(FiniteStateMachineTypeClass):
    '''
    https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.3/
    Implementation of an ProgramStateMachine its quite a complex statemachine with the 
    optional possibility to make the statchange from clientside via opcua-methods
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "ProgramStateMachine"
        self._state_machine_type = ua.NodeId(2391, 0)
        self.evtype = ProgramTransitionEvent()

        # 5.2.3.2 ProgramStateMachineType states
        self._ready_state_node = None #State node
        self._halted_state_node = None #State node
        self._running_state_node = None #State node
        self._suspended_state_node = None #State node

        # 5.2.3.3 ProgramStateMachineType transitions
        self._halted_to_ready_node = None #Transition node
        self._ready_to_running_node = None #Transition node
        self._running_to_halted_node = None #Transition node
        self._running_to_ready_node = None #Transition node
        self._running_to_suspended_node = None #Transition node
        self._suspended_to_running_node = None #Transition node
        self._suspended_to_halted_node = None #Transition node
        self._suspended_to_ready_node = None #Transition node
        self._ready_to_halted_node = None #Transition node

        # 5.2.3.2 ProgramStateMachineType states
        self._halted_state_id_node = None #State property (StateNumber value 11)
        self._ready_state_id_node = None #State property (StateNumber value 12)
        self._running_state_id_node = None #State property (StateNumber value 13)
        self._suspended_state_id_node = None #State property (StateNumber value 14)

        # 5.2.3.3 ProgramStateMachineType transitions
        self._halted_to_ready_id_node = None #Transition property (TransitionNumber value 1)
        self._ready_to_running_id_node = None #Transition property (TransitionNumber value 2)
        self._running_to_halted_id_node = None #Transition property (TransitionNumber value 3)
        self._running_to_ready_id_node = None #Transition property (TransitionNumber value 4)
        self._running_to_suspended_id_node = None #Transition property (TransitionNumber value 5)
        self._suspended_to_running_id_node = None #Transition property (TransitionNumber value 6)
        self._suspended_to_halted_id_node = None #Transition property (TransitionNumber value 7)
        self._suspended_to_ready_id_node = None #Transition property (TransitionNumber value 8)
        self._ready_to_halted_id_node = None #Transition property (TransitionNumber value 9)

        # 4.2.7 Program Control Methods (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.7/)
        self._halt_method_node = None #uamethod node
        self._reset_method_node = None #uamethod node
        self._resume_method_node = None #uamethod node
        self._start_method_node = None #uamethod node
        self._suspend_method_node = None #uamethod node

        #can be overwritten if you want a different language
        self.localizedtext_ready = ua.LocalizedText("Ready", "en-US")
        self.localizedtext_running = ua.LocalizedText("Running", "en-US")
        self.localizedtext_halted = ua.LocalizedText("Halted", "en-US")
        self.localizedtext_suspended= ua.LocalizedText("Suspended", "en-US")
        self.localizedtext_halted_to_ready = ua.LocalizedText("HaltedToReady", "en-US")
        self.localizedtext_ready_to_running = ua.LocalizedText("ReadyToRunning", "en-US")
        self.localizedtext_running_to_halted = ua.LocalizedText("RunningToHalted", "en-US")
        self.localizedtext_running_to_ready = ua.LocalizedText("RunningToReady", "en-US")
        self.localizedtext_running_to_suspended = ua.LocalizedText("RunningToSuspended", "en-US")
        self.localizedtext_suspended_to_running = ua.LocalizedText("SuspendedToRunning", "en-US")
        self.localizedtext_suspended_to_halted = ua.LocalizedText("SuspendedToHalted", "en-US")
        self.localizedtext_suspended_to_ready = ua.LocalizedText("SuspendedToReady", "en-US")
        self.localizedtext_ready_to_halted = ua.LocalizedText("ReadyToHalted", "en-US")

    async def install(self, optionals=False):
        '''
        setup adressspace and initialize 
        '''
        self._optionals = optionals
        self._state_machine_node = await self._parent.add_object(
            self._idx, 
            self._name, 
            objecttype=self._state_machine_type, 
            instantiate_optional=optionals
            )
        #FIXME get children and map children

    #Transition
    async def HaltedToReady(self):
        await self._current_state.write_value(
            self.localizedtext_ready,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._ready_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_halted_to_ready,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._halted_to_ready.nodeid,
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def ReadyToRunning(self):
        await self._current_state.write_value(
            self.localizedtext_running,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._running_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_ready_to_running,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._ready_to_running.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def RunningToHalted(self):
        await self._current_state.write_value(
            self.localizedtext_halted,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._halted_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_running_to_halted,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._running_to_halted.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def RunningToReady(self):
        await self._current_state.write_value(
            self.localizedtext_ready,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._ready_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_running_to_ready,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._running_to_ready.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def RunningToSuspended(self):
        await self._current_state.write_value(
            self.localizedtext_suspended,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._suspended_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_running_to_suspended,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._running_to_suspended.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition 
    async def SuspendedToRunning(self):
        await self._current_state.write_value(
            self.localizedtext_running,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._running_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_suspended_to_running,
            varianttype=ua.VariantType.LocalizedText
            )
        await self._last_transition_id.write_value(
            self._suspended_to_running.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def SuspendedToHalted(self):
        await self._current_state.write_value(
            self.localizedtext_halted,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._halted_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_suspended_to_halted,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._suspended_to_halted.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition
    async def SuspendedToReady(self):
        await self._current_state.write_value(
            self.localizedtext_ready,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._ready_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_suspended_to_ready,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._suspended_to_ready.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #Transition 
    async def ReadyToHalted(self):
        await self._current_state.write_value(
            self.localizedtext_halted,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._current_state_id.write_value(
            self._halted_state.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        await self._last_transition.write_value(
            self.localizedtext_ready_to_halted,
            varianttype=ua.VariantType.LocalizedText
            ) 
        await self._last_transition_id.write_value(
            self._ready_to_halted.nodeid, 
            varianttype=ua.VariantType.NodeId
            )
        #FIXME 
        # trigger ProgramTransitionEventType and 
        # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
        return ua.StatusCode(ua.status_codes.StatusCodes.Good)

    #method to be linked to uamethod
    async def Start(self):
        if await self._current_state.read_value() == self.localizedtext_ready:
            return await ReadyToRunning()
        else:
            return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

    #method to be linked to uamethod
    async def Suspend(self):
        if await self._current_state.read_value() == self.localizedtext_running:
            return await RunningToSuspended()
        else:
            return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

    #method to be linked to uamethod
    async def Resume(self):
        if await self._current_state.read_value() == self.localizedtext_suspended:
            return await SuspendedToRunning()
        else:
            return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

    #method to be linked to uamethod
    async def Halt(self):
        if await self._current_state.read_value() == self.localizedtext_ready:
            return await ReadyToHalted()
        elif await self._current_state.read_value() == self.localizedtext_running:
            return await RunningToHalted()
        elif await self._current_state.read_value() == self.localizedtext_suspended:
            return await SuspendedToHalted()
        else:
            return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

    #method to be linked to uamethod
    async def Reset(self):
        if await self._current_state.read_value() == self.localizedtext_halted:
            return await HaltedToReady()
        else:
            return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

class ShelvedStateMachineTypeClass(FiniteStateMachineTypeClass):
    '''
    NOT IMPLEMENTED "ShelvedStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "ShelvedStateMachine"
        self._state_machine_type = ua.NodeId(2929, 0)
        raise NotImplementedError



#FIXME REMOVE BEFOR MERGE
#Devtest / Workbench
if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        _logger = logging.getLogger('asyncua')

        server = Server()
        await server.init()

        idx = await server.register_namespace("http://testnamespace.org/UA")

        mystatemachine = StateMachineTypeClass(server, server.nodes.objects, idx, "StateMachine")
        await mystatemachine.install(optionals=True)

        state1 = StateTypeClass("Idle")
        await mystatemachine.add_state(state1)
        state2 = StateTypeClass("Loading")
        await mystatemachine.add_state(state2)
        state3 = StateTypeClass("Initializing")
        await mystatemachine.add_state(state3)
        state4 = StateTypeClass("Processing")
        await mystatemachine.add_state(state4)
        state5 = StateTypeClass("Finished")
        await mystatemachine.add_state(state5)

        trans1 = TransitionTypeClass("to Idle")
        await mystatemachine.add_transition(trans1)
        trans2 = TransitionTypeClass("to Loading")
        await mystatemachine.add_transition(trans2)
        trans3 = TransitionTypeClass("to Initializing")
        await mystatemachine.add_transition(trans3)
        trans4 = TransitionTypeClass("to Processing")
        await mystatemachine.add_transition(trans4)
        trans5 = TransitionTypeClass("to Finished")
        await mystatemachine.add_transition(trans5)

        await mystatemachine.change_state(state1, trans1, f"{mystatemachine._name}: Idle", 300)


        async with server:
            while 1:
                await asyncio.sleep(2)
                await mystatemachine.change_state(state2, trans2, f"{mystatemachine._name}: Loading", 350)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state3, trans3, f"{mystatemachine._name}: Initializing", 400)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state4, trans4, f"{mystatemachine._name}: Processing", 600)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state5, trans5, f"{mystatemachine._name}: Finished", 800)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state1, trans1, f"{mystatemachine._name}: Idle", 500)

    asyncio.run(main())
