import sys
sys.path.insert(0, "..")
import logging
import asyncio

from IPython import embed

from asyncua import Client
from asyncua import ua



async def main():
    logging.basicConfig(level=logging.WARN)
    async with Client("opc.tcp://opcua.demo-this.com:51210/UA/SampleServer") as client:
        struct = client.get_node("ns=2;i=10239")
        before = await struct.read_value()
        data = await client.load_type_definitions()  # scan server for custom structures and import them
        after = await struct.read_value()
        print("BEFORE", before)
        print("AFTER", after)

if __name__ == '__main__':
    asyncio.run(main())
