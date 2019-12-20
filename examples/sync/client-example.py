import sys
sys.path.insert(0, "..")
import logging
import time

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()


from asyncua.sync import Client, ThreadLoop


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    #logger = logging.getLogger("KeepAlive")
    #logger.setLevel(logging.DEBUG)

    with ThreadLoop() as tloop:
        with Client("opc.tcp://localhost:4840/freeopcua/server/", tloop=tloop) as client:
            # client = Client("opc.tcp://admin@localhost:4840/freeopcua/server/") #connect using a user
            client.load_type_definitions()  # load definition of server specific structures/extension objects

            # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
            print("Objects node is: ", client.nodes.objects)

            # Node objects have methods to read and write node attributes as well as browse or populate address space
            print("Children of root are: ", client.nodes.root.get_children())

            # get a specific node knowing its node id
            #var = client.get_node(ua.NodeId(1002, 2))
            #var = client.get_node("ns=3;i=2002")
            #print(var)
            #var.get_data_value() # get value of node as a DataValue object
            #var.read() # get value of node as a python builtin
            #var.write(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
            #var.write(3.9) # set node value using implicit data type

            # gettting our namespace idx
            uri = "http://examples.freeopcua.github.io"
            idx = client.get_namespace_index(uri)

            # Now getting a variable node using its browse path
            myvar = client.nodes.root.get_child(["0:Objects", "{}:MyObject".format(idx), "{}:MyVariable".format(idx)])
            obj = client.nodes.root.get_child(["0:Objects", "{}:MyObject".format(idx)])
            print("myvar is: ", myvar)

            # subscribing to a variable node
            handler = SubHandler()
            sub = client.create_subscription(500, handler)
            handle = sub.subscribe_data_change(myvar)
            time.sleep(0.1)

            # we can also subscribe to events from server
            sub.subscribe_events()
            # sub.unsubscribe(handle)
            # sub.delete()

            # calling a method on server
            res = obj.call_method("{}:multiply".format(idx), 3, "klk")
            print("method result is: ", res)

            embed()
