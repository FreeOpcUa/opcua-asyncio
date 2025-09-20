"""
missing features:
    Uadp: - implement a lot of specs correct  (timing, publishing)
          - DeltaFrames
          - PromotedFields
    JsonEncoding: all
    DataSetWriter: implement state
"""

from __future__ import annotations
import asyncio
import logging
from typing import List, TYPE_CHECKING, Tuple, Union
from datetime import timezone

from ..common.node import Node
from ..common import instantiate_util
from ..ua import WriterGroupDataType, status_codes
from ..ua.object_ids import ObjectIds
from ..ua.uatypes import (
    DataValue,
    DateTime,
    Int16,
    Int32,
    LocalizedText,
    NodeId,
    StatusCode,
    String,
    UInt16,
    UInt32,
    VariantType,
)
from ..ua.uaerrors import UaError
from ..ua.uaprotocol_auto import (
    DataSetFieldContentMask,
    DataSetOrderingType,
    DataSetWriterDataType,
    Duration,
    JsonWriterGroupMessageDataType,
    PubSubState,
    UadpDataSetMessageContentMask,
    UadpDataSetWriterMessageDataType,
    UadpWriterGroupMessageDataType,
    UadpNetworkMessageContentMask,
    Variant,
    VersionTime,
)

from .dataset import PublishedDataSet
from .information_model import PubSubInformationModel
from .protocols import IPubSub, PubSubSender
from .uadp import (
    UadpDataSetDataValue,
    UadpDataSetMessage,
    UadpDataSetMessageHeader,
    UadpDataSetRaw,
    UadpDataSetVariant,
    UadpGroupHeader,
    UadpNetworkMessage,
)

if TYPE_CHECKING:
    from ..server.server import Server

logger = logging.getLogger(__name__)


