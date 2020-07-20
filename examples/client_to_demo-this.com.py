import sys
sys.path.insert(0, "..")
import logging
import asyncio

from IPython import embed

from asyncua import Client
from asyncua import ua



async def main():
    logging.basicConfig(level=logging.INFO)

    #async with Client("opc.tcp://opcua.demo-this.com:51210/UA/SampleServer") as client:
    client = Client("opc.tcp://opcuaserver.com:48010")
    client.name = "TOTO"
    client.application_uri = "urn:freeopcua:clientasync"
    async with client:
        struct = client.get_node("ns=3;s=ControllerConfigurations")
        #struct = client.get_node("ns=2;i=10239")
        before = await struct.read_value()
        #data = await client.load_type_definitions()  # scan server for custom structures and import them
        data = await client.load_data_type_definitions()  # scan server for custom structures and import them
        after = await struct.read_value()
        print("DATA TYPE", await struct.read_data_type())
        print("BEFORE", before)
        print("AFTER", after)
        n = client.get_node("ns=3;i=9")
        path = await n.get_path(as_string=True)
        bname = await n.read_browse_name()
        embed()

if __name__ == '__main__':
    asyncio.run(main())
