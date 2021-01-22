import asyncio
import logging
import sys
sys.path.insert(0, "..")
from IPython import embed

from asyncua import ua, uamethod, Server


async def main():
    logging.basicConfig(level=logging.INFO)
    server = Server()
    await server.init()
    # import some nodes from xml
    await server.import_xml("../schemas/UA-Nodeset-master/DI/Opc.Ua.Di.NodeSet2.xml")
    await server.import_xml("../schemas/UA-Nodeset-master/Robotics/Opc.Ua.Robotics.NodeSet2.xml")

    # starting!
    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
