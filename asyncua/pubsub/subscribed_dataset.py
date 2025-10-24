"""
Links PubSub received DataSets to the AddressSpace
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from ..common.node import Node
from ..ua import TargetVariablesDataType, SubscribedDataSetMirrorDataType
from ..ua.attribute_ids import AttributeIds
from ..ua.uaprotocol_auto import (
    FieldMetaData,
    FieldTargetDataType,
    OverrideValueHandling,
    PubSubState,
)
from ..ua.uatypes import (
    Int16,
    NodeId,
    Variant,
)
from .dataset import DataSetField, DataSetMeta, DataSetValue

if TYPE_CHECKING:
    from .. import Server

logger = logging.getLogger(__name__)


class SubscribedDataSetMirror:
    """Mirrors DataSet Variables in the AddressSpace, needs a parent node where the variables are inserts"""

    def __init__(self, cfg: SubscribedDataSetMirrorDataType, node: Node):
        self._cfg = cfg
        self._parent = node
        self._node = None
        self._nodes = {}

    async def _create_and_set_node(self, f: FieldMetaData):
        if self._node is None:
            raise RuntimeError(
                "SubscribedDataSetMirror._node is not initialized. Did you forget to call on_state_change?"
            )
        n = await self._node.add_variable(
            NodeId(NamespaceIndex=Int16(1)), "1:" + str(f.Name), Variant(), datatype=f.DataType
        )
        await n.write_attribute(AttributeIds.Description, f.Description)
        await n.write_attribute(AttributeIds.ValueRank, f.ValueRank)
        await n.write_attribute(AttributeIds.ArrayDimensions, f.ArrayDimensions)
        return n

    async def on_state_change(self, meta: DataSetMeta, state: PubSubState) -> None:
        """Called when a DataSet state changes"""
        if state == PubSubState.Operational:
            if self._node is None:
                self._node = await self._parent.add_object(
                    NodeId(NamespaceIndex=Int16(1)),  # FIXME this NamespaceIndex looks wrong
                    bname="1:" + str(self._cfg.ParentNodeName),
                )
            self.nodes = {f.DataSetFieldId: await self._create_and_set_node(f) for f in meta.get_config().Fields}

    def get_subscribed_dataset(self) -> SubscribedDataSetMirrorDataType:
        return self._cfg


class FieldTargets:
    def __init__(self, cfg: FieldTargetDataType):
        self._cfg = cfg

    @classmethod
    def createTarget(cls, field: DataSetField, nodeid: NodeId):
        """
        Helper to create a target from a DataSetField and an NodeId
        """
        cfg = FieldTargetDataType(
            DataSetFieldId=field.DataSetFieldId,
            TargetNodeId=nodeid,
            AttributeId=AttributeIds.Value,
        )
        return cls(cfg)


class SubScribedTargetVariables:
    """Maps the values to targeted variables in the AddressSpace"""

    def __init__(self, server: Server, cfg: TargetVariablesDataType | list[FieldTargets]):
        if isinstance(cfg, TargetVariablesDataType):
            self._cfg = cfg
            self._fields = [FieldTargets(f) for f in cfg.TargetVariables]
        else:
            self._cfg = TargetVariablesDataType([f._cfg for f in cfg])
            self._fields = cfg
        self.server = server
        self.nodes = {}

    async def on_dataset_received(self, meta: DataSetMeta, fields: list[DataSetValue]) -> None:
        """Called when a published dataset received an update"""
        for field in fields:
            try:
                node, cfg = self.nodes[field.Meta.DataSetFieldId]
                if field.Value.StatusCode is not None and not field.Value.StatusCode.is_good():
                    logger.info("Error field %s value with %s", field.Name, field.Value)
                    # if status code is bad, check overridevalue handling to handle the cases
                    if cfg._cfg.OverrideValueHandling == OverrideValueHandling.OverrideValue:
                        await node.set_value(cfg.OverrideValue)
                    elif cfg._cfg.OverrideValueHandling == OverrideValueHandling.Disabled:
                        # Set errorcode
                        await node.write_attribute(AttributeIds.Value, field.Value)
                else:
                    await node.write_value(field.Value)
            except KeyError:
                pass

    async def on_state_change(self, meta: DataSetMeta, state: PubSubState) -> None:
        """Called when a DataSet state changes"""
        if state == PubSubState.Operational:
            self.nodes = {f._cfg.DataSetFieldId: (self.server.get_node(f._cfg.TargetNodeId), f) for f in self._fields}

    def get_subscribed_dataset(self) -> TargetVariablesDataType:
        return self._cfg
