'''
https://reference.opcfoundation.org/v104/Core/docs/Part10/
https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.1/
Basic statemachines described in OPC UA Spec.:
StateMachineType
FiniteStateMachineType
ExclusiveLimitStateMachineType - not implemented
FileTransferStateMachineType - not implemented
ProgramStateMachineType - not implemented
ShelvedStateMachineType - not implemented
Relevant information:
Overview - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.3/#5.2.3.1
States - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.3/#5.2.3.2
Transitions - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.3/#5.2.3.3
Events - https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.5/
'''
import logging
import datetime

from asyncua import Server, ua, Node
from asyncua.common.event_objects import TransitionEvent, ProgramTransitionEvent
from typing import Optional, Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from asyncua.server.event_generator import EventGenerator

_logger = logging.getLogger(__name__)

class State:
    '''
    Helperclass for States (StateVariableType)
    https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.3/
    name: type string will be converted automatically to qualifiedname 
        -> Name is a QualifiedName which uniquely identifies the current state within the StateMachineType.
    id: "BaseVariableType" Id is a name which uniquely identifies the current state within the StateMachineType. A subtype may restrict the DataType.
    number: Number is an integer which uniquely identifies the current state within the StateMachineType.
    '''
    def __init__(self, id, name: str=None, number: int=None, node: Optional[Node]=None):
        if id is not None:
            self.id = ua.Variant(id)
        else:
            self.id = id #in this case it needs to be added with add_state which takes the nodeid returen from add_state
        self.name = name
        self.number = number
        self.effectivedisplayname = ua.LocalizedText(name, "en-US")
        self.node: Node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml


class Transition:
    '''
    Helper class for Transitions (TransitionVariableType)
    https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.4/
    name: type string will be converted automatically to qualifiedname 
        -> Name is a QualifiedName which uniquely identifies a transition within the StateMachineType.
    id: "BaseVariableType" Id is a name which uniquely identifies a Transition within the StateMachineType. A subtype may restrict the DataType.
    number: Number is an integer which uniquely identifies the current state within the StateMachineType.
    transitiontime: TransitionTime specifies when the transition occurred.
    effectivetransitiontime: EffectiveTransitionTime specifies the time when the current state or one of its substates was entered. 
    If, for example, a StateA is active and – while active – switches several times between its substates SubA and SubB, 
    then the TransitionTime stays at the point in time when StateA became active whereas the EffectiveTransitionTime changes
    with each change of a substate.
    '''
    def __init__(self, id, name: str=None, number: int=None, node: Node=None):
        if id is not None:
            self.id = ua.Variant(id)
        else:
            self.id = id #in this case it needs to be added with add_transition which takes the nodeid returen from add_transition
        self.name = name
        self.number = number
        self._transitiontime = datetime.datetime.utcnow() #will be overwritten from _write_transition()
        self.node: Node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml


