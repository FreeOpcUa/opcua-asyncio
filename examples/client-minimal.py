import asyncio
import sys
sys.path.insert(0, "..")
import logging
from opcua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('opcua')


async def main():
    # url = 'opc.tcp://192.168.2.64:4840'
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
    try:
        async with Client(url=url) as client:
            # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
            root = client.get_root_node()
            _logger.info('Objects node is: %r', root)

            # Node objects have methods to read and write node attributes as well as browse or populate address space
            _logger.info('Children of root are: %r', await root.get_children())

            uri = 'http://examples.freeopcua.github.io'
            idx = await client.get_namespace_index(uri)
            # get a specific node knowing its node id
            # var = client.get_node(ua.NodeId(1002, 2))
            # var = client.get_node("ns=3;i=2002")
            var = await root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"]) 
            print("My variable", var, await var.get_value())
            # print(var)
            # var.get_data_value() # get value of node as a DataValue object
            # var.get_value() # get value of node as a python builtin
            # var.set_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
            # var.set_value(3.9) # set node value using implicit data type

            # Now getting a variable node using its browse path
    except Exception:
        _logger.exception('error')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main())
    loop.close()
