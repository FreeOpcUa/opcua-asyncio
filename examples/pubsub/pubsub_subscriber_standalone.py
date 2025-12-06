"""
Example creating a standalone publisher that receives an Int32, String, Bool and ArrayInt16 matching the pubsubpublisher standalone example
"""

import asyncio
import logging

from asyncua import pubsub, ua
from asyncua.pubsub.udp import UdpSettings

# This Parameter must match the Publisher Settings!
CFG = {
    "PublisherID": ua.Variant(ua.UInt16(1)),
    "WriterId": ua.UInt16(1),
    "DataSetWriterId": ua.UInt16(32),
    "url": "opc.udp://239.0.0.1:4840",
}


def create_meta_data():
    # This is the description of the incoming data
    dataset = pubsub.DataSetMeta.Create("Simple")
    dataset.add_field(pubsub.DataSetField.CreateScalar("Int32", ua.VariantType.Int32))
    dataset.add_field(pubsub.DataSetField.CreateScalar("String", ua.VariantType.String))
    dataset.add_field(pubsub.DataSetField.CreateScalar("Bool", ua.ObjectIds.Boolean))
    dataset.add_field(pubsub.DataSetField.CreateArray("ArrayInt16", ua.ObjectIds.Double))
    return dataset


def create_reader(handler: pubsub.SubscribedDataSet):
    # Register Handler to get the DataSetResults
    cfg = pubsub.ReaderGroupDataType("ReaderGroup1", True)
    reader = pubsub.ReaderGroup(cfg)
    cfg = pubsub.DataSetReaderDataType(
        "SimpleDataSetReader", True, CFG["PublisherID"], CFG["WriterId"], CFG["DataSetWriterId"]
    )
    dsr = pubsub.DataSetReader(cfg)
    dsr.set_subscribed(handler)
    meatadata = create_meta_data()
    dsr.set_meta_data(meatadata)
    reader.add_dataset_reader(dsr)
    return reader


def create_connection() -> pubsub.PubSubConnection:
    # The PublisherId here is 2 but could be any number because we are just subscribing
    return pubsub.PubSubConnection.udp_uadp(
        "Subscriber Connection1 UDP UADP", ua.UInt16(2), UdpSettings(Url=CFG["url"])
    )


class OnDataReceived:
    """
    This is called when a dataset is received
    """

    def on_dataset_received(self, meta: pubsub.DataSetMeta, fields: list[pubsub.DataSetValue]):
        print("Got Msg:")
        for f in fields:
            print(f"{f.Name} -> {f.Value}")

    def on_state_change(self, meta: pubsub.DataSetMeta, state: ua.PubSubState):
        """Called when a DataSet state changes"""
        print(f"State changed {meta.Name} - {state.name}")


async def main():
    handler = OnDataReceived()
    logging.basicConfig(level=logging.INFO)
    app = pubsub.PubSubApplication()
    con = create_connection()
    reader = create_reader(handler)
    await con.add_reader_group(reader)
    app.add_connection(con)
    async with app:
        while 1:
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
