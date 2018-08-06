import asyncio
import logging
from opcua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('opcua')


async def browse_nodes(node: Node):
    """
    Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
    """
    node_class = await node.get_node_class()
    children = []
    for child in await node.get_children():
        if await child.get_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable]:
            children.append(
                await browse_nodes(child)
            )
    if node_class != ua.NodeClass.Variable:
        var_type = None
    else:
        try:
            var_type = (await node.get_data_type_as_variant_type()).value
        except ua.UaError:
            _logger.warning('Node Variable Type could not be determined for %r', node)
            var_type = None
    return {
        'id': node.nodeid.to_string(),
        'name': (await node.get_display_name()).Text,
        'cls': node_class.value,
        'children': children,
        'type': var_type,
    }


async def task(loop):
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

            # get a specific node knowing its node id
            # var = client.get_node(ua.NodeId(1002, 2))
            # var = client.get_node("ns=3;i=2002")
            # print(var)
            # var.get_data_value() # get value of node as a DataValue object
            # var.get_value() # get value of node as a python builtin
            # var.set_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
            # var.set_value(3.9) # set node value using implicit data type

            # Now getting a variable node using its browse path
            tree = await browse_nodes(client.get_objects_node())
            _logger.info('Node tree: %r', tree)
    except Exception:
        _logger.exception('error')


def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(task(loop))
    loop.close()


if __name__ == '__main__':
    main()
