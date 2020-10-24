import sys
sys.path.insert(0, "..")
import logging
import asyncio

from asyncua import Client


async def main():
    client = Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/")
    client.set_security_string("Basic256Sha256,Sign,certificate-example.der,private-key-example.pem")
    async with client:
        root = client.nodes.root
        objects = client.nodes.objects
        print("childs og objects are: ", await objects.get_children())
        await asyncio.sleep(3)



if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main())
