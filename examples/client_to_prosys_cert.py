import sys

sys.path.insert(0, "..")
import logging

from IPython import embed

from asyncua import Client

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    client = Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/")
    client.load_client_certificate("server_cert.pem")
    client.load_private_key("mykey.pem")
    try:
        client.connect()
        root = client.nodes.root
        objects = client.nodes.objects
        print("childs og objects are: ", objects.get_children())

        embed()
    finally:
        client.disconnect()
