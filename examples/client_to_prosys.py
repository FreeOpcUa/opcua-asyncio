import sys
import asyncio
sys.path.insert(0, "..")
import logging

from asyncua import Client, ua


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)




async def main():
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer/"
    # url = "opc.tcp://olivier:olivierpass@localhost:53530/OPCUA/SimulationServer/"
    async with Client(url=url) as client:
        print("Root children are", await client.nodes.root.get_children())


        myfloat = client.get_node("ns=4;s=Float")
        mydouble = client.get_node("ns=4;s=Double")
        myint64 = client.get_node("ns=4;s=Int64")
        myuint64 = client.get_node("ns=4;s=UInt64")
        myint32 = client.get_node("ns=4;s=Int32")
        myuint32 = client.get_node("ns=4;s=UInt32")

        var = client.get_node(ua.NodeId("Random1", 5))
        print("var is: ", var)
        print("value of var is: ", await var.read_value())
        await var.write_value(ua.Variant([23], ua.VariantType.Double))
        print("setting float value")
        await myfloat.write_value(ua.Variant(1.234, ua.VariantType.Float))
        print("reading float value: ", await myfloat.read_value())


        device = await client.nodes.objects.get_child(["2:MyObjects", "2:MyDevice"])
        method = await device.get_child("2:MyMethod")
        result = await device.call_method(method, ua.Variant("sin"), ua.Variant(180, ua.VariantType.Double))
        print("Mehtod result is: ", result)


        handler = SubHandler()
        sub = await client.create_subscription(500, handler)
        handle = await sub.subscribe_data_change(var)

        handle2 = await sub.subscribe_events(evtypes=2788)
        cond = await client.nodes.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "0:ConditionType"])
        for _ in range(5):
            # refresh server condition to force generation of events
            await cond.call_method("0:ConditionRefresh", ua.Variant(sub.subscription_id, ua.VariantType.UInt32))

            await asyncio.sleep(1)

        await sub.unsubscribe(handle)
        await sub.unsubscribe(handle2)
        await sub.delete()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main())
    loop.close()
