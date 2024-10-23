import sys

sys.path.insert(0, "..")
import logging
import asyncio

from IPython import embed

from asyncua import Client


async def main():
    logging.basicConfig(level=logging.WARN)
    # async with Client("opc.tcp://asyncua.demo-this.com:51210/UA/SampleServer") as client:
    async with Client("opc.tcp://localhost:4840/UA/SampleServer") as client:
        uri = "http://examples.freeopcua.github.io"
        idx = await client.get_namespace_index(uri)

        struct = await client.nodes.objects.get_child(f"{idx}:BasicStruct")
        nested_struct = await client.nodes.objects.get_child(f"{idx}:NestedStruct")
        before = await struct.read_value()
        before_array = await nested_struct.read_value()
        await client.load_type_definitions()  # scan server for custom structures and import them
        after = await struct.read_value()
        after_array = await nested_struct.read_value()
        print("before", before, before_array)
        print("after", after, after_array)
        embed(header="use %autowait on to call async calls")


if __name__ == "__main__":
    asyncio.run(main())
