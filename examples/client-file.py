import asyncio
from asyncua.client import Client
from asyncua.client.ua_file import UaFileRead

async def read_file():
    """ read file example """

    url = "opc.tcp://10.0.0.199:4840"
    async with Client(url=url) as client:
        file_node = client.get_node("ns=2;s=NameOfNode")
        async with UaFileRead(file_node) as ua_file:
            # read file
            contents = await ua_file.read()
            print(contents)

asyncio.run(read_file())
