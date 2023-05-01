import sys
sys.path.insert(0, "..")
import asyncio

from asyncua import Server
from asyncua.common.instantiate_util import instantiate


async def main():

    # setup our server
    server = Server()
    await server.init()

    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # create our custom object type
    dev = await server.nodes.base_object_type.add_object_type(0, "MyDevice")
    var = await dev.add_variable(0, "sensor1", 1.0)
    await var.set_modelling_rule(True)  # make that child instantiated by default
    prop = await dev.add_property(0, "device_id", "0340")
    await prop.set_modelling_rule(True)
    ctrl = await dev.add_object(0, "controller")
    await ctrl.set_modelling_rule(True)
    prop = await ctrl.add_property(0, "state", "Idle")
    await prop.set_modelling_rule(True)

    # instantiate our new object type
    nodes = await instantiate(server.nodes.objects, dev, bname="2:Device0001")
    mydevice = nodes[0]  # the first node created is our main object
    #mydevice = server.nodes.objects.add_object(2, "Device0001", objecttype=dev)  # specificying objecttype to add_object also instanciate a node type
    mydevice_var = await mydevice.get_child(["0:controller", "0:state"])  # get proxy to our device state variable

    # starting!
    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
