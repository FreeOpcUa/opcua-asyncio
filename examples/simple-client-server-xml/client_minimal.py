import asyncio
import logging

from asyncua import Client


class HelloClient:
    def __init__(self, endpoint):
        self.client = Client(endpoint)

    async def __aenter__(self):
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()


async def main():
    async with HelloClient("opc.tcp://localhost:4840/freeopcua/server/") as client:
        root = client.nodes.root
        print("Root node is: ", root)
        objects = client.nodes.objects
        print("Objects node is: ", objects)

        hellower = await objects.get_child("0:Hellower")
        print("Hellower is: ", hellower)

        resulting_text = await hellower.call_method("0:SayHello", False)
        print(resulting_text)

        resulting_text = await hellower.call_method("1:SayHello2", True)
        print(resulting_text)

        resulting_array = await hellower.call_method("1:SayHelloArray", False)
        print(resulting_array)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
