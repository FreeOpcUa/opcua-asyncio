from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from asyncua import Server, ua
from asyncua.ua import uatypes
import asyncua.ua

TEST_DIR = Path(__file__).parent


class ExampleEnum(IntEnum):
    EnumVal1 = 0
    EnumVal2 = 1
    EnumVal3 = 2


setattr(asyncua.ua, 'ExampleEnum', ExampleEnum)


@dataclass
class ExampleStruct:
    IntVal1: uatypes.Int16 = 0
    EnumVal: ExampleEnum = ExampleEnum(0)


async def add_server_custom_enum_struct(server: Server):
    # import some nodes from xml
    ns = await server.register_namespace('http://yourorganisation.org/struct_enum_example/')
    uatypes.register_enum('ExampleEnum', ua.NodeId(3002, ns), ExampleEnum)
    uatypes.register_extension_object('ExampleStruct', ua.NodeId(5001, ns), ExampleStruct)
    await server.import_xml(TEST_DIR / "enum_struct_test_nodes.xml"),
    val = ExampleStruct()
    val.IntVal1 = 242
    val.EnumVal = ExampleEnum.EnumVal2
    myvar = server.get_node(ua.NodeId(6009, ns))
    await myvar.write_value(val)
