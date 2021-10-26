import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import ua, Server
from asyncua.common.methods import uamethod



@uamethod
def func(parent, value):
    return value * 2


async def main():
    """
    This example show how to host the server in an environment, where the expected endpoint addresses does not match
    the address the server listens to. This, for example, can be behind a NAT or in a Docker container.

    The server address the server listens to could be in range 172.16.x.x in case of Docker (represented by 0.0.0.0),
    while the endpoint description can be a real IP:port that the Docker host
    machine has (example-endpoint.freeopcua.github.com:32000 in this example)
    """
    _logger = logging.getLogger('asyncua')
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://example-endpoint.freeopcua.github.com:32000/freeopcua/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    # setting the network properties
    server.socket_address = ("0.0.0.0", 4840)
    server.set_match_discovery_client_ip(False)

    # populating our address space
    myvar = await server.get_objects_node().add_variable(idx, 'MyVariable', 0.0)
    # Set MyVariable to be writable by clients
    await myvar.set_writable()

    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(1)
            new_val = await myvar.get_value() + 0.1
            _logger.info('Set value of %s to %.1f', myvar, new_val)
            await myvar.write_value(new_val)


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    asyncio.run(main(), debug=True)
