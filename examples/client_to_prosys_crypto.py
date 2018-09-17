import sys
sys.path.insert(0, "..")
import logging

from IPython import embed

from opcua import Client


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    client = Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/")
    client.set_security_string("Basic256Sha256,Sign,certificate-example.der,private-key-example.pem")
    try:
        client.connect()
        root = client.get_root_node()
        objects = client.get_objects_node()
        print("childs og objects are: ", objects.get_children())

        embed()
    finally:
        client.disconnect()
