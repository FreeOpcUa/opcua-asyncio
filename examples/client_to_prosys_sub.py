import asyncio
import logging

from asyncua import Client
from asyncua.common.subscription import DataChangeEvent, OpcEvent, StatusChangeEvent

URL = "opc.tcp://localhost:53530/OPCUA/SimulationServer"
NODE_ID = "ns=3;i=1002"


async def main() -> None:
    client = Client(url=URL)
    await client.connect(auto_reconnect=True, reconnect_max_delay=5.0)
    try:
        node = client.get_node(NODE_ID)
        async with await client.create_subscription(500) as sub:
            await sub.subscribe_data_change(node)
            async for event in sub:
                match event:
                    case DataChangeEvent(node=n, value=v):
                        print(f"data change {n} = {v}")
                    case OpcEvent(event=evt):
                        print(f"event {evt}")
                    case StatusChangeEvent(notification=n):
                        print(f"status change {n.Status}")
                        if n.Status.is_bad():
                            break
    finally:
        await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
