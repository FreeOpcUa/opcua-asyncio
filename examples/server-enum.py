'''
  This example demonstrates the use of custom enums by:
  - Create a custom enum type
  - Create an object that contains a variable of this type
'''
import sys
sys.path.insert(0, "..")
import time
import asyncio

from IPython import embed

from asyncua import ua, Server


async def main():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    nsidx = await server.register_namespace(uri)

    # --------------------------------------------------------
    # create custom enum data type
    # --------------------------------------------------------

    # 1.
    # Create Enum Type
    myenum_type = await server.nodes.enum_data_type.add_data_type(nsidx, 'MyEnum')

    # 2.
    # Add enumerations as EnumStrings (Not yet tested with EnumValues)
    # Essential to use namespace 0 for EnumStrings !

    es = await myenum_type.add_property(0, "EnumStrings", [
        ua.LocalizedText("ok"),
        ua.LocalizedText("idle"),
    ])

    # 3. load enums froms erver
    await server.load_enums()

    # now we have a python enum available to play with
    val = ua.MyEnum.ok

    # not sure these are necessary
    #es.write_value_rank(1)
    #es.write_array_dimensions([0])

    # --------------------------------------------------------
    # create object with enum variable
    # --------------------------------------------------------

    # create object
    myobj = await server.nodes.objects.add_object(nsidx, 'MyObjectWithEnumVar')

    # add var with as type the custom enumeration
    myenum_var = await myobj.add_variable(nsidx, 'MyEnum2Var', val, datatype=myenum_type.nodeid)
    await myenum_var.set_writable()
    await myenum_var.write_value(ua.MyEnum.idle)  # change value of enumeration

    async with server:
        while True:
            time.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
