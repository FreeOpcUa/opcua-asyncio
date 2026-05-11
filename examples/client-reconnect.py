import asyncio
import logging

from asyncua import Client, ua
from asyncua.common.subscription import DataChangeEvent, StatusChangeEvent

_logger = logging.getLogger(__name__)


async def main():
    """
    Demonstrates auto_reconnect=True: the client recovers transport drops
    transparently, and the supervisor re-creates subscriptions for us. We
    consume notifications via the async-iterator API.
    """
    client = Client(url="opc.tcp://localhost:4840/freeopcua/server/")
    await client.connect(auto_reconnect=True, reconnect_max_delay=2.0)
    try:
        async with await client.create_subscription(500) as sub:
            node = client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime)
            await sub.subscribe_data_change([node])
            async for event in sub:
                match event:
                    case DataChangeEvent(node=n, value=v):
                        _logger.info("data change %r %s", n, v)
                    case StatusChangeEvent(status=s):
                        _logger.info("status change %s", s)
                        if s.is_bad():
                            break
    finally:
        await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
