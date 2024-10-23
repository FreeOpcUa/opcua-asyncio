import sys

sys.path.insert(0, "..")
import logging
import asyncio

from asyncua import Client


async def main():
    client = Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/")
    await client.set_security_string("Basic256Sha256,Sign,certificate-example.der,private-key-example.pem")
    client.session_timeout = 2000
    async with client:
        root = client.nodes.root
        objects = client.nodes.objects
        while True:
            print("childs og objects are: ", await objects.get_children())
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main())