class DataSetWriter(PubSubInformationModel):
    """
    Write of an Dataset
    """

    _node: Node | None = None

    def __init__(self, cfg: DataSetWriterDataType | None):
        if cfg is None:
            self._cfg = DataSetWriterDataType()
        else:
            self._cfg = cfg
        self._seq_no = 0
        super().__init__()

    def get_id(self) -> UInt16:
        return self._cfg.DataSetWriterId

    def get_name(self) -> String:
        return self._cfg.Name

    @classmethod
    def new_uadp(
        cls,
        name: String,
        dataset_name: String,
        dataset_writer_id: UInt16,
        datavalue: bool | None = False,
        raw: bool | None = False,
        enabled: bool | None = True,
        *,
        message_timestamp: bool | None = None,
        message_status: bool | None = None,
    ):
        """
        Create a DataSetWriter for UADP with sane defaults
        name: Name of the DataSetWriter
        dataset_name: Name of the Dataset this is used to get a PublishedDataSet
        dataset_writer_id: Id for the subscriber to identify the DataSetWriter
        enabled: if not enabled no msg are generated
        datavalue: each value sends ServerTimestamp, SourceTimestamp and StatusCode otherwise only a variant is send or binary data (raw flag).
        raw: sends raw value. data either datavalue or raw can be used
        message_timestamp: whether the timestamp is added to message header
        message_status: whether the overall status is added to message header
        """
        message_mask = UadpDataSetMessageContentMask.SequenceNumber
        mask: DataSetFieldContentMask
        if datavalue:
            if message_status:
                message_mask |= UadpDataSetMessageContentMask.Status
            if message_timestamp:  # Default to no timestamp for datavalue
                message_mask |= UadpDataSetMessageContentMask.Timestamp
            mask = (
                DataSetFieldContentMask.ServerTimestamp
                | DataSetFieldContentMask.StatusCode
                | DataSetFieldContentMask.SourceTimestamp
            )
        else:
            if message_status is None or message_status:  # Default to status for variant/raw
                message_mask |= UadpDataSetMessageContentMask.Status
            if message_timestamp is None or message_timestamp:  # Default to timestamp for variant/raw
                message_mask |= UadpDataSetMessageContentMask.Timestamp
            if raw:
                mask = DataSetFieldContentMask.RawData
            else:  # Variant encoding
                mask = DataSetFieldContentMask(0)
        message_settings = UadpDataSetWriterMessageDataType(DataSetMessageContentMask=message_mask)
        dsw_cfg = DataSetWriterDataType(
            Name=name,
            Enabled=bool(enabled),
            DataSetWriterId=dataset_writer_id,
            DataSetName=dataset_name,
            KeyFrameCount=UInt32(1),
            MessageSettings=message_settings,
            DataSetFieldContentMask_=mask,
        )
        return cls(dsw_cfg)

    def generate_promoted_fields(self) -> List[Variant]:  # type: ignore[empty-body]
        # @TODO
        pass

    async def generate_uadp_dataset(self, pds: PublishedDataSet) -> UadpDataSetMessage:
        msg_cfg: UadpDataSetWriterMessageDataType = self._cfg.MessageSettings
        header = UadpDataSetMessageHeader(Valid=True)
        self._seq_no += 1
        if UadpDataSetMessageContentMask.MajorVersion in msg_cfg.DataSetMessageContentMask:
            header.CfgMajorVersion = pds.dataset._meta.ConfigurationVersion.MajorVersion
        if UadpDataSetMessageContentMask.MinorVersion in msg_cfg.DataSetMessageContentMask:
            header.CfgMinorVersion = pds.dataset._meta.ConfigurationVersion.MinorVersion
        if UadpDataSetMessageContentMask.PicoSeconds in msg_cfg.DataSetMessageContentMask:
            header.PicoSeconds = UInt16(0)  # Not supported
        if UadpDataSetMessageContentMask.SequenceNumber in msg_cfg.DataSetMessageContentMask:
            header.SequenceNo = UInt16(self._seq_no)
        if DataSetFieldContentMask.RawData in self._cfg.DataSetFieldContentMask:
            data, status, dt = await pds.get_source().get_raw()
            ds = UadpDataSetRaw(header, b"".join(data))
        elif self._cfg.DataSetFieldContentMask == DataSetFieldContentMask(0):
            data, status, dt = await pds.get_source().get_variant()
            ds = UadpDataSetVariant(header, data)
        else:
            status = DataSetFieldContentMask.StatusCode
            source = DataSetFieldContentMask.SourceTimestamp
            server = DataSetFieldContentMask.ServerTimestamp
            data = await pds.get_source().get_value(status, server, source)
            ds = UadpDataSetDataValue(header, data)
            dt = DateTime.now(timezone.utc)
            status = StatusCode(UInt32(status_codes.StatusCodes.Good))
        if UadpDataSetMessageContentMask.Status in msg_cfg.DataSetMessageContentMask:
            # per OPC UA v1.05, 7.2.4.5.4, Header.Status is the high word of a StatusCode
            ds.Header.Status = UInt16((status.value >> 16) & 0xFFFF)
        if UadpDataSetMessageContentMask.Timestamp in msg_cfg.DataSetMessageContentMask:
            ds.Header.Timestamp = dt
        return ds

    async def _init_information_model(self, parent: Node, server: Server, pubsub: IPubSub | None) -> None:
        dsw_type = server.get_node(NodeId(Int32(ObjectIds.DataSetWriterType), Int16(0)))
        objs = await instantiate_util.instantiate(
            parent,
            dsw_type,
            idx=1,
            bname=self._cfg.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._cfg.Name, ""),
        )
        dsw_obj = objs[0]
        self._node = dsw_obj
        await self._init_node(dsw_obj, server)
        await parent.add_reference(dsw_obj, NodeId(Int32(ObjectIds.HasDataSetWriter)))
        await parent.delete_reference(dsw_obj, ObjectIds.HasComponent)
        # Add Reference to Dataset
        if pubsub:
            ds = pubsub.get_published_dataset(self._cfg.DataSetName)
            if ds is not None:
                if ds._node is None:
                    raise RuntimeError(f"DataSet node for '{self._cfg.DataSetName}' is not initialized")
                await ds._node.add_reference(dsw_obj, NodeId(Int32(ObjectIds.DataSetToWriter)))
        await self.set_node_value("0:DataSetFieldContentMask", self._cfg.DataSetFieldContentMask_)

        await self._node.add_variable(NodeId(NamespaceIndex=Int16(1)), "0:KeyFrameCount", self._cfg.KeyFrameCount)

        await self.set_node_value(
            "0:DataSetWriterProperties",
            Variant(
                self._cfg.DataSetWriterProperties,
                is_array=True,
                VariantType=VariantType.ExtensionObject,
            ),
        )
        # @TODO await self.set_node_value("0:TransportSettings")
        #      await self.set_node_value("0:Enabled", self._cfg.Enabled)
        # UadpDataSetWriterMessageType

        msg_cfg: Union[UadpDataSetWriterMessageDataType, None] = self._cfg.MessageSettings
        if isinstance(msg_cfg, UadpDataSetWriterMessageDataType):
            object_type_id = NodeId(Int32(ObjectIds.UadpDataSetWriterMessageType), Int16(0))
            nodes = await instantiate_util.instantiate(
                dsw_obj,
                server.get_node(object_type_id),
                idx=1,
                bname="0:MessageSettings",
                dname=LocalizedText("MessageSettings"),
            )
            msg_settings = nodes[0]
            n = await msg_settings.get_child("0:ConfiguredSize")
            await n.set_data_value(DataValue(Variant(msg_cfg.ConfiguredSize, VariantType.UInt16)))
            n = await msg_settings.get_child("0:DataSetMessageContentMask")
            await n.set_data_value(
                DataValue(Variant(msg_cfg.DataSetMessageContentMask, VariantType.UInt32))
            )  # FIXME: subtype
            n = await msg_settings.get_child("0:DataSetOffset")
            await n.set_data_value(DataValue(Variant(msg_cfg.DataSetOffset, VariantType.UInt16)))
            n = await msg_settings.get_child("0:NetworkMessageNumber")
            await n.set_data_value(DataValue(Variant(msg_cfg.NetworkMessageNumber, VariantType.UInt16)))


