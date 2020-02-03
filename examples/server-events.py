import asyncio
import logging
from asyncua import ua
from asyncua.server import Server, EventGenerator

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def start_server(loop: asyncio.AbstractEventLoop):
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    # get Objects node, this is where we should put our custom stuff
    objects = server.get_objects_node()
    # populating our address space
    myobj = await objects.add_object(idx, "MyObject")
    # Creating a custom event: Approach 1
    # The custom event object automatically will have members from its parent (BaseEventType)
    etype = await server.create_custom_event_type(
        idx, 'MyFirstEvent', ua.ObjectIds.BaseEventType,
        [('MyNumericProperty', ua.VariantType.Float),
         ('MyStringProperty', ua.VariantType.String)]
    )
    myevgen = await server.get_event_generator(etype, myobj)
    # Creating a custom event: Approach 2
    custom_etype = await server.nodes.base_event_type.add_object_type(2, 'MySecondEvent')
    await custom_etype.add_property(2, 'MyIntProperty', ua.Variant(0, ua.VariantType.Int32))
    await custom_etype.add_property(2, 'MyBoolProperty', ua.Variant(True, ua.VariantType.Boolean))
    mysecondevgen = await server.get_event_generator(custom_etype, myobj)
    await server.start()
    loop.call_later(2, emmit_event, loop, myevgen, mysecondevgen, 1)


def emmit_event(loop: asyncio.AbstractEventLoop, myevgen: EventGenerator, mysecondevgen: EventGenerator, count: int):
    myevgen.event.Message = ua.LocalizedText("MyFirstEvent %d" % count)
    myevgen.event.Severity = count
    myevgen.event.MyNumericProperty = count
    myevgen.event.MyStringProperty = "Property %d" % count
    await myevgen.trigger()
    await mysecondevgen.trigger(message="MySecondEvent %d" % count)
    count += 1
    loop.call_later(2, emmit_event, loop, myevgen, mysecondevgen, count)


def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.create_task(start_server(loop))
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
