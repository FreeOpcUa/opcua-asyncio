from .standard_address_space_services import create_standard_address_space_Services
from asyncio import sleep

class PostponeReferences:
    def __init__(self, server):
        self.server = server
        self.postponed_refs = None
        self.postponed_nodes = None
        # self.add_nodes = self.server.add_nodes

    async def add_nodes(self, nodes):
        async for node in self.server.try_add_nodes(nodes, check=False):
            self.postponed_nodes.append(node)

    async def add_references(self, refs):
        async for ref in self.server.try_add_references(refs):
            self.postponed_refs.append(ref)
        # no return

    async def __aenter__(self):
        self.postponed_refs = []
        self.postponed_nodes = []
        await sleep(0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and exc_val is None:
            remaining_nodes = []
            remaining_refs = []
            async for remaining_node in self.server.try_add_nodes(self.postponed_nodes, check=False):
                remaining_nodes.append(remaining_node)
            #remaining_nodes = self.server.try_add_nodes(self.postponed_nodes, check=False)
            if len(remaining_nodes):
                raise RuntimeError(f"There are remaining nodes: {remaining_nodes!r}")
            async for remaining_reference in self.server.try_add_references(self.postponed_refs):
                remaining_refs.append(remaining_reference)
            #remaining_refs = list(await self.server.try_add_references(self.postponed_refs))
            if len(remaining_refs):
                raise RuntimeError(f"There are remaining refs: {remaining_refs!r}")


async def fill_address_space(nodeservice):
    async with PostponeReferences(nodeservice) as server:
        await create_standard_address_space_Services(server)
