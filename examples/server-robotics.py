import asyncio
import copy
import logging
from datetime import datetime
import time
from math import sin
import sys
sys.path.insert(0, "..")
from IPython import embed



from asyncua import ua, uamethod, Server


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


# method to be exposed through server

def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


# method to be exposed through server
# uses a decorator to automatically convert to and from variants

@uamethod
def multiply(parent, x, y):
    print("multiply method call with parameters: ", x, y)
    return x * y


async def main():
    # optional: setup logging
    logging.basicConfig(level=logging.INFO)
    #logger = logging.getLogger("asyncua.address_space")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.internal_server")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    #logger = logging.getLogger("asyncua.uaprocessor")
    # logger.setLevel(logging.DEBUG)

    # now setup our server
    server = Server()
    await server.init()
    # import some nodes from xml
    await server.import_xml("../schemas/UA-Nodeset/DI/Opc.Ua.Di.NodeSet2.xml")
    await server.import_xml("../schemas/UA-Nodeset/Robotics/Opc.Ua.Robotics.NodeSet2.xml")

    # starting!
    async with server:
        embed()


if __name__ == "__main__":
    asyncio.run(main())