class WriterGroup(PubSubInformationModel):
    """
    Configures a group of datasets writer
    """

    _app: Server | None = None

    uadp = True  # Currently only uadp is supported

    def __init__(self, cfg: WriterGroupDataType | None) -> None:
        super().__init__()
        if cfg is not None:
            self._cfg = cfg
            self._writer = [DataSetWriter(writer) for writer in self._cfg.DataSetWriters]
        else:
            self._cfg = WriterGroupDataType()
            self._writer = []
        self._status = PubSubState.Disabled
        self._ps = None
        self._sequence_number = 0  # UInt16

    @classmethod
    def new_uadp(
        cls,
        name: String,
        writer_group_id: UInt16,
        group_version: VersionTime = VersionTime(0),
        enabled: bool | None = True,
        publishing_interval: Duration | None = Duration(1000),
        keep_alive_time: Duration | None = Duration(5000),
        max_network_message_size: UInt32 | None = UInt32(1500),
        writer: List[DataSetWriter] | None = None,
        *,
        payload_header: bool | None = True,
    ):
        """
        Create a WriterGroup for UADP with sane defaults
        name: Name of the WriterGroup
        writer_group_id: Id for the subscriber to identify the writer_group
        enabled: if not enabled no msg are generated
        publishing_interval: time between each publish
        payload_header: add the count and list of DataSetWriterIds to the UADP header
        """
        mask = (
            UadpNetworkMessageContentMask.PublisherId
            | UadpNetworkMessageContentMask.GroupHeader
            | UadpNetworkMessageContentMask.WriterGroupId
            | UadpNetworkMessageContentMask.GroupVersion
            | UadpNetworkMessageContentMask.NetworkMessageNumber
            | UadpNetworkMessageContentMask.SequenceNumber
        )
        if payload_header:
            mask |= UadpNetworkMessageContentMask.PayloadHeader
        message_settings = UadpWriterGroupMessageDataType(
            GroupVersion=group_version,
            NetworkMessageContentMask=mask,
            DataSetOrdering=DataSetOrderingType.AscendingWriterId,
        )
        cfg = WriterGroupDataType(
            Name=name,
            Enabled=bool(enabled),
            WriterGroupId=writer_group_id,
            PublishingInterval=publishing_interval or Duration(0),
            KeepAliveTime=keep_alive_time or Duration(0),
            MaxNetworkMessageSize=max_network_message_size or UInt32(0),
            MessageSettings=message_settings,
        )
        o = cls(cfg)
        if writer:
            for wr in writer:
                o._writer.append(wr)
                o._cfg.DataSetWriters.append(wr._cfg)
        return o

    async def add_writer(self, writer: DataSetWriter) -> None:
        self._writer.append(writer)
        self._cfg.DataSetWriters.append(writer._cfg)
        if self.model_is_init():
            await writer._init_information_model(self._node, self._server, self._app)

    def get_writer(self, name: String) -> DataSetWriter | None:
        return next((c for c in self._writer if c._cfg.Name == name), None)

    def _init_msg(
        self, sender: PubSubSender, msg_cfg: UadpWriterGroupMessageDataType, msg_no: int
    ) -> Tuple[UadpNetworkMessage, bool, bool]:
        msg = UadpNetworkMessage()
        payload_header = False
        promoted_fields = False
        if UadpNetworkMessageContentMask.PublisherId in msg_cfg.NetworkMessageContentMask:
            msg.Header.PublisherId = sender.get_publisher_id()
        if UadpNetworkMessageContentMask.GroupHeader in msg_cfg.NetworkMessageContentMask:
            msg.GroupHeader = UadpGroupHeader()
            if UadpNetworkMessageContentMask.GroupVersion in msg_cfg.NetworkMessageContentMask:
                msg.GroupHeader.GroupVersion = msg_cfg.GroupVersion
            if UadpNetworkMessageContentMask.WriterGroupId in msg_cfg.NetworkMessageContentMask:
                msg.GroupHeader.WriterGroupId = self._cfg.WriterGroupId
            if UadpNetworkMessageContentMask.NetworkMessageNumber in msg_cfg.NetworkMessageContentMask:
                msg.GroupHeader.NetworkMessageNo = UInt16(msg_no)
            if UadpNetworkMessageContentMask.SequenceNumber in msg_cfg.NetworkMessageContentMask:
                msg.GroupHeader.SequenceNo = UInt16(self._sequence_number)
                self._sequence_number = (self._sequence_number + 1) % 0xFFFF
        if UadpNetworkMessageContentMask.PayloadHeader in msg_cfg.NetworkMessageContentMask:
            payload_header = True
        if UadpNetworkMessageContentMask.Timestamp in msg_cfg.NetworkMessageContentMask:
            msg.Timestamp = DateTime.now(timezone.utc)
        if UadpNetworkMessageContentMask.PicoSeconds in msg_cfg.NetworkMessageContentMask:
            msg.PicoSeconds = UInt16(0)  # Not supported
        if UadpNetworkMessageContentMask.DataSetClassId in msg_cfg.NetworkMessageContentMask:
            # @TODO where to get the DataSetClassId?
            logger.warn("Uadp DataSetClassId is not supported.")
            pass
            # msg.Header.DataSetClassId = Guid()
        if UadpNetworkMessageContentMask.PromotedFields in msg_cfg.NetworkMessageContentMask:
            promoted_fields = True
        msg.Payload = []
        return msg, promoted_fields, payload_header

    async def _generate_uadp(self, sender: PubSubSender, ps: IPubSub):
        msg_cfg = self.get_msg_cfg()
        # Narrow type to UadpWriterGroupMessageDataType to safely access DataSetOrdering
        if not isinstance(msg_cfg, UadpWriterGroupMessageDataType):
            raise UaError("Invalid message configuration type for UADP generation")
        # Determine writer grouping based on DataSetOrdering
        if msg_cfg.DataSetOrdering == DataSetOrderingType.AscendingWriterId:
            writer = [sorted(self._writer, key=lambda w: w.get_id())]
        elif msg_cfg.DataSetOrdering == DataSetOrderingType.AscendingWriterIdSingle:
            writer = [[x] for x in sorted(self._writer, key=lambda w: w.get_id())]
        elif msg_cfg.DataSetOrdering == DataSetOrderingType.Undefined:
            writer = [self._writer]
        else:
            raise RuntimeError(f"Unknown DataSetOrderingType: {msg_cfg.DataSetOrdering}")
        msg_no = 1  # 0 is invalid, 1 is the only value for unsplit messages
        msgs: list[UadpNetworkMessage] = []
        for msg_writers in writer:
            msg, promoted_fields, payload_header = self._init_msg(sender, msg_cfg, msg_no)
            if promoted_fields and len(msg_writers) > 1:
                logger.error("Promoted Fields only work if number Datasets in a message is 1")
                raise UaError("Promoted Fields only work if number Datasets in a message is 1")
            for w in msg_writers:
                if payload_header:
                    msg.DataSetPayloadHeader.append(w.get_id())
                pds = ps.get_published_dataset(w._cfg.DataSetName)
                if pds is None:
                    logger.error("Pds with name %s not found!", w._cfg.DataSetName)
                    raise UaError("Error in Connection!")
                if isinstance(msg.Payload, list):
                    msg.Payload.append(await w.generate_uadp_dataset(pds))
                else:
                    raise UaError(f"Unexpected Payload type: {type(msg.Payload)}")
                if promoted_fields:
                    msg.PromotedFields = w.generate_promoted_fields()
            msg_no += 1  # NOTE: There is no need to split unless payload size > 65535
            msgs.append(msg)
        sender.send_uadp(msgs)

    async def run(self, sender: PubSubSender, ps: IPubSub):
        try:
            logging.info("WriterGroup %s running with %s ms", self._cfg.Name, self._cfg.PublishingInterval)
            await self._set_state(PubSubState.Operational)
            while 1:
                await self._generate_uadp(sender, ps)
                await asyncio.sleep(self._cfg.PublishingInterval / 1000)
            await self._set_state(PubSubState.Disabled)
        except Exception:
            await self._set_state(PubSubState.Error)
            raise

    def get_msg_cfg(self) -> Union[UadpWriterGroupMessageDataType, JsonWriterGroupMessageDataType]:
        if isinstance(self._cfg.MessageSettings, UadpWriterGroupMessageDataType):
            return self._cfg.MessageSettings
        if isinstance(self._cfg.MessageSettings, JsonWriterGroupMessageDataType):
            return self._cfg.MessageSettings
        raise Exception("Configuration error")

    async def _init_information_model(self, parent: Node, server: Server, pubsub: IPubSub) -> None:
        writer_grp_type = server.get_node(NodeId(Int32(ObjectIds.WriterGroupType)))
        self._ps = pubsub
        nodes = await instantiate_util.instantiate(
            parent,
            writer_grp_type,
            idx=1,
            bname=self._cfg.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._cfg.Name, ""),
        )
        writer_gp_obj = nodes[0]
        self._node = writer_gp_obj
        await parent.add_reference(writer_gp_obj, NodeId(Int32(ObjectIds.HasWriterGroup)))
        await parent.delete_reference(writer_gp_obj, ObjectIds.HasComponent)
        await self._init_node(writer_gp_obj, server)
        await self.set_node_value("0:SecurityMode", self._cfg.SecurityMode)
        await self.set_node_value(
            "0:MaxNetworkMessageSize",
            Variant(self._cfg.MaxNetworkMessageSize, VariantType.UInt32),
        )
        await self.set_node_value(
            "0:GroupProperties",
            Variant(
                self._cfg.GroupProperties,
                VariantType=VariantType.ExtensionObject,
                is_array=True,
            ),
        )
        if self._node is None:
            raise UaError("Writer node is not initialized")
        await self._node.add_variable(NodeId(NamespaceIndex=1), "0:SecurityGroupId", self._cfg.SecurityGroupId)
        await self._node.add_variable(
            NodeId(NamespaceIndex=Int16(1)),
            "0:SecurityKeyServices",
            Variant(
                self._cfg.SecurityKeyServices,
                VariantType=VariantType.ExtensionObject,
                is_array=True,
            ),
            datatype=ObjectIds.EndpointDescription,
        )
        await self.set_node_value("0:WriterGroupId", Variant(self._cfg.WriterGroupId, VariantType.UInt16))
        await self.set_node_value("0:PublishingInterval", self._cfg.PublishingInterval)
        await self.set_node_value("0:KeepAliveTime", self._cfg.KeepAliveTime)
        await self.set_node_value("0:Priority", Variant(self._cfg.WriterGroupId, VariantType.Byte))
        await self.set_node_value(
            "0:LocaleIds",
            Variant(self._cfg.LocaleIds, VariantType.String, is_array=True),
        )
        if self._cfg.HeaderLayoutUri is None:
            self._cfg.HeaderLayoutUri = ""
        await self.set_node_value("0:HeaderLayoutUri", self._cfg.HeaderLayoutUri)
        # UadpWriterGroupMessageType
        object_type_id = NodeId(Int32(ObjectIds.UadpWriterGroupMessageType))
        nodes = await instantiate_util.instantiate(
            writer_gp_obj,
            server.get_node(object_type_id),
            idx=1,
            bname="0:MessageSettings",
            dname=LocalizedText("MessageSettings"),
        )
        msg_settings = nodes[0]
        msg_cfg = self.get_msg_cfg()
        group_version = await msg_settings.get_child("0:GroupVersion")
        await group_version.set_data_value(DataValue(msg_cfg.GroupVersion))
        ordering = await msg_settings.get_child("0:DataSetOrdering")
        await ordering.set_data_value(DataValue(msg_cfg.DataSetOrdering))
        mask = await msg_settings.get_child("0:NetworkMessageContentMask")
        await mask.set_data_value(DataValue(msg_cfg.NetworkMessageContentMask))
        sampling_offset = await msg_settings.get_child("0:SamplingOffset")
        await sampling_offset.set_data_value(DataValue(msg_cfg.SamplingOffset))
        publishing_offset = await msg_settings.get_child("0:PublishingOffset")
        await publishing_offset.set_data_value(
            DataValue(Variant(msg_cfg.PublishingOffset, VariantType.Double, is_array=True))
        )

        for writer in self._writer:
            await writer._init_information_model(self._node, server, pubsub)
        # @TODO add transport settings  DatagramWriterGroupTransportType
        # transport_settings = await wgrp.get_child("0:TransportSettings")
        # a = await wgrp.get_child("0:MessageSettings")
        # @TODO fill methods
        # add_w = await self._node.get_child("0:AddDataSetWriter")
        # remove_w = await self._node.get_child("0:RemoveDataSetWriter")
