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
import asyncio, logging, datetime

#FIXME 
# -change to relativ imports!
# -remove unused imports
from asyncua import Server, ua, Node
from asyncua.common.event_objects import TransitionEvent, ProgramTransitionEvent

_logger = logging.getLogger(__name__)

class StateMachineTypeClass(object):
    '''
    Implementation of an StateMachineType (most basic type)
    CurrentState: Mandatory "StateVariableType"
    LastTransition: Optional "TransitionVariableType"
    Generates TransitionEvent's
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
        self._current_state_name_node = None
        self._current_state_number_node = None
        self._last_transition_node = None
        self._last_transition_id_node = None
        self._last_transition_name_node = None
        self._last_transition_number_node = None
        self._last_transition_transitiontime_node = None
        self._last_transition_effectivetransitiontime_node = None
        self._evgen = None
        self.evtype = TransitionEvent()

    class State(object):
        '''
        Helperclass for States (StateVariableType)
        https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.3/
        name: type string will be converted automatically to qualifiedname 
            -> Name is a QualifiedName which uniquely identifies the current state within the StateMachineType.
        id: Id is a name which uniquely identifies the current state within the StateMachineType. A subtype may restrict the DataType.
        number: Number is an integer which uniquely identifies the current state within the StateMachineType.
        '''
        def __init__(self, name, id=0, node=None, issub=False):
            self.name = name
            self.id = str(id)
            self.number = id
            self.node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml
            self.issub = issub #true if it is a substate

    class Transition(object):
        '''
        Helperclass for Transitions (TransitionVariableType)
        https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.4/
        name: type string will be converted automatically to qualifiedname 
            -> Name is a QualifiedName which uniquely identifies a transition within the StateMachineType.
        id: Id is a name which uniquely identifies a Transition within the StateMachineType. A subtype may restrict the DataType.
        number: Number is an integer which uniquely identifies the current state within the StateMachineType.
        transitiontime: TransitionTime specifies when the transition occurred.
        effectivetransitiontime: EffectiveTransitionTime specifies the time when the current state or one of its substates was entered. 
        If, for example, a StateA is active and – while active – switches several times between its substates SubA and SubB, 
        then the TransitionTime stays at the point in time where StateA became active whereas the EffectiveTransitionTime changes 
        with each change of a substate.
        '''
        def __init__(self, name, id=0, node=None, issub=False):
            self.name = name
            self.id = str(id)
            self.number = id
            self._transitiontime = datetime.datetime.utcnow() #will be overwritten from _write_transition()
            self._effectivetransitiontime = datetime.datetime.utcnow() #will be overwritten from _write_transition()
            self.node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml
            self.issub = issub #true if it is a transition between substates

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
        initialize and get subnodes
        '''
        self._current_state_node = await statemachine.get_child(["CurrentState"])
        current_state_props = await self._current_state_node.get_properties()
        for prop in current_state_props:
            dn = await prop.read_display_name()
            if dn.Text == "Id":
                self._current_state_id_node = await statemachine.get_child(["CurrentState","Id"])
            elif dn.Text == "Name":
                self._current_state_name_node = await statemachine.get_child(["CurrentState","Name"])
            elif dn.Text == "Number":
                self._current_state_number_node = await statemachine.get_child(["CurrentState","Number"])
            else:
                _logger.warning(f"{statemachine._name} CurrentState Unknown propertie: {dn.Text}")
        if self._optionals:
            self._last_transition_node = await statemachine.get_child(["LastTransition"])
            last_transition_props = await self._last_transition_node.get_properties()
            for prop in last_transition_props:
                dn = await prop.read_display_name()
                if dn.Text == "Id":
                    self._last_transition_id_node = await statemachine.get_child(["LastTransition", "Id"])
                elif dn.Text == "Name":
                    self._last_transition_name_node = await statemachine.get_child(["LastTransition", "Name"])
                elif dn.Text == "Number":
                    self._last_transition_number_node = await statemachine.get_child(["LastTransition", "Number"])
                elif dn.Text == "TransitionTime":
                    self._last_transition_transitiontime_node = await statemachine.get_child(["LastTransition", "TransitionTime"])
                elif dn.Text == "EffectiveTransitionTime":
                    self._last_transition_effectivetransitiontime_node = await statemachine.get_child(["LastTransition", "EffectiveTransitionTime"])
                else:
                    _logger.warning(f"{statemachine._name} LastTransition Unknown propertie: {dn.Text}")
        self._evgen = await self._server.get_event_generator(self.evtype, self._state_machine_node)

    async def change_state(self, state, transition=None, event_msg=None, severity=500):
        '''
        method to change the state of the statemachine
        state: "self.State" mandatory
        transition: "self.Transition" optional
        event_msg: "string/LocalizedText" optional
        severity: "Int" optional
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
        if not isinstance(state, self.State):
            raise ValueError
        await self._current_state_node.write_value(ua.LocalizedText(state.name, self.locale), ua.VariantType.LocalizedText)
        if state.node:
            if self._current_state_id_node:
                await self._current_state_id_node.write_value(state.node.nodeid, ua.VariantType.NodeId)
            if self._current_state_name_node:
                await self._current_state_name_node.write_value(state.name, ua.VariantType.QualifiedName)
            if self._current_state_number_node:
                await self._current_state_number_node.write_value(state.number, ua.VariantType.UInt32)

    async def _write_transition(self, transition):
        '''
        transition: self.Transition
        issub: boolean (true if it is a transition between substates)
        '''
        if not isinstance(transition, self.Transition):
            raise ValueError
        if transition.issub == False:
            transition._transitiontime = datetime.datetime.utcnow()
        transition._effectivetransitiontime = datetime.datetime.utcnow()
        await self._last_transition_node.write_value(ua.LocalizedText(transition.name, self.locale), ua.VariantType.LocalizedText)
        if transition.node:
            if self._last_transition_id_node:
                await self._last_transition_id_node.write_value(transition.node.nodeid, ua.VariantType.NodeId)
            if self._last_transition_name_node:
                await self._last_transition_name_node.write_value(ua.QualifiedName(transition.name, self._idx), ua.VariantType.QualifiedName)
            if self._last_transition_number_node:
                await self._last_transition_number_node.write_value(transition.number, ua.VariantType.UInt32)
            if self._last_transition_transitiontime_node:
                await self._last_transition_transitiontime_node.write_value(transition._transitiontime, ua.VariantType.DateTime)
            if self._last_transition_effectivetransitiontime_node:
                await self._last_transition_effectivetransitiontime_node.write_value(transition._effectivetransitiontime, ua.VariantType.DateTime)
            
    async def add_state(self, state, state_type=ua.NodeId(2307, 0), optionals=False):
        '''
        this method adds a state object to the statemachines address space
        state: self.State,
        InitialStateType: ua.NodeId(2309, 0),
        StateType: ua.NodeId(2307, 0),
        ChoiceStateType: ua.NodeId(15109,0),
        '''
        if not isinstance(state, self.State):
            raise ValueError
        state.node = await self._state_machine_node.add_object(
            self._idx, 
            state.name, 
            objecttype=state_type, 
            instantiate_optional=optionals
            )
        state_number = await state.node.get_child(["StateNumber"])
        await state_number.write_value(state.number, ua.VariantType.UInt32)
        return state.node

    async def add_transition(self, transition, transition_type=ua.NodeId(2310, 0), optionals=False):
        '''
        this method adds a transition object to the statemachines address space
        transition: self.Transition,
        transition_type: ua.NodeId(2310, 0),
        '''
        if not isinstance(transition, self.Transition):
            raise ValueError
        transition.node = await self._state_machine_node.add_object(
            self._idx, 
            transition.name, 
            objecttype=transition_type, 
            instantiate_optional=optionals
            )
        transition_number = await transition.node.get_child(["TransitionNumber"])
        await transition_number.write_value(transition.number, ua.VariantType.UInt32)
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

        state1 = mystatemachine.State("Idle", 1)
        await mystatemachine.add_state(state1)
        state2 = mystatemachine.State("Loading", 2)
        await mystatemachine.add_state(state2)
        state3 = mystatemachine.State("Initializing", 3)
        await mystatemachine.add_state(state3)
        state4 = mystatemachine.State("Processing", 4)
        await mystatemachine.add_state(state4)
        state5 = mystatemachine.State("Finished", 5)
        await mystatemachine.add_state(state5)

        trans1 = mystatemachine.Transition("to Idle", 1)
        await mystatemachine.add_transition(trans1)
        trans2 = mystatemachine.Transition("to Loading", 2)
        await mystatemachine.add_transition(trans2)
        trans3 = mystatemachine.Transition("to Initializing", 3)
        await mystatemachine.add_transition(trans3)
        trans4 = mystatemachine.Transition("to Processing", 4)
        await mystatemachine.add_transition(trans4)
        trans5 = mystatemachine.Transition("to Finished", 5)
        await mystatemachine.add_transition(trans5)

        await mystatemachine.change_state(state1, trans1, f"{mystatemachine._name}: Idle", 300)

        mystatemachine2 = StateMachineTypeClass(server, server.nodes.objects, idx, "StateMachine2")
        await mystatemachine2.install(optionals=False)
        sm2state1 = mystatemachine2.State("Idle", 1)
        await mystatemachine2.add_state(sm2state1)
        await mystatemachine2.change_state(sm2state1)

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
