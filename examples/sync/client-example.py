import sys

sys.path.insert(0, "..")
import logging
import threading
import time

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()


from asyncua.common.subscription import DataChangeEvent, OpcEvent
from asyncua.sync import Client, ThreadLoop

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    with ThreadLoop() as tloop:
        with Client("opc.tcp://localhost:4840/freeopcua/server/", tloop=tloop) as client:
            client.load_type_definitions()
            print("Objects node is: ", client.nodes.objects)
            print("Children of root are: ", client.nodes.root.get_children())

            uri = "http://examples.freeopcua.github.io"
            idx = client.get_namespace_index(uri)
            myvar = client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
            obj = client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject"])
            print("myvar is: ", myvar)

            with client.create_subscription(500) as sub:
                sub.subscribe_data_change(myvar)
                sub.subscribe_events()

                def consume() -> None:
                    for event in sub:
                        match event:
                            case DataChangeEvent(node=node, value=value):
                                print("Python: New data change event", node, value)
                            case OpcEvent(event=evt):
                                print("Python: New event", evt)

                consumer = threading.Thread(target=consume, daemon=True)
                consumer.start()

                time.sleep(0.1)
                res = obj.call_method(f"{idx}:multiply", 3, "klk")
                print("method result is: ", res)

                embed()
