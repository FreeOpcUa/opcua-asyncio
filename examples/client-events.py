import asyncio
import logging

from asyncua import Client

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class SubHandler:
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def event_notification(self, event):
        _logger.info("New event received: %r", event)


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

        msclt = SubHandler()
        sub = await client.create_subscription(100, msclt)
        handle = await sub.subscribe_events(obj, myevent)
        await asyncio.sleep(10)
        await sub.unsubscribe(handle)
        await sub.delete()


if __name__ == "__main__":
    asyncio.run(main())
