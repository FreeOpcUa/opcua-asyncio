import sys
sys.path.insert(0, "..")
import time
import logging
from IPython import embed

from asyncua import Client
from asyncua import ua



if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    client = Client("opc.tcp://asyncua.demo-this.com:51210/UA/SampleServer")
    try:
        client.connect()
        root = client.get_root_node()
        objects = client.get_objects_node()
        struct = client.get_node("ns=2;i=10239")
        before = struct.read_value()
        client.load_type_definitions()  # scan server for custom structures and import them
        after = struct.read_value()
        

        embed()
    finally:
        client.disconnect()
