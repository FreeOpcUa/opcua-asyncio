import asyncio
from copy import copy

import logging
from weakref import ReferenceType 
from typing import Union
from asyncua import ua, Server, Node
from asyncua.common.statemachine import StateMachine
from asyncua.ua.object_ids import ObjectIds
from asyncua.common.event_objects import ProgramTransitionEvent
import asyncua.common.statemachine as sm 

import datetime
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
        return self.name == __o.name and self.number == __o.number

class Cause: 
    def __init__(self, node, name, state_machine, transition): 
        self.node = node 
        self.state_machine = state_machine
        self.name = name

    async def callback(self, parent):
        transition = self.state_machine.get_transition_by_cause(self)
        if transition: 
            from_state = transition.from_state
            to_state = transition.to_state
            _logger.debug(f'Transitioning from {from_state.name} to {to_state.name}. Caused by {self.name} ({self.node}).')
        return await self.state_machine.change_state(transition=transition)

    def __eq__(self, __o: object) -> bool:
        return self.name == __o.name and self.node.nodeid == __o.node.nodeid

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
        self.from_state = None 
        self.to_state = None 
        self.cause = None

    async def init(self): 
        nbr = await self.node.get_child('TransitionNumber')
        self.number = await nbr.read_value() 
        self.name = (await self.node.read_browse_name()).Name

    def check_transition(self, to_state): 
        return True if self.to_state == to_state else False 

    def __eq__(self, __o: object) -> bool:
        return self.name == __o.name and self.number == __o.number

class FiniteStateMachine(StateMachine):
    '''
    Implementation of an FiniteStateMachineType a little more advanced than the basic one
    if you need to know the available states and transition from clientside
    '''
    def __init__(self, server: Server=None, node:Node=None, parent: Node=None, idx: int=None, name: str=None):
        super().__init__(server, parent, idx, name)
        if name is None:
            self._name = "FiniteStateMachine"
        self._state_machine_node = node
        self._state_machine_type = ua.NodeId(2771, 0)
        self._available_states_node = None
        self._available_transitions_node = None
        self._current_state = State(None)
        self._state_machine_base_type = None
        self.states = []
        self.transitions = []
        self.causes = []

        self._optionals = True 

    async def install(self): 
        self.name = (await self._state_machine_node.read_browse_name()).Name
        self._state_machine_type = await self._state_machine_node.read_type_definition()
        type_node = self._server.get_node(self._state_machine_type)
        children = await type_node.get_children()
        await self._add_states(children)
        await self._add_transitions(children)

        children = await self._state_machine_node.get_children() 
        await self._add_methods(children)
    
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
            print(transition.name, cause.name)
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

    async def change_state(self, state: State=None, transition: Transition=None, event_msg:Union[str, ua.LocalizedText]=None, severity: int=500):
        if not transition and state: 
            transition = self.get_transition(self._current_state, state) 
        elif not state and transition: 
            transition = self.get_transition(self._current_state, transition.to_state)

        if transition:  
            res = await self._current_state.on_exit()
            if res != False: 
                logging.info(f"Transitioning from state {self._current_state.name} to state {transition.to_state.name}.")
                await super().change_state(transition.to_state, transition=transition, event_msg=event_msg, severity=severity)
                await self._current_state.on_entry()
                return ua.StatusCode(ua.StatusCodes.Good)
            else: 
                return ua.StatusCode(ua.StatusCodes.BadUnexpectedError)
        else: 
            logging.error(f"Transition in state {self._current_state.name} failed. InvalidState.")
            return ua.StatusCode(ua.StatusCodes.BadInvalidState)

    async def _write_state(self, state: State):
      #  if not isinstance(state, State):
      #      raise ValueError(f"Statemachine: {self._name} -> state: {state} is not a instance of StateMachine.State class")
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
        #if not isinstance(transition, Transition):
        #    raise ValueError(f"Statemachine: {self._name} -> state: {transition} is not a instance of StateMachine.Transition class")
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
            
    async def _add_states(self, children): 
        for child in children: 
            type_id = await child.read_type_definition()
            if type_id == ua.NodeId(ua.ObjectIds.StateType): 
                await self._add_state(child.nodeid)
            elif type_id == ua.NodeId(ua.ObjectIds.InitialStateType): 
                await self._add_state(child.nodeid)
                await self.change_state(self.get_state_by_id(child.nodeid))

    async def _add_transitions(self, children): 
        for child in children: 
            type_id = await child.read_type_definition()
            if type_id == ua.NodeId(ua.ObjectIds.TransitionType): 
                await self._add_transition(child.nodeid)

    async def _add_methods(self, children): 
        for child in children: 
            node_class = await child.read_node_class()
            if node_class == ua.NodeClass.Method:
                name = (await child.read_browse_name()).Name 
                cause = self.get_cause_by_name(name)
                self._server.link_method(child, cause.callback)
                
    async def _add_state(self, id): 
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
        try: 
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
    
            _logger.debug(f'Added transition {name} to {self.name} ({self._state_machine_node})')

        except Exception as e: 
            _logger.warning(f'Failed to add transition {name}. {e}')

    async def _add_cause(self, id, transition): 
        node = self._server.get_node(id)
        name = (await node.read_browse_name()).Name
        cause = Cause(node, name, self, transition)
        if cause in self.causes: 
            cause = self.causes[self.causes.index(cause)]
        else: 
            setattr(self, name, cause)
            self.causes.append(cause)
        self._server.link_method(node, cause.callback)
        transition.cause = cause