class StateMachine(object):
    '''
    Implementation of an StateMachineType (most basic type)
    CurrentState: Mandatory "StateVariableType"
    LastTransition: Optional "TransitionVariableType"
    Generates TransitionEvent's
    '''
    def __init__(self, server: Server=None, parent: Node=None, idx: int=None, name: str=None):
        if not isinstance(server, Server): 
            raise ValueError(f"server: {type(server)} is not a instance of Server class")
        if not isinstance(parent, Node): 
            raise ValueError(f"parent: {type(parent)} is not a instance of Node class")
        if idx is None:
            idx = parent.nodeid.NamespaceIndex
        if name is None:
            name = "StateMachine"
        self.locale = "en-US"
        self._server = server
        self._parent = parent
        self._state_machine_node: Node = None
        self._state_machine_type = ua.NodeId(2299, 0) #StateMachineType
        self._name = name
        self._idx = idx
        self._optionals = False
        self._current_state_node: Node = None
        self._current_state_id_node = None
        self._current_state_name_node = None
        self._current_state_number_node = None
        self._current_state_effective_display_name_node = None
        self._last_transition_node: Node = None
        self._last_transition_id_node = None
        self._last_transition_name_node = None
        self._last_transition_number_node = None
        self._last_transition_transitiontime_node = None
        self._evgen: EventGenerator = None
        self.evtype = TransitionEvent()
        self._current_state = State(None)

    async def install(self, optionals: bool=False):
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
        if self._optionals:
            self._last_transition_node = await self._state_machine_node.get_child(["LastTransition"])
            children = await self._last_transition_node.get_children()
            childnames = []
            for each in children:
                childnames.append(await each.read_browse_name())
            if "TransitionTime" not in childnames:
                self._last_transition_transitiontime_node = await self._last_transition_node.add_property(
                    0, 
                    "TransitionTime", 
                    ua.Variant(datetime.datetime.utcnow(), VariantType=ua.VariantType.DateTime)
                    )
            else:
                self._last_transition_transitiontime_node = await self._last_transition_node.get_child("TransitionTime")
        await self.init(self._state_machine_node)
    
    async def init(self, statemachine: Node):
        '''
        initialize and get subnodes
        '''
        self._current_state_node = await statemachine.get_child(["CurrentState"])
        current_state_props = await self._current_state_node.get_properties()
        for prop in current_state_props:
            dn = await prop.read_display_name()
            if dn.Text == "Id":
                self._current_state_id_node = await self._current_state_node.get_child(["Id"])
            elif dn.Text == "Name":
                self._current_state_name_node = await self._current_state_node.get_child(["Name"])
            elif dn.Text == "Number":
                self._current_state_number_node = await self._current_state_node.get_child(["Number"])
            elif dn.Text == "EffectiveDisplayName":
                self._current_state_effective_display_name_node = await self._current_state_node.get_child(["EffectiveDisplayName"])
            else:
                _logger.warning(f"{await statemachine.read_browse_name()} CurrentState Unknown property: {dn.Text}")
        if self._optionals:
            self._last_transition_node = await statemachine.get_child(["LastTransition"])
            last_transition_props = await self._last_transition_node.get_properties()
            for prop in last_transition_props:
                dn = await prop.read_display_name()
                if dn.Text == "Id":
                    self._last_transition_id_node = await self._last_transition_node.get_child(["Id"])
                elif dn.Text == "Name":
                    self._last_transition_name_node = await self._last_transition_node.get_child(["Name"])
                elif dn.Text == "Number":
                    self._last_transition_number_node = await self._last_transition_node.get_child(["Number"])
                elif dn.Text == "TransitionTime":
                    self._last_transition_transitiontime_node = await self._last_transition_node.get_child(["TransitionTime"])
                else:
                    _logger.warning(f"{await statemachine.read_browse_name()} LastTransition Unknown property: {dn.Text}")
        self._evgen = await self._server.get_event_generator(self.evtype, self._state_machine_node)

    async def change_state(self, state: State, transition: Transition=None, event_msg:Union[str, ua.LocalizedText]=None, severity: int=500):
        '''
        method to change the state of the statemachine
        state: "State" mandatory
        transition: "Transition" optional
        event_msg: "LocalizedText" optional
        severity: "Int" optional
        '''
        await self._write_state(state)
        if transition:
            await self._write_transition(transition)
        if event_msg:
            if isinstance(event_msg, str):
                event_msg = ua.LocalizedText(event_msg, self.locale)
            if not isinstance(event_msg, ua.LocalizedText):
                raise ValueError(f"Statemachine: {self._name} -> event_msg: {event_msg} is not a instance of LocalizedText")
            self._evgen.event.Message = event_msg  # type: ignore
            self._evgen.event.Severity = severity  # type: ignore
            self._evgen.event.ToState = ua.LocalizedText(state.name, self.locale)  # type: ignore
            if transition:
                self._evgen.event.Transition = ua.LocalizedText(transition.name, self.locale)  # type: ignore
            self._evgen.event.FromState = ua.LocalizedText(self._current_state.name)  # type: ignore
            await self._evgen.trigger()
        self._current_state = state

    async def _write_state(self, state: State):
        if not isinstance(state, State):
            raise ValueError(f"Statemachine: {self._name} -> state: {state} is not a instance of StateMachine.State class")
        await self._current_state_node.write_value(ua.LocalizedText(state.name, self.locale), ua.VariantType.LocalizedText)
        if state.node:
            if self._current_state_id_node:
                await self._current_state_id_node.write_value(state.node.nodeid, varianttype=ua.VariantType.NodeId)
            if self._current_state_name_node and state.name:
                await self._current_state_name_node.write_value(state.name, ua.VariantType.QualifiedName)
            if self._current_state_number_node and state.number:
                await self._current_state_number_node.write_value(state.number, ua.VariantType.UInt32)
            if self._current_state_effective_display_name_node and state.effectivedisplayname:
                await self._current_state_effective_display_name_node.write_value(state.effectivedisplayname, ua.VariantType.LocalizedText)

    async def _write_transition(self, transition: Transition):
        '''
        transition: Transition
        issub: boolean (true if it is a transition between substates)
        '''
        if not isinstance(transition, Transition):
            raise ValueError(f"Statemachine: {self._name} -> state: {transition} is not a instance of StateMachine.Transition class")
        transition._transitiontime = datetime.datetime.utcnow()
        await self._last_transition_node.write_value(ua.LocalizedText(transition.name, self.locale), ua.VariantType.LocalizedText)
        if self._optionals:
            if self._last_transition_id_node:
                await self._last_transition_id_node.write_value(transition.node.nodeid, varianttype=ua.VariantType.NodeId)
            if self._last_transition_name_node and transition.name:
                await self._last_transition_name_node.write_value(ua.QualifiedName(transition.name, self._idx), ua.VariantType.QualifiedName)
            if self._last_transition_number_node and transition.number:
                await self._last_transition_number_node.write_value(transition.number, ua.VariantType.UInt32)
            if self._last_transition_transitiontime_node and transition._transitiontime:
                await self._last_transition_transitiontime_node.write_value(transition._transitiontime, ua.VariantType.DateTime)
            
    async def add_state(self, state: State, state_type: ua.NodeId=ua.NodeId(2307, 0), optionals: bool=False):
        '''
        this method adds a state object to the statemachines address space
        state: State,
        InitialStateType: ua.NodeId(2309, 0),
        StateType: ua.NodeId(2307, 0),
        ChoiceStateType: ua.NodeId(15109,0),
        '''
        if not isinstance(state, State):
            raise ValueError(f"Statemachine: {self._name} -> state: {state} is not a instance of StateMachine.State class")
        if state_type not in [ua.NodeId(2309, 0), ua.NodeId(2307, 0), ua.NodeId(15109, 0)]:
            # unknown state type!
            raise ValueError(f"Statemachine: {self._name} -> state_type: {state_type} is not in list: [ua.NodeId(2309, 0),ua.NodeId(2307, 0),ua.NodeId(15109,0)]")
        if not state.name:
            raise ValueError(f"Statemachine: {self._name} -> State.name is None")
        if not state.number:
            raise ValueError(f"Statemachine: {self._name} -> State.number is None")
        state.node = await self._state_machine_node.add_object(
            self._idx, 
            state.name, 
            objecttype=state_type, 
            instantiate_optional=optionals
            )
        state_number = await state.node.get_child(["StateNumber"])
        await state_number.write_value(state.number, ua.VariantType.UInt32)
        if not state.id:
            state.id = state.node.nodeid
        return state.node

    async def add_transition(self, transition: Transition, transition_type: ua.NodeId=ua.NodeId(2310, 0), optionals: bool=False):
        '''
        this method adds a transition object to the statemachines address space
        transition: Transition,
        transition_type: ua.NodeId(2310, 0),
        '''
        if not isinstance(transition, Transition):
            raise ValueError(f"Statemachine: {self._name} -> state: {transition} is not a instance of StateMachine.Transition class")
        transition.node = await self._state_machine_node.add_object(
            self._idx, 
            transition.name, 
            objecttype=transition_type, 
            instantiate_optional=optionals
            )
        transition_number = await transition.node.get_child(["TransitionNumber"])
        await transition_number.write_value(transition.number, ua.VariantType.UInt32)
        if not transition.id:
            transition.id = transition.node.nodeid
        return transition.node


