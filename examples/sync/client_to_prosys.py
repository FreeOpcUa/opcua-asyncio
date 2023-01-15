import logging

from asyncua.sync import Client


class SubHandler(object):

    """
    Client to subscription. It will receive events from server
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


if __name__ == "__main__":
    from IPython import embed
    logging.basicConfig(level=logging.DEBUG)
    #client = Client("opc.tcp://olivier:olivierpass@localhost:53530/OPCUA/SimulationServer/")
    #client.set_security_string("Basic256Sha256,SignAndEncrypt,certificate-example.der,private-key-example.pem")
    with Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/") as client:
        root = client.nodes.root
        print("Root is", root)
        print("children of root are: ", root.get_children())
        print("name of root is", root.read_browse_name())
        objects = client.nodes.objects
        print("children og objects are: ", objects.get_children())
        embed()
