import os.path
import asyncio
import logging

from asyncua import ua, uamethod, Server


@uamethod
def say_hello_xml(parent, happy):
    print("Calling say_hello_xml")
    if happy:
        result = "I'm happy"
    else:
        result = "I'm not happy"
    print(result)
    return result


@uamethod
def say_hello(parent, happy):
    if happy:
        result = "I'm happy"
    else:
        result = "I'm not happy"
    print(result)
    return result


@uamethod
def say_hello_array(parent, happy):
    if happy:
        result = "I'm happy"
    else:
        result = "I'm not happy"
    print(result)
    return [result, "Actually I am"]


class HelloServer:
    def __init__(self, endpoint, name, model_filepath):
        self.server = Server()
        self.model_filepath = model_filepath
        self.server.set_server_name(name)
        self.server.set_endpoint(endpoint)

    async def init(self):
        await self.server.init()

        #  This need to be imported at the start or else it will overwrite the data
        await self.server.import_xml(self.model_filepath)

        objects = self.server.nodes.objects

        freeopcua_namespace = await self.server.get_namespace_index(
            "urn:freeopcua:python:server"
        )
        hellower = await objects.get_child("0:Hellower")
        hellower_say_hello = await hellower.get_child("0:SayHello")

        self.server.link_method(hellower_say_hello, say_hello_xml)

        await hellower.add_method(
            freeopcua_namespace,
            "SayHello2",
            say_hello,
            [ua.VariantType.Boolean],
            [ua.VariantType.String],
        )

        await hellower.add_method(
            freeopcua_namespace,
            "SayHelloArray",
            say_hello_array,
            [ua.VariantType.Boolean],
            [ua.VariantType.String],
        )

    async def __aenter__(self):
        await self.init()
        await self.server.start()
        return self.server

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.server.stop()


async def main():
    script_dir = os.path.dirname(__file__)
    async with HelloServer(
        "opc.tcp://0.0.0.0:4840/freeopcua/server/",
        "FreeOpcUa Example Server",
        os.path.join(script_dir, "test_saying.xml"),
    ) as server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
