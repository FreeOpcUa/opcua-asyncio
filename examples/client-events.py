import asyncio
import logging

from asyncua import Client
from asyncua.common.subscription import OpcEvent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


async def main():
    url = "opc.tcp://localhost:4840/freeopcua/server/"
    # url = "opc.tcp://admin@localhost:4840/freeopcua/server/"  #connect using a user
    async with Client(url=url) as client:
        # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
        _logger.info("Objects node is: %r", client.nodes.root)

        # Now getting a variable node using its browse path
        obj = await client.nodes.root.get_child(["0:Objects", "2:MyObject"])
        _logger.info("MyObject is: %r", obj)

        myevent = await client.nodes.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "2:MyFirstEvent"])
        _logger.info("MyFirstEventType is: %r", myevent)

        # Iterator-mode subscription (no handler).
        async with await client.create_subscription(100) as sub:
            await sub.subscribe_events(obj, myevent)

            async def consume():
                async for event in sub:
                    if isinstance(event, OpcEvent):
                        _logger.info("New event received: %r", event.event)

            consumer = asyncio.create_task(consume())
            await asyncio.sleep(10)
            consumer.cancel()


if __name__ == "__main__":
    asyncio.run(main())
