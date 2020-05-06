import asyncio
import sys
import time
import logging
sys.path.insert(0, "..")

from asyncua import ua
from asyncua import Server

logging.basicConfig(level=logging.INFO)


async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    # load server certificate and private key. This enables endpoints
    # with signing and encryption.
    await server.load_certificate("my_cert.der")
    await server.load_private_key("my_private_key.pem")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.get_objects_node()

    # populating our address space
    myobj = await objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()  # Set MyVariable to be writable by clients

    # starting!
    await server.start()
    try:
        count = 0
        while True:
            await asyncio.sleep(0.1)
            count += 0.1
            await myvar.write_value(count)
    finally:
        # close connection, remove subcsriptions, etc
        await server.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main())
    # setup our server
