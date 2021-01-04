import asyncio, logging
from asyncua import Server, ua, Node
from statemachine import StateMachine

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

if __name__ == "__main__":
    async def main():
        server = Server()
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        idx = await server.register_namespace("http://examples.freeopcua.github.io")

        # get a instance of the StateMachine-Class def "__init__(self, server=None, parent=None, idx=None, name=None):"
        mystatemachine = StateMachine(server, server.nodes.objects, idx, "StateMachine")
        # call statemachine.install() to instantiate the statemachinetype (with or without optional nodes)
        await mystatemachine.install(optionals=True)

        # the StateMachine provides helperclasses for states and transition each class is a representation of the state- and transition-variabletype
        # "def __init__(self, name, id=0, node=None):"
        # if the state node already exist for example from xml model you can assign it here aswell as if its a substate this is importent for the change of the state
        state1 = mystatemachine.State("Idle", "S-Id-1", 1)
        # adds the state (StateType) to the statemachine childs - this is optional!
        await mystatemachine.add_state(state1, state_type=ua.NodeId(2309, 0)) #this is a init state -> InitialStateType: ua.NodeId(2309, 0)
        state2 = mystatemachine.State("Loading", "S-Id-2", 2, issub=True)
        await mystatemachine.add_state(state2)
        state3 = mystatemachine.State("Initializing", "S-Id-3", 3, issub=True)
        await mystatemachine.add_state(state3)
        state4 = mystatemachine.State("Processing", "S-Id-4", 4)
        await mystatemachine.add_state(state4)
        state5 = mystatemachine.State("Finished", "S-Id-5", 5)
        await mystatemachine.add_state(state5)

        # setup your transition helperclass 
        # "def __init__(self, name, id=0, node=None):"
        # if the transition node already exist for example from xml model you can assign it here        
        trans1 = mystatemachine.Transition("to Idle", "T-Id-1", 1)
        # adds the state (TransitionType) to the statemachine childs - this is optional!
        await mystatemachine.add_transition(trans1)
        trans2 = mystatemachine.Transition("to Loading", "T-Id-2", 2)
        await mystatemachine.add_transition(trans2)
        trans3 = mystatemachine.Transition("to Initializing", "T-Id-3", 3)
        await mystatemachine.add_transition(trans3)
        trans4 = mystatemachine.Transition("to Processing", "T-Id-4", 4)
        await mystatemachine.add_transition(trans4)
        trans5 = mystatemachine.Transition("to Finished", "T-Id-5", 5)
        await mystatemachine.add_transition(trans5)

        # initialise the StateMachine by call change_state() with the InitialState
        # if the statechange should trigger an TransitionEvent the Message can be assigned here 
        # if event_msg is None no event will be triggered
        await mystatemachine.change_state(state1, trans1, f"{mystatemachine._name}: Idle", 300)

        mystatemachine2 = StateMachine(server, server.nodes.objects, idx, "StateMachine2")
        await mystatemachine2.install(optionals=False)
        await mystatemachine2.change_state(state1)

        mystatemachine3 = StateMachine(server, server.nodes.objects, idx, "StateMachine3")
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
