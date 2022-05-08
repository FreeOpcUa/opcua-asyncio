from asyncio import transports
from os import remove
from typing import List, Optional, Tuple, Union
from asyncua.common.methods import uamethod
from asyncua.common.node import Node
from asyncua.pubsub.connection import PubSubConnection
from asyncua.pubsub.reader import ReaderGroup
from asyncua.pubsub.udp import UdpSettings
from asyncua.pubsub.writer import WriterGroup
from asyncua.ua import uaerrors

from asyncua.ua.status_codes import StatusCodes
from asyncua.ua.uaprotocol_auto import ObjectAttributes, PubSubState
from asyncua.ua.uatypes import NodeId, QualifiedName, Variant
from ..common.instantiate_util import instantiate
from ..ua.object_ids import ObjectIds
from ..server import Server
from .. import ua
from pubsub import PubSubApplication


class PubSubInformationModel:
    '''
        Wraps some helper for PubSubObjects in the Addressspace.
        If used without node it provids fallbacks.
        Also the class handles the state of the  pubsub component (PubSubState)
    '''
    def __init__(self) -> None:
        self._node = None
        self._state_node = None
        self.__state_fallback = PubSubState.Disabled

    def model_is_init(self) -> bool:
        return self._node is not None

    @uamethod
    async def enable(self) -> StatusCodes:
        raise uaerrors.UaStatusCodeError(StatusCodes.BadNotImplemented)

    @uamethod
    async def disable(self) -> StatusCodes:
        raise uaerrors.UaStatusCodeError(StatusCodes.BadNotImplemented)

    async def _init_node(self, node: Node, server: Optional[Server]) -> None:
        '''
            links a node to the pubsub internals
            and prepares common nodes
        '''
        self._node = node
        self._state_node = await node.get_child(["0:Status", "0:State"])
        self._server = server
        if self._has_state:
            try:
                self._state_node = await node.get_child(["0:Status", "0:State"])
            except uaerrors.UaStatusCodeError:
                pass
            # @TODO fill methods
            # en = await self._node.get_child(["0:Status", "0:Enable"])
            # den = await self._node.get_child(["0:Status", "0:Disable"])

    async def set_node_value(self, path: Union[str, QualifiedName, List[str], List[QualifiedName]], value: Variant) -> None:
        '''
            Sets the value of the child node
        '''
        if self._node is None:
            n = await self._node.get_child(path)
            await n.write_value(ua.DataValue(value))

    async def get_node_value(self, path: Union[str, QualifiedName, List[str], List[QualifiedName]]) -> Optional[Variant]:
        '''
            Get value of child node value returns `None` if no information model is used
        '''
        if self._node is None:
            n = await self._node.get_child(path)
            return n.read_value()
        else:
            return None

    async def _set_state(self, state: PubSubState) -> None:
        '''
            Internal sets the state of the information model
        '''
        if self._state_node:
            await self._state_node.write_value(ua.DataValue(state))
        else:
            self.__state_fallback = state

    async def get_state(self) -> PubSubState:
        '''
            Internal gets the state of the information model
        '''
        if self._state_node:
            return await self._state_node.read_value()
        else:
            return self.__state_fallback








async def fill_writer_grp(wgrp: Node, wg: WriterGroup) -> None:
    security_mode = await wgrp.get_child("0:SecurityMode")
    await security_mode.set_data_value(ua.DataValue(wg._cfg.SecurityMode))
    max_network_message_size = await wgrp.get_child("0:MaxNetworkMessageSize")
    await max_network_message_size.write_value(ua.DataValue(wg._cfg.MaxNetworkMessageSize))
    security_groupid = await wgrp.get_child("0:SecurityGroupId")
    await security_groupid.set_data_value(ua.DataValue(wg._cfg.SecurityGroupId))
    security_key_services = await wgrp.get_child("0:SecurityKeyServices")
    await security_key_services.write_value(ua.DataValue(wg._cfg.SecurityKeyServices))
    group_properties = await wgrp.get_child("0:GroupProperties")
    await group_properties.write_value(ua.DataValue(wg._cfg.GroupProperties))
    fill_status(await wgrp.get_child("0:Status"), wg.get_state())

    writer_group_id = await wgrp.get_child("0:WriterGroupId")
    await writer_group_id.write_value(ua.DataValue(wg._cfg.WriterGroupId))
    publishing_interval = await wgrp.get_child("0:PublishingInterval")
    await publishing_interval.write_value(ua.DataValue(wg._cfg.PublishingInterval))
    keep_alive_time = await wgrp.get_child("0:KeepAliveTime")
    await keep_alive_time.write_value(ua.DataValue(wg._cfg.KeepAliveTime))
    priority = await wgrp.get_child("0:Priority")
    await priority.write_value(ua.DataValue(wg._cfg.Priority))
    locale_ids = await wgrp.get_child("0:LocaleIds")
    await locale_ids.write_value(ua.DataValue(wg._cfg.LocaleIds))
    header_layout_uri = await wgrp.get_child("0:HeaderLayoutUri")
    await header_layout_uri.write_value(ua.DataValue(wg._cfg.HeaderLayoutUri))

    # UadpWriterGroupMessageType

    msg_settings = await wgrp.get_child("0:MessageSettings")
    msg_cfg = wg.get_msg_cfg()
    group_version = await msg_settings.get_child("0:GroupVersion")
    group_version.set_data_value(ua.DataValue(msg_cfg.GroupVersion))
    ordering = await msg_settings.get_child("0:DataSetOrdering")
    ordering.set_data_value(ua.DataValue(msg_cfg.DataSetOrdering))
    mask = await msg_settings.get_child("0:NetworkMessageContentMask")
    mask.set_data_value(ua.DataValue(msg_cfg.NetworkMessageContentMask))
    sampling_offset = await msg_settings.get_child("0:SamplingOffset")
    sampling_offset.set_data_value(ua.DataValue(msg_cfg.SamplingOffset))
    publishing_offset = await msg_settings.get_child("0:PublishingOffset")
    publishing_offset.set_data_value(ua.DataValue(msg_cfg.PublishingOffset))

    # @TODO add transport settings  DatagramWriterGroupTransportType
    # transport_settings = await wgrp.get_child("0:TransportSettings")
    #a = await wgrp.get_child("0:MessageSettings")
    # @TODO fill methods
    add_w = await wgrp.get_child("0:AddDataSetWriter")
    await add_w.delete()
    remove_w = await wgrp.get_child("0:RemoveDataSetWriter")
    await remove_w.delete()

