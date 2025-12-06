import asyncio
import logging

from asyncua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")


async def browse_nodes(node: Node):
    """
    Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
    """
    node_class = await node.read_node_class()
    children = []
    for child in await node.get_children():
        if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable]:
            children.append(await browse_nodes(child))
    if node_class != ua.NodeClass.Variable:
        var_type = None
    else:
        try:
            var_type = (await node.read_data_type_as_variant_type()).value
        except ua.UaError:
            _logger.warning("Node Variable Type could not be determined for %r", node)
            var_type = None
    return {
        "id": node.nodeid.to_string(),
        "name": (await node.read_display_name()).Text,
        "cls": node_class.value,
        "children": children,
        "type": var_type,
    }


async def task(loop):
    url = "opc.tcp://192.168.2.64:4840"
    # url = "opc.tcp://localhost:4840/freeopcua/server/"
    try:
        client = Client(url=url)
        client.set_user("test")
        client.set_password("test")
        # client.set_security_string()
        await client.connect()
        # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
        root = client.nodes.root
        _logger.info("Objects node is: %r", root)

        # Node objects have methods to read and write node attributes as well as browse or populate address space
        _logger.info("Children of root are: %r", await root.get_children())

        tree = await browse_nodes(client.nodes.objects)
        _logger.info("Node tree: %r", tree)
    except Exception:
        _logger.exception("error")
    finally:
        await client.disconnect()


def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(task(loop))
    loop.close()


if __name__ == "__main__":
    main()
