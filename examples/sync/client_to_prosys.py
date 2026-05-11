import logging

from asyncua.sync import Client

if __name__ == "__main__":
    from IPython import embed

    logging.basicConfig(level=logging.DEBUG)
    with Client("opc.tcp://localhost:53530/OPCUA/SimulationServer/") as client:
        root = client.nodes.root
        print("Root is", root)
        print("children of root are: ", root.get_children())
        print("name of root is", root.read_browse_name())
        objects = client.nodes.objects
        print("children og objects are: ", objects.get_children())
        embed()
