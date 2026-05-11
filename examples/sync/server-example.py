import copy
import logging
import sys
import time
from datetime import UTC, datetime
from math import sin
from threading import Thread

sys.path.insert(0, "../..")

try:
    from IPython import embed
except ImportError:
    import code

    def embed() -> None:
        myvars = globals()
        myvars.update(locals())
        shell = code.InteractiveConsole(myvars)
        shell.interact()


from asyncua import ua, uamethod
from asyncua.sync import Server, ThreadLoop


def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


@uamethod
def multiply(parent, x, y):
    print("multiply method call with parameters: ", x, y)
    return x * y


class VarUpdater(Thread):
    def __init__(self, var) -> None:
        Thread.__init__(self)
        self._stopev = False
        self.var = var

    def stop(self) -> None:
        self._stopev = True

    def run(self) -> None:
        while not self._stopev:
            v = sin(time.time() / 10)
            self.var.write_value(v)
            time.sleep(0.1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    with ThreadLoop() as tloop:
        server = Server(tloop=tloop)
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
        idx = server.register_namespace(uri)
        print("IDX", idx)

        dev = server.nodes.base_object_type.add_object_type(idx, "MyDevice")
        dev.add_variable(idx, "sensor1", 1.0).set_modelling_rule(True)
        dev.add_property(idx, "device_id", "0340").set_modelling_rule(True)
        ctrl = dev.add_object(idx, "controller")
        ctrl.set_modelling_rule(True)
        ctrl.add_property(idx, "state", "Idle").set_modelling_rule(True)

        myfolder = server.nodes.objects.add_folder(idx, "myEmptyFolder")
        mydevice = server.nodes.objects.add_object(idx, "Device0001", dev)
        mydevice_var = mydevice.get_child([f"{idx}:controller", f"{idx}:state"])
        myobj = server.nodes.objects.add_object(idx, "MyObject")
        myvar = myobj.add_variable(idx, "MyVariable", 6.7)
        mysin = myobj.add_variable(idx, "MySin", 0, ua.VariantType.Float)
        myvar.set_writable()
        mystringvar = myobj.add_variable(idx, "MyStringVariable", "Really nice string")
        mystringvar.set_writable()
        mydtvar = myobj.add_variable(idx, "MyDateTimeVar", datetime.now(UTC))
        mydtvar.set_writable()
        myarrayvar = myobj.add_variable(idx, "myarrayvar", [6.7, 7.9])
        myarrayvar = myobj.add_variable(idx, "myStronglyTypedVariable", ua.Variant([], ua.VariantType.UInt32))
        myprop = myobj.add_property(idx, "myproperty", "I am a property")
        mymethod = myobj.add_method(idx, "mymethod", func, [ua.VariantType.Int64], [ua.VariantType.Boolean])
        multiply_node = myobj.add_method(
            idx, "multiply", multiply, [ua.VariantType.Int64, ua.VariantType.Int64], [ua.VariantType.Int64]
        )

        server.import_xml("custom_nodes.xml")

        myevgen = server.get_event_generator()
        myevgen.event.Severity = 300

        with server:
            print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())
            vup = VarUpdater(mysin)
            vup.start()

            var = myarrayvar.read_value()
            var = copy.copy(var)
            var.append(9.3)
            myarrayvar.write_value(var)
            mydevice_var.write_value("Running")
            myevgen.trigger(message="This is BaseEvent")
            server.write_attribute_value(myvar.nodeid, ua.DataValue(9.9))

            embed()
            vup.stop()
