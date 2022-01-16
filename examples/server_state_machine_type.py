import os 
import asyncio
import logging
from asyncua import ua, Server, Node
from asyncua.common.statemachine import ProgramStateMachine, ExclusiveLimitStateMachine

class ExampleStateMachine(ProgramStateMachine): 
    def __init__(self, server: Server, node: Node, max=3): 
        super().__init__(server, node)
        self._running = False 
        self._task_running: asyncio.Task = None
        self._index = 0
        self._max = max

    async def install(self): 
        await super().install()
        self.result = self.FinalResultDataSet.Result 

    async def on_entry_ready(self):
        self._index = 0 

    async def execute_running(self): 
        while self._running and self._index < self._max: 
            self._index+=1
            print(f'Executing the Running state {self._index}/{self._max}')
            await asyncio.sleep(1)
        
        if self._index == self._max and self.result.value: 
            await self.change_state(self.Ready, event_msg=f'Execution successfully finished. Result: {self.result.value}')
        else: 
            await self.change_state(self.Halted, event_msg=f'Execution failed. Result: {self.result.value}')

    async def on_entry_running(self): 
        self._running = True 
        self._task_running = asyncio.create_task(self.execute_running())

    async def on_exit_running(self): 
        self._running = False 

async def main(): 
    server = Server()
    logging.basicConfig(level=logging.FATAL)
    al = logging.getLogger('asyncua')
    al.setLevel(logging.ERROR)
    al = logging.getLogger('asyncua.common.statemachine')
    al.setLevel(logging.DEBUG)
    await server.init()

    await server.import_xml(os.path.join('examples','StateMachine.Example.NodeSet2.xml'))
    idx = await server.get_namespace_index('/StateMachine/Example/')
    state_machine_id = ua.NodeId(Identifier=5002, NamespaceIndex=idx)
    state_machine_node = server.get_node(state_machine_id)

    # Example ProgramStateMachine
    esm = ExampleStateMachine(server, node=state_machine_node, max=10)
    await esm.install()
    await esm.set_initial_state(esm.Ready)

    await esm.FinalResultDataSet.print_parameter_list()
    await esm.FinalResultDataSet.set_value('Result', True)
    print(esm.FinalResultDataSet.Result.value)
    #await esm.FinalResultDataSet.update_subscription_interval(50)

    # ExclusiveLimitStateMachine
    limit_state_machine_id = ua.NodeId(Identifier=5012, NamespaceIndex=idx)
    limit_state_machine_node = server.get_node(limit_state_machine_id)
    limit_sm = ExclusiveLimitStateMachine(server, limit_state_machine_node)
    await limit_sm.install(optionals=False) 
    await limit_sm.set_initial_state(limit_sm.Low)

    val = 0
    async with server:
        while True:
            if val == 5: 
                await limit_sm.change_state(limit_sm.LowLow, event_msg='Now its freezing cold.')
            elif val == 10: 
                await limit_sm.change_state(limit_sm.Low, event_msg='Temperature is to low.')
            elif val == 12: 
                res = await limit_sm.change_state(limit_sm.High, event_msg='Temperature is to hot')
                print(f'Changeing to high failed. {res}')

            val += 1

            if val > 12: 
                val = 0

            await asyncio.sleep(1)

if __name__ == "__main__": 
    asyncio.run(main())
