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
from asyncua.common.instantiate_util import instantiate
from asyncua.common.event_objects import TransitionEvent

_logger = logging.getLogger(__name__)

class StateMachineTypeClass(object):
    '''
    Implementation of an StateMachineType (most basic type)
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        if not isinstance(server, Server): 
            raise f"server={server} is not a instance of Server"
        if not isinstance(parent, Node): 
            raise f"parent={parent} is not a instance of Node"
        if idx == None:
            _logger.warning("StateMachineTypeClass -> idx = None")
            idx = parent.nodeid.NamespaceIndex
        if name == None:
            _logger.warning("StateMachineTypeClass -> Name = None")
            name = "StateMachine"
        self._server = server
        self._parent = parent
        self._state_machine_node = None
        self._state_machine_type = ua.NodeId(2299, 0)
        self._name = name
        self._idx = idx
        self._optionals = False
        self._current_state_node = None
        self._current_state_id_node = None
        self._last_transition_node = None
        self._last_transition_id_node = None
        self._evgen = None

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

    async def change_state(self, state_name, state_node, transition_name=None, transition_node=None):
        '''
        method to change the state of the statemachine
        state_name: ua.LocalizedText()
        state: ua.NodeId() <- StateType node
        transition_name: ua.LocalizedText()
        transition: ua.NodeId() <- TransitionType node
        '''
        #FIXME check StateType exist
        #FIXME check TransitionTypeType exist
        await self.write_state(state_name, state_node)
        if self._optionals and transition_name and transition_node:
            await self.write_transition(transition_name, transition_node)
        self._evgen = await self._server.get_event_generator(TransitionEvent(), self._state_machine_node)
        self._evgen.event.Message = ua.LocalizedText(f"{self._name}: statechange to {state_name.Text}", "en-US")
        self._evgen.event.Severity = 500
        await self._evgen.trigger()

    async def write_state(self, state_name, state_node):
        #FIXME check types/class
        await self._current_state_node.write_value(state_name)
        await self._current_state_id_node.write_value(state_node)

    async def write_transition(self, transition_name, transition_node):
        #FIXME check types/class
        await self._last_transition_node.write_value(transition_name)
        await self._last_transition_id_node.write_value(transition_node)
    
    async def add_state(self, name, state_type=ua.NodeId(2307, 0), optionals=False):
        '''
        InitialStateType: ua.NodeId(2309, 0)
        StateType: ua.NodeId(2307, 0)
        ChoiceStateType: ua.NodeId(15109,0)
        '''
        #FIXME check types/class
        return await self._state_machine_node.add_object(
            self._idx, 
            name, 
            objecttype=state_type, 
            instantiate_optional=optionals
            )

    async def add_transition(self, name, transition_type=ua.NodeId(2310, 0), optionals=False):
        #FIXME check types/class
        return await self._state_machine_node.add_object(
            self._idx, 
            name, 
            objecttype=transition_type, 
            instantiate_optional=optionals
            )

    # async def remove(self):
    #     #FIXME
    #     raise NotImplementedError

    # async def add_substate(self):
    #     #FIXME
    #     raise NotImplementedError

    # async def add_subtransition(self):
    #     #FIXME
    #     raise NotImplementedError

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

        sm = StateMachineTypeClass(server, server.nodes.objects, 0, "StateMachine")
        await sm.install(True)
        init = await sm.add_state("Initstate", ua.NodeId(2309, 0))
        st1 = await sm.add_state("State1")
        st2 = await sm.add_state("State2")
        st3 = await sm.add_state("State3")
        st4 = await sm.add_state("State4")
        tr1 = await sm.add_transition("Transition1")
        tr2 = await sm.add_transition("Transition2")
        tr3 = await sm.add_transition("Transition3")
        tr4 = await sm.add_transition("Transition4")
        tr5 = await sm.add_transition("Transition5")

        await sm.change_state(
            ua.LocalizedText("Initstate", "en-US"), 
            init.nodeid,
            ua.LocalizedText("Transition1", "en-US"), 
            tr1.nodeid
            )

        # fsm = FiniteStateMachineTypeClass(server, server.nodes.objects, 0, "FiniteStateMachine")
        # await fsm.install(True)
        # pfsm = ProgramStateMachineTypeClass(server, server.nodes.objects, 0, "ProgramStateMachine")
        # await pfsm.install(True)

        async with server:
            while 1:
                await asyncio.sleep(10)
                await sm.change_state(
                    ua.LocalizedText("State2", "en-US"), 
                    st1.nodeid,
                    ua.LocalizedText("Transition2", "en-US"), 
                    tr2.nodeid
                )
                await asyncio.sleep(10)
                await sm.change_state(
                    ua.LocalizedText("State3", "en-US"), 
                    st2.nodeid,
                    ua.LocalizedText("Transition3", "en-US"), 
                    tr3.nodeid
                    )

    asyncio.run(main())
