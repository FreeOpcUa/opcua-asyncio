import asyncio
import io
from typing import List, Tuple
from asyncua import pubsub
from asyncua.common.node import Node
from asyncua.common.utils import Buffer
from asyncua.pubsub.connection import PubSubConnection
from asyncua.pubsub.dataset import DataSetMeta, PublishedDataSet
from asyncua.pubsub.reader import DataSetReader, ReaderGroup
from asyncua.pubsub.uadp import UadpDataSetDataValue, UadpDataSetMessageHeader, UadpDataSetVariant, UadpGroupHeader, UadpHeader, UadpNetworkMessage
from asyncua.pubsub.udp import UdpSettings
from asyncua.server.server import Server
from asyncua.ua.object_ids import ObjectIds
from asyncua.ua.status_codes import StatusCodes
from asyncua.ua.uaprotocol_auto import DataSetReaderDataType, ReaderGroupDataType
from asyncua.ua.uatypes import Byte, DataValue, DateTime, ExtensionObject, Int16, Int32, NodeId, StatusCode, UInt16, UInt32, UInt64, Variant, VariantType
import logging
import pytest

from tests.test_common import expect_file_creation
_logger = logging.getLogger(__name__)


def _get_test_msg():
    gp_header = UadpGroupHeader(UInt16(2), NetworkMessageNo=UInt16(3), SequenceNo=UInt16(5))
    datasets = [
        UadpDataSetVariant(Header=UadpDataSetMessageHeader(True, UInt16(5), DateTime.utcnow(), None, UInt16(StatusCodes.Good)), Data=[Variant(123), Variant(True), Variant("1234565456")]),
        UadpDataSetDataValue(
            Header=UadpDataSetMessageHeader(True, UInt16(5), DateTime.utcnow(), None, UInt16(StatusCodes.Good)),
            Data=[
                DataValue(Variant(123), StatusCode(StatusCodes.Good), None, DateTime.utcnow()),
                DataValue(Variant(True), StatusCode(StatusCodes.Good), None, DateTime.utcnow()),
                DataValue(Variant("1234565456"), StatusCode(StatusCodes.Good), None, DateTime.utcnow()),
                DataValue(None, StatusCode(StatusCodes.BadNodeIdUnknown), None, DateTime.utcnow()),
            ]
        )
    ]
    return UadpNetworkMessage(UadpHeader(UInt16(16)), GroupHeader=gp_header, TimeStamp=DateTime.utcnow(), DataSetPayloadHeader=[UInt16(5), UInt16(4)], Payload=datasets)


def test_uadp_basic():
    msg = _get_test_msg()
    b = msg.to_binary()
    buffer = Buffer(b)
    new_msg = msg.from_binary(buffer)
    assert msg, new_msg


class _Reciver:
    msgs: List[UadpNetworkMessage]

    def __init__(self) -> None:
        self.msgs = []

    async def got_uadp(self, msg: UadpNetworkMessage):
        # Called when a msg is recived
        self.msgs.append(msg)


pytestmark = pytest.mark.asyncio


async def test_connection():
    for ids in [Byte(5), UInt16(13), UInt32(55), UInt64(33), "TestPub"]:
        con = PubSubConnection.udp_udadp("test", ids, UdpSettings(Url="opc.udp://127.0.0.1:4840"))
        recv = _Reciver()
        con.set_receiver(recv)
        msg = _get_test_msg()
        try:
            await con.start()
            await asyncio.sleep(0.001)
            await con.send_uadp_msg(msg)
            await asyncio.sleep(0.01)
            assert msg == recv.msgs[0]
        finally:
            await con.stop()


CFG = {
    'PublisherId': UInt16(1),
    'WriterId': UInt16(1),
    'DataSetWriterId': UInt16(32),
    'url': "opc.udp://224.0.0.22:4840",
    'PdsName': "SimpleDataSet"
}


async def create_published_dataset() -> PublishedDataSet:
    dataset = DataSetMeta.Create("Simple")
    dataset.add_field(pubsub.DataSetField.CreateScalar("Int32", VariantType.Int32))
    dataset.add_field(pubsub.DataSetField.CreateScalar("String", VariantType.String))
    dataset.add_field(pubsub.DataSetField.CreateScalar("Bool", ObjectIds.Boolean))
    dataset.add_field(pubsub.DataSetField.CreateArray("ArrayInt16", ObjectIds.Double))
    return pubsub.PublishedDataSet.Create(CFG['PdsName'], dataset)


