'''
   Show 3 different examples for creating an object:
   1) create a basic object
   2) create a new object type and a instance of the new object type
   3) import a new object from xml address space and create a instance of the new object type
'''
import sys
sys.path.insert(0, "..")
import asyncio

import asyncua

from asyncua import ua, Server


async def main():

    # setup our server
    server = Server()
    await server.init()

    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # Example 1 - create a basic object
    #-------------------------------------------------------------------------------
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    #-------------------------------------------------------------------------------

    # Example 2 - create a new object type and a instance of the new object type
    #-------------------------------------------------------------------------------
    mycustomobj_type = await server.nodes.base_object_type.add_object_type(idx, "MyCustomObjectType")
    await mycustomobj_type.add_variable(0, "var_should_be_there_after_instantiate", 1.0)  # demonstrates instantiate

    myobj = await server.nodes.objects.add_object(idx, "MyCustomObjectA", mycustomobj_type.nodeid)
    #-------------------------------------------------------------------------------

    # Example 3 - import a new object from xml address space and create a instance of the new object type
    #-------------------------------------------------------------------------------
    # Import customobject type
    await server.import_xml('customobject.xml')

    # get nodeid of custom object type by one of the following 2 ways:
    # 1) Use node ID
    # 3) Or As child from BaseObjectType
    myobject1_type_nodeid = ua.NodeId.from_string('ns=%d;i=2' % idx)
    myobject2_type_nodeid = (await server.nodes.base_object_type.get_child([f"{idx}:MyCustomObjectType"])).nodeid

    # populating our address space
    myobj = await server.nodes.objects.add_object(idx, "MyCustomObjectB", myobject2_type_nodeid)
    #-------------------------------------------------------------------------------

    # starting!
    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
