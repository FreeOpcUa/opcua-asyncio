"""
    A DataSet (ds) descripes the data of pubsub
"""
from __future__ import annotations
from asyncua.common.methods import uamethod
from asyncua.ua import uaerrors
from ..common import instantiate_util
from ..common.node import Node
from ..pubsub.information_model import PubSubInformationModel
from ..ua.attribute_ids import AttributeIds
from ..ua.ua_binary import pack_uatype
from ..ua import DataSetMetaDataType, String, LocalizedText, FieldMetaData, ObjectIds
from ..ua.status_codes import StatusCodes
from .untils import version_time_now
from ..ua.uatypes import (
    Boolean,
    DataValue,
    DateTime,
    Guid,
    Int32,
    NodeId,
    StatusCode,
    UInt32,
    Byte,
    Variant,
    VariantType,
)
from ..ua.uaprotocol_auto import (
    ConfigurationVersionDataType,
    DataSetFieldFlags,
    PublishedDataItemsDataType,
    PublishedDataSetDataType,
    PublishedVariableDataType,
)
from asyncua import ua

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..server.server import Server


def _get_datatype_or_build_in(
    datatype: Union[NodeId, ObjectIds, VariantType, int]
) -> Tuple[NodeId, int]:
    """
    Returns the DataType NodeId and the corresponding BuildIn number if
    possible to determine.
    """
    if isinstance(datatype, ObjectIds):
        datatype = NodeId(datatype)
    elif isinstance(datatype, int):
        datatype = NodeId(datatype)
    if isinstance(datatype, NodeId):
        if (
            datatype.NamespaceIndex == 0
            and isinstance(datatype.Identifier, int)
            and datatype.Identifier < 24
        ):
            dt = NodeId()
            build_in = datatype.Identifier
        else:
            dt = datatype
            build_in = 0
    else:
        id = int(datatype.value)
        dt = NodeId(id)
        build_in = id
    return (dt, build_in)


class DataSetField:
    """
    DataSetField class descripes the content of a field
    """

    def __init__(self, meta: Optional[FieldMetaData] = None) -> None:
        if meta is None:
            self._meta = FieldMetaData(
                DataSetFieldId=uuid.uuid4(), FieldFlags=DataSetFieldFlags(0)
            )
        else:
            self._meta = meta

    @classmethod
    def CreateScalar(
        cls, name: String, datatype: Union[NodeId, ObjectIds, VariantType]
    ):
        """
        Creates a scalar Field with datatype and name
        """
        meta = FieldMetaData(
            Name=name,
            DataSetFieldId=uuid.uuid4(),
            FieldFlags=DataSetFieldFlags(0),
            ValueRank=-1,
        )
        meta.DataType, meta.BuiltInType = _get_datatype_or_build_in(datatype)
        return cls(meta)

    @classmethod
    def CreateArray(cls, name: String, datatype: Union[NodeId, ObjectIds, VariantType]):
        """
        Creates a scalar Field with datatype and name
        """
        meta = FieldMetaData(
            Name=name,
            DataSetFieldId=uuid.uuid4(),
            FieldFlags=DataSetFieldFlags(0),
            ValueRank=1,
        )
        meta.DataType, meta.BuiltInType = _get_datatype_or_build_in(datatype)
        return cls(meta)

    def set_promoted(self, promoted: bool) -> None:
        self._meta.FieldFlags = (
            DataSetFieldFlags.PromotedField if promoted else DataSetFieldFlags(0)
        )

    def get_promoted(self) -> bool:
        return (
            True if DataSetFieldFlags.PromotedField in self._meta.FieldFlags else False
        )

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
    def ArrayDimensions(self) -> List[UInt32]:
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
    def BuildInType(self) -> Byte:
        return self._meta.BuiltInType

    def get_config(self) -> FieldMetaData:
        return self._meta

    def get_datatype_name(self) -> str:
        """
        returns the name of DataType
        """
        if self._meta.DataType.is_null():
            if self._meta.BuiltInType != 0:
                return VariantType(self._meta.BuiltInType).name
        return ua.extension_objects_by_datatype[self._meta.DataType].__name__


