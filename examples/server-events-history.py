import sys
sys.path.insert(0, "..")
import time
from datetime import datetime
import asyncio

from asyncua import ua, Server
from asyncua.server.history_sql import HistorySQLite


async def main():

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.nodes.objects

    # populating our address space
    myobj = objects.add_object(idx, "MyObject")

    # Creating a custom event: Approach 1
    # The custom event object automatically will have members from its parent (BaseEventType)
    etype = server.create_custom_event_type(2, 'MyFirstEvent', ua.ObjectIds.BaseEventType,
                                            [('MyNumericProperty', ua.VariantType.Float),
                                             ('MyStringProperty', ua.VariantType.String)])
    # create second event
    etype2 = server.create_custom_event_type(2, 'MySecondEvent', ua.ObjectIds.BaseEventType,
                                             [('MyOtherProperty', ua.VariantType.Float)])

    # get an event generator for the myobj node which generates custom events
    myevgen = await server.get_event_generator(etype, myobj)
    myevgen.event.Severity = 500
    myevgen.event.MyStringProperty = ua.Variant("hello world")
    myevgen.event.MyNumericProperty = ua.Variant(-456)

    # get another event generator for the myobj node which generates different custom events
    myevgen2 = await server.get_event_generator(etype2, myobj)
    myevgen2.event.Severity = 123
    myevgen2.event.MyOtherProperty = ua.Variant(1.337)

    # get an event generator for the server node which generates BaseEventType
    serverevgen = await server.get_event_generator()
    serverevgen.event.Severity = 111

    # Configure server to use sqlite as history database (default is a simple in memory dict)
    server.iserver.history_manager.set_storage(HistorySQLite("my_event_history.sql"))

    # starting!
    await server.start()

    # enable history for myobj events; must be called after start since it uses subscription
    server.iserver.enable_history_event(myobj, period=None)

    # enable history for server events; must be called after start since it uses subscription
    server_node = server.get_node(ua.ObjectIds.Server)
    await server.historize_node_event(server_node, period=None)

    try:
        count = 0
        while True:
            time.sleep(1)
            count += 0.1

            # generate events for subscribed clients and history
            await myevgen.trigger(message="This is MyFirstEvent " + str(count))
            await myevgen2.trigger(message="This is MySecondEvent " + str(count))
            await serverevgen.trigger(message="Server Event Message")

            # read event history from sql
            end_time = datetime.utcnow()
            server_event_history = server_node.read_event_history(None, end_time, 0)

    finally:
        # close connection, remove subscriptions, etc
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
