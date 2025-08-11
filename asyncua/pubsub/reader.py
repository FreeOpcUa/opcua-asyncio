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
    SubScripedDataSet:
        - all @TODO
"""

from __future__ import annotations
from typing import Iterable, List, Optional, TYPE_CHECKING
import asyncio
from asyncua.common import instantiate_util
from asyncua.common.node import Node
from asyncua.common.utils import Buffer
from asyncua.pubsub.information_model import PubSubInformationModel
from asyncua.pubsub.subscriped_dataset import (
    SubScripedTargetVariables,
    SubscribedDataSetMirror,
)

if TYPE_CHECKING:
    from asyncua.server.server import Server
from asyncua.ua import uaerrors
from asyncua.ua.object_ids import ObjectIds
from asyncua.ua.ua_binary import from_binary
from ..ua.uatypes import (
    DataValue,
    LocalizedText,
    NodeId,
    String,
    UInt16,
    Variant,
    VariantType,
)
from .dataset import DataSetValue
import logging
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
from .dataset import DataSetMeta
from .protocols import SubscripedDataSet
from ..ua.uaprotocol_auto import (
    DataSetReaderDataType,
    PubSubState,
    ReaderGroupDataType,
    SubscribedDataSetMirrorDataType,
    TargetVariablesDataType,
)

logger = logging.getLogger(__name__)


def datavalue_from_variant(v: Variant, header: UadpDataSetMessageHeader) -> DataValue:
    return DataValue(v, header.Status, None, None, header.Timestamp, header.PicoSeconds)


class DataSetReader(PubSubInformationModel):
    """
    Reads a Pubsub Message
    """

    __reader_cnt = 0

    def __init__(
        self,
        cfg: Optional[DataSetReaderDataType] = None,
        subscriped: Optional[SubscripedDataSet] = None,
    ) -> None:
        super().__init__()
        if cfg is None:
            self._cfg = DataSetReaderDataType()
        else:
            self._cfg = cfg
        self._meta = DataSetMeta(self._cfg.DataSetMetaData)
        self._subscriped = None
        if subscriped is not None:
            self._subscriped = subscriped
            get_subscribed_dataset = getattr(self._subscriped, "get_subscribed_dataset", None)
            if callable(get_subscribed_dataset):
                self._cfg.SubscribedDataSet = self._subscriped.get_subscribed_dataset()
        self._task = None

    @classmethod
    def new(
        cls,
        publisherId: Variant,
        writer_group_id: UInt16,
        dataset_writer_id: UInt16,
        meta: Optional[DataSetMeta] = None,
        name: Optional[str] = None,
        enabled: Optional[bool] = False,
        subscriped: Optional[SubscripedDataSet] = None,
    ):
        if name is None:
            name = f"Reader{cls.__reader_cnt}"
            cls.__reader_cnt += 1
        cfg = DataSetReaderDataType(
            Name=name,
            PublisherId=publisherId,
            Enabled=enabled,
            WriterGroupId=writer_group_id,
            DataSetWriterId=dataset_writer_id,
        )
        o = cls(cfg, subscriped)
        if meta is not None:
            o._meta = meta
            o._cfg.DataSetMetaData = meta._meta
        return o

    def set_subscriped(self, subscriped: SubscripedDataSet) -> None:
        self._subscriped = subscriped

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
            values = self._datavalues_from_raw(ds.Data, ds.Header)
            fields = [DataSetValue(m.Name, d, m) for d, m in zip(values, self._meta._fields)]
        else:
            raise NotImplementedError(f"Not implemented Dataset for Reader {ds}")
        if self._subscriped:
            await self._subscriped.on_dataset_recived(self._meta, fields)
        else:
            logger.warning("DataSet %s: got Message without a SubsripedDataSet Handler", self._cfg.Name)

    def _datavalues_from_raw(self, data: UadpDataSetRaw, header: UadpDataSetMessageHeader) -> List[DataValue]:
        """Converts Raw dataset to Datavalue"""
        buf = Buffer(data.Data)
        values = []
        for field in self._meta._fields:
            dtname = field.get_datatype_name()
            if dtname:
                v = from_binary(dtname, buf)
                values.append(
                    DataValue(
                        v,
                        header.Status,
                        None,
                        None,
                        header.Timestamp,
                        header.PicoSeconds,
                    )
                )
            else:
                raise uaerrors.UaError(f"Unimplemented field found in decoding {field}")
        return values

    async def _timeout_task(self) -> None:
        await self._set_state(PubSubState.Operational)
        # Check if timeouted
        if self._subscriped:
            await self._subscriped.on_state_change(self._cfg, PubSubState.Operational)
        while 1:
            if self._cfg.MessageReceiveTimeout == 0:
                await asyncio.sleep(0.1)
            else:
                try:
                    await asyncio.wait_for(self.timeout_ev.wait(), self._cfg.MessageReceiveTimeout * 1000)
                except asyncio.TimeoutError:
                    logger.warning("%s: Timed out", self._cfg.Name)
                    await self._set_state(PubSubState.Error)
                    if self._subscriped:
                        await self._subscriped.on_state_change(self._cfg, PubSubState.Error)

    async def start(self) -> None:
        self.timeout_ev = asyncio.Event()
        self._task = asyncio.create_task(self._timeout_task())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await self._set_state(PubSubState.Disabled)
            if self._subscriped:
                await self._subscriped.on_state_change(self._cfg, PubSubState.Disabled)
            await self._task

    async def _init_information_model(self, parent: Node, server: Server) -> None:
        """
        Inits the information model
        """
        reader_grp_type = server.get_node(NodeId(ObjectIds.DataSetReaderType, 0))
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
        await parent.add_reference(reader_obj, NodeId(ObjectIds.HasDataSetReader))
        await parent.delete_reference(reader_obj, ObjectIds.HasComponent)
        # @FIXME currently the datatype is wrong in the addresspace! Need to change schema generator
        await self.set_node_value("0:PublisherId", Variant(str(self._cfg.PublisherId)))
        await self.set_node_value("0:WriterGroupId", self._cfg.WriterGroupId)
        await self.set_node_value("0:DataSetMetaData", self._cfg.DataSetMetaData)
        await self.set_node_value("0:DataSetFieldContentMask", self._cfg.DataSetFieldContentMask_)
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
        if self._subscriped is not None:
            if self._cfg.SubscribedDataSet.data_type == SubscribedDataSetMirrorDataType.data_type:
                self._subscriped = SubscribedDataSetMirror(self._cfg.SubscribedDataSet, self._node)
            elif self._cfg.SubscribedDataSet.data_type == TargetVariablesDataType.data_type:
                self._subscriped = SubScripedTargetVariables(self._server, self._cfg.SubscribedDataSet)
        if self._subscriped is not None:
            if isinstance(self._subscriped, SubScripedTargetVariables):
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
                    self._subscriped._cfg.TargetVariables,
                )
            elif isinstance(self._subscriped, SubscribedDataSetMirror):
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
    Manages diffrent reader
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
        name: Optional[str] = None,
        reader: Optional[List[DataSetReader]] = None,
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
        if msg.DataSetPayloadHeader is None or not msg.DataSetPayloadHeader:
            logger.info("Got UadpMessage without Payload header!")
            return
        pubid = Variant(msg.Header.PublisherId)
        if msg.GroupHeader is not None:
            writer_id_groupe = msg.GroupHeader.WriterGroupId
        else:
            writer_id_groupe = None
        found_reader = False
        assert isinstance(msg.Payload, Iterable)
        for reader in self._reader:
            # Check if the message is for this reader WriterGroupId = 0 and DatSetWriterId = 0 are wildcards
            if reader._cfg.Enabled:
                if reader._cfg.PublisherId == pubid:
                    if reader._cfg.WriterGroupId == 0 or reader._cfg.WriterGroupId == writer_id_groupe:
                        if reader._cfg.DataSetWriterId != 0:
                            for i, dsid in enumerate(msg.DataSetPayloadHeader):
                                if dsid == reader._cfg.DataSetWriterId:
                                    await reader.handle_dataset(msg.Payload[i])
                                    found_reader = True
                        else:
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
        reader_grp_type = server.get_node(NodeId(ObjectIds.ReaderGroupType, 0))
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
        await parent.add_reference(reader_gp_obj, NodeId(ObjectIds.HasReaderGroup))
        await parent.delete_reference(reader_gp_obj, ObjectIds.HasComponent)
        await self.set_node_value("0:SecurityMode", self._cfg.SecurityMode)
        await self.set_node_value(
            "0:MaxNetworkMessageSize",
            Variant(self._cfg.MaxNetworkMessageSize, VariantType.UInt32),
        )
        if self._node is not None:
            await self._node.add_variable(NodeId(NamespaceIndex=1), "0:SecurityGroupId", self._cfg.SecurityGroupId)
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
