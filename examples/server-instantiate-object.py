import sys
sys.path.insert(0, "..")
import time
from IPython import embed


from asyncua import ua, Server, instantiate


if __name__ == "__main__":

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # create our custom object type
    dev = server.nodes.base_object_type.add_object_type(0, "MyDevice")
    dev.add_variable(0, "sensor1", 1.0)
    dev.add_property(0, "device_id", "0340")
    ctrl = dev.add_object(0, "controller")
    ctrl.add_property(0, "state", "Idle")

    # instantiate our new object type
    mydevice = instantiate(server.nodes.objects, dev, bname="2:Device0001")
    #mydevice = server.nodes.objects.add_object(2, "Device0001", objecttype=dev)  # specificying objecttype to add_object also instanciate a node type
    mydevice_var = mydevice.get_child(["0:controller", "0:state"])  # get proxy to our device state variable 

    # starting!
    server.start()

    try:
        mydevice_var.set_value("Running")
        embed()
    finally:
        # close connection, remove subcsriptions, etc
        server.stop()
