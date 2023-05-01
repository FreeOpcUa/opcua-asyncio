import asyncio
import logging

from asyncua import Client, ua
from asyncua.common.structures104 import load_custom_struct



async def main():
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
    async with Client(url=url) as client:
        uri = 'http://examples.freeopcua.github.io'
        idx = await client.register_namespace(uri)
        await client.load_data_type_definitions()
        my_enum = await client.nodes.objects.get_child(f"{idx}:my_enum")
        val = await my_enum.get_value()
        print("ENUM", val, type(val), val == ua.MyEnum.toto)  # enums are int32 in UA, we do not convert them back to IntEnum yet
        my_struct = await client.nodes.objects.get_child(f"{idx}:my_struct")
        print("STRUCT", await my_struct.read_value())
        my_struct_opt = await client.nodes.objects.get_child(f"{idx}:my_struct_optional")
        print("STRUCT WITH OPTIA VALUE", await my_struct_opt.read_value())

        # loading one specific custom struct
        mystructnode = await client.nodes.base_structure_type.get_child(f"{idx}:MyStruct")
        my_type = await load_custom_struct(mystructnode)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    _logger = logging.getLogger('asyncua')
    asyncio.run(main())
