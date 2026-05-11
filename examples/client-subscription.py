import sys

sys.path.insert(0, "..")
# os.environ['PYOPCUA_NO_TYPO_CHECK'] = 'True'

import asyncio
import logging

from asyncua import Client, ua
from asyncua.common.subscription import DataChangeEvent, StatusChangeEvent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")


async def main():
    """
    Client-Subscription example using the async-iterator API.
    """
    client = Client(url="opc.tcp://localhost:4840/freeopcua/server/")
    async with client:
        idx = await client.get_namespace_index(uri="http://examples.freeopcua.github.io")
        var = await client.nodes.objects.get_child(f"{idx}:MyObject/{idx}:MyVariable")
        # Create a Client Subscription without a handler: this opts into the
        # async-iterator API. Events are buffered in a queue (queue_maxsize)
        # and consumed via `async for` — user code never blocks the publish loop.
        async with await client.create_subscription(500) as subscription:
            nodes = [
                var,
                client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime),
            ]
            await subscription.subscribe_data_change(nodes)

            async def consume():
                async for event in subscription:
                    match event:
                        case DataChangeEvent(node=node, value=value):
                            _logger.info("data change %r %s", node, value)
                        case StatusChangeEvent(status=status):
                            _logger.info("status change %s", status)

            consumer = asyncio.create_task(consume())
            await asyncio.sleep(10)
            consumer.cancel()
            # Exiting the `async with subscription` block deletes the subscription.


if __name__ == "__main__":
    asyncio.run(main())
