import asyncio
from asyncua import Client

async def read_file():
    """ read file example """

    url = "opc.tcp://10.0.0.199:4840"
    async with Client(url=url) as client:
        node = client.get_node("ns=2;s=NameOfNode")
        contents = await client.read_file(node)
        print(contents)

asyncio.run(read_file())
