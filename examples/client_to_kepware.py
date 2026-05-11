import asyncio
import logging
import sys

sys.path.insert(0, "..")

from asyncua import Client
from asyncua.common.subscription import DataChangeEvent, OpcEvent


async def main() -> None:
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer/"
    async with Client(url=url) as client:
        print("Root children are", await client.nodes.root.get_children())

        tag1 = client.get_node("ns=2;s=Channel1.Device1.Tag1")
        print(f"tag1 is: {tag1} with value {await tag1.read_value()} ")
        tag2 = client.get_node("ns=2;s=Channel1.Device1.Tag2")
        print(f"tag2 is: {tag2} with value {await tag2.read_value()} ")

        async with await client.create_subscription(500) as sub:
            await sub.subscribe_data_change(tag1)
            await sub.subscribe_data_change(tag2)

            async for event in sub:
                match event:
                    case DataChangeEvent(node=node, value=value):
                        print("Python: New data change event", node, value)
                    case OpcEvent(event=evt):
                        print("Python: New event", evt)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main())
