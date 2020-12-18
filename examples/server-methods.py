import asyncio
import logging

from asyncua import ua, uamethod, Server


# method to be exposed through server
def func(parent, variant):
    print("func method call with parameters: ", variant.Value)
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


# method to be exposed through server
async def func_async(parent, variant):
    if variant.Value % 2 == 0:
        print("Sleeping asynchronously for 1 second")
        await asyncio.sleep(1)
    else:
        print("Not sleeping!")


# method to be exposed through server
# uses a decorator to automatically convert to and from variants


@uamethod
def multiply(parent, x, y):
    print("multiply method call with parameters: ", x, y)
    return x * y


@uamethod
async def multiply_async(parent, x, y):
    sleep_time = x * y
    print(f"Sleeping asynchronously for {x * y} seconds")
    await asyncio.sleep(sleep_time)


async def main():
    # optional: setup logging
    logging.basicConfig(level=logging.WARN)
    # logger = logging.getLogger("asyncua.address_space")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("asyncua.internal_server")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("asyncua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("asyncua.uaprocessor")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("asyncua.subscription_service")
    # logger.setLevel(logging.DEBUG)

    # now setup our server
    server = Server()
    await server.init()
    # server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("FreeOpcUa Example Server")

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.nodes.objects

    # populating our address space
    await objects.add_folder(idx, "myEmptyFolder")
    myobj = await objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()  # Set MyVariable to be writable by clients
    myarrayvar = await myobj.add_variable(idx, "myarrayvar", [6.7, 7.9])
    await myobj.add_variable(
        idx, "myStronglytTypedVariable", ua.Variant([], ua.VariantType.UInt32)
    )
    await myobj.add_property(idx, "myproperty", "I am a property")
    await myobj.add_method(idx, "mymethod", func, [ua.VariantType.Int64], [ua.VariantType.Boolean])

    inargx = ua.Argument()
    inargx.Name = "x"
    inargx.DataType = ua.NodeId(ua.ObjectIds.Int64)
    inargx.ValueRank = -1
    inargx.ArrayDimensions = []
    inargx.Description = ua.LocalizedText("First number x")
    inargy = ua.Argument()
    inargy.Name = "y"
    inargy.DataType = ua.NodeId(ua.ObjectIds.Int64)
    inargy.ValueRank = -1
    inargy.ArrayDimensions = []
    inargy.Description = ua.LocalizedText("Second number y")
    outarg = ua.Argument()
    outarg.Name = "Result"
    outarg.DataType = ua.NodeId(ua.ObjectIds.Int64)
    outarg.ValueRank = -1
    outarg.ArrayDimensions = []
    outarg.Description = ua.LocalizedText("Multiplication result")

    await myobj.add_method(idx, "multiply", multiply, [inargx, inargy], [outarg])
    await myobj.add_method(idx, "multiply_async", multiply_async, [inargx, inargy], [])
    await myobj.add_method(idx, "func_async", func_async, [ua.VariantType.Int64], [])

    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
