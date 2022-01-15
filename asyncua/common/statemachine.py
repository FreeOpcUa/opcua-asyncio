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
from asyncua.common.parameter_set import ParameterSet
from asyncua.common.event_objects import TransitionEvent, ProgramTransitionEvent
from typing import Union, List

_logger = logging.getLogger(__name__)

class State(object):
    '''
    Helperclass for States (StateVariableType)
    https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.3/
    name: type string will be converted automatically to qualifiedname 
        -> Name is a QualifiedName which uniquely identifies the current state within the StateMachineType.
    id: "BaseVariableType" Id is a name which uniquely identifies the current state within the StateMachineType. A subtype may restrict the DataType.
    number: Number is an integer which uniquely identifies the current state within the StateMachineType.
    '''
    def __init__(self, id, name: str=None, number: int=None, node: Node=None):
        if id is not None:
            self.id = ua.Variant(id)
        else:
            self.id = id #in this case it needs to be added with add_state which takes the nodeid returen from add_state
        self.name = name
        self.number = number
        self.effectivedisplayname = ua.LocalizedText(name, "en-US")
        self.node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml

    async def init(self): 
        nbr = await self.node.get_child('StateNumber')
        self.number = await nbr.read_value()
        self.name = (await self.node.read_browse_name()).Name
            
    async def on_entry(self): 
        _logger.debug(f'Entering the {self.name} state.')

    async def on_exit(self): 
        _logger.debug(f'Leaving the {self.name} state.')

    async def execute(self): 
        _logger.debug(f'Executing the {self.name} state.')

    def __eq__(self, __o: object) -> bool:
        return __o != None and  self.name == __o.name and self.number == __o.number

