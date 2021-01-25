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
import asyncio, logging, datetime

#FIXME 
# -change to relativ imports!
# -remove unused imports
from asyncua import Server, ua, Node
from asyncua.common.event_objects import TransitionEvent, ProgramTransitionEvent

_logger = logging.getLogger(__name__)

############
''' Workaround till fixed in event_objects.py'''
class TransitionEvent(TransitionEvent):
    """
    TransitionEvent:
    """
    def __init__(self, sourcenode=None, message=None, severity=1):
        super(TransitionEvent, self).__init__(sourcenode, message, severity)
        self.EventType = ua.NodeId(ua.ObjectIds.TransitionEventType)
        self.add_property('Transition', None, ua.VariantType.LocalizedText)
        self.add_property('FromState', None, ua.VariantType.LocalizedText)
        self.add_property('ToState', None, ua.VariantType.LocalizedText)
############

class StateMachine(object):
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
        self._current_state_effective_display_name_node = None
        self._last_transition_node = None
        self._last_transition_id_node = None
        self._last_transition_name_node = None
        self._last_transition_number_node = None
        self._last_transition_transitiontime_node = None
        self._last_transition_effectivetransitiontime_node = None
        self._evgen = None
        self.evtype = TransitionEvent()
        self._current_state = self.State(None, None, None)

    class State(object):
        '''
        Helperclass for States (StateVariableType)
        https://reference.opcfoundation.org/v104/Core/docs/Part5/B.4.3/
        name: type string will be converted automatically to qualifiedname 
            -> Name is a QualifiedName which uniquely identifies the current state within the StateMachineType.
        id: Id is a name which uniquely identifies the current state within the StateMachineType. A subtype may restrict the DataType.
        number: Number is an integer which uniquely identifies the current state within the StateMachineType.
        '''
        def __init__(self, name, id, number, node=None, issub=False):
            self.name = name
            self.id = id
            self.number = number
            self.effectivedisplayname = ua.LocalizedText(name, "en-US")
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
        def __init__(self, name, id, number, node=None):
            self.name = name
            self.id = id
            self.number = number
            self._transitiontime = datetime.datetime.utcnow() #will be overwritten from _write_transition()
            self._effectivetransitiontime = datetime.datetime.utcnow() #will be overwritten from _write_transition()
            self.node = node #will be written from statemachine.add_state() or you need to overwrite it if the state is part of xml

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
                    ua.Variant(datetime.datetime.utcnow(), varianttype=ua.VariantType.DateTime)
                    )
            if "EffectiveTransitionTime" not in childnames:
                self._last_transition_effectivetransitiontime_node = await self._last_transition_node.add_property(
                    0, 
                    "EffectiveTransitionTime", 
                    ua.Variant(datetime.datetime.utcnow(), varianttype=ua.VariantType.DateTime)
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
                elif dn.Text == "EffectiveTransitionTime":
                    self._last_transition_effectivetransitiontime_node = await self._last_transition_node.get_child(["EffectiveTransitionTime"])
                else:
                    _logger.warning(f"{await statemachine.read_browse_name()} LastTransition Unknown propertie: {dn.Text}")
        self._evgen = await self._server.get_event_generator(self.evtype, self._state_machine_node)

    async def change_state(self, state, transition=None, event_msg=None, severity=500):
        '''
        method to change the state of the statemachine
        state: "self.State" mandatory
        transition: "self.Transition" optional
        event_msg: "string/LocalizedText" optional
        severity: "Int" optional
        '''
        await self._write_state(state)
        if transition:
            await self._write_transition(transition, state.issub)
        if event_msg:
            if isinstance(event_msg, str):
                event_msg = ua.LocalizedText(event_msg, self.locale)
            self._evgen.event.Message = event_msg
            self._evgen.event.Severity = severity
            self._evgen.event.ToState = ua.LocalizedText(state.name, self.locale)
            if transition:
                self._evgen.event.Transition = ua.LocalizedText(transition.name, self.locale)
            self._evgen.event.FromState = ua.LocalizedText(self._current_state.name)
            await self._evgen.trigger()
        self._current_state = state

    async def _write_state(self, state):
        if not isinstance(state, self.State):
            raise ValueError
        await self._current_state_node.write_value(ua.LocalizedText(state.name, self.locale), ua.VariantType.LocalizedText)
        if state.node:
            if self._current_state_id_node:
                await self._current_state_id_node.write_value(state.id, ua.VariantType.String)
            if self._current_state_name_node:
                await self._current_state_name_node.write_value(state.name, ua.VariantType.QualifiedName)
            if self._current_state_number_node:
                await self._current_state_number_node.write_value(state.number, ua.VariantType.UInt32)
            if self._current_state_effective_display_name_node:
                await self._current_state_effective_display_name_node.write_value(state.effectivedisplayname, ua.VariantType.LocalizedText)

    async def _write_transition(self, transition, issub=False):
        '''
        transition: self.Transition
        issub: boolean (true if it is a transition between substates)
        '''
        if not isinstance(transition, self.Transition):
            raise ValueError
        if issub == False:
            transition._transitiontime = datetime.datetime.utcnow()
        transition._effectivetransitiontime = datetime.datetime.utcnow()
        await self._last_transition_node.write_value(ua.LocalizedText(transition.name, self.locale), ua.VariantType.LocalizedText)
        if self._optionals:
            if self._last_transition_id_node:
                await self._last_transition_id_node.write_value(transition.id, ua.VariantType.String)
            if self._last_transition_name_node:
                await self._last_transition_name_node.write_value(ua.QualifiedName(transition.name, self._idx), ua.VariantType.QualifiedName)
            if self._last_transition_number_node:
                await self._last_transition_number_node.write_value(transition.id, ua.VariantType.UInt32)
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
        if not state_type in [ua.NodeId(2309, 0),ua.NodeId(2307, 0),ua.NodeId(15109,0)]:
            # unknown state type!
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


class FiniteStateMachine(StateMachine):
    '''
    Implementation of an FiniteStateMachineType a little more advanced than the basic one
    if you need to know the available states and transition from clientside
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "FiniteStateMachine"
        self._state_machine_type = ua.NodeId(2771, 0)
        self._available_states_node = None
        self._available_transitions_node = None

    async def set_available_states(self, states):
        if not self._available_states_node:
            self._available_states_node = await self._state_machine_node.get_child(["AvailableStates"])
        if isinstance(states, list):
            return await self._available_states_node.write_value(states, varianttype=ua.VariantType.NodeId)
        return ValueError

    async def set_available_transitions(self, transitions):
        if self._optionals:
            if not self._available_transitions_node:
                self._available_transitions_node = await self._state_machine_node.get_child(["AvailableTransitions"])
            if isinstance(transitions, list):
                return await self._available_transitions_node.write_value(transitions, varianttype=ua.VariantType.NodeId)
            return ValueError


class ExclusiveLimitStateMachine(FiniteStateMachine):
    '''
    NOT IMPLEMENTED "ExclusiveLimitStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
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
        if name == None:
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
        if name == None:
            name = "ProgramStateMachine"
        self._state_machine_type = ua.NodeId(2391, 0)
        self.evtype = ProgramTransitionEvent()
        raise NotImplementedError

#         # 5.2.3.2 ProgramStateMachineType states
#         self._ready_state_node = None #State node
#         self._halted_state_node = None #State node
#         self._running_state_node = None #State node
#         self._suspended_state_node = None #State node

#         # 5.2.3.3 ProgramStateMachineType transitions
#         self._halted_to_ready_node = None #Transition node
#         self._ready_to_running_node = None #Transition node
#         self._running_to_halted_node = None #Transition node
#         self._running_to_ready_node = None #Transition node
#         self._running_to_suspended_node = None #Transition node
#         self._suspended_to_running_node = None #Transition node
#         self._suspended_to_halted_node = None #Transition node
#         self._suspended_to_ready_node = None #Transition node
#         self._ready_to_halted_node = None #Transition node

#         # 5.2.3.2 ProgramStateMachineType states
#         self._halted_state_id_node = None #State property (StateNumber value 11)
#         self._ready_state_id_node = None #State property (StateNumber value 12)
#         self._running_state_id_node = None #State property (StateNumber value 13)
#         self._suspended_state_id_node = None #State property (StateNumber value 14)

#         # 5.2.3.3 ProgramStateMachineType transitions
#         self._halted_to_ready_id_node = None #Transition property (TransitionNumber value 1)
#         self._ready_to_running_id_node = None #Transition property (TransitionNumber value 2)
#         self._running_to_halted_id_node = None #Transition property (TransitionNumber value 3)
#         self._running_to_ready_id_node = None #Transition property (TransitionNumber value 4)
#         self._running_to_suspended_id_node = None #Transition property (TransitionNumber value 5)
#         self._suspended_to_running_id_node = None #Transition property (TransitionNumber value 6)
#         self._suspended_to_halted_id_node = None #Transition property (TransitionNumber value 7)
#         self._suspended_to_ready_id_node = None #Transition property (TransitionNumber value 8)
#         self._ready_to_halted_id_node = None #Transition property (TransitionNumber value 9)

#         # 4.2.7 Program Control Methods (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.7/)
#         self._halt_method_node = None #uamethod node
#         self._reset_method_node = None #uamethod node
#         self._resume_method_node = None #uamethod node
#         self._start_method_node = None #uamethod node
#         self._suspend_method_node = None #uamethod node

#         # other possible props/comps https://reference.opcfoundation.org/v104/Core/docs/Part10/5.2.1/
#         self._deletable_node = None
#         self._deletable = False
#         self._autodelete_node = None
#         self._autodelete = False
#         self._recyclecount_node = None
#         self._recyclecount = 0

#         #can be overwritten if you want a different language
#         self.localizedtext_ready = ua.LocalizedText("Ready", "en-US")
#         self.localizedtext_running = ua.LocalizedText("Running", "en-US")
#         self.localizedtext_halted = ua.LocalizedText("Halted", "en-US")
#         self.localizedtext_suspended= ua.LocalizedText("Suspended", "en-US")
#         self.localizedtext_halted_to_ready = ua.LocalizedText("HaltedToReady", "en-US")
#         self.localizedtext_ready_to_running = ua.LocalizedText("ReadyToRunning", "en-US")
#         self.localizedtext_running_to_halted = ua.LocalizedText("RunningToHalted", "en-US")
#         self.localizedtext_running_to_ready = ua.LocalizedText("RunningToReady", "en-US")
#         self.localizedtext_running_to_suspended = ua.LocalizedText("RunningToSuspended", "en-US")
#         self.localizedtext_suspended_to_running = ua.LocalizedText("SuspendedToRunning", "en-US")
#         self.localizedtext_suspended_to_halted = ua.LocalizedText("SuspendedToHalted", "en-US")
#         self.localizedtext_suspended_to_ready = ua.LocalizedText("SuspendedToReady", "en-US")
#         self.localizedtext_ready_to_halted = ua.LocalizedText("ReadyToHalted", "en-US")

#     async def install(self, optionals=False):
#         '''
#         setup adressspace
#         '''
#         self._optionals = optionals
#         self._state_machine_node = await self._parent.add_object(
#             self._idx, 
#             self._name, 
#             objecttype=self._state_machine_type, 
#             instantiate_optional=optionals
#             )
#         await self.init(self._state_machine_node)
    
#     async def init(self, statemachine):
#         '''
#         initialize and get subnodes
#         '''
#         self._current_state_node = await statemachine.get_child(["CurrentState"])
#         current_state_props = await self._current_state_node.get_properties()
#         for prop in current_state_props:
#             dn = await prop.read_display_name()
#             if dn.Text == "Id":
#                 self._current_state_id_node = await self._current_state_node.get_child(["Id"])
#             elif dn.Text == "Name":
#                 self._current_state_name_node = await self._current_state_node.get_child(["Name"])
#             elif dn.Text == "Number":
#                 self._current_state_number_node = await self._current_state_node.get_child(["Number"])
#             else:
#                 _logger.warning(f"{await statemachine.read_browse_name()} CurrentState Unknown propertie: {dn.Text}")
#         if self._optionals:
#             self._last_transition_node = await statemachine.get_child(["LastTransition"])
#             last_transition_props = await self._last_transition_node.get_properties()
#             for prop in last_transition_props:
#                 dn = await prop.read_display_name()
#                 if dn.Text == "Id":
#                     self._last_transition_id_node = await self._last_transition_node.get_child(["Id"])
#                 elif dn.Text == "Name":
#                     self._last_transition_name_node = await self._last_transition_node.get_child(["Name"])
#                 elif dn.Text == "Number":
#                     self._last_transition_number_node = await self._last_transition_node.get_child(["Number"])
#                 elif dn.Text == "TransitionTime":
#                     self._last_transition_transitiontime_node = await self._last_transition_node.get_child(["TransitionTime"])
#                 elif dn.Text == "EffectiveTransitionTime":
#                     self._last_transition_effectivetransitiontime_node = await self._last_transition_node.get_child(["EffectiveTransitionTime"])
#                 else:
#                     _logger.warning(f"{await statemachine.read_browse_name()} LastTransition Unknown propertie: {dn.Text}")
#         self._evgen = await self._server.get_event_generator(self.evtype, self._state_machine_node)

#         #bind methods if method node exist
#         #write defaults

#     #Transition
#     async def HaltedToReady(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_ready,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._ready_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_halted_to_ready,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._halted_to_ready.nodeid,
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition
#     async def ReadyToRunning(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_running,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._running_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_ready_to_running,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._ready_to_running.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition
#     async def RunningToHalted(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_halted,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._halted_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_running_to_halted,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._running_to_halted.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition
#     async def RunningToReady(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_ready,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._ready_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_running_to_ready,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._running_to_ready.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition
#     async def RunningToSuspended(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_suspended,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._suspended_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_running_to_suspended,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._running_to_suspended.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition 
#     async def SuspendedToRunning(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_running,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._running_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_suspended_to_running,
#             varianttype=ua.VariantType.LocalizedText
#             )
#         await self._last_transition_id_node.write_value(
#             self._suspended_to_running.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition
#     async def SuspendedToHalted(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_halted,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._halted_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_suspended_to_halted,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._suspended_to_halted.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition
#     async def SuspendedToReady(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_ready,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._ready_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_suspended_to_ready,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._suspended_to_ready.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #Transition 
#     async def ReadyToHalted(self):
#         await self._current_state_node.write_value(
#             self.localizedtext_halted,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._current_state_id_node.write_value(
#             self._halted_state.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         await self._last_transition_node.write_value(
#             self.localizedtext_ready_to_halted,
#             varianttype=ua.VariantType.LocalizedText
#             ) 
#         await self._last_transition_id_node.write_value(
#             self._ready_to_halted.nodeid, 
#             varianttype=ua.VariantType.NodeId
#             )
#         #FIXME 
#         # trigger ProgramTransitionEventType and 
#         # AuditUpdateMethodEvents/AuditProgramTransitionEventType (https://reference.opcfoundation.org/v104/Core/docs/Part10/4.2.2/)
#         return ua.StatusCode(ua.status_codes.StatusCodes.Good)

#     #method to be linked to uamethod
#     async def Start(self):
#         if await self._current_state_node.read_value() == self.localizedtext_ready:
#             return await ReadyToRunning()
#         else:
#             return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

#     #method to be linked to uamethod
#     async def Suspend(self):
#         if await self._current_state_node.read_value() == self.localizedtext_running:
#             return await RunningToSuspended()
#         else:
#             return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

#     #method to be linked to uamethod
#     async def Resume(self):
#         if await self._current_state_node.read_value() == self.localizedtext_suspended:
#             return await SuspendedToRunning()
#         else:
#             return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

#     #method to be linked to uamethod
#     async def Halt(self):
#         val = await self._current_state_node.read_value()
#         if val == self.localizedtext_ready:
#             return await ReadyToHalted()
#         elif val == self.localizedtext_running:
#             return await RunningToHalted()
#         elif val == self.localizedtext_suspended:
#             return await SuspendedToHalted()
#         else:
#             return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)

#     #method to be linked to uamethod
#     async def Reset(self):
#         if await self._current_state_node.read_value() == self.localizedtext_halted:
#             return await HaltedToReady()
#         else:
#             return ua.StatusCode(ua.status_codes.StatusCodes.BadNotExecutable)


class ShelvedStateMachine(FiniteStateMachine):
    '''
    NOT IMPLEMENTED "ShelvedStateMachineType"
    '''
    def __init__(self, server=None, parent=None, idx=None, name=None):
        super().__init__(server, parent, idx, name)
        if name == None:
            name = "ShelvedStateMachine"
        self._state_machine_type = ua.NodeId(2929, 0)
        raise NotImplementedError

