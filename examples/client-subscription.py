import asyncio
import logging

from asyncua import Client, ua
from asyncua.common.subscription import DataChangeEvent, StatusChangeEvent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")


async def main() -> None:
    """
    Client-Subscription example with auto-reconnect.

    Run against examples/server-example.py. Kill and restart the server while
    this script is running: the supervisor reconnects transparently and the
    subscription resumes producing notifications without user intervention.
    """
    client = Client(url="opc.tcp://localhost:4840/freeopcua/server/")
    await client.connect(auto_reconnect=True, reconnect_max_delay=2.0)
    try:
        idx = await client.get_namespace_index(uri="http://examples.freeopcua.github.io")
        var = await client.nodes.objects.get_child(f"{idx}:MyObject/{idx}:MyVariable")
        async with await client.create_subscription(500) as subscription:
            nodes = [
                var,
                client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime),
            ]
            await subscription.subscribe_data_change(nodes)
            async for event in subscription:
                match event:
                    case DataChangeEvent(node=node, value=value):
                        _logger.info("data change %r %s", node, value)
                    case StatusChangeEvent(notification=notif):
                        _logger.info("status change %s", notif.Status)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
