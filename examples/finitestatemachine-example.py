import asyncio
import logging
from asyncua import Server, ua, Node
from asyncua.common.statemachine import FiniteStateMachine, State, Transition

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

if __name__ == "__main__":
    async def main():
        server = Server()
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        idx = await server.register_namespace("http://examples.freeopcua.github.io")
        
        # get a instance of the FiniteStateMachine-Class def "__init__(self, server=None, parent=None, idx=None, name=None):"
        mystatemachine = FiniteStateMachine(server, server.nodes.objects, idx, "FiniteStateMachine")
        # call statemachine.install() to instantiate the statemachinetype (with or without optional nodes)
        await mystatemachine.install(optionals=True)

        # the FiniteStateMachine provides helperclasses for states and transition each class is a representation of the state- and transition-variabletype
        # if the state node already exist for example from xml model you can assign it here: node=<StateNode>
        state1 = State("State-Id-1", "Idle", 1, node=None)
        # adds the state (StateType) to the statemachine childs - this is mandatory for the FiniteStateMachine!
        await mystatemachine.add_state(state1, state_type=ua.NodeId(2309, 0)) #this is a init state -> InitialStateType: ua.NodeId(2309, 0)
        state2 = State("State-Id-2", "Loading", 2)
        await mystatemachine.add_state(state2)
        state3 = State("State-Id-3", "Initializing", 3)
        await mystatemachine.add_state(state3)
        state4 = State("State-Id-4", "Processing", 4)
        await mystatemachine.add_state(state4)
        state5 = State("State-Id-5", "Finished", 5)
        await mystatemachine.add_state(state5)

        # sets the avalible states of the FiniteStateMachine
        # this is mandatory!
        await mystatemachine.set_available_states([
            state1.node.nodeid,
            state2.node.nodeid,
            state3.node.nodeid,
            state4.node.nodeid,
            state5.node.nodeid
        ])

        # setup your transition helperclass 
        # if the transition node already exist for example from xml model you can assign it here: node=<TransitionNode> 
        trans1 = Transition("Transition-Id-1", "to Idle", 1)
        # adds the transition (TransitionType) to the statemachine childs - this is optional for the FiniteStateMachine
        await mystatemachine.add_transition(trans1)
        trans2 = Transition("Transition-Id-2", "to Loading", 2)
        await mystatemachine.add_transition(trans2)
        trans3 = Transition("Transition-Id-3", "to Initializing", 3)
        await mystatemachine.add_transition(trans3)
        trans4 = Transition("Transition-Id-4", "to Processing", 4)
        await mystatemachine.add_transition(trans4)
        trans5 = Transition("Transition-Id-5", "to Finished", 5)
        await mystatemachine.add_transition(trans5)

        # this is optional for the FiniteStateMachine
        await mystatemachine.set_available_transitions([
            trans1.node.nodeid,
            trans2.node.nodeid,
            trans3.node.nodeid,
            trans4.node.nodeid,
            trans5.node.nodeid
        ])

        # initialise the FiniteStateMachine by call change_state() with the InitialState
        # if the statechange should trigger an TransitionEvent the Message can be assigned here 
        # if event_msg is None no event will be triggered
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
