import time
import uvloop
import asyncio
import sys
import logging
import cProfile

sys.path.insert(0, "..")
from asyncua import Client, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    async with Client(url=url) as client:
        uri = 'http://examples.freeopcua.github.io'
        idx = await client.get_namespace_index(uri)
        var = await client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])

        nb = 4000
        start = time.time()
        attr = ua.WriteValue()
        attr.NodeId = var.nodeid
        attr.AttributeId = ua.AttributeIds.Value
        attr.Value = ua.DataValue(ua.Variant(1.0, ua.VariantType.Float))
        params = ua.WriteParameters()
        params.NodesToWrite = [attr]
        for i in range(nb):
            params.NodesToWrite[0].Value.Value.Value = i
            result = await client.uaclient.write(params)
            #result[0].check()
            #await var.set_value(i)
    print("\n Write frequency: \n", nb / (time.time() - start))

if __name__ == '__main__':
    #uvloop.install()
    asyncio.run(main())
    #cProfile.run('asyncio.run(mymain(), debug=True)', filename="perf.cprof")
