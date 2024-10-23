import sys

sys.path.insert(0, "..")
import logging
import asyncio

from IPython import embed

from asyncua import Client


async def main():
    logging.basicConfig(level=logging.INFO)

    # client = Client("opc.tcp://opcua.demo-this.com:51210/UA/SampleServer")
    client = Client("opc.tcp://opcuaserver.com:48010")
    client.name = "TOTO"
    client.application_uri = "urn:freeopcua:clientasync"
    async with client:
        struct = client.get_node("ns=3;s=ControllerConfigurations")
        # struct = client.get_node("ns=2;i=10239")
        before = await struct.read_value()
        # data = await client.load_type_definitions()  # scan server for custom structures and import them. legacy code
        data = await client.load_data_type_definitions()  # scan server for custom structures and import them
        after = await struct.read_value()
        print("BEFORE", before)
        print("AFTER", after)
        embed()


if __name__ == "__main__":
    asyncio.run(main())
