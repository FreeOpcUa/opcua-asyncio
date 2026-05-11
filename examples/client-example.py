import asyncio
import logging

from asyncua import Client
from asyncua.common.subscription import DataChangeEvent, OpcEvent

_logger = logging.getLogger(__name__)


async def main():
    url = "opc.tcp://localhost:4840/freeopcua/server/"
    async with Client(url=url) as client:
        _logger.info("Root node is: %r", client.nodes.root)
        _logger.info("Objects node is: %r", client.nodes.objects)

        # Node objects have methods to read and write node attributes as well as browse or populate address space
        _logger.info("Children of root are: %r", await client.nodes.root.get_children())

        uri = "http://examples.freeopcua.github.io"
        idx = await client.get_namespace_index(uri)
        _logger.info("index of our namespace is %s", idx)

        # Now getting a variable node using its browse path
        myvar = await client.nodes.root.get_child("/Objects/2:MyObject/2:MyVariable")
        obj = await client.nodes.root.get_child("Objects/2:MyObject")
        _logger.info("myvar is: %r", myvar)

        # Subscribe with the async-iterator API: notifications arrive in a
        # buffered queue that we consume here without blocking the publish loop.
        async with await client.create_subscription(10) as sub:
            await sub.subscribe_data_change(myvar)
            await sub.subscribe_events()

            async def consume():
                async for event in sub:
                    match event:
                        case DataChangeEvent(node=node, value=value):
                            print("New data change event", node, value)
                        case OpcEvent(event=evt):
                            print("New event", evt)

            consumer = asyncio.create_task(consume())

            # calling a method on server
            res = await obj.call_method("2:multiply", 3, "klk")
            _logger.info("method result is: %r", res)
            try:
                while True:
                    await asyncio.sleep(1)
            finally:
                consumer.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
