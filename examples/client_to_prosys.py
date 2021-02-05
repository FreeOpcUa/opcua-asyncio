import asyncio
import logging

from asyncua import Client, ua


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    """
    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


async def main():
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer/"
    # url = "opc.tcp://olivier:olivierpass@localhost:53530/OPCUA/SimulationServer/"
    async with Client(url=url) as client:
        print("Root children are", await client.nodes.root.get_children())


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main())
