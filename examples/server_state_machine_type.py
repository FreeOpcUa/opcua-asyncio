import os 
import asyncio
import logging
from asyncua import ua, Server, Node
from asyncua.common.statemachine import ProgramStateMachine, ExclusiveLimitStateMachine
from asyncua.common.parameter_set import ParameterSet

class ExampleParameterSet(ParameterSet): 
    MaxProgramIterationsCount: Node = None 
    CurrentProgramIterationsCount: Node = None 

    @property
    def CurrentProgramIterationsCountValue(self): 
        return self.CurrentProgramIterationsCount.value  

class ExampleStateMachine(ProgramStateMachine): 
    def __init__(self, server: Server, node: Node, max: Node, cnt: Node): 
        super().__init__(server, node)
        self._running = False 
        self._task_running: asyncio.Task = None
        self._index = 0
        self._max = max
        self._result = None
        self._index = cnt 

    # Make the parameter value a read only property 
    @property
    def max(self):
        return self._max.value

    async def install(self): 
        await super().install()
        self._result = self.FinalResultData.Result 

    async def on_entry_ready(self):
        await self._index.write_value(0, varianttype=ua.VariantType.UInt16) 

    async def execute_running(self): 
        while self._running and self._index.value < self.max: 
            print(f'Executing the Running state {self._index.value+1}/{self.max}')
            await self._index.write_value(self._index.value+1, varianttype=ua.VariantType.UInt16)
            await asyncio.sleep(1)
        
        if self._index.value == self.max and self._result.value: 
            await self.change_state(self.Ready, event_msg=f'Execution successfully finished. Result: {self._result.value}')
     
    async def on_entry_running(self): 
        if not self._running: 
            self._running = True
            self._task_running = asyncio.create_task(self.execute_running())

    async def on_exit_running(self): 
        if self._running: 
            #self._task_running.cancel()
            self._running = False 

async def main(): 
    logging.basicConfig(level=logging.FATAL)
    al = logging.getLogger('asyncua')
    al.setLevel(logging.ERROR)
    al = logging.getLogger('asyncua.common.statemachine')
    al.setLevel(logging.DEBUG)

    server = Server()
    await server.init()

    nodeset_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'StateMachine.Example.NodeSet2.xml')
    await server.import_xml(nodeset_path)
    idx = await server.get_namespace_index('/StateMachine/Example/')

    # Example ParameterSet
    parameter_set_id = ua.NodeId(Identifier=5013, NamespaceIndex=idx)
    parameter_set_node = server.get_node(parameter_set_id)
    eps = ExampleParameterSet(parameter_set_node, subscribe=True, source=server, interval=50)
    await eps.init() 
    
    # Example ProgramStateMachine
    state_machine_id = ua.NodeId(Identifier=5002, NamespaceIndex=idx)
    state_machine_node = server.get_node(state_machine_id)
    esm = ExampleStateMachine(server, node=state_machine_node, max=eps.MaxProgramIterationsCount, cnt=eps.CurrentProgramIterationsCount)
    await esm.install()
    await esm.set_initial_state(esm.Ready)

    await esm.FinalResultData.print_parameter_list()
    await esm.FinalResultData.set_value('Result', True)
    print(esm.FinalResultData.Result.value)

    await esm.start('Starting execution.')
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
                # Since there is no valid transition defined by the type to go from Low to High it will fail here
                res = await limit_sm.change_state(limit_sm.High, event_msg='Temperature is to high.')
                if not res.is_good():          
                    print(f'Changeing to high failed. {res.name}')

            val += 1
            if val > 12: 
                val = 0
        
            if esm.current_state_name == 'Suspended':
                print('The example state machine is now paused.') 

            if eps.CurrentProgramIterationsCountValue == 5: 
                print('Program count reached 5')

            await asyncio.sleep(1)

if __name__ == "__main__": 
    asyncio.run(main())
