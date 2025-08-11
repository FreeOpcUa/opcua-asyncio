"""
Example creating a publisher standalone that sends an Int32, String, Bool and ArrayInt16
"""

import asyncio
from datetime import datetime
import logging
from asyncua import pubsub, ua
from asyncua.pubsub.udp import UdpSettings
from asyncua.ua import Variant


URL = "opc.udp://239.0.0.1:4840"
PDSNAME = "SimpleDataSet"


def create_published_dataset() -> pubsub.PublishedDataSet:
    # Create a Published Dataset containing a Int32, String, Bool and List[Int16]
    dataset = pubsub.DataSetMeta.Create("Simple")
    dataset.add_scalar("Int32", ua.VariantType.Int32)
    dataset.add_scalar("String", ua.VariantType.String)
    dataset.add_scalar("Bool", ua.ObjectIds.Boolean)
    dataset.add_array("ArrayInt16", ua.ObjectIds.Int16)
    return pubsub.PublishedDataSet.Create(PDSNAME, dataset)


def init_data_source(source: pubsub.PubSubDataSource):
    source.datasources["Simple"] = {}
    # Create the values for the Dataset
    source.datasources["Simple"]["Int32"] = ua.DataValue(
        ua.Variant(ua.Int32(1)),
        ua.StatusCode(ua.status_codes.StatusCodes.Good),
        ua.DateTime.utcnow(),
        ua.DateTime.utcnow(),
    )
    source.datasources["Simple"]["String"] = ua.DataValue(
        ua.Variant("0"),
        ua.StatusCode(ua.status_codes.StatusCodes.Good),
        ua.DateTime.utcnow(),
        ua.DateTime.utcnow(),
    )
    source.datasources["Simple"]["Bool"] = ua.DataValue(
        ua.Variant(True),
        ua.StatusCode(ua.status_codes.StatusCodes.Good),
        ua.DateTime.utcnow(),
        ua.DateTime.utcnow(),
    )
    source.datasources["Simple"]["ArrayInt16"] = ua.DataValue(
        ua.Variant([ua.UInt16(123), ua.UInt16(234)]),
        ua.StatusCode(ua.status_codes.StatusCodes.Good),
        ua.DateTime.utcnow(),
        ua.DateTime.utcnow(),
    )


async def main():
    logging.basicConfig(level=logging.INFO)
    pds = create_published_dataset()
    source = pds.get_source()
    init_data_source(source)
    con = pubsub.PubSubConnection.udp_udadp(
        "Publisher Connection1 UDP UADP",
        ua.UInt16(1),
        UdpSettings(Url=URL),
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
    ps = pubsub.PubSub.new(connections=[con], datasets=[pds])
    async with ps:
        i32 = ua.Int32(0)
        while 1:
            i32 += 1
            # Update all Values
            source.datasources["Simple"]["Int32"] = ua.DataValue(
                i32, SourceTimestamp=datetime.now(), ServerTimestamp=datetime.now()
            )
            source.datasources["Simple"]["String"] = ua.DataValue(
                str(i32), SourceTimestamp=datetime.now(), ServerTimestamp=datetime.now()
            )
            source.datasources["Simple"]["Bool"] = ua.DataValue(
                (i32 % 2) > 0,
                SourceTimestamp=datetime.now(),
                ServerTimestamp=datetime.now(),
            )
            source.datasources["Simple"]["ArrayInt16"] = ua.DataValue(
                Variant([ua.UInt16(1), ua.UInt16(2), ua.UInt16(3)]),
                SourceTimestamp=datetime.now(),
                ServerTimestamp=datetime.now(),
            )
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
