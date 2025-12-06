"""
Decodes DatasetMessages
unimplemented:
    DSReader:
        - 6.2.8.4 DataSetMetaData
        - implement messageSettings
        - timeouthandling
        - inital value handling
        - DeltaRaw
        - enabled disabled of dataset and callback
        - Keyframecount update
        - implement state
    SubScribedDataSet:
        - all @TODO
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING

from ..common import instantiate_util
from ..common.node import Node
from ..common.utils import Buffer
from ..ua.object_ids import ObjectIds
from ..ua.ua_binary import unpack_uatype
from ..ua.uaerrors import UaError
from ..ua.uaprotocol_auto import (
    DataSetReaderDataType,
    PubSubState,
    ReaderGroupDataType,
    SubscribedDataSetMirrorDataType,
    TargetVariablesDataType,
)
from ..ua.uatypes import (
    DataValue,
    Int16,
    Int32,
    LocalizedText,
    NodeId,
    StatusCode,
    String,
    UInt16,
    UInt32,
    Variant,
    VariantType,
)
from .dataset import DataSetMeta, DataSetValue
from .information_model import PubSubInformationModel
from .protocols import SubscribedDataSet
from .subscribed_dataset import (
    SubscribedDataSetMirror,
    SubScribedTargetVariables,
)
from .uadp import (
    UadpDataSetDataValue,
    UadpDataSetDeltaDataValue,
    UadpDataSetDeltaVariant,
    UadpDataSetMessage,
    UadpDataSetMessageHeader,
    UadpDataSetRaw,
    UadpDataSetVariant,
    UadpNetworkMessage,
)

if TYPE_CHECKING:
    from ..server.server import Server

logger = logging.getLogger(__name__)


def status_to_status_code(status: UInt16 | None) -> StatusCode:
    """Upgrade the header status to a full StatusCode."""
    return StatusCode(UInt32(((status or 0) & 0xFFFF) << 16))


def datavalue_from_variant(v: Variant, header: UadpDataSetMessageHeader) -> DataValue:
    """Upgrade a Variant-encoded field of a Data Key Frame to DataValue for our callback."""
    return DataValue(
        v,
        status_to_status_code(header.Status),
        SourceTimestamp=None,
        ServerTimestamp=header.Timestamp,
        SourcePicoseconds=None,
        ServerPicoseconds=header.PicoSeconds,
    )


class DataSetReader(PubSubInformationModel):
    """
    Reads a Pubsub Message
    """

    __reader_cnt = 0

    def __init__(
        self,
        cfg: DataSetReaderDataType | None = None,
        subscribed: SubscribedDataSet | None = None,
    ) -> None:
        super().__init__()
        if cfg is None:
            self._cfg = DataSetReaderDataType()
        else:
            self._cfg = cfg
        self._meta = DataSetMeta(self._cfg.DataSetMetaData)
        self._subscribed = None
        if subscribed is not None:
            self._subscribed = subscribed
            get_subscribed_dataset = getattr(self._subscribed, "get_subscribed_dataset", None)
            if callable(get_subscribed_dataset):
                self._cfg.SubscribedDataSet = self._subscribed.get_subscribed_dataset()
        self._task = None

    @classmethod
    def new(
        cls,
        publisherId: Variant,
        writer_group_id: UInt16,
        dataset_writer_id: UInt16,
        meta: DataSetMeta | None = None,
        name: str | None = None,
        enabled: bool | None = False,
        subscribed: SubscribedDataSet | None = None,
    ):
        if name is None:
            name = f"Reader{cls.__reader_cnt}"
            cls.__reader_cnt += 1
        cfg = DataSetReaderDataType(
            Name=String(name),
            PublisherId=publisherId,
            Enabled=bool(enabled),
            WriterGroupId=writer_group_id,
            DataSetWriterId=dataset_writer_id,
        )
        o = cls(cfg, subscribed)
        if meta is not None:
            o._meta = meta
            o._cfg.DataSetMetaData = meta._meta
        return o

    def set_subscribed(self, subscribed: SubscribedDataSet) -> None:
        self._subscribed = subscribed

    async def set_meta_data(self, meta: DataSetMeta) -> None:
        self._meta = meta
        self._cfg.DataSetMetaData = meta._meta

    async def handle_dataset(self, ds: UadpDataSetMessage) -> None:
        if isinstance(ds, UadpDataSetDataValue):
            fields = [DataSetValue(m.Name, d, m) for d, m in zip(ds.Data, self._meta._fields)]
        elif isinstance(ds, UadpDataSetDeltaDataValue):
            fields = [DataSetValue(self._meta._fields[d.No].Name, d.Value, self._meta._fields[d.No]) for d in ds.Data]
        elif isinstance(ds, UadpDataSetVariant):
            fields = [
                DataSetValue(m.Name, datavalue_from_variant(d, ds.Header), m)
                for d, m in zip(ds.Data, self._meta._fields)
            ]
        elif isinstance(ds, UadpDataSetDeltaVariant):
            fields = [
                DataSetValue(
                    self._meta._fields[d.No].Name,
                    datavalue_from_variant(d.Value, ds.Header),
                    self._meta._fields[d.No],
                )
                for d in ds.Data
            ]
        elif isinstance(ds, UadpDataSetRaw):
            values = self._datavalues_from_raw(ds, ds.Header)
            fields = [DataSetValue(m.Name, d, m) for d, m in zip(values, self._meta._fields)]
        else:
            raise NotImplementedError(f"Not implemented Dataset for Reader {ds}")
        if self._subscribed:
            await self._subscribed.on_dataset_received(self._meta, fields)
        else:
            logger.warning("DataSet %s: got Message without a SubscribedDataSet Handler", self._cfg.Name)

    def _datavalues_from_raw(self, data: UadpDataSetRaw, header: UadpDataSetMessageHeader) -> list[DataValue]:
        """Converts Raw dataset to DataValue"""
        buf = Buffer(data.Data)
        values = []
        for field in self._meta._fields:
            vt = field.BuiltInType
            if vt:
                # FIXME: Properly we should use field.DataType, due to BuiltInType special cases 2, 4, & 5
                # in https://reference.opcfoundation.org/Core/Part14/v105/docs/6.2.3.2.4
                v = unpack_uatype(VariantType(vt), buf)
                values.append(
                    DataValue(
                        v,
                        header.Status,
                        SourceTimestamp=None,
                        ServerTimestamp=header.Timestamp,
                        SourcePicoseconds=None,
                        ServerPicoseconds=header.PicoSeconds,
                    )
                )
            else:
                raise UaError(f"Unimplemented field found in decoding {field}")
        return values

    async def _timeout_task(self) -> None:
        await self._set_state(PubSubState.Operational)
        # Check if timeouted
        if self._subscribed:
            await self._subscribed.on_state_change(self._cfg, PubSubState.Operational)
        while 1:
            if self._cfg.MessageReceiveTimeout == 0:
                await asyncio.sleep(0.1)
            else:
                try:
                    await asyncio.wait_for(self.timeout_ev.wait(), self._cfg.MessageReceiveTimeout * 1000)
                except asyncio.TimeoutError:
                    logger.warning("%s: Timed out", self._cfg.Name)
                    await self._set_state(PubSubState.Error)
                    if self._subscribed:
                        await self._subscribed.on_state_change(self._cfg, PubSubState.Error)

    async def start(self) -> None:
        self.timeout_ev = asyncio.Event()
        self._task = asyncio.create_task(self._timeout_task())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await self._set_state(PubSubState.Disabled)
            if self._subscribed:
                await self._subscribed.on_state_change(self._cfg, PubSubState.Disabled)
            await self._task

    async def _init_information_model(self, parent: Node, server: Server) -> None:
        """
        Inits the information model
        """
        reader_grp_type = server.get_node(NodeId(Int32(ObjectIds.DataSetReaderType)))
        nodes = await instantiate_util.instantiate(
            parent,
            reader_grp_type,
            idx=1,
            bname=self._cfg.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._cfg.Name, ""),
        )
        reader_obj = nodes[0]
        await self._init_node(reader_obj, server)
        await parent.add_reference(reader_obj, NodeId(Int32(ObjectIds.HasDataSetReader)))
        await parent.delete_reference(reader_obj, ObjectIds.HasComponent)
        # @FIXME currently the datatype is wrong in the AddressSpace! Need to change schema generator
        await self.set_node_value("0:PublisherId", Variant(str(self._cfg.PublisherId)))
        await self.set_node_value("0:WriterGroupId", self._cfg.WriterGroupId)
        await self.set_node_value("0:DataSetMetaData", self._cfg.DataSetMetaData)
        await self.set_node_value("0:DataSetFieldContentMask", self._cfg.DataSetFieldContentMask)
        await self.set_node_value("0:MessageReceiveTimeout", self._cfg.MessageReceiveTimeout)
        await self.set_node_value("0:KeyFrameCount", Variant(self._cfg.KeyFrameCount, VariantType.UInt32))
        if self._cfg.HeaderLayoutUri is None:
            self._cfg.HeaderLayoutUri = ""
        await self.set_node_value("0:HeaderLayoutUri", self._cfg.HeaderLayoutUri)
        # await self.set_node_value("0:SecurityMode", self._cfg.SecurityMode)
        # await self.set_node_value("0:SecurityGroupId", self._cfg.SecurityGroupId)
        # await self.set_node_value("0:SecurityKeyServices", self._cfg.SecurityKeyServices)
        await self.set_node_value(
            "0:DataSetReaderProperties",
            Variant(
                self._cfg.DataSetReaderProperties,
                VariantType.ExtensionObject,
                is_array=True,
            ),
        )
        """ @TODO
        # "0:Enabled" ignore for now
        TransportSettings
        MessageSettings
        """
        if self._subscribed is not None:
            if self._cfg.SubscribedDataSet.data_type == SubscribedDataSetMirrorDataType.data_type:
                self._subscribed = SubscribedDataSetMirror(self._cfg.SubscribedDataSet, self._node)
            elif self._cfg.SubscribedDataSet.data_type == TargetVariablesDataType.data_type:
                self._subscribed = SubScribedTargetVariables(self._server, self._cfg.SubscribedDataSet)
        if self._subscribed is not None:
            if isinstance(self._subscribed, SubScribedTargetVariables):
                nodes = await instantiate_util.instantiate(
                    self._node,
                    server.get_node(NodeId(ObjectIds.TargetVariablesType)),
                    bname="0:SubscribedDataSet",
                    dname=LocalizedText("SubscribedDataSet"),
                    idx=1,
                    instantiate_optional=False,
                )
                await self.set_node_value(
                    ["0:SubscribedDataSet", "0:TargetVariables"],
                    self._subscribed._cfg.TargetVariables,
                )
            elif isinstance(self._subscribed, SubscribedDataSetMirror):
                nodes = await instantiate_util.instantiate(
                    self._node,
                    server.get_node(NodeId(ObjectIds.SubscribedDataSetMirrorType)),
                    bname="0:SubscribedDataSet",
                    dname=LocalizedText("SubscribedDataSet"),
                    idx=1,
                    instantiate_optional=False,
                )
        # @TODO fill methods
        # add_r = await self._node.get_child("0:CreateTargetVariables")
        # remove_r = await self._node.get_child("0:CreateDataSetMirror")


class ReaderGroup(PubSubInformationModel):
    """
    Manages different reader
    """

    __reader_cnt = 0

    def __init__(self, cfg: ReaderGroupDataType) -> None:
        super().__init__()
        self._cfg = ReaderGroupDataType()
        self._reader = [DataSetReader(r) for r in cfg.DataSetReaders]
        self._tasks = None

    @classmethod
    def new(
        cls,
        name: str | None = None,
        reader: list[DataSetReader] | None = None,
        enable=False,
    ):
        obj = cls(ReaderGroupDataType())
        obj._reader = reader if reader is not None else []
        if name is not None:
            obj._cfg.Name = name
        else:
            obj._cfg.Name = "Reader" + str(cls.__reader_cnt)
            cls.__reader_cnt += 1
        obj._cfg.Enabled = enable
        return obj

    def get_name(self) -> String:
        return self._cfg.Name

    async def set_name(self) -> String:
        return self._cfg.Name

    async def add_dataset_reader(self, reader: DataSetReader) -> None:
        self._reader.append(reader)
        self._cfg.DataSetReaders.append(reader._cfg)
        if self.model_is_init():
            await reader._init_information_model(self._node, self._server)

    async def handle_msg(self, msg: UadpNetworkMessage) -> None:
        pubid = Variant(msg.Header.PublisherId)
        if msg.GroupHeader is not None:
            writer_group_id = msg.GroupHeader.WriterGroupId
        else:
            writer_group_id = None
        assert isinstance(msg.Payload, Iterable)
        if msg.DataSetPayloadHeader:
            ds_writer_ids = msg.DataSetPayloadHeader
        else:
            logger.info("Got UadpMessage without Payload header!")
            # This raw"fixed layout" is extremely hard to parse, because without DataSetWriterIds,
            # you must deal out DataSetMessages to readers (filtered PublisherId & WriterGroupId)
            # by their DataSetOffset.
            # FIXME: For now, wildcard readers get everything.
            ds_writer_ids = [UInt16(0)] * len(msg.Payload)
        found_reader = False
        for reader in self._reader:
            # Check if the message is for this reader
            # NOTE: WriterGroupId = 0 and DataSetWriterId = 0 are wildcards
            if reader._cfg.Enabled:
                if reader._cfg.PublisherId == pubid:
                    if reader._cfg.WriterGroupId == 0 or reader._cfg.WriterGroupId == writer_group_id:
                        if reader._cfg.DataSetWriterId != 0:
                            for i, ds_w_id in enumerate(ds_writer_ids):
                                if ds_w_id == reader._cfg.DataSetWriterId:
                                    await reader.handle_dataset(msg.Payload[i])
                                    found_reader = True
                        else:
                            for i, _ in enumerate(ds_writer_ids):
                                await reader.handle_dataset(msg.Payload[i])
                                found_reader = True
        if not found_reader:
            logger.info("Got Message with no matching reader: %s %s!", msg.Header.PublisherId, msg)

    async def start(self):
        await self._set_state(PubSubState.Operational)
        try:
            for reader in self._reader:
                await reader.start()
        except Exception:
            await self._set_state(PubSubState.Error)
            raise

    async def stop(self):
        await self._set_state(PubSubState.Disabled)
        for reader in self._reader:
            await reader.stop()

    async def _init_information_model(self, parent: Node, server: Server) -> None:
        """
        Inits the information model
        """
        reader_grp_type = server.get_node(NodeId(Int32(ObjectIds.ReaderGroupType)))
        nodes = await instantiate_util.instantiate(
            parent,
            reader_grp_type,
            idx=1,
            bname=self._cfg.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._cfg.Name, ""),
        )
        reader_gp_obj = nodes[0]
        await self._init_node(reader_gp_obj, server)
        await parent.add_reference(reader_gp_obj, NodeId(Int32(ObjectIds.HasReaderGroup)))
        await parent.delete_reference(reader_gp_obj, ObjectIds.HasComponent)
        await self.set_node_value("0:SecurityMode", self._cfg.SecurityMode)
        await self.set_node_value(
            "0:MaxNetworkMessageSize",
            Variant(self._cfg.MaxNetworkMessageSize, VariantType.UInt32),
        )
        if self._node is not None:
            await self._node.add_variable(
                NodeId(NamespaceIndex=Int16(1)), "0:SecurityGroupId", self._cfg.SecurityGroupId
            )
        else:
            logger.warning("self._node is None, cannot add variable")
        await self.set_node_value(
            "0:GroupProperties",
            Variant(self._cfg.GroupProperties, VariantType.ExtensionObject, is_array=True),
        )
        # await self._node.add_variable(NodeId(NamespaceIndex=1), "0:SecurityKeyServices", Variant(self._cfg.SecurityKeyServices, VariantType.ExtensionObject, is_array=True), VariantType.ExtensionObject)
        # @TODO fill methods
        # add_r = await self._node.get_child("0:AddDataSetReader")
        # remove_r = await self._node.get_child("0:RemoveDataSetReader")

        for reader in self._reader:
            await reader._init_information_model(self._node, self._server)
