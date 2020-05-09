import sys
import asyncio
import logging

sys.path.insert(0, "..")

from asyncua import Server, ua


async def main():

    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # load server certificate and private key. This enables endpoints
    # with signing and encryption.
    await server.load_certificate("certificate-example.der")
    await server.load_private_key("private-key-example.pem")

    # set all possible endpoint policies for clients to connect through
    server.set_security_policy([
        ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
        ua.SecurityPolicyType.Basic256Sha256_Sign,
    ])

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # populating our address space
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()  # Set MyVariable to be writable by clients

    # starting!
    async with server:
        count = 0
        while True:
            await asyncio.sleep(1)
            count += 0.1
            await myvar.write_value(count)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
