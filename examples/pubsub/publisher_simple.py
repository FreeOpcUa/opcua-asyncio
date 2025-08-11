"""
Example creating a publisher that sends an Int32, String, Bool and ArrayInt16 from AddressSpace
"""

import asyncio
import logging
from typing import List
from asyncua import ua, pubsub, Server
from asyncua.common.node import Node


from asyncua.ua.uatypes import NodeId, VariantType

URL = "opc.udp://239.0.0.1:4840"
PDSNAME = "SimpleDataSet"


async def create_published_dataset(server: Server, nodes: List[Node]) -> pubsub.PublishedDataItems:
    # Links nodes from AddressSpace to PubSub (To simplfy use displayname as fieldname)
    variables = []
    for node in nodes:
        name = await node.read_display_name()
        variables.append(pubsub.TargetVariable(name.Text, node.nodeid))
    return await pubsub.PublishedDataItems.Create(PDSNAME, server, variables)


async def create_variables(node: Node, ns: ua.UInt16) -> List[Node]:
    nodes = []
    folder = await node.add_folder(NodeId("PublisherDemo", ns), "PublisherDemoNodes")
    nodes.append(await folder.add_variable(NodeId("PubInt32", ns), "Int32", 1, VariantType.Int32))
    nodes.append(await folder.add_variable(NodeId("PubString", ns), "String", "DemoString"))
    nodes.append(await folder.add_variable(NodeId("PubBool", ns), "Bool", True, VariantType.Boolean))
    nodes.append(await folder.add_variable(NodeId("PubArrayInt16", ns), "ArrayInt16", [1, 2, 3], VariantType.Int16))
    for n in nodes:
        await n.set_writable()
    return nodes


async def main():
    logging.basicConfig(level=logging.INFO)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    nodes = await create_variables(server.nodes.objects, idx)
    ps = await server.get_pubsub()
    async with server:
        pds = await create_published_dataset(server, nodes)
        con = pubsub.PubSubConnection.udp_udadp(
            "Publisher Connection1 UDP UADP",
            ua.UInt16(1),
            pubsub.UdpSettings(Url=URL),
            writer_groups=[
                # Configures the writer the publish every 5000
                pubsub.WriterGroup.new_uadp(
                    name="WriterGroup1",
                    writer_group_id=ua.UInt32(1),
                    publishing_interval=5000,
                    writer=[
                        pubsub.DataSetWriter.new_uadp(
                            name="Writer1",
                            dataset_writer_id=ua.UInt32(32),
                            dataset_name=PDSNAME,
                            datavalue=True,
                        )
                    ],
                )
            ],
        )
        await ps.add_connection(con)
        await ps.add_published_dataset(pds)
        await ps.start()
        while 1:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
