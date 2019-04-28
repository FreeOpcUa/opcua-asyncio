import sys
sys.path.insert(0, "..")
import os
# os.environ['PYOPCUA_NO_TYPO_CHECK'] = 'True'

import asyncio
import logging

from asyncua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        _logger.info('datachange_notification %r %s', node, val)


async def main():
    """
    Main task of this Client-Subscription example.
    """
    client = Client(url='opc.tcp://localhost:4840/freeopcua/server/')
    async with client:
        idx = await client.get_namespace_index(uri="http://examples.freeopcua.github.io")
        var = await client.nodes.objects.get_child([f"{idx}:MyObject", f"{idx}:MyVariable"])
        handler = SubscriptionHandler()
        # We create a Client Subscription.
        subscription = await client.create_subscription(500, handler)
        nodes = [
            var,
            client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime),
        ]
        # We subscribe to data changes for two nodes (variables).
        await subscription.subscribe_data_change(nodes)
        # We let the subscription run for ten seconds
        await asyncio.sleep(10)
        # We delete the subscription (this un-subscribes from the data changes of the two variables).
        # This is optional since closing the connection will also delete all subscriptions.
        await subscription.delete()
        # After one second we exit the Client context manager - this will close the connection.
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
