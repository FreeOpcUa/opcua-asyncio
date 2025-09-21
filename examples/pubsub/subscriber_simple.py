"""
Example creating a subscriber that receives an Int32, String, Bool and ArrayInt16 matching the publisher_simple.py
"""

import asyncio
import logging

from asyncua import ua, pubsub, Node, Server
from dataclasses import dataclass


# This Parameter must match the Publisher Settings!
@dataclass
class PubSubCFG:
    PublisherID: ua.Variant = ua.Variant(ua.UInt16(1))
    WriterId: ua.UInt16 = ua.UInt16(1)
    DataSetWriterId: ua.UInt16 = ua.UInt16(32)
    Url: str = "opc.udp://239.0.0.1:4840"


CFG = PubSubCFG()


def create_meta_data():
    dataset = pubsub.DataSetMeta.Create("Simple")
    dataset.add_scalar("Int32", ua.VariantType.Int32)
    dataset.add_scalar("String", ua.VariantType.String)
    dataset.add_scalar("Bool", ua.ObjectIds.Boolean)
    dataset.add_array("ArrayInt16", ua.ObjectIds.Int16)
    return dataset


async def init_pubsub_connection(server: Server, nodes: list[Node]) -> pubsub.PubSubConnection:
    metadata = create_meta_data()
    # link metafields with the nodes in the AddressSpace
    subscribed_ds = pubsub.SubScribedTargetVariables(
        server,
        [
            pubsub.FieldTargets.createTarget(metadata.get_field((await n.read_browse_name()).Name), n.nodeid)
            for n in nodes
        ],
    )
    # Configure ReaderGroup and DataSetReader this must match the WriterGroup/DataSetWriter configured on the publisher
    reader = pubsub.ReaderGroup.new(
        name="ReaderGroup1",
        enable=True,
        reader=[
            pubsub.DataSetReader.new(
                CFG.PublisherID,
                CFG.WriterId,
                CFG.DataSetWriterId,
                metadata,
                name="SimpleDataSetReader",
                subscribed=subscribed_ds,
                enabled=True,
            )
        ],
    )
    # Create a connection
    # The PublisherId here is 2 but could be any number because we are just subscribing
    return pubsub.PubSubConnection.udp_uadp(
        "Subscriber Connection1 UDP UADP",
        ua.UInt16(2),
        pubsub.UdpSettings(Url=CFG.Url),
        reader_groups=[reader],
    )


async def create_variables(node: Node, ns: ua.UInt16) -> list[Node]:
    folder = await node.add_folder(ua.NodeId("SubscriberDemo", ns), "PublisherDemoNodes")
    return [
        await folder.add_variable(ua.NodeId("SubInt32", ns), "Int32", 1, ua.VariantType.Int32),
        await folder.add_variable(ua.NodeId("SubString", ns), "String", "DemoString"),
        await folder.add_variable(ua.NodeId("SubBool", ns), "Bool", True, ua.VariantType.Boolean),
        await folder.add_variable(
            ua.NodeId("SubArrayInt16", ns),
            "ArrayInt16",
            [1, 2, 3],
            ua.VariantType.Int16,
        ),
    ]


async def main():
    logging.basicConfig(level=logging.INFO)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4841/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    nodes = await create_variables(server.nodes.objects, idx)
    ps = await server.get_pubsub()
    async with server:
        connection = await init_pubsub_connection(server, nodes)
        await ps.add_connection(connection)
        await ps.init_information_model()
        await ps.start()
        while 1:
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
