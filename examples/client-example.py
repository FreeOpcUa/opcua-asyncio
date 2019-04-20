
import asyncio
import logging

from asyncua import Client

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another 
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        print("New data change event", node, val)

    def event_notification(self, event):
        print("New event", event)


async def run():
    url = "opc.tcp://localhost:4840/freeopcua/server/"
    try:
        async with Client(url=url) as client:
            root = client.get_root_node()
            _logger.info("Root node is: %r", root)
            objects = client.get_objects_node()
            _logger.info("Objects node is: %r", objects)

            # Node objects have methods to read and write node attributes as well as browse or populate address space
            _logger.info("Children of root are: %r", await root.get_children())

            uri = "http://examples.freeopcua.github.io"
            idx = await client.get_namespace_index(uri)
            _logger.info("index of our namespace is %s", idx)
            # get a specific node knowing its node id
            #var = client.get_node(ua.NodeId(1002, 2))
            #var = client.get_node("ns=3;i=2002")
            #print(var)
            #var.get_data_value() # get value of node as a DataValue object
            #var.get_value() # get value of node as a python builtin
            #var.set_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
            #var.set_value(3.9) # set node value using implicit data type

            # Now getting a variable node using its browse path
            myvar = await root.get_child(["0:Objects", "2:MyObject", "2:MyVariable"])
            obj = await root.get_child(["0:Objects", "2:MyObject"])
            _logger.info("myvar is: %r", myvar)

            # subscribing to a variable node
            handler = SubHandler()
            sub = await client.create_subscription(500, handler)
            handle = await sub.subscribe_data_change(myvar)
            await asyncio.sleep(0.1)

            # we can also subscribe to events from server
            await sub.subscribe_events()
            # await sub.unsubscribe(handle)
            # await sub.delete()

            # calling a method on server
            res = await obj.call_method("2:multiply", 3, "klk")
            _logger.info("method result is: %r", res)
    except Exception:
        _logger.exception('error')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run())

