import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.methods import uamethod


@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger("asyncua")
    # setup our server
    server = Server()

    # set some hard connection limits
    #server.limits.max_recv_buffer = 1024
    #server.limits.max_send_buffer = 1024
    #server.limits.max_send_buffer = 102400000000
    server.limits.max_chunk_count = 10
    print(server.limits)
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # populating our address space
    # set up a variable far too big for our limits
    test_string = b'a' * (100 * 1024 * 1024)
    test_string = b'a' * 100 * 1024
    print("LENGTH VAR", len(test_string))
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", test_string)
    # Set MyVariable to be writable by clients
    await myvar.set_writable()
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main(), debug=False)
