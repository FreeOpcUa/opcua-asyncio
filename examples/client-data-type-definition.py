import asyncio
import logging

from asyncua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
    async with Client(url=url) as client:
        uri = 'http://examples.freeopcua.github.io'
        idx = await client.register_namespace(uri)
        await client.load_data_type_definitions()
        my_enum = await client.nodes.objects.get_child(f"{idx}:my_enum")
        print("ENUM", await my_enum.get_value())
        my_struct = await client.nodes.objects.get_child(f"{idx}:my_struct")
        print("STRUCT", await my_struct.read_value())
        my_struct_opt = await client.nodes.objects.get_child(f"{idx}:my_struct_optional")
        print("STRUCT WITH OPTIA VALUE", await my_struct_opt.read_value())

if __name__ == '__main__':
    asyncio.run(main())