class FiniteStateMachine(StateMachine):
    '''
    Implementation of an FiniteStateMachineType a little more advanced than the basic one
    if you need to know the available states and transition from clientside
    '''
    def __init__(self, server: Server=None, parent: Node=None, idx: int=None, name: str=None):
        super().__init__(server, parent, idx, name)
        if name is None:
            self._name = "FiniteStateMachine"
        self._state_machine_type = ua.NodeId(2771, 0)
        self._available_states_node: Node = None
        self._available_transitions_node: Node = None

    async def set_available_states(self, states: List[ua.NodeId]):
        if not self._available_states_node:
            self._available_states_node = await self._state_machine_node.get_child(["AvailableStates"])
        if isinstance(states, list) and all(isinstance(state, ua.NodeId) for state in states):
            return await self._available_states_node.write_value(states, varianttype=ua.VariantType.NodeId)
        return ValueError(f"Statemachine: {self._name} -> states: {states} is not a list")

    async def set_available_transitions(self, transitions: List[ua.NodeId]):
        if self._optionals:
            if not self._available_transitions_node:
                self._available_transitions_node = await self._state_machine_node.get_child(["AvailableTransitions"])
            if isinstance(transitions, list) and all(isinstance(transition, ua.NodeId) for transition in transitions):
                return await self._available_transitions_node.write_value(transitions, varianttype=ua.VariantType.NodeId)
            return ValueError(f"Statemachine: {self._name} -> transitions: {transitions} is not a list")


class ExclusiveLimitStateMachine(FiniteStateMachine):
    '''
    NOT IMPLEMENTED "ExclusiveLimitStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name is None:
            name = "ExclusiveLimitStateMachine"
        self._state_machine_type = ua.NodeId(9318, 0)
        raise NotImplementedError


class FileTransferStateMachine(FiniteStateMachine):
    '''
    NOT IMPLEMENTED "FileTransferStateMachineType"
    https://reference.opcfoundation.org/v104/Core/ObjectTypes/FileTransferStateMachineType/
    https://reference.opcfoundation.org/v104/Core/docs/Part5/C.4.6/
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name is None:
            name = "FileTransferStateMachine"
        self._state_machine_type = ua.NodeId(15803, 0)
        raise NotImplementedError


class ProgramStateMachine(FiniteStateMachine):
    '''
    https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.3/
    Implementation of an ProgramStateMachine its quite a complex statemachine with the 
    optional possibility to make the statchange from clientside via opcua-methods
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name is None:
            name = "ProgramStateMachine"
        self._state_machine_type = ua.NodeId(2391, 0)
        self.evtype = ProgramTransitionEvent()
        raise NotImplementedError
        

class ShelvedStateMachine(FiniteStateMachine):
    '''
    NOT IMPLEMENTED "ShelvedStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name is None:
            name = "ShelvedStateMachine"
        self._state_machine_type = ua.NodeId(2929, 0)
        raise NotImplementedError

