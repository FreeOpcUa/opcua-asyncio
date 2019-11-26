# coding: utf-8

import asyncio

from asyncua import Client, ua


class SubHandler(object):

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val, data)

    def event_notification(self, event):
        print("Python new event:", event)


class OpcUaClient(object):

    def __init__(self, endpoint):
        self.client = Client(endpoint)

    async def init(self):
        await self.client.connect()
        objects = self.client.get_objects_node()
        idx = await self.client.get_namespace_index("http://examples.freeopcua.github.io")

        path = ['%s:ConditionObject' % idx]
        con_obj = await objects.get_child(path)
        condition = self.client.get_node(ua.NodeId(2830))

        handler = SubHandler()
        sub = await self.client.create_subscription(500, handler)
        con_handle = await sub.subscribe_events(con_obj, condition)

        path = ['%s:AlarmObject' % idx]
        alarm_obj = await objects.get_child(path)
        alarm = self.client.get_node(ua.NodeId(10637))

        alarm_handle = await sub.subscribe_events(alarm_obj, alarm)


async def start():
    client = OpcUaClient("opc.tcp://localhost:4840")
    await client.init()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
