import asyncio
from asyncua import ua
from asyncua.client import Client
from asyncua.client.ua_file import UaFile


async def read_file():
    """ read file example """

    url = "opc.tcp://10.0.0.199:4840"
    async with Client(url=url) as client:

        file_node = client.get_node("ns=2;s=NameOfNode")
        async with UaFile(file_node) as ua_file:
            # open(), read(), close() all in one operation
            contents = await ua_file.read_once()
            print(contents)

            # handling all methods by the user
            handle = await ua_file.open(ua.OpenFileMode.Read.value)
            size = await ua_file.get_size()
            contents = await ua_file.read(handle, size)
            await ua_file.close(handle)
            print(contents)


asyncio.run(read_file())
