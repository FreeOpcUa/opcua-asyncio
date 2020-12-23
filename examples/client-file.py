import asyncio
from asyncua import ua
from asyncua.client import Client
from asyncua.client.ua_file import UaFile

async def read_file():
    """ read file example """

    url = "opc.tcp://10.0.0.199:4840"
    async with Client(url=url) as client:
        file_node = client.get_node("ns=2;s=NameOfNode")
        ua_file_client = UaFile(file_node)

        # open(), read(), close() all in one operation
        contents = await ua_file_client.read_once()
        print(contents)

        # handling all methods by the user
        handle = await ua_file_client.open(ua.OpenFileMode.Read.value)
        size = await ua_file_client.get_size()
        contents = await ua_file_client.read(handle, size)
        await ua_file_client.close(handle)
        print(contents)


asyncio.run(read_file())
