import asyncio
import sys
sys.path.insert(0, "..")
import logging
from asyncua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
    async with Client(url=url) as client:
        # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
        # Node objects have methods to read and write node attributes as well as browse or populate address space
        _logger.info('Children of root are: %r', await client.nodes.root.get_children())

        uri = 'http://examples.freeopcua.github.io'
        idx = await client.get_namespace_index(uri)
        # get a specific node knowing its node id
        # var = client.get_node(ua.NodeId(1002, 2))
        # var = client.get_node("ns=3;i=2002")
        var = await client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
        print("My variable", var, await var.read_value())
        # print(var)
        # await var.read_data_value() # get value of node as a DataValue object
        # await var.read_value() # get value of node as a python builtin
        # await var.write_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
        # await var.write_value(3.9) # set node value using implicit data type

if __name__ == '__main__':
    asyncio.run(main())
