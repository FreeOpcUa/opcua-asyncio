import sys
sys.path.insert(0, "..")
import os
# os.environ['PYOPCUA_NO_TYPO_CHECK'] = 'True'

import asyncio
import logging

from opcua import Client, Node, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('opcua')


class SubscriptionHandler:
    def datachange_notification(self, node: Node, val, data):
        """Callback for opcua Subscription"""
        _logger.info('datachange_notification %r %s', node, val)


async def main():
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    client = Client(url=url)
    # client.set_security_string()
    async with client:
        uri = 'http://examples.freeopcua.github.io'
        idx = await client.get_namespace_index(uri)
        var = await client.nodes.objects.get_child([f"{idx}:MyObject", f"{idx}:MyVariable"])

        handler = SubscriptionHandler()
        subscription = await client.create_subscription(500, handler)
        nodes = [
            var,
            client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime),
        ]
        await subscription.subscribe_data_change(nodes)
        await asyncio.sleep(10)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
