import sys
sys.path.insert(0, "..")
import time
import logging

from asyncua.sync import Client, start_thread_loop, stop_thread_loop
from asyncua import ua


class SubHandler(object):

    """
    Client to subscription. It will receive events from server
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


if __name__ == "__main__":
    #from IPython import embed
    logging.basicConfig(level=logging.DEBUG)
    #client = Client("opc.tcp://olivier:olivierpass@localhost:53530/OPCUA/SimulationServer/")
    #client.set_security_string("Basic256Sha256,SignAndEncrypt,certificate-example.der,private-key-example.pem")
    try:
        start_thread_loop()
        client = Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/")
        client.connect()
        root = client.nodes.root
        print("Root is", root)
        print("childs of root are: ", root.get_children())
        print("name of root is", root.get_browse_name())
        objects = client.nodes.objects
        print("childs og objects are: ", objects.get_children())
        myfloat = client.get_node("ns=4;s=Float")
        mydouble = client.get_node("ns=4;s=Double")
        myint64 = client.get_node("ns=4;s=Int64")
        myuint64 = client.get_node("ns=4;s=UInt64")
        myint32 = client.get_node("ns=4;s=Int32")
        myuint32 = client.get_node("ns=4;s=UInt32")

        var = client.get_node(ua.NodeId("Random1", 5))
        print("var is: ", var)
        print("value of var is: ", var.get_value())
        var.set_value(ua.Variant([23], ua.VariantType.Double))
        print("setting float value")
        myfloat.set_value(ua.Variant(1.234, ua.VariantType.Float))
        print("reading float value: ", myfloat.get_value())

        handler = SubHandler()
        sub = client.create_subscription(500, handler)
        handle = sub.subscribe_data_change(var)

        device = objects.get_child(["2:MyObjects", "2:MyDevice"])
        method = device.get_child("2:MyMethod")
        result = device.call_method(method, ua.Variant("sin"), ua.Variant(180, ua.VariantType.Double))
        print("Mehtod result is: ", result)

        #embed()
        time.sleep(3)
        sub.unsubscribe(handle)
        sub.delete()
        #client.close_session()
    finally:
        client.disconnect()
        stop_thread_loop()
