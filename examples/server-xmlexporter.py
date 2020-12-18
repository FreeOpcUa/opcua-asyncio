import sys
sys.path.insert(0, "..")
import asyncio

from asyncua import ua, Server
from asyncua.common.instantiate_util import instantiate
from asyncua.common.xmlexporter import XmlExporter


async def main():
    # setup our server
    server = Server()
    await server.init()

    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()    # Set MyVariable to be writable by clients

    dev = await server.nodes.base_object_type.add_object_type(0, "MyDevice")
    await dev.add_variable(0, "sensor1", 1.0)

    mydevice = await instantiate(server.nodes.objects, dev, bname="2:Device0001")

    node_list = [dev, mydevice[0], myobj, myvar]

    exporter = XmlExporter(server)
    await exporter.build_etree(node_list, ['http://myua.org/test/'])
    await exporter.write_xml('ua-export.xml')

if __name__ == "__main__":
    asyncio.run(main())
