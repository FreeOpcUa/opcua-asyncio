# coding: utf-8

from aioconsole import ainput

import asyncio

from asyncua import Server, ua


class OpcUaServer(object):

    def __init__(self, endpoint):
        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.server.set_server_name('Alarms and Conditions Test Server')
        self.server.application_type = ua.ApplicationType.Server
        self.server.iserver.bind_condition_methods = True
        self.con_gen = None
        self.alarm_gen = None

    async def __aenter__(self):
        await self.init()
        await self.server.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.server.stop()

    async def init(self):
        await self.server.init()
        uri = "http://examples.freeopcua.github.io"
        idx = await self.server.register_namespace(uri)
        objects = self.server.get_objects_node()

        noti_node = await objects.add_object(idx, 'NotifierObject')

        con_obj = await noti_node.add_object(idx, "ConditionObject")
        condition = self.server.get_node(ua.NodeId(2830))
        self.con_gen = await self.server.get_event_generator(condition, con_obj,
                                                             notifier_path=[ua.ObjectIds.Server, noti_node, con_obj])
        self.con_gen.event.add_property('NodeId', con_obj.nodeid, ua.VariantType.NodeId)

        alarm_obj = await noti_node.add_object(idx, "AlarmObject")
        alarm = self.server.get_node(ua.NodeId(10637))
        self.alarm_gen = await self.server.get_event_generator(alarm, alarm_obj,
                                                               notifier_path=[ua.ObjectIds.Server, noti_node, alarm_obj])

    def generate_condition(self, retain):
        self.con_gen.event.ConditionName = 'Example Condition'
        self.con_gen.event.Message = ua.LocalizedText("Some Message")
        self.con_gen.event.Severity = 500
        self.con_gen.event.BranchId = ua.NodeId(0)
        if retain == 1:
            self.con_gen.event.Retain = True
        else:
            self.con_gen.event.Retain = False
        self.con_gen.trigger()

    def generate_alarm(self, active):
        self.alarm_gen.event.ConditionName = 'Example Alarm1'
        self.alarm_gen.event.Message = ua.LocalizedText("error in module1")
        self.alarm_gen.event.Severity = 500
        self.alarm_gen.event.BranchId = ua.NodeId(0)
        self.alarm_gen.event.AckedState = ua.LocalizedText('Unacknowledged', 'en')
        setattr(self.alarm_gen.event, 'AckedState/Id', False)
        if active == 1:
            self.alarm_gen.event.Retain = True
            self.alarm_gen.event.ActiveState = ua.LocalizedText('Active', 'en')
            setattr(self.alarm_gen.event, 'ActiveState/Id', True)
        else:
            self.alarm_gen.event.Retain = False
            self.alarm_gen.event.ActiveState = ua.LocalizedText('Inactive', 'en')
            setattr(self.alarm_gen.event, 'ActiveState/Id', False)
        self.alarm_gen.trigger()


async def interactive(server):
    while True:
        # server.generate_condition(1)
        # server.generate_alarm(1)
        line = await ainput(">>> ")
        print('execute:', line)
        if line == 'exit':
            break
        try:
            eval(line)
        except Exception as msg:
            print('Exception:', msg)
            raise Exception


async def main():
    async with OpcUaServer("opc.tcp://0.0.0.0:4840") as server:
        await interactive(server)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
