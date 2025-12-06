import asyncio
import sys

sys.path.insert(0, "..")
import math

from asyncua import Server, ua
from asyncua.server.history_sql import HistorySQLite


async def main():
    # setup our server
    server = Server()

    # Configure server to use sqlite as history database (default is a simple memory dict)
    server.iserver.history_manager.set_storage(HistorySQLite("my_datavalue_history.sql"))

    # initialize server
    await server.init()

    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.nodes.objects

    # populating our address space
    myobj = await objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", ua.Variant(0, ua.VariantType.Double))
    await myvar.set_writable()  # Set MyVariable to be writable by clients
    print(myvar)

    # starting!
    await server.start()

    # enable data change history for this particular node, must be called after start since it uses subscription
    await server.historize_node_data_change(myvar, period=None, count=100)

    try:
        count = 0
        while True:
            await asyncio.sleep(1)
            count += 0.1
            await myvar.write_value(math.sin(count))

    finally:
        # close connection, remove subscriptions, etc
        await server.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main())
