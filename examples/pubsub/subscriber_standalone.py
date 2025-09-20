"""
Example creating a standalone subscriber that receives an Int32, String, Bool and ArrayInt16 matching the pubsubpublisher standalone example
"""

import asyncio
import logging

from asyncua import ua, pubsub
from asyncua.pubsub.udp import UdpSettings
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
    # This is the description of the incoming data
    dataset = pubsub.DataSetMeta.Create("Simple")
    dataset.add_scalar("Int32", ua.VariantType.Int32)
    dataset.add_scalar("String", ua.VariantType.String)
    dataset.add_scalar("Bool", ua.ObjectIds.Boolean)
    dataset.add_array("ArrayInt16", ua.ObjectIds.Double)
    return dataset


class OnDataReceived:
    """
    This is called when a dataset is received
    """

    async def on_dataset_received(self, _meta: pubsub.DataSetMeta, fields: list[pubsub.DataSetValue]):
        print("Got Msg:")
        for f in fields:
            print(f"{f.Name} -> {f.Value}")

    async def on_state_change(self, meta: pubsub.DataSetMeta, state: ua.PubSubState):
        """Called when a DataSet state changes"""
        print(f"State changed {meta.Name} - {state.name}")


async def main():
    handler = OnDataReceived()
    logging.basicConfig(level=logging.INFO)
    metadata = create_meta_data()
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
                subscribed=handler,
                enabled=True,
            )
        ],
    )
    # Create a connection
    # The PublisherId here is 2 but could be any number because we are just subscribing
    connection = pubsub.PubSubConnection.udp_uadp(
        "Subscriber Connection1 UDP UADP",
        ua.UInt16(2),
        UdpSettings(Url=CFG.Url),
        reader_groups=[reader],
    )
    ps = pubsub.PubSub.new(connections=[connection])
    # Run the connection
    async with ps:
        while 1:
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
