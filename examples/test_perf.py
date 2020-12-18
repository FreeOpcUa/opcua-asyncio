import asyncio
import time
import sys
import logging
import cProfile

sys.path.insert(0, "..")
from asyncua import Server, ua



async def mymain():

    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # populating our address space
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()    # Set MyVariable to be writable by clients

    # starting!
    async with server:
        while True:
            await asyncio.sleep(10)
        nb = 100000
        start = time.time()
        for i in range(nb):
            await server.write_attribute_value(myvar.nodeid, ua.DataValue(i))
            await myvar.write_value(i)
    print("\n Write frequency: \n", nb / (time.time() - start))


if __name__ == "__main__":
    #uvloop.install()
    logging.basicConfig(level=logging.WARNING)
    cProfile.run('asyncio.run(mymain(), debug=True)', filename="perf.cprof")
    #asyncio.run(mymain())
