import asyncio
import logging

from asyncua import Client

url = "opc.tcp://localhost:4840/freeopcua/server/"
namespace = "http://examples.freeopcua.github.io"


async def main():
    print(f"Connecting to {url} ...")
    async with Client(url=url, watchdog_intervall=1000) as client:
        # Find the namespace index
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")

        # Get the variable node for read / write
        var = await client.nodes.root.get_child(["0:Objects", f"{nsidx}:MyObject", f"{nsidx}:MyVariable"])
        print("READ!!!!!!!!!!!!!!!!!")
        value = await var.read_value()
        print("Received value of length !!!!!!!!!!!!!!!!!!!!!", len(value))

        print("writting back value of MyVariable ")
        await var.write_value(value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