class OnDataRecived:
    values = {}

    async def on_dataset_recived(self, meta: pubsub.DataSetMeta, fields: List[pubsub.DataSetValue]):
        _logger.info(f"Got Dataset {meta.Name}")
        if meta.Name not in self.values:
            self.values[meta.Name] = {}
        for f in fields:
            self.values[meta.Name][f.Meta.Name] = f.Value

    async def on_state_change(self, meta: pubsub.DataSetMeta, state):
        _logger.info(f"State changed {meta.Name} - {state.name}")


async def test_full_simple():
    pds = await create_published_dataset()
    source = pds.get_source()
    source.datasources["Simple"] = {
        "Int32": DataValue(Variant(Int32(1))),
        "String": DataValue(Variant("0")),
        "Bool": DataValue(Variant(True)),
        "ArrayInt16": DataValue(Variant([UInt16(123), UInt16(234)]))
    }
    sink = OnDataRecived()
    pub_writer = pubsub.WriterGroup.new_uadp(name="WriterGroup1", writer_group_id=CFG['WriterId'], publishing_interval=100, writer=[
        pubsub.DataSetWriter.new_uadp(name="Writer1", dataset_writer_id=CFG['DataSetWriterId'], dataset_name=CFG['PdsName'], datavalue=True)
    ])
    pub_reader = ReaderGroup.new(name="ReaderGroup1", reader=[
        DataSetReader.new(name="SimpleDataSetReader", publisherId=Variant(CFG['PublisherId']), writer_group_id=CFG["WriterId"], dataset_writer_id=CFG["DataSetWriterId"], meta=await pds.get_meta(), subscriped=sink, enabled=True)
    ], enable=True)
    con = pubsub.PubSubConnection.udp_udadp("Publisher Connection1 UDP UADP", CFG['PublisherId'], UdpSettings(Url=CFG['url']))
    await con.add_writer_group(pub_writer)
    await con.add_reader_group(pub_reader)
    ps = pubsub.PubSub()
    await ps.add_connection(con)
    await ps.add_published_dataset(pds)
    async with ps:
        await asyncio.sleep(0.5)
        for x in range(0, 10):
            i32 = Int32(x)
            source.datasources["Simple"]["Int32"] = DataValue(Variant(i32))
            source.datasources["Simple"]["String"] = DataValue(Variant(str(i32)))
            source.datasources["Simple"]["Bool"] = DataValue(Variant((i32 % 2) > 0))
            source.datasources["Simple"]["ArrayInt16"] = DataValue(Variant([UInt16(1), UInt16(2), UInt16(3)]))
            await asyncio.sleep(0.2)
            for key in source.datasources:
                assert source.datasources[key] == sink.values[key]


@pytest.fixture
async def pusbsub_src_nodes(server) -> List[NodeId]:
    node = server.nodes.objects
    ns = 1
    folder = await node.add_folder(NodeId("SrcTestNodes", ns), "TestNodes")
    nodes = [
        await folder.add_variable(NodeId("PubInt32", ns), "Int32", 1, VariantType.Int32),
        await folder.add_variable(NodeId("PubString", ns), "String", "DemoString"),
        await folder.add_variable(
            NodeId("PubBool", ns), "Bool", True, VariantType.Boolean
        ),
        await folder.add_variable(
            NodeId("PubArrayInt16", ns), "ArrayInt16", [1, 2, 3], VariantType.Int16
        )
    ]
    for n in nodes:
        await n.set_writable()
    return nodes


@pytest.fixture
async def pubsub_dest_nodes(server) -> List[NodeId]:
    node = server.nodes.objects
    ns = 1
    destfolder = await node.add_folder(NodeId("DestTestNodes", ns), "TestNodes")
    destnodes = [
        await destfolder.add_variable(NodeId("DestPubInt32", ns), "Int32", 1, VariantType.Int32),
        await destfolder.add_variable(NodeId("DestPubString", ns), "String", "DemoString"),
        await destfolder.add_variable(
            NodeId("DestPubBool", ns), "Bool", True, VariantType.Boolean
        ),
        await destfolder.add_variable(
            NodeId("DestPubArrayInt16", ns), "ArrayInt16", [1, 2, 3], VariantType.Int16
        )
    ]
    for n in destnodes:
        await n.set_writable()
    return destnodes


