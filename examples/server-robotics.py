import asyncio
import logging
import sys
sys.path.insert(0, "..")

from asyncua import Server


async def main():
    logging.basicConfig(level=logging.INFO)
    server = Server()
    await server.init()
    # import some nodes from xml
    nodes1 = await server.import_xml("../schemas/UA-Nodeset-master/DI/Opc.Ua.Di.NodeSet2.xml")
    nodes2 = await server.import_xml("../schemas/UA-Nodeset-master/Robotics/Opc.Ua.Robotics.NodeSet2.xml")
    nodes1 = [server.get_node(node) for node in nodes1]
    nodes2 = [server.get_node(node) for node in nodes2]
    await server.export_xml(nodes1, "di.xml")
    await server.export_xml(nodes2, "rob.xml")

    # starting!
    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