class ProgramStateMachine(FiniteStateMachine): 
    def __init__(self, server: Server=None, node:Node=None, parent: Node=None, idx: int=None, name: str=None):
        super().__init__(server, node, parent, idx, name)

        self.Running: State = None 
        self.Ready: State = None 
        self.Halted: State = None 
        self.Suspended: State = None 

    async def install(self): 
        await super().install()

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

class ExampleStateMachin(ProgramStateMachine): 
    def __init__(self, server: Server, node: Node, parent: Node, max=3): 
        super().__init__(server, node, parent)
        self._running = False 
        self._task_running: asyncio.Task = None
        self._index = 0
        self._max = max

    async def on_entry_ready(self):
        self._index = 0 

    async def execute_running(self): 
        while self._running and self._index < self._max: 
            self._index+=1
            print(f'Executing the Running state {self._index}/{self._max}')
            await asyncio.sleep(1)
        
        if self._index == self._max: 
            await self.change_state(self.Ready)

    async def on_entry_running(self): 
        print('\nEntered the running state\n')
        self._running = True 
        self._task_running = asyncio.create_task(self.execute_running())

    async def on_exit_running(self): 
        print('\nLeaving the running state\n')
        self._running = False 


async def main(): 
    server = Server()
    logging.basicConfig(level=logging.DEBUG)
    al = logging.getLogger('asyncua')
    al.setLevel(logging.ERROR)
    await server.init()
    await server.import_xml('StateMachine.Example.NodeSet2.xml')
    idx = await server.get_namespace_index('/StateMachine/Example/')
    state_machine_id = ua.NodeId(Identifier=5002, NamespaceIndex=idx)
    state_machine_node = server.get_node(state_machine_id)
    state_machine_parent = await state_machine_node.get_parent() 
    print(state_machine_id, type(state_machine_node), type(state_machine_parent))
    state_machine = ExampleStateMachin(server, node=state_machine_node, parent=state_machine_parent)
    await state_machine.init(state_machine._state_machine_node)
    await state_machine.install()
    print(type(state_machine.Ready))
    await state_machine.set_initial_state(state_machine.Ready)
    print(state_machine.Halted.id)
    print(state_machine.RunningToHalted.from_state.number)
    await state_machine.change_state(state_machine.Running)
  #  await state_machine.causes[0].call()

    # program = ProgramStateMachine(state_machine_node)
    # await program.init() 
    # await program.install() 

    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__": 
    asyncio.run(main())
