import sys
sys.path.insert(0, "..")
import logging

from asyncua import Client


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
    logging.basicConfig(level=logging.WARN)
    client = Client("opc.tcp://192.168.56.100:49320/OPCUA/SimulationServer/")
    #client = Client("opc.tcp://192.168.56.100:4840/OPCUA/SimulationServer/")
    #client = Client("opc.tcp://olivier:olivierpass@localhost:53530/OPCUA/SimulationServer/")
    try:
        client.connect()
        root = client.get_root_node()
        print("Root is", root)
        print("childs of root are: ", root.get_children())
        print("name of root is", root.get_browse_name())
        objects = client.get_objects_node()
        print("childs og objects are: ", objects.get_children())


        tag1 = client.get_node("ns=2;s=Channel1.Device1.Tag1")
        print("tag1 is: {0} with value {1} ".format(tag1, tag1.read_value()))
        tag2 = client.get_node("ns=2;s=Channel1.Device1.Tag2")
        print("tag2 is: {0} with value {1} ".format(tag2, tag2.read_value()))

        handler = SubHandler()
        sub = client.create_subscription(500, handler)
        handle1 = sub.subscribe_data_change(tag1)
        handle2 = sub.subscribe_data_change(tag2)

        from IPython import embed
        embed()

        
        sub.unsubscribe(handle1)
        sub.unsubscribe(handle2)
        sub.delete()
    finally:
        client.disconnect()
