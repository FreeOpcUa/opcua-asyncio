import asyncio
import logging
from asyncua import Server, ua
from asyncua.common.statemachine import FiniteStateMachine, State, Transition

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

if __name__ == "__main__":
    async def main():
        server = Server()
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        idx = await server.register_namespace("http://examples.freeopcua.github.io")

        # creating a own FiniteStateMachine as Subtype of FiniteStateMachineType
        finitestatemachinetype = server.get_node(ua.NodeId(2771, 0))
        myfinitstatemachine = await finitestatemachinetype.add_object_type(idx, "MyFiniteStateMachine")
        n = await myfinitstatemachine.add_object(idx, "MyState1", ua.NodeId.from_string("i=2307"))
        await n.set_modelling_rule(True)
        n = await myfinitstatemachine.add_object(idx, "MyState2", ua.NodeId.from_string("i=2307"))
        await n.set_modelling_rule(True)
        
        # get a instance of the FiniteStateMachine-Class def "__init__(self, server=None, parent=None, idx=None, name=None):"
        mystatemachine = FiniteStateMachine(server, server.nodes.objects, idx, "FiniteStateMachine", myfinitstatemachine)
        # call statemachine.install() to instantiate the statemachinetype (with or without optional nodes)
        await mystatemachine.install(optionals=True)

        state1 = State()

        async with server:
            while 1:
                await asyncio.sleep(2)
                # FIXME

    asyncio.run(main())
