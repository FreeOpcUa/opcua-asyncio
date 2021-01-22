# coding: utf-8

from aioconsole import ainput

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
        self.subscriptions = {}

    async def __aenter__(self):
        await self.client.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        for sub in self.subscriptions:
            for handle in self.subscriptions[sub]:
                await sub.unsubscribe(handle)
            await sub.delete()
        await self.client.disconnect()

    async def init(self):
        objects = self.client.get_objects_node()
        idx = await self.client.get_namespace_index("http://examples.freeopcua.github.io")

        path = ['%s:NotifierObject' % idx]
        noti_obj = await objects.get_child(path)

        path = ['%s:ConditionObject' % idx]
        con_obj = await noti_obj.get_child(path)
        condition = self.client.get_node(ua.NodeId(2830))

        handler = SubHandler()
        sub = await self.client.create_subscription(500, handler)
        self.subscriptions[sub] = []
        con_handle = await sub.subscribe_events(self.client.nodes.server, condition)
        self.subscriptions[sub].append(con_handle)

        path = ['%s:AlarmObject' % idx]
        alarm_obj = await noti_obj.get_child(path)
        alarm = self.client.get_node(ua.NodeId(10637))

        alarm_handle = await sub.subscribe_events(self.client.nodes.server, alarm)
        self.subscriptions[sub].append(alarm_handle)


async def interactive(client):
    while True:
        # exit to disconnect
        line = await ainput(">>> ")
        print('execute:', line)
        if line == 'exit':
            break
        try:
            eval(line)
        except Exception as msg:
            print('Exception:', msg)
            raise Exception


async def start():
    async with OpcUaClient("opc.tcp://localhost:4840") as client:
        await client.init()
        while True:
            await asyncio.sleep(10)
        # await interactive(client)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
