import asyncio

from asyncua.client import Client
from asyncua.client.ua_file import UaFile


async def read_file():
    """read file example"""

    url = "opc.tcp://10.0.0.199:4840"
    async with Client(url=url) as client:
        file_node = client.get_node("ns=2;s=NameOfNode")
        async with UaFile(file_node, "r") as ua_file:
            contents = await ua_file.read()  # read file
            print(contents)


asyncio.run(read_file())
