import asyncio
import copy
import logging
from datetime import datetime
import time
from math import sin
import sys
sys.path.insert(0, "..")


from asyncua import ua, uamethod, Server


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


# method to be exposed through server

def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


# method to be exposed through server
# uses a decorator to automatically convert to and from variants

@uamethod
def multiply(parent, x, y):
    print("multiply method call with parameters: ", x, y)
    return x * y


async def main():
    # optional: setup logging
    logging.basicConfig(level=logging.INFO)
    #logger = logging.getLogger("asyncua.address_space")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.internal_server")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.uaprocessor")
    # logger.setLevel(logging.DEBUG)

    # now setup our server
    server = Server()
    await server.init()
    #server.disable_clock()
    #server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("FreeOpcUa Example Server")
    # set all possible endpoint policies for clients to connect through
    server.set_security_policy([
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign])

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # create a new node type we can instantiate in our address space
    dev = await server.nodes.base_object_type.add_object_type(idx, "MyDevice")
    await (await dev.add_variable(idx, "sensor1", 1.0)).set_modelling_rule(True)
    await (await dev.add_property(idx, "device_id", "0340")).set_modelling_rule(True)
    ctrl = await dev.add_object(idx, "controller")
    await ctrl.set_modelling_rule(True)
    await (await ctrl.add_property(idx, "state", "Idle")).set_modelling_rule(True)

    # populating our address space

    # First a folder to organise our nodes
    myfolder = await server.nodes.objects.add_folder(idx, "myEmptyFolder")
    # instanciate one instance of our device
    mydevice = await server.nodes.objects.add_object(idx, "Device0001", dev)
    mydevice_var = await mydevice.get_child([f"{idx}:controller", f"{idx}:state"])  # get proxy to our device state variable 
    # create directly some objects and variables
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()    # Set MyVariable to be writable by clients
    mystringvar = await myobj.add_variable(idx, "MyStringVariable", "Really nice string")
    await mystringvar.set_writable()    # Set MyVariable to be writable by clients
    mydtvar = await myobj.add_variable(idx, "MyDateTimeVar", datetime.utcnow())
    await mydtvar.set_writable()    # Set MyVariable to be writable by clients
    myarrayvar = await myobj.add_variable(idx, "myarrayvar", [6.7, 7.9])
    myarrayvar = await myobj.add_variable(idx, "myStronglytTypedVariable", ua.Variant([], ua.VariantType.UInt32))
    myprop = await myobj.add_property(idx, "myproperty", "I am a property")
    mymethod = await myobj.add_method(idx, "mymethod", func, [ua.VariantType.Int64], [ua.VariantType.Boolean])
    multiply_node = await myobj.add_method(idx, "multiply", multiply, [ua.VariantType.Int64, ua.VariantType.Int64], [ua.VariantType.Int64])

    # import some nodes from xml
    await server.import_xml("custom_nodes.xml")

    # creating a default event object
    # The event object automatically will have members for all events properties
    # you probably want to create a custom event type, see other examples
    myevgen = await server.get_event_generator()
    myevgen.event.Severity = 300

    # starting!
    await server.start()
    print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())
    try:
        # enable following if you want to subscribe to nodes on server side
        #handler = SubHandler()
        #sub = server.create_subscription(500, handler)
        #handle = sub.subscribe_data_change(myvar)
        # trigger event, all subscribed clients wil receive it
        var = await myarrayvar.get_value()  # return a ref to value in db server side! not a copy!
        var = copy.copy(var)  # WARNING: we need to copy before writting again otherwise no data change event will be generated
        var.append(9.3)
        await myarrayvar.set_value(var)
        await mydevice_var.set_value("Running")
        myevgen.trigger(message="This is BaseEvent")
        server.set_attribute_value(myvar.nodeid, ua.DataValue(0.9))  # Server side write method which is a but faster than using set_value
        while True:
            await asyncio.sleep(0.1)
            server.set_attribute_value(myvar.nodeid, ua.DataValue(sin(time.time())))


    finally:
        await server.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main())
