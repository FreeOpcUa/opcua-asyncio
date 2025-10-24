"""
A DataSet (ds) describes the data of pubsub
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timezone
from typing import TYPE_CHECKING

from ..common import instantiate_util
from ..common.methods import uamethod
from ..common.node import Node
from ..pubsub.information_model import PubSubInformationModel
from ..ua import DataSetMetaDataType, String, LocalizedText, FieldMetaData, ObjectIds
from ..ua.attribute_ids import AttributeIds
from ..ua.status_codes import StatusCodes
from ..ua.ua_binary import pack_uatype
from ..ua.uaerrors import UaStatusCodeError
from ..ua.uatypes import (
    Boolean,
    DataValue,
    DateTime,
    Guid,
    Int16,
    Int32,
    NodeId,
    StatusCode,
    UInt32,
    Byte,
    ValueRank,
    Variant,
    VariantType,
    extension_objects_by_datatype,
)
from ..ua.uaprotocol_auto import (
    ConfigurationVersionDataType,
    DataSetFieldFlags,
    PublishedDataItemsDataType,
    PublishedDataSetDataType,
    PublishedVariableDataType,
)
from .utils import version_time_now

if TYPE_CHECKING:
    from ..server.server import Server


def _get_datatype_or_built_in(datatype: NodeId | VariantType | int) -> tuple[NodeId, Byte]:
    """
    Returns the DataType NodeId and the corresponding BuiltIn number if
    possible to determine.
    """
    if isinstance(datatype, VariantType):
        dt = NodeId(Int32(datatype))
        built_in = Byte(datatype.value)
        return (dt, built_in)

    if isinstance(datatype, int):  # Assume it's in ObjectIds
        datatype = NodeId(Int32(datatype))

    if datatype.NamespaceIndex == 0 and isinstance(datatype.Identifier, int) and datatype.Identifier < 24:
        dt = datatype
        built_in = Byte(datatype.Identifier)
    else:
        dt = datatype
        built_in = Byte(0)
    return (dt, built_in)


class DataSetField:
    """
    DataSetField class describes the content of a field
    """

    def __init__(self, meta: FieldMetaData | None = None) -> None:
        if meta is None:
            self._meta = FieldMetaData(DataSetFieldId=uuid.uuid4(), FieldFlags=DataSetFieldFlags(0))
        else:
            self._meta = meta

    @classmethod
    def CreateScalar(cls, name: String, datatype: NodeId | VariantType):
        """
        Creates a scalar Field with datatype and name
        """
        datatype_nid, built_in = _get_datatype_or_built_in(datatype)
        meta = FieldMetaData(
            Name=name,
            DataSetFieldId=uuid.uuid4(),
            FieldFlags=DataSetFieldFlags(0),
            BuiltInType=built_in,
            DataType=datatype_nid,
            ValueRank=Int32(-1),
        )
        return cls(meta)

    @classmethod
    def CreateArray(cls, name: String, datatype: NodeId | VariantType):
        """
        Creates a scalar Field with datatype and name
        """
        datatype_nid, built_in = _get_datatype_or_built_in(datatype)
        meta = FieldMetaData(
            Name=name,
            DataSetFieldId=uuid.uuid4(),
            FieldFlags=DataSetFieldFlags(0),
            BuiltInType=built_in,
            DataType=datatype_nid,
            ValueRank=Int32(1),
        )
        return cls(meta)

    def set_promoted(self, promoted: bool) -> None:
        self._meta.FieldFlags = DataSetFieldFlags.PromotedField if promoted else DataSetFieldFlags(0)

    def get_promoted(self) -> bool:
        return True if DataSetFieldFlags.PromotedField in self._meta.FieldFlags else False

    def get_dataset_field_id(self) -> Guid:
        return self._meta.DataSetFieldId

    @property
    def Description(self) -> LocalizedText:
        return self._meta.Description

    @property
    def DataSetFieldId(self) -> Guid:
        return self._meta.DataSetFieldId

    @property
    def Name(self) -> String:
        return self._meta.Name

    @property
    def ArrayDimensions(self) -> list[UInt32]:
        return self._meta.ArrayDimensions

    @property
    def MaxStringLength(self) -> UInt32:
        return self._meta.MaxStringLength

    @property
    def ValueRank(self) -> Int32:
        return self._meta.ValueRank

    @property
    def DataType(self) -> NodeId:
        return self._meta.DataType

    @property
    def BuiltInType(self) -> Byte:
        return self._meta.BuiltInType

    def get_config(self) -> FieldMetaData:
        return self._meta

    def get_datatype_name(self) -> str:
        """
        returns the name of DataType
        """
        if self._meta.BuiltInType != 0:
            return VariantType(self._meta.BuiltInType).name
        return extension_objects_by_datatype[self._meta.DataType].__name__


class DataSetMeta:
    """
    Describes a the meta data of a dataset
    """

    def __init__(
        self,
        meta: DataSetMetaDataType,
        dataset_fields: list[DataSetField] | None = None,
    ) -> None:
        self._meta = meta
        if dataset_fields is not None:
            self._fields = dataset_fields
            self._meta.Fields = [ds.get_config() for ds in dataset_fields]
        else:
            self._fields = [DataSetField(cfg) for cfg in self._meta.Fields]

    @classmethod
    def Create(
        cls,
        name: String,
        description: LocalizedText | None = None,
        dataset_fields: list[DataSetField] | None = None,
    ):
        """creates a datasetmeta"""
        meta = DataSetMetaDataType()
        if description is not None:
            meta.Description = description
        if name is not None:
            meta.Name = name
        meta.ConfigurationVersion.MajorVersion = version_time_now()
        meta.ConfigurationVersion.MinorVersion = version_time_now()
        return cls(meta, dataset_fields)

    @property
    def Name(self) -> String:
        return self._meta.Name

    @property
    def Description(self) -> LocalizedText:
        return self._meta.Description

    def add_field(self, ds_field: DataSetField | FieldMetaData) -> None:
        if isinstance(ds_field, FieldMetaData):
            ds_field = DataSetField(ds_field)
        self._fields.append(ds_field)
        self._meta.Fields.append(ds_field._meta)

    def add_scalar(self, name: String, datatype: NodeId | VariantType):
        self.add_field(DataSetField.CreateScalar(name, datatype))

    def add_array(self, name: String, datatype: NodeId | VariantType):
        self.add_field(DataSetField.CreateScalar(name, datatype))

    def get_field(self, name) -> DataSetField | None:
        return next((f for f in self._fields if f.Name == name), None)

    def remove_field(self, field_name: str) -> None:
        f = next((f for f in self._fields if f.Name == field_name), None)
        if f is not None:
            del f
            f = next((f for f in self._meta.Fields if f.Name == field_name), None)
            if f is not None:
                del f

    def get_config(self) -> DataSetMetaDataType:
        return self._meta


class PubSubDataSource:
    """
    Baseclass for all DataSources
    """

    async def get_variant(self) -> tuple[list[Variant | None], StatusCode, DateTime]:
        """
        return all variants for a dataset as Variant
        """
        dt = DateTime.now(timezone.utc)
        vars = await self.on_get_value()
        ret = [v.Value for v in vars]
        st = StatusCode(UInt32(StatusCodes.Good))
        for v in vars:
            if v.StatusCode is not None and not v.StatusCode.is_good():
                st = v.StatusCode
        return (ret, st, dt)

    async def get_value(self, status: bool, server_timestamp: bool, source_timestamp: bool) -> list[DataValue]:
        """
        returns all values for a dataset as DataValues
        """
        vars = await self.on_get_value()
        for v in vars:
            if not status:
                v.StatusCode = None
            if not server_timestamp:
                v.ServerTimestamp = None
            if not source_timestamp:
                v.SourceTimestamp = None
        return vars

    async def get_raw(self) -> tuple[list[bytes], StatusCode, DateTime]:
        """
        returns all values for a dataset as rawbytes
        """
        dt = DateTime.now(timezone.utc)
        vars = await self.on_get_value()
        ret = [pack_uatype(v.Value.VariantType, v.Value.Value) for v in vars if v.Value is not None]

        st = StatusCode(UInt32(StatusCodes.Good))
        for v in vars:
            if v.StatusCode is not None and not v.StatusCode.is_good():
                st = v.StatusCode
        return ret, st, dt

    async def on_get_value(self) -> list[DataValue]:
        """
        Return all values of the dataset
        """
        raise UaStatusCodeError(StatusCodes.BadNotImplemented)


class PubSubDataSourceDict(PubSubDataSource):
    """
    Implements getting the values to publishing.
    """

    datasources: dict[String, dict[String, DataValue]]

    def __init__(self, ds: DataSetMeta) -> None:
        super().__init__()
        self.datasources = {}
        self.ds = ds

    async def on_get_value(self) -> list[DataValue]:
        """
        returns all values for a dataset
        """
        fields = self.datasources.get(self.ds._meta.Name, {})
        ret = []
        for fld in self.ds._meta.Fields:
            ret.append(
                fields.get(
                    fld.Name,
                    DataValue(StatusCode=StatusCode(UInt32(StatusCodes.BadNoDataAvailable))),
                )
            )
        return ret


class PubSubDataSourceServer(PubSubDataSource):
    """
    Implements getting the values to publishing.
    """

    def __init__(self, server: Server, ds: DataSetMeta, data_items: PublishedDataItemsDataType) -> None:
        super().__init__()
        self.ds = ds
        self.data_items = data_items
        self._server = server

    async def on_get_value(self) -> list[DataValue]:
        """
        returns all values for a dataset
        """
        ret = []
        for pd in self.data_items.PublishedData:
            dv = self._server.read_attribute_value(pd.PublishedVariable, attr=pd.AttributeId)
            if (
                dv.StatusCode is not None
                and not dv.StatusCode.is_good()
                and pd.SubstituteValue.VariantType != VariantType.Null
            ):
                dv = DataValue(
                    pd.SubstituteValue,
                    SourceTimestamp=DateTime.now(timezone.utc),
                    ServerTimestamp=DateTime.now(timezone.utc),
                    StatusCode=StatusCode(UInt32(StatusCodes.UncertainSubstituteValue)),
                )
            ret.append(dv)
        return ret

    async def add_variable(self, published_variable: PublishedVariableDataType):
        self.data_items.PublishedData.append(published_variable)


class PublishedDataSet(PubSubInformationModel):
    """
    Defines a PublishedDataSet for use with a custom datasource (Name => Value via dict)
    """

    def __init__(
        self,
        cfg: PublishedDataSetDataType,
        source: PubSubDataSource | None = None,
        dataset: DataSetMeta | None = None,
    ) -> None:
        super().__init__(False)
        self._data = cfg
        if dataset is not None:
            self.dataset = dataset
            self._data.DataSetMetaData = dataset.get_config()
        else:
            self.dataset = DataSetMeta(self._data.DataSetMetaData)
        if source is not None:
            self._source = source
        else:
            self._source = PubSubDataSourceDict(self.dataset)

    async def _init_information_model(self, parent: Node, server: Server) -> None:
        pds_type = server.get_node(NodeId(Int32(ObjectIds.PublishedDataItemsType)))
        instance = await instantiate_util.instantiate(
            parent,
            pds_type,
            idx=1,
            bname=self._data.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._data.Name, ""),
        )
        pds_obj = instance[0]
        await self._init_node(pds_obj, server)
        await self.set_node_value("0:DataSetMetaData", self.dataset)
        if self._node is not None:
            await self._node.add_variable(
                NodeId(NamespaceIndex=Int16(1)),
                "0:DataSetClassId",
                self.dataset._meta.DataSetClassId,
            )
        else:
            raise RuntimeError("self._node is not initialized")
        await self._node.add_variable(
            NodeId(NamespaceIndex=Int16(1)),
            "0:DataSetClassId",
            self.dataset._meta.DataSetClassId,
        )
        # @TODO ExtensionFields
        # @TODO fill method
        # await self.set_node_value("0:PublishedData", self._pubdata)
        # add = await self._node.get_child("0:AddVariables")
        # rem = await self._node.get_child("0:RemoveVariables")

    @classmethod
    def Create(
        cls,
        name: String,
        dataset: DataSetMeta,
        source: PubSubDataSource | None = None,
    ):
        """Allows to construct a PublishDataSet without using the ua structures."""
        s = cls(PublishedDataSetDataType(Name=name), source, dataset)
        return s

    def set_source_custom(self, source: PubSubDataSource):
        """Set the source as custom user defined one"""
        self._source = source

    def get_source(self) -> PubSubDataSource:
        return self._source

    def get_name(self) -> String:
        # @TODO return node value
        return self._data.Name

    def get_config(self) -> PublishedDataSetDataType:
        return self._data

    async def get_meta(self) -> DataSetMeta:
        # @TODO return node value
        return self.dataset


@dataclass
class TargetVariable:
    """
    :ivar Name: Name of the variable in the dataset has to unique in the dataset
    :vartype Name: String
    :ivar SourceNode: NodeId of the variable
    :vartype SourceNode: NodeId
    :ivar ValueRank_: ValueRank of the Variable default Scalar
    :vartype ValueRank_: ValueRank
    :ivar DataType: The datatype, if not provided it extracted by the target node
    :vartype DataType: Optional[NodeId]
    :ivar SubstituteValue: Value to substitute if variable can't be read
    :vartype SubstituteValue: Variant
    :ivar Promoted: Value should be prompoted
    :vartype Promoted: Bool
    """

    Name: String = None
    SourceNode: NodeId = None
    ValueRank: ValueRank = ValueRank.Scalar
    DataType: NodeId | None = None
    SubstituteValue: Variant = field(default_factory=Variant)
    Promoted: Boolean = False


class PublishedDataItems(PubSubInformationModel):
    """
    Defines a PublishedDataItems which links variables in the server AddressSpace
    """

    def __init__(
        self,
        cfg: PublishedDataSetDataType,
        server: Server,
        dataset: DataSetMeta | None = None,
    ) -> None:
        super().__init__(False)
        self._data = cfg
        if dataset is not None:
            self.dataset = dataset
            self._data.DataSetMetaData = dataset.get_config()
        else:
            self.dataset = DataSetMeta(self._data.DataSetMetaData)
        self._published_data: PublishedDataItemsDataType = self._data.DataSetSource
        self._source = PubSubDataSourceServer(server, self.dataset, self._published_data)
        self._server = server

    async def _init_information_model(self, parent: Node, server: Server) -> None:
        pds_type = server.get_node(NodeId(Int32(ObjectIds.PublishedDataItemsType)))
        instance = await instantiate_util.instantiate(
            parent,
            pds_type,
            idx=1,
            bname=self._data.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._data.Name, ""),
        )
        pds_obj = instance[0]
        await self._init_node(pds_obj, server)
        await self.set_node_value("0:DataSetMetaData", self.dataset)
        await self.set_node_value("0:ConfigurationVersion", self.dataset._meta.ConfigurationVersion)
        if self._node is not None:
            await self._node.add_variable(
                NodeId(NamespaceIndex=Int16(1)),
                "0:DataSetClassId",
                self.dataset._meta.DataSetClassId,
            )
        else:
            raise RuntimeError("self._node is not initialized")
        # @TODO ExtensionFields
        # @TODO fill method
        await self.set_node_value(
            ["0:PublishedData"],
            Variant(
                self._published_data.PublishedData,
                VariantType=VariantType.ExtensionObject,
            ),
        )
        meth = await instantiate_util.instantiate(
            pds_obj,
            server.get_node(NodeId(Int32(ObjectIds.PublishedDataItemsType_AddVariables))),
            idx=1,
            bname="0:AddVariables",
            dname=LocalizedText("AddVariables"),
        )
        server.link_method(meth[0], self._add_variables)
        meth = await instantiate_util.instantiate(
            pds_obj,
            server.get_node(NodeId(Int32(ObjectIds.PublishedDataItemsType_RemoveVariables))),
            idx=1,
            bname="0:RemoveVariables",
            dname=LocalizedText("RemoveVariables"),
        )
        server.link_method(meth[0], self._remove_variables)

    @uamethod
    async def _add_variables(
        self,
        config_version: ConfigurationVersionDataType,
        field_name_aliases: list[String],
        promoted_fields: list[Boolean],
        published_variable_data_type: list[PublishedVariableDataType],
    ) -> tuple[ConfigurationVersionDataType, list[StatusCodes]]:
        if self._data.DataSetMetaData.ConfigurationVersion != config_version:
            raise UaStatusCodeError(StatusCodes.BadInvalidState)
        if not field_name_aliases:
            # When empty arguments
            raise UaStatusCodeError(StatusCodes.BadNothingToDo)
        if self._source is None:
            # If no source then no variables can be added
            raise UaStatusCodeError(StatusCodes.BadNotWritable)
        self._source
        self._results = []
        if len(field_name_aliases) != len(promoted_fields) or len(promoted_fields) != len(published_variable_data_type):
            raise UaStatusCodeError(StatusCodes.BadInvalidArgument)
        raise UaStatusCodeError(StatusCodes.BadNotImplemented)

    @uamethod
    async def _remove_variables(
        self,
        config_version: ConfigurationVersionDataType,
        variables_to_remove: list[UInt32],
    ) -> tuple[ConfigurationVersionDataType, list[StatusCodes]]:
        if self._data.DataSetMetaData.ConfigurationVersion != config_version:
            raise UaStatusCodeError(StatusCodes.BadInvalidState)
        if not variables_to_remove:
            # When empty arguments
            raise UaStatusCodeError(StatusCodes.BadNothingToDo)
        if self._source is None:
            # If no source then no variables can be added
            raise UaStatusCodeError(StatusCodes.BadNotWritable)
        raise UaStatusCodeError(StatusCodes.BadNotImplemented)

    @classmethod
    async def Create(cls, name: String, server: Server, variables: list[TargetVariable]):
        """Allows to construct a PublishedDataItems without using the ua structures."""
        items = PublishedDataItemsDataType()
        fields = []
        for v in variables:
            items.PublishedData.append(
                PublishedVariableDataType(v.SourceNode, AttributeIds.Value, SubstituteValue=v.SubstituteValue)
            )
            flags = DataSetFieldFlags(0) if v.Promoted else DataSetFieldFlags.PromotedField
            meta = FieldMetaData(
                Name=v.Name,
                DataSetFieldId=uuid.uuid4(),
                FieldFlags=flags,
                ValueRank=v.ValueRank,
            )
            if v.DataType is not None:
                datatype = v.DataType
            else:
                datatype = await server.get_node(v.SourceNode).read_data_type()
            meta.DataType, meta.BuiltInType = _get_datatype_or_built_in(datatype)
            fields.append(DataSetField(meta))
        meta = DataSetMetaDataType(Name=name, Fields=fields, DataSetClassId=uuid.uuid4())
        s = cls(
            PublishedDataSetDataType(Name=name, DataSetSource=items, DataSetMetaData=meta),
            server,
        )
        return s

    def get_source(self) -> PubSubDataSource:
        return self._source

    def get_name(self) -> String:
        # @TODO return node value
        return self._data.Name

    async def get_meta(self) -> DataSetMeta:
        # @TODO return node value
        return self.dataset


@dataclass
class DataSetValue:
    """Value of a subscribed value, with all infos need to process it"""

    Name: String
    Value: DataValue
    Meta: DataSetField
