import logging
import asyncio

from asyncua import ua, Server
from asyncua.common.structures104 import new_struct, new_enum, new_struct_field

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    snode1, _ = await new_struct(server, idx, "MyStruct", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32List", ua.VariantType.UInt32, array=True),
    ])
    snode2, _ = await new_struct(server, idx, "MyOptionalStruct", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32List", ua.VariantType.UInt32, array=True),
        new_struct_field("MyInt64", ua.VariantType.Int64, optional=True),
    ])
    enode = await new_enum(server, idx, "MyEnum", [
        "titi",
        "toto",
        "tutu",
    ])

    custom_objs = await server.load_data_type_definitions()
    print("Custom objects on server")
    for name, obj in custom_objs.items():
        print("    ", obj)

    valnode = await server.nodes.objects.add_variable(idx, "my_enum", ua.MyEnum.toto)
    await server.nodes.objects.add_variable(idx, "my_struct", ua.Variant(ua.MyStruct(), ua.VariantType.ExtensionObject))
    my_struct_optional = ua.MyOptionalStruct()
    my_struct_optional.MyUInt32List = [45, 67]
    my_struct_optional.MyInt64 = -67
    await server.nodes.objects.add_variable(idx, "my_struct_optional", ua.Variant(my_struct_optional, ua.VariantType.ExtensionObject))

    await server.export_xml([server.nodes.objects, server.nodes.root, snode1, snode2, enode, valnode], "structs_and_enum.xml")

    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
