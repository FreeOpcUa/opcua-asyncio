import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.statemachine import State, StateMachine, Transition

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")

if __name__ == "__main__":

    async def main():
        server = Server()
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        idx = await server.register_namespace("http://examples.freeopcua.github.io")

        # get an instance of the StateMachine-Class def "__init__(self, server=None, parent=None, idx=None, name=None):"
        mystatemachine = StateMachine(server, server.nodes.objects, idx, "StateMachine")
        # call statemachine.install() to instantiate the statemachinetype (with or without optional nodes)
        await mystatemachine.install(optionals=True)

        # the StateMachine provides helperclasses for states and transition each class is a representation of the state- and transition-variabletype
        # if the state node already exist for example from xml model you can assign it here: node=<StateNode>
        state1 = State("State-Id-1", "Idle", 1)
        # adds the state (StateType) to the statemachine childs - this is optional!
        await mystatemachine.add_state(
            state1, state_type=ua.NodeId(2309, 0)
        )  # this is an init state -> InitialStateType: ua.NodeId(2309, 0)
        state2 = State("State-Id-2", "Loading", 2)
        await mystatemachine.add_state(state2)
        state3 = State("State-Id-3", "Initializing", 3)
        await mystatemachine.add_state(state3)
        state4 = State("State-Id-4", "Processing", 4)
        await mystatemachine.add_state(state4)
        state5 = State("State-Id-5", "Finished", 5)
        await mystatemachine.add_state(state5)

        # set up your transition helperclass
        # if the transition node already exist for example from xml model you can assign it here: node=<TransitionNode>
        trans1 = Transition("Transition-Id-1", "to Idle", 1)
        # adds the transition (TransitionType) to the statemachine childs - this is optional!
        await mystatemachine.add_transition(trans1)
        trans2 = Transition("Transition-Id-2", "to Loading", 2)
        await mystatemachine.add_transition(trans2)
        trans3 = Transition("Transition-Id-3", "to Initializing", 3)
        await mystatemachine.add_transition(trans3)
        trans4 = Transition("Transition-Id-4", "to Processing", 4)
        await mystatemachine.add_transition(trans4)
        trans5 = Transition("Transition-Id-5", "to Finished", 5)
        await mystatemachine.add_transition(trans5)

        # initialise the StateMachine by call change_state() with the InitialState
        # if the statechange should trigger an TransitionEvent the Message can be assigned here
        # if event_msg is None no event will be triggered
        await mystatemachine.change_state(state1, trans1, f"{mystatemachine._name}: Idle", 300)

        mystatemachine2 = StateMachine(server, server.nodes.objects, idx, "StateMachineMinimal")
        await mystatemachine2.install(optionals=False)
        await mystatemachine2.change_state(state1)

        mystatemachine3 = StateMachine(server, server.nodes.objects, idx, "StateMachineRegular")
        await mystatemachine3.install(optionals=True)
        await mystatemachine3.change_state(state1, trans1)

        async with server:
            while 1:
                await asyncio.sleep(2)
                await mystatemachine.change_state(state2, trans2, f"{mystatemachine._name}: Loading", 350)
                await mystatemachine2.change_state(state2)
                await mystatemachine3.change_state(state2, trans2)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state3, trans3, f"{mystatemachine._name}: Initializing", 400)
                await mystatemachine2.change_state(state3)
                await mystatemachine3.change_state(state3)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state4, trans4, f"{mystatemachine._name}: Processing", 600)
                await mystatemachine2.change_state(state4)
                await mystatemachine3.change_state(state4, trans3)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state5, trans5, f"{mystatemachine._name}: Finished", 800)
                await mystatemachine2.change_state(state5)
                await mystatemachine3.change_state(state5, trans5)
                await asyncio.sleep(2)
                await mystatemachine.change_state(state1, trans1, f"{mystatemachine._name}: Idle", 500)
                await mystatemachine2.change_state(state1)
                await mystatemachine3.change_state(state1, trans1)

    asyncio.run(main())
