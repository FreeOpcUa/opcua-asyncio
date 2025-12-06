import asyncio
import logging
import sys
import time

# import asyncua
sys.path.insert(0, "..")

from asyncua import Server, ua
from asyncua.client.ha.ha_client import HaClient, HaConfig, HaMode

# set up logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)
# diable logging for the servers
logging.getLogger("asyncua.server").setLevel(logging.WARNING)


class SubHandler:
    """
    Basic subscription handler to support datachange_notification.
    No need to implement the other handlermethods since the
    HA_CLIENT only supports datachange for now.
    """

    def datachange_notification(self, node, val, data):
        """
        called for every datachange notification from server
        """
        print(f"Node: {node} has value: {val}\n")


async def start_servers():
    """Spin up two servers with identical configurations"""
    ports = [4840, 4841]
    urls = []
    loop = asyncio.get_event_loop()
    tasks = []
    for port in ports:
        server = Server()
        await server.init()
        url = f"opc.tcp://0.0.0.0:{port}/freeopcua/server/"
        urls.append(url)
        server.set_endpoint(url)
        server.set_server_name("FreeOpcUa Example Server {port}")
        # setup our own namespace
        uri = "http://examples.freeopcua.github.io"
        idx = await server.register_namespace(uri)

        myobj = await server.nodes.objects.add_object(idx, "MyObject")
        myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
        await server.start()
        tasks.append(loop.create_task(server_var_update(server, myvar)))
    return urls, myvar, tasks


async def server_var_update(server, myvar):
    """
    Constantly increment the variable with epoch time
    to simulate data notifications.
    """
    while True:
        await asyncio.sleep(1)
        await server.write_attribute_value(myvar.nodeid, ua.DataValue(time.time()))


async def main():
    # start the servers
    urls, node, _tasks = await start_servers()

    # set up ha_client with the serveur urls
    ha_config = HaConfig(
        HaMode.WARM, keepalive_timer=15, manager_timer=15, reconciliator_timer=15, urls=urls, session_timeout=30
    )
    ha = HaClient(ha_config)
    await ha.start()

    publish_interval = 1000
    handler = SubHandler()

    # subscribe to two nodes
    sub1 = await ha.create_subscription(publish_interval, handler)
    await ha.subscribe_data_change(sub1, [node])

    # Watch the debug log and check what's happening in the background.
    # A basic check could be to `iptables -A OUTPUT -p tcp --dport 4840 -j DROP`
    # and observe the failover in action
    await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