class Transition(object):
    '''
    Helperclass for Transitions (TransitionVariableType)
    https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.4/
    name: type string will be converted automatically to qualifiedname 
        -> Name is a QualifiedName which uniquely identifies a transition within the StateMachineType.
    id: "BaseVariableType" Id is a name which uniquely identifies a Transition within the StateMachineType. A subtype may restrict the DataType.
    number: Number is an integer which uniquely identifies the current state within the StateMachineType.
    transitiontime: TransitionTime specifies when the transition occurred.
    effectivetransitiontime: EffectiveTransitionTime specifies the time when the current state or one of its substates was entered. 
    If, for example, a StateA is active and – while active – switches several times between its substates SubA and SubB, 
    then the TransitionTime stays at the point in time where StateA became active whereas the EffectiveTransitionTime changes 
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
        self.node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml
        self.from_state: State = None 
        self.to_state: State = None 
        self.cause:Cause = None

    async def init(self): 
        nbr = await self.node.get_child('TransitionNumber')
        self.number = await nbr.read_value() 
        self.name = (await self.node.read_browse_name()).Name

    def check_transition(self, to_state): 
        return True if self.to_state == to_state else False 

    def __eq__(self, __o: object) -> bool:
        return self.name == __o.name and self.number == __o.number

class Cause: 
    def __init__(self, node, name, state_machine): 
        self.node = node 
        self.state_machine = state_machine
        self.name = name

    async def callback(self, parent):
        transition = self.state_machine.get_transition_by_cause(self)
        if transition: 
            from_state = transition.from_state
            to_state = transition.to_state
            _logger.debug(f'Transitioning from {from_state.name} to {to_state.name}. Caused by {self.name} ({self.node}).')
        
            msg = f'Event was triggered by invoking the {self.name} method'
            return await self.state_machine.change_state(transition.to_state, event_msg=msg)

        else: 
            _logger.error(f'Triggering transition by cause {self.name} ({self.node}) failed. InvalidState.')
            return ua.StatusCode(ua.StatusCodes.BadInvalidState)
            
    def __eq__(self, __o: object) -> bool:
        return __o != None and self.name == __o.name and self.node.nodeid == __o.node.nodeid

class StateMachine(object):
    '''
    Implementation of an StateMachineType (most basic type)
    CurrentState: Mandatory "StateVariableType"
    LastTransition: Optional "TransitionVariableType"
    Generates TransitionEvent's
    '''
    def __init__(self, server: Server=None, node: Node=None, parent: Node=None, idx: int=None, name: str=None):
        if not isinstance(server, Server): 
            raise ValueError(f"server: {type(server)} is not a instance of Server class")
        # if not isinstance(parent, Node): 
        #     raise ValueError(f"parent: {type(parent)} is not a instance of Node class")
    
        if parent and idx is None:
            idx = parent.nodeid.NamespaceIndex
        if node and idx is None: 
            idx = node.nodeid.NamespaceIndex
        if name is None:
            name = "StateMachine"
        self.locale = "en-US"
        self._server = server
        self._parent = parent
        self._state_machine_node = node
        self._state_machine_type = ua.NodeId(2299, 0) #StateMachineType
        self._name = name
        self._idx = idx
        self._optionals = False
        self._current_state_node = None
        self._current_state_id_node = None
        self._current_state_name_node = None
        self._current_state_number_node = None
        self._current_state_effective_display_name_node = None
        self._last_transition_node = None
        self._last_transition_id_node = None
        self._last_transition_name_node = None
        self._last_transition_number_node = None
        self._last_transition_transitiontime_node = None
        self._evgen = None
        self.evtype = TransitionEvent()
        self._current_state = State(None)

        self.states = []
        self.transitions = []
        self.causes = []
        
    async def install(self, optionals: bool=True):
        '''
        setup adressspace
        '''
        self._optionals = optionals
        if not self._state_machine_node and self._parent: 
            self._state_machine_node = await self._parent.add_object(
                self._idx, 
                self._name, 
                objecttype=self._state_machine_type, 
                instantiate_optional=optionals
                )

        elif self._state_machine_node:
            self.name = (await self._state_machine_node.read_browse_name()).Name
            self._state_machine_type = await self._state_machine_node.read_type_definition()
            type_node = self._server.get_node(self._state_machine_type)
            children = await type_node.get_children()
            await self._add_states(children)
            await self._add_transitions(children)

            children = await self._state_machine_node.get_children() 
            await self._add_methods(children)        
        else: 
            raise ValueError(f"""Failed to set up state machine {self._state_machine_node}. 
                    A parent node is needed to create a new state machine node. If the node already exists
                    in the server its node should be provided.""" ) 

        if self._optionals:
            self._last_transition_node = await self._state_machine_node.get_child(["LastTransition"])
            children = await self._last_transition_node.get_children()
            childnames = []
            for each in children:
                childnames.append((await each.read_browse_name()).Name)
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
                _logger.warning(f"{await statemachine.read_browse_name()} CurrentState Unknown propertie: {dn.Text}")
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
                    _logger.warning(f"{await statemachine.read_browse_name()} LastTransition Unknown propertie: {dn.Text}")
        self._evgen = await self._server.get_event_generator(self.evtype, self._state_machine_node)

    async def change_state(self, state: State, transition: Transition=None, event_msg:Union[str, ua.LocalizedText]=None, severity: int=500):
        '''
        Triggering a transition to change the state 

        Provide either a state or a transition to provide a target state information. 
        If an `event_msg` is passed, also the transition event will be triggered. 

        :param state: target state
        :param transition: transition to trigger 
        :param event_msg: "LocalizedText" optional
        :param severity: "Int" optional
        '''
        if not transition: 
            transition = self.get_transition(self._current_state, state) 

        if transition: 
            res = await self._current_state.on_exit() 
            if res != False: 
                _logger.debug(f"Transitioning from state {self._current_state.name} to state {transition.to_state.name}.")
                self._current_state = transition.to_state
                await self._write_state(transition.to_state)
                await self._write_transition(transition)

                if event_msg:
                    if isinstance(event_msg, str):
                        event_msg = ua.LocalizedText(event_msg, self.locale)
                    if not isinstance(event_msg, ua.LocalizedText):
                        raise ValueError(f"Statemachine: {self._name} -> event_msg: {event_msg} is not a instance of LocalizedText")
                    self._evgen.event.Message = event_msg
                    self._evgen.event.Severity = severity
                    self._evgen.event.ToState = ua.LocalizedText(state.name, self.locale)
                    if transition:
                        self._evgen.event.Transition = ua.LocalizedText(transition.name, self.locale)
                    self._evgen.event.FromState = ua.LocalizedText(self._current_state.name)
                    await self._evgen.trigger()
                
                await self._current_state.on_entry()
                return ua.StatusCode(ua.StatusCodes.Good)
            else: 
                return ua.StatusCode(ua.StatusCodes.BadUnexpectedError)

    def get_current_state(self): 
        return self._current_state

    def get_state_by_name(self, name: str): 
        for state in self.states: 
            if state.name == name: 
                return state 
    
    def get_transition_by_name(self, name: str): 
        for transition in self.transitions: 
            if transition.name == name: 
                return transition 
    
    def get_cause_by_name(self, name: str): 
        for cause in self.causes: 
            if cause.name == name: 
                return cause 
    
    def get_state_by_number(self, number: ua.Int32): 
        for state in self.states: 
            if state.number == number: 
                return state 
            
    def get_transition_by_number(self, number: ua.Int32): 
        for transition in self.transitions: 
            if transition.number == number: 
                return transition 
                        
    def get_state_by_id(self, id: ua.NodeId): 
        for state in self.states: 
            if state.id.Value == id: 
                return state 

    def get_transition_by_id(self, id: ua.NodeId): 
        for transition in self.transitions: 
            if transition.id.Value == id: 
                return transition

    def get_cause_by_id(self, id: ua.NodeId): 
        for cause in self.causes: 
            if cause.id == id: 
                return cause

    def get_transition_by_cause(self, cause: Cause): 
        for transition in self.transitions: 
            if transition.from_state ==self._current_state and transition.cause == cause: 
                return transition

    async def set_initial_state(self, state: State): 
        await self._write_state(state)
        self._current_state = state 
        pass

    def get_transition(self, from_state: State, to_state: State): 
        for transition in self.transitions:
            if transition.from_state.number == from_state.number \
                and transition.to_state.number == to_state.number: 
                return transition
        return None

    async def _add_states(self, children): 
        """
        Create an instance of each state in the type definition

        :param children: children of the state machine type node 
        """
        for child in children: 
            type_id = await child.read_type_definition()
            if type_id == ua.NodeId(ua.ObjectIds.StateType): 
                await self._add_state(child.nodeid)
            elif type_id == ua.NodeId(ua.ObjectIds.InitialStateType): 
                await self._add_state(child.nodeid)
                await self.change_state(self.get_state_by_id(child.nodeid))

    async def _add_transitions(self, children): 
        """
        Create an instance for each transition in the type defintion

        :param children: children of the state machine type node 
        """
        for child in children: 
            type_id = await child.read_type_definition()
            if type_id == ua.NodeId(ua.ObjectIds.TransitionType): 
                await self._add_transition(child.nodeid)

    async def _add_methods(self, children): 
        """
        Create an instance for each method (Cause) in the state machine instance node

        :param children: children of the state machine instance node
        """
        for child in children:  
            node_class = await child.read_node_class()
            if node_class == ua.NodeClass.Method:
                name = (await child.read_browse_name()).Name 
                cause = self.get_cause_by_name(name)
                self._server.link_method(child, cause.callback)
                
    async def _add_state(self, id): 
        """
        Create a new state object and add it to the state machine 

        :param id: node id of the state node
        """
        try: 
            node = self._server.get_node(id)
            state = State(id, node=node)
            name = (await node.read_browse_name()).Name
            await state.init()
            setattr(self, name, state)
            self.states.append(state)
            _logger.debug(f'Added state {name} to {self.name} ({self._state_machine_node})')

        except Exception as e: 
            _logger.warning(f'Failed to add state {name}. {e}')

    async def _add_transition(self, id):
        """
        Createing a new transition object and adding it to the state machine 

        :param id: node id of the transition node
        """

        node = self._server.get_node(id)
        name = (await node.read_browse_name()).Name
        transition = Transition(id, node=node)
        await transition.init()
        setattr(self, name, transition)
        self.transitions.append(transition)

        from_state = (await transition.node.get_referenced_nodes(refs=ua.ObjectIds.FromState))[0]
        to_state = (await transition.node.get_referenced_nodes(refs=ua.ObjectIds.ToState))[0]
        cause = await transition.node.get_referenced_nodes(refs=ua.ObjectIds.HasCause)
        transition.from_state = self.get_state_by_id(from_state.nodeid)
        transition.to_state = self.get_state_by_id(to_state.nodeid)  

        # Not all transitions have a cause reference 
        if cause: 
            await self._add_cause(cause[0], transition)
            _logger.debug(f'Added cause {self.causes[-1].name} to transition {name}.')

        _logger.debug(f'Added transition {name} to {self.name} ({self._state_machine_node}).')

 
    async def _add_cause(self, id: ua.NodeId, transition: Transition): 
        """
        Creating a new cause object and adding it to the transition and state machine 

        :param id: id of the method (cause) node 
        :param transition: the transition that is triggered by the method
        """
        node = self._server.get_node(id)
        name = (await node.read_browse_name()).Name
        cause = Cause(node, name, self)
        if cause in self.causes: 
            cause = self.causes[self.causes.index(cause)]
        else: 
            setattr(self, name, cause)
            self.causes.append(cause)
        self._server.link_method(node, cause.callback)
        transition.cause = cause

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
        if not state_type in [ua.NodeId(2309, 0),ua.NodeId(2307, 0),ua.NodeId(15109,0)]:
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
    def __init__(self, server: Server=None, node: Node=None, parent: Node=None, idx: int=None, name: str=None):
        super().__init__(server, node, parent, idx, name)
        if name is None:
            self._name = "FiniteStateMachine"
        self._state_machine_type = ua.NodeId(2771, 0)
        self._available_states_node = None
        self._available_transitions_node = None

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
    def __init__(self, server: Server=None, node:Node=None, parent: Node=None, idx: int=None, name: str=None):
        super().__init__(server, node, parent, idx, name)

        self.evtype = ProgramTransitionEvent() 

        self.Running: State = None 
        self.Ready: State = None 
        self.Halted: State = None 
        self.Suspended: State = None 

        self.ReadyToRunning: Transition = None 
        self.ReadyToHalted: Transition = None 
        self.RunningToReady: Transition = None 
        self.RunningToHalted: Transition = None 
        self.RunningToSuspended: Transition = None 
        self.SuspendedToReady: Transition = None 
        self.SuspendedToRunning: Transition = None 
        self.SuspendedToHalted: Transition = None 
        self.HaltedToReady: Transition = None

        self.Start: Cause = None 
        self.Suspend: Cause = None 
        self.Resume: Cause = None 
        self.Halt: Cause = None  

        self.FinalResultDataSet = None


    async def install(self): 
        await super().install()

        await self._add_parameter_set()

        self.Ready.on_entry = self.on_entry_ready
        self.Ready.on_exit = self.on_exit_ready
        #self.Ready.execute = self.execute_ready
        self.Running.on_entry = self.on_entry_running 
        self.Running.on_exit = self.on_exit_running
        #self.Running.execute = self.execute_running 
        self.Suspended.on_entry = self.on_entry_suspended
        self.Suspended.on_exit = self.on_exit_suspended 
        #self.Suspended.execute = self.execute_suspended
        self.Halted.on_entry = self.on_entry_halted 
        self.Halted.on_exit = self.on_exit_halted 
        #self.Halted.execute = self.execute_halted 
        
    async def _add_parameter_set(self): 
        try: 
            final_result_data_node = await self._state_machine_node.get_child(['FinalResultData'])
            if final_result_data_node: 
                self.FinalResultDataSet = ParameterSet(final_result_data_node, subscribe=True, source=self._server)
                await self.FinalResultDataSet.init()
        except Exception as e: 
            _logger.debug(f'ProgramStateMachine {self._state_machine_node} has nod FinalResultData set. {e}')

    async def on_entry_ready(self): 
        _logger.debug(f'Entering the Ready state of {self.name} ({self._state_machine_node}).')

    async def on_exit_ready(self): 
        _logger.debug(f'Leaving the Ready state of {self.name} ({self._state_machine_node}).')
    
    async def on_entry_running(self): 
        _logger.debug(f'Entering the Running state of {self.name} ({self._state_machine_node}).')

    async def on_exit_running(self):
       _logger.debug(f'Leaving the Running state of {self.name} ({self._state_machine_node}).')

    async def on_entry_suspended(self): 
       _logger.debug(f'Entering the Suspended state of {self.name} ({self._state_machine_node}).')

    async def on_exit_suspended(self): 
        _logger.debug(f'Leaving the Suspended state of {self.name} ({self._state_machine_node}).')
    
    async def on_entry_halted(self): 
        _logger.debug(f'Entering the Halted state of {self.name} ({self._state_machine_node}).')

    async def on_exit_halted(self): 
        _logger.debug(f'Leaving the Halted state of {self.name} ({self._state_machine_node}).')  

    async def start(self, msg=''): 
        return await self.change_state(self.Running, event_msg=msg)
    
    async def suspend(self, msg=''): 
        return await self.change_state(self.Suspended, event_msg=msg)

    async def resume(self, msg=''): 
        return await self.change_state(self.Running, event_msg=msg)
    
    async def halt(self, msg=''): 
        return await self.change_state(self.Halted, event_msg=msg)


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

