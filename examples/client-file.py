import asyncio
from asyncua import Client

async def read_file():
    """ read file examples """

    url = "opc.tcp://10.0.0.199:4840"
    async with Client(url=url) as client:
        # option 1
        contents = await client.read_file(index=2, name_of_node="NameOfNode")
        print(contents)

        # option 2
        node = client.get_node("ns=2;s=NameOfNode")
        contents = await client.read_file(node=node)
        print(contents)

asyncio.run(read_file())
