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

    await new_struct(server, idx, "MyStruct", [new_struct_field("MyBool", ua.VariantType.Boolean), new_struct_field("MyUInt32", ua.VariantType.UInt32)])
    await new_enum(server, idx, "MyEnum", "titi", "toto", "tutu")

    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
