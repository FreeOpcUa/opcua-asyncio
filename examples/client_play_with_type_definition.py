import sys
import asyncio

sys.path.insert(0, "..")
import logging

from IPython import embed

from asyncua import Client
from asyncua.common.structures104 import load_enums


async def main():
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer/"
    # url = "opc.tcp://olivier:olivierpass@localhost:53530/OPCUA/SimulationServer/"
    client = Client(url=url)
    # client.session_timeout=5000
    # client.secure_channel_timeout=8000
    async with client:
        dt = await client.nodes.base_structure_type.get_child("AddNodesItem")
        df = await dt.read_data_type_definition()
        await client.load_data_type_definitions()
        edt = await client.nodes.enum_data_type.get_child("ApplicationType")
        df = await edt.read_data_type_definition()
        await load_enums(client)
        embed()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
