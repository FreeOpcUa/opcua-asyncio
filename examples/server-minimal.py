
import logging
import asyncio

from asyncua import ua, Server
from asyncua.common.methods import uamethod


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


@uamethod
def func(parent, value):
    return value * 2


async def main():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')
    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)
    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()
    # populating our address space
    myobj = await objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable(idx, 'MyVariable', 6.7)
    # Set MyVariable to be writable by clients
    await myvar.set_writable()
    await objects.add_method(
        ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2),
        func, [ua.VariantType.Int64], [ua.VariantType.Int64]
    )
    _logger.info('Starting server!')
    async with server:
        count = 0
        while True:
            await asyncio.sleep(1)
            count += 0.1
            _logger.info('Set value of %s to %.1f', myvar, count)
            await myvar.write_value(count)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    loop.run_until_complete(main())
    loop.close()
