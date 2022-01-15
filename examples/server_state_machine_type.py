import os 
import asyncio
from copy import copy

import logging
from typing import Union
from asyncua import ua, Server, Node
from asyncua.common.statemachine import ProgramStateMachine

import datetime
_logger = logging.getLogger(__name__)

class ExampleStateMachine(ProgramStateMachine): 
    def __init__(self, server: Server, node: Node, max=3): 
        super().__init__(server, node)
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
            await self.change_state(self.Ready, event_msg='Execution successfully finished.')

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
    esm = ExampleStateMachine(server, node=state_machine_node)
    await esm.install()
    await esm.set_initial_state(esm.Ready)

    async with server:
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__": 
    asyncio.run(main())
