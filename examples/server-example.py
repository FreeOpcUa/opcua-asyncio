import asyncio
import copy
import logging
import time
from datetime import UTC, datetime
from math import sin

from asyncua import Server, ua, uamethod
from asyncua.common.subscription import DataChangeEvent, OpcEvent

_logger = logging.getLogger(__name__)


def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


@uamethod
def multiply(parent, x, y):
    _logger.warning("multiply method call with parameters: %s %s", x, y)
    return x * y


async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("FreeOpcUa Example Server")
    server.set_security_policy(
        [
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
        ]
    )

    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    dev = await server.nodes.base_object_type.add_object_type(idx, "MyDevice")
    await (await dev.add_variable(idx, "sensor1", 1.0)).set_modelling_rule(True)
    await (await dev.add_property(idx, "device_id", "0340")).set_modelling_rule(True)
    ctrl = await dev.add_object(idx, "controller")
    await ctrl.set_modelling_rule(True)
    await (await ctrl.add_property(idx, "state", "Idle")).set_modelling_rule(True)

    await server.nodes.objects.add_folder(idx, "myEmptyFolder")
    mydevice = await server.nodes.objects.add_object(idx, "Device0001", dev)
    mydevice_var = await mydevice.get_child([f"{idx}:controller", f"{idx}:state"])
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()
    mystringvar = await myobj.add_variable(idx, "MyStringVariable", "Really nice string")
    await mystringvar.set_writable()
    mydtvar = await myobj.add_variable(idx, "MyDateTimeVar", datetime.now(UTC))
    await mydtvar.set_writable()
    myarrayvar = await myobj.add_variable(idx, "myarrayvar", [6.7, 7.9])
    await myobj.add_variable(idx, "myuintvar", ua.UInt16(4))
    await myobj.add_variable(idx, "myStronglyTypedVariable", ua.Variant([], ua.VariantType.UInt32))
    await myarrayvar.set_writable(True)
    await myobj.add_property(idx, "myproperty", "I am a property")
    await myobj.add_method(idx, "mymethod", func, [ua.VariantType.Int64], [ua.VariantType.Boolean])
    await myobj.add_method(
        idx,
        "multiply",
        multiply,
        [ua.VariantType.Int64, ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )

    await server.import_xml("custom_nodes.xml")

    myevgen = await server.get_event_generator()
    myevgen.event.Severity = 300

    async with server:
        print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())

        async with await server.create_subscription(500) as sub:
            await sub.subscribe_data_change(myvar)

            async def consume_subscription():
                async for event in sub:
                    match event:
                        case DataChangeEvent(node=node, value=value):
                            _logger.warning("New data change event %s %s", node, value)
                        case OpcEvent(event=evt):
                            _logger.warning("New event %s", evt)

            consumer = asyncio.create_task(consume_subscription())

            var = await myarrayvar.read_value()
            var = copy.copy(var)
            var.append(9.3)
            await myarrayvar.write_value(var)
            await mydevice_var.write_value("Running")
            await myevgen.trigger(message="This is BaseEvent")
            await server.write_attribute_value(myvar.nodeid, ua.DataValue(0.9))

            try:
                while True:
                    await asyncio.sleep(0.1)
                    await server.write_attribute_value(myvar.nodeid, ua.DataValue(sin(time.time())))
            finally:
                consumer.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
