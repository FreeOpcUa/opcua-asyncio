
from .standard_address_space_part3 import create_standard_address_space_Part3
from .standard_address_space_part4 import create_standard_address_space_Part4
from .standard_address_space_part5 import create_standard_address_space_Part5
from .standard_address_space_part8 import create_standard_address_space_Part8
from .standard_address_space_part9 import create_standard_address_space_Part9
from .standard_address_space_part10 import create_standard_address_space_Part10
from .standard_address_space_part11 import create_standard_address_space_Part11
from .standard_address_space_part13 import create_standard_address_space_Part13

__all__ = ["fill_address_space"]


class PostponeReferences:
    def __init__(self, server):
        self.server = server
        self.postponed_refs = None
        self.postponed_nodes = None
        #self.add_nodes = self.server.add_nodes

    def add_nodes(self, nodes):
        self.postponed_nodes.extend(self.server.try_add_nodes(nodes, check=False))

    def add_references(self, refs):
        self.postponed_refs.extend(self.server.try_add_references(refs))
        # no return

    def __enter__(self):
        self.postponed_refs = []
        self.postponed_nodes = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and exc_val is None:
            remaining_nodes = list(self.server.try_add_nodes(self.postponed_nodes, check=False))
            if len(remaining_nodes):
                raise RuntimeError(f"There are remaining nodes: {remaining_nodes!r}")
            remaining_refs = list(self.server.try_add_references(self.postponed_refs))
            if len(remaining_refs):
                raise RuntimeError(f"There are remaining refs: {remaining_refs!r}")


def fill_address_space(nodeservice):
    with PostponeReferences(nodeservice) as server:
        create_standard_address_space_Part3(server)
        create_standard_address_space_Part4(server)
        create_standard_address_space_Part5(server)
        create_standard_address_space_Part8(server)
        create_standard_address_space_Part9(server)
        create_standard_address_space_Part10(server)
        create_standard_address_space_Part11(server)
        create_standard_address_space_Part13(server)