async def test_datasource_and_subscriped_dataset(server: Server, pubsub_dest_nodes: List[Node], pusbsub_src_nodes: List[Node]):
    ps = await server.get_pubsub()
    pubid = Variant(UInt32(1))
    writer_group_id = UInt16(2)
    datasetwriter_id = UInt16(32)
    dataset = pubsub.DataSetMeta.Create("Simple")
    dataset.add_scalar("Int32", VariantType.Int32)
    dataset.add_scalar("String", VariantType.String)
    dataset.add_scalar("Bool", ObjectIds.Boolean)
    dataset.add_array("ArrayInt16", ObjectIds.Int16)
    subscriped_ds = pubsub.SubScripedTargetVariables(server,
        [
            pubsub.FieldTargets.createTarget(
                dataset.get_field((await n.read_browse_name()).Name), n.nodeid
            )
            for n in pubsub_dest_nodes
        ],)
    variables = []
    for node in pusbsub_src_nodes:
        name = await node.read_display_name()
        variables.append(pubsub.TargetVariable(name.Text, node.nodeid))

    await ps.add_published_dataset(await pubsub.PublishedDataItems.Create('Simple', server, variables))
    con = PubSubConnection.udp_udadp("Publisher Connection1 UDP UADP", pubid, UdpSettings(Url="opc.udp://127.0.0.1:4841"), reader_groups=[
        pubsub.ReaderGroup.new(
        name="ReaderGroup1",
        enable=True,
        reader=[
            pubsub.DataSetReader.new(
                pubid,
                writer_group_id,
                datasetwriter_id,
                dataset,
                name="SimpleDataSetReader",
                subscriped=subscriped_ds,
                enabled=True,
            )
        ],
    )
    ],
    writer_groups=[
        pubsub.WriterGroup.new_uadp(
                    name="WriterGroup1",
                    writer_group_id=writer_group_id,
                    publishing_interval=100,
                    writer=[pubsub.DataSetWriter.new_uadp(
                        name="Writer1",
                        dataset_writer_id=datasetwriter_id,
                        dataset_name='Simple',
                        datavalue=True,
                    )],
                )
    ])
    await ps.add_connection(con)
    async with ps:
        for i in range(20):
            await pusbsub_src_nodes[0].write_value(Int32(i))
            await pusbsub_src_nodes[1].write_value(str(i))
            await pusbsub_src_nodes[2].write_value(i % 2 == 0)
            await pusbsub_src_nodes[3].write_value([Int16(x) for x in range(i, i + 3)])
            await asyncio.sleep(0.200)
            for dest, src in zip(pubsub_dest_nodes, pusbsub_src_nodes):
                assert await dest.read_value() == await src.read_value()


async def test_load_save_ua_binary_publisher(server: Server, tmpdir_factory):
    ps = await server.get_pubsub()
    in_file = 'tests/check_publisher_configuration.bin'
    out_file = tmpdir_factory.mktemp("pubsub") / 'check_publisher_configuration.bin'
    await ps.load_binary_file(in_file)
    assert len(ps._con) == 1
    con = ps.get_connection('UADP Connection 1')
    assert con is not None
    assert len(con._writer_groups) == 1
    wgr = con.get_writer_group('Demo WriterGroup')
    assert wgr is not None
    assert len(wgr._writer) == 1
    dsw = wgr.get_writer('Demo DataSetWriter')
    assert dsw is not None
    await ps.save_binary_file(out_file)

    ps = pubsub.PubSub(None, server)
    in_file = 'tests/check_publisher_configuration.bin'
    out_file = tmpdir_factory.mktemp("pubsub") / 'check_publisher_configuration.bin'
    await ps.load_binary_file(in_file)
    assert len(ps._con) == 1
    con = ps.get_connection('UADP Connection 1')
    assert con is not None
    assert len(con._writer_groups) == 1
    wgr = con.get_writer_group('Demo WriterGroup')
    assert wgr is not None
    assert len(wgr._writer) == 1
    dsw = wgr.get_writer('Demo DataSetWriter')
    assert dsw is not None