class DataSetMeta:
    """
    Descripes a the meta data of a dataset
    """

    def __init__(
        self,
        meta: DataSetMetaDataType,
        dataset_fields: Optional[List[DataSetField]] = None,
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
        description: Optional[LocalizedText] = None,
        dataset_fields: Optional[List[DataSetField]] = None,
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

    def add_field(self, ds_field: Union[DataSetField, FieldMetaData]) -> None:
        if isinstance(ds_field, FieldMetaData):
            ds_field = DataSetField(ds_field)
        self._fields.append(ds_field)
        self._meta.Fields.append(ds_field._meta)

    def add_scalar(self, name: String, datatype: Union[NodeId, ObjectIds, VariantType]):
        self.add_field(DataSetField.CreateScalar(name, datatype))

    def add_array(self, name: String, datatype: Union[NodeId, ObjectIds, VariantType]):
        self.add_field(DataSetField.CreateScalar(name, datatype))

    def get_field(self, name) -> Optional[DataSetField]:
        return next((f for f in self._fields if f.Name == name), None)

    def remove_field(self, field_name: str) -> None:
        f = next((f for f in self._fields if f.name == field_name), None)
        if f is not None:
            del f
            f = next((f for f in self._meta if f.Name == field_name), None)
            if f is not None:
                del f

    def get_config(self) -> DataSetMetaDataType:
        return self._meta


class PubSubDataSource:
    """
    Baseclass for all DataSources
    """

    async def get_variant(self) -> Tuple[List[Optional[Variant]], StatusCode, DateTime]:
        """
        return all variants for a dataset as Variant
        """
        dt = DateTime.utcnow()
        vars = await self.on_get_value()
        ret = [v.Value for v in vars]
        st = StatusCode(StatusCodes.Good)
        for v in vars:
            if v.StatusCode is not None and not v.StatusCode.is_good():
                st = v.StatusCode
        return (ret, st, dt)

    async def get_value(
        self, status: bool, server_timestamp: bool, source_timestamp: bool
    ) -> List[DataValue]:
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

    async def get_raw(self) -> Tuple[List[bytes], StatusCode, DateTime]:
        """
        returns all values for a dataset as rawbytes
        """
        dt = DateTime.utcnow()
        vars = await self.on_get_value()
        ret = [ pack_uatype(v.VariantType, v.Value) for v in vars]
        st = StatusCode(StatusCodes.Good)
        for v in vars:
            if v.StatusCode is not None and not v.StatusCode.is_good():
                st = v.StatusCode
        return ret, st, dt

    async def on_get_value(self) -> List[DataValue]:
        """
        Return all values of the dataset
        """
        raise ua.UaStatusCodeError(StatusCodes.BadNotImplemented)


class PubSubDataSourceDict(PubSubDataSource):
    """
    Implements getting the values to publishing.
    """

    datasources: Dict[String, Dict[String, DataValue]]

    def __init__(self, ds: DataSetMeta) -> None:
        super().__init__()
        self.datasources = {}
        self.ds = ds

    async def on_get_value(self) -> List[DataValue]:
        """
        returns all values for a datatset
        """
        fields = self.datasources.get(self.ds._meta.Name, {})
        ret = []
        for fld in self.ds._meta.Fields:
            ret.append(
                fields.get(
                    fld.Name,
                    DataValue(StatusCode_=StatusCode(StatusCodes.BadNoDataAvailable)),
                )
            )
        return ret


class PubSubDataSourceServer(PubSubDataSource):
    """
    Implements getting the values to publishing.
    """

    def __init__(
        self, server: Server, ds: DataSetMeta, data_items: PublishedDataItemsDataType
    ) -> None:
        super().__init__()
        self.ds = ds
        self.data_items = data_items
        self._server = server

    async def on_get_value(self) -> List[DataValue]:
        """
        returns all values for a datatset
        """
        ret = []
        for pd in self.data_items.PublishedData:
            dv = self._server.read_attribute_value(
                pd.PublishedVariable, attr=pd.AttributeId
            )
            if (
                not dv.StatusCode_.is_good()
                and pd.SubstituteValue.VariantType != VariantType.Null
            ):
                dv = DataValue(
                    pd.SubstituteValue,
                    SourceTimestamp=DateTime.utcnow(),
                    ServerTimestamp=DateTime.utcnow(),
                    StatusCode_=StatusCodes.UncertainSubstituteValue,
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
        source: Optional[PubSubDataSource] = None,
        dataset: Optional[DataSetMeta] = None,
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
        pds_type = server.get_node(NodeId(ObjectIds.PublishedDataItemsType, 0))
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
        await self.set_node_value(
            "0:ConfigurationVersion", self.dataset._meta.ConfigurationVersion
        )
        await self._node.add_variable(
            ua.NodeId(NamespaceIndex=1),
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
        source: Optional[PubSubDataSource] = None,
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
    ValueRank: ua.ValueRank = ua.ValueRank.Scalar
    DataType: Optional[NodeId] = None
    SubstituteValue: Variant = field(default_factory=Variant)
    Promoted: Boolean = False


class PublishedDataItems(PubSubInformationModel):
    """
    Defines a PublishedDataItems which links variables in the server Addresspace
    """

    def __init__(
        self,
        cfg: PublishedDataSetDataType,
        server: Server,
        dataset: Optional[DataSetMeta] = None,
    ) -> None:
        super().__init__(False)
        self._data = cfg
        if dataset is not None:
            self.dataset = dataset
            self._data.DataSetMetaData = dataset.get_config()
        else:
            self.dataset = DataSetMeta(self._data.DataSetMetaData)
        self._published_data: PublishedDataItemsDataType = self._data.DataSetSource
        self._source = PubSubDataSourceServer(
            server, self.dataset, self._published_data
        )
        self._server = server

    async def _init_information_model(self, parent: Node, server: Server) -> None:
        pds_type = server.get_node(NodeId(ObjectIds.PublishedDataItemsType, 0))
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
        await self.set_node_value(
            "0:ConfigurationVersion", self.dataset._meta.ConfigurationVersion
        )
        await self._node.add_variable(
            ua.NodeId(NamespaceIndex=1),
            "0:DataSetClassId",
            self.dataset._meta.DataSetClassId,
        )
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
            server.get_node(NodeId(ObjectIds.PublishedDataItemsType_AddVariables)),
            idx=1,
            bname="0:AddVariables",
            dname=LocalizedText("AddVariables"),
        )
        server.link_method(meth[0], self._add_variables)
        meth = await instantiate_util.instantiate(
            pds_obj,
            server.get_node(NodeId(ObjectIds.PublishedDataItemsType_RemoveVariables)),
            idx=1,
            bname="0:RemoveVariables",
            dname=LocalizedText("RemoveVariables"),
        )
        server.link_method(meth[0], self._remove_variables)

    @uamethod
    async def _add_variables(
        self,
        config_version: ConfigurationVersionDataType,
        field_name_aliases: List[String],
        promoted_fields: List[Boolean],
        published_variable_data_type: List[PublishedVariableDataType],
    ) -> Tuple[ConfigurationVersionDataType, List[StatusCodes]]:
        if self._data.DataSetMetaData.ConfigurationVersion != config_version:
            raise uaerrors.UaStatusCodeError(StatusCodes.BadInvalidState)
        if not field_name_aliases:
            # When emtpy arguments
            raise uaerrors.UaStatusCodeError(StatusCodes.BadNothingToDo)
        if self._source is None:
            # If no source then no variables can be added
            raise uaerrors.UaStatusCodeError(StatusCodes.Bad_NotWritable)
        self._source
        self._results = []
        if len(field_name_aliases) != len(promoted_fields) or len(
            promoted_fields
        ) != len(published_variable_data_type):
            raise uaerrors.UaStatusCodeError(StatusCodes.BadInvalidArgument)
        raise uaerrors.UaStatusCodeError(StatusCodes.BadNotImplemented)

    @uamethod
    async def _remove_variables(
        self,
        config_version: ConfigurationVersionDataType,
        variables_to_remove: List[UInt32],
    ) -> Tuple[ConfigurationVersionDataType, List[StatusCodes]]:
        if self._data.DataSetMetaData.ConfigurationVersion != config_version:
            raise uaerrors.UaStatusCodeError(StatusCodes.BadInvalidState)
        if not variables_to_remove:
            # When emtpy arguments
            raise uaerrors.UaStatusCodeError(StatusCodes.BadNothingToDo)
        if self._source is None:
            # If no source then no variables can be added
            raise uaerrors.UaStatusCodeError(StatusCodes.BadNotWritable)
        raise uaerrors.UaStatusCodeError(StatusCodes.BadNotImplemented)

    @classmethod
    async def Create(cls, name: String, server: Server, variables: TargetVariable):
        """Allows to construct a PublishedDataItems without using the ua structures."""
        items = PublishedDataItemsDataType()
        fields = []
        for v in variables:
            items.PublishedData.append(
                PublishedVariableDataType(
                    v.SourceNode, AttributeIds.Value, SubstituteValue=v.SubstituteValue
                )
            )
            flags = (
                DataSetFieldFlags(0) if v.Promoted else DataSetFieldFlags.PromotedField
            )
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
            meta.DataType, meta.BuiltInType = _get_datatype_or_build_in(datatype)
            fields.append(DataSetField(meta))
        meta = DataSetMetaDataType(
            Name=name, Fields=fields, DataSetClassId=uuid.uuid4()
        )
        s = cls(
            PublishedDataSetDataType(
                Name=name, DataSetSource=items, DataSetMetaData=meta
            ),
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
    """Value of a subscriped value, with all infos need to proccess it"""

    Name: String
    Value: DataValue
    Meta: DataSetField
