import os
from opcua import ua
from opcua.ua import uatypes
from enum import IntEnum
from opcua import Server

TEST_DIR = os.path.dirname(__file__) + os.sep


class ExampleEnum(IntEnum):
    EnumVal1 = 0
    EnumVal2 = 1
    EnumVal3 = 2


import opcua.ua

setattr(opcua.ua, 'ExampleEnum', ExampleEnum)


class ExampleStruct(uatypes.FrozenClass):
    ua_types = [
        ('IntVal1', 'Int16'),
        ('EnumVal', 'ExampleEnum'),
    ]

    def __init__(self):
        self.IntVal1 = 0
        self.EnumVal = ExampleEnum(0)
        self._freeze = True

    def __str__(self):
        return f'ExampleStruct(IntVal1:{self.IntVal1}, EnumVal:{self.EnumVal})'

    __repr__ = __str__


async def add_server_custom_enum_struct(server: Server):
    # import some nodes from xml
    await server.import_xml(f"{TEST_DIR}enum_struct_test_nodes.xml")
    ns = await server.get_namespace_index('http://yourorganisation.org/struct_enum_example/')
    uatypes.register_extension_object('ExampleStruct', ua.NodeId(5001, ns), ExampleStruct)
    val = ua.ExampleStruct()
    val.IntVal1 = 242
    val.EnumVal = ua.ExampleEnum.EnumVal2
    myvar = server.get_node(ua.NodeId(6009, ns))
    await myvar.set_value(val)