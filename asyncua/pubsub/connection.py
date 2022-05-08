"""
    Connection which sends/generates and recives/handles pubsub message
    over the network
"""
from __future__ import annotations
from typing import List, Optional, Union, TYPE_CHECKING
from asyncua.ua.status_codes import StatusCodes
from asyncua.ua.uaprotocol_auto import ReaderGroupDataType, WriterGroupDataType

if TYPE_CHECKING:
    from ..server.server import Server
from ..pubsub.information_model import PubSubInformationModel
from ..ua import (
    AttributeIds,
    ObjectIds,
    Byte,
    DataValue,
    ExtensionObject,
    LocalizedText,
    NodeId,
    UInt16,
    UInt32,
    UInt64,
    String,
    Variant,
    VariantType,
    PubSubConnectionDataType,
    PubSubState,
)
from ..common.methods import uamethod
from ..ua.ua_binary import struct_to_binary
from ..ua.uaerrors import UaError
from ..common.instantiate_util import instantiate
from .reader import DataSetReader, ReaderGroup
from .protocols import IPubSub, PubSubReciver
from .writer import DataSetWriter, WriterGroup
from .uadp import UadpNetworkMessage
from .udp import OpcUdp, UdpSettings

import logging
import asyncio

from asyncua.ua import uaerrors

logger = logging.getLogger(__name__)


UDP_UADP_PROFILE = "http://opcfoundation.org/UA-Profile/Transport/pubsub-udp-uadp"


class PubSubConnection(PubSubInformationModel):
    def __init__(self, cfg: PubSubConnectionDataType) -> None:
        """
        Inits a PubSubConnection from opcua PubSubConnectionDataType
        """
        super().__init__()
        self._cfg = cfg
        if self._cfg.PublisherId.VariantType not in [
            VariantType.Byte,
            VariantType.UInt16,
            VariantType.UInt32,
            VariantType.UInt64,
            VariantType.String,
        ]:
            raise UaError(f"No valid publisher_id: {self._cfg.PublisherId}")
        if self._cfg.TransportProfileUri != UDP_UADP_PROFILE:
            raise UaError(
                f"Not supported PubSub Profile: f{self._cfg.TransportProfileUri}"
            )
        udp_cfg = UdpSettings.from_cfg(self._cfg)
        self._network_factory = OpcUdp
        self._network_settings = udp_cfg
        self._writer_groups = [WriterGroup(cfg) for cfg in self._cfg.WriterGroups]
        self._reader_groups = [ReaderGroup(cfg) for cfg in self._cfg.ReaderGroups]
        self._receiver = self
        self._transport = None
        self._protocol = None
        self._writer_tasks = None
        self._reader_tasks = None
        self._nodes = {}

    @classmethod
    def udp_udadp(
        cls,
        name: str,
        publisher_id: Union[Byte, UInt16, UInt32, UInt64, String, Variant],
        network_cfg: UdpSettings,
        reader_groups: Optional[List[ReaderGroup]] = None,
        writer_groups: Optional[List[WriterGroup]] = None,
    ):
        """
        Creates UDP UADP Connection
        """
        if isinstance(publisher_id, Byte):
            pubid = Variant(publisher_id, VariantType.Byte)
        elif isinstance(publisher_id, UInt16):
            pubid = Variant(publisher_id, VariantType.UInt16)
        elif isinstance(publisher_id, UInt32):
            pubid = Variant(publisher_id, VariantType.UInt32)
        elif isinstance(publisher_id, UInt64):
            pubid = Variant(publisher_id, VariantType.UInt64)
        elif isinstance(publisher_id, int):
            pubid = Variant(publisher_id, VariantType.UInt32)
        elif isinstance(publisher_id, str) or isinstance(publisher_id, String):
            pubid = Variant(publisher_id, VariantType.String)
        elif isinstance(publisher_id, Variant):
            pubid = publisher_id
        else:
            raise UaError(f"No valid publisher_id: {publisher_id}")
        address = network_cfg.get_address()
        address = ExtensionObject(
            TypeId=address.data_type, Body=struct_to_binary(address)
        )
        properties = network_cfg.get_key_value()
        cfg = PubSubConnectionDataType(
            Name=name,
            Enabled=True,
            PublisherId=pubid,
            TransportProfileUri=UDP_UADP_PROFILE,
            Address=address,
            ConnectionProperties=properties,
        )
        o = cls(cfg)
        if writer_groups is not None:
            o._writer_groups = writer_groups
        if reader_groups is not None:
            o._reader_groups = reader_groups
        return o

    async def get_name(self) -> String:
        """
        the name of the connection
        """
        if self.model_is_init():
            return await self._get_node_name()
        else:
            return self._cfg.Name

    async def add_writer_group(self, writer_group: WriterGroup) -> None:
        """
        Adds a writer group
        """
        self._cfg.WriterGroups.append(writer_group._cfg)
        self._writer_groups.append(writer_group)
        if self.model_is_init():
            await writer_group._init_information_model(
                self._node, self._server, self._app
            )

    async def add_reader_group(self, reader: ReaderGroup) -> None:
        """
        Adds a reader group
        """
        self._cfg.ReaderGroups.append(reader._cfg)
        self._reader_groups.append(reader)
        if self.model_is_init():
            await reader._init_information_model(self._node, self._server)

    def get_writer_group(self, name: String) -> Optional[DataSetWriter]:
        """
        Returns a writer group via name, if found.
        """
        return next((w for w in self._writer_groups if w.get_name() == name), None)

    def get_reader_group(self, name: String) -> Optional[DataSetReader]:
        """
        Returns a reader group via name, if found.
        """
        return next((r for r in self._reader_groups if r.get_name() == name), None)

    async def remove_reader_group(self, name: String) -> None:
        """
        Removes a reader group from the connection
        """
        r = self.get_reader_group(name)
        if r is not None:
            await r._node.delete()
            del r._meta
            del r

    async def remove_writer_group(self, name: String) -> None:
        """
        Removes a writer group from the connection
        """
        w = self.get_writer_group(name)
        if w is not None:
            await w._node.delete()
            del w._meta
            del w

    async def start(self) -> None:
        """
        Starts the connection, which listens to incoming messages
        and sends messages from writers
        """
        logging.info(f"Starting Connection {await self.get_name()}")
        loop = asyncio.get_event_loop()
        sock, _, _ = self._network_settings.create_socket()
        self._transport, self._protocol = await loop.create_datagram_endpoint(
            lambda: self._network_factory(
                self._network_settings, self._receiver, self._cfg.PublisherId
            ),
            sock=sock,
        )
        self._writer_tasks = asyncio.gather(
            *[writer.run(self._protocol, self._app) for writer in self._writer_groups]
        )
        reader_tasks = asyncio.gather(
            *[reader.start() for reader in self._reader_groups]
        )
        await reader_tasks
        self._protocol.set_receiver(self._receiver)
        await self._set_state(PubSubState.Operational)

    async def stop(self) -> None:
        """Stops alle activity of a connection"""
        logging.info(f"Stopping Connection {await self.get_name()}")
        reader_tasks = asyncio.gather(
            *[reader.stop() for reader in self._reader_groups]
        )
        await reader_tasks
        if self._writer_tasks is not None:
            self._writer_tasks.cancel()
            await self._writer_tasks
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        if self._protocol is not None:
            self._protocol = None
        await self._set_state(PubSubState.Disabled)

    async def send_uadp_msg(self, msg: UadpNetworkMessage) -> None:
        """Send a pubsub message in uadp format"""
        if self._network_factory != OpcUdp:
            await self._set_state(PubSubState.Error)
            raise UaError(
                "Sending a Uadp Encoded Message is not supported with this connection"
            )
        self._protocol.send_uadp([msg])

    def set_if(self, ps: IPubSub) -> None:
        """
        Registers an IPubSub for the connection
        """
        self._app = ps

    def set_receiver(self, receiver: PubSubReciver) -> None:
        """
        Sets a PubSubReciver which recives pubsub events
        """
        if self._protocol is not None:
            self._protocol.set_receiver(receiver)
        self._receiver = receiver

    async def got_uadp(self, msg: UadpNetworkMessage) -> None:
        """Handels a Uadp Message"""
        for r in self._reader_groups:
            await r.handle_msg(msg)

    @uamethod
    async def _add_reader_group(self, rg: ReaderGroupDataType) -> NodeId:
        rgp = ReaderGroup(rg)
        await self.add_reader_group(rgp)
        return rgp._node.nodeid

    @uamethod
    async def _add_writer_group(self, wg: WriterGroupDataType) -> NodeId:
        wgp = WriterGroup(wg)
        await self.add_reader_group(wgp)
        return wgp._node.nodeid

    @uamethod
    async def _remove_group(self, nid: NodeId) -> None:
        for r in self._reader_groups:
            if r._node.nodeid == nid:
                self.remove_reader_group(r)
                return
        for w in self._writer_groups:
            if w._node.nodeid == nid:
                self.remove_writer_group(w)
                return
        raise uaerrors.UaStatusCodeError(StatusCodes.BadNodeIdUnknown)

    async def _init_information_model(self, server: Server) -> None:
        """
        Inits the information model
        """
        parent_pubsub = server.get_node(NodeId(ObjectIds.PublishSubscribe, 0))
        con_type = server.get_node(NodeId(ObjectIds.PubSubConnectionType, 0))
        objs = await instantiate(
            parent_pubsub,
            con_type,
            idx=1,
            bname=self._cfg.Name,
            instantiate_optional=False,
            dname=LocalizedText(self._cfg.Name, ""),
        )
        con_var = objs[0]
        await parent_pubsub.add_reference(
            con_var, NodeId(ObjectIds.HasPubSubConnection)
        )
        await parent_pubsub.delete_reference(con_var, ObjectIds.HasComponent)
        await self._init_node(con_var, server)
        # @FIXME currently the datatype is wrong in the addresspace! Need to change schema generator
        await self.set_node_value("0:PublisherId", Variant(str(self._cfg.PublisherId)))
        await self.set_node_value(
            "0:TransportProfileUri", self._cfg.TransportProfileUri
        )
        await self.set_node_value(
            "0:ConnectionProperties", self._cfg.ConnectionProperties
        )
        addr = await self._node.get_child("0:Address")
        await addr.delete()
        object_type_id = NodeId(ObjectIds.NetworkAddressUrlType, 0)
        await instantiate(
            con_var,
            server.get_node(object_type_id),
            idx=1,
            bname="0:Address",
            dname=LocalizedText("Address"),
        )
        con_addr = self._network_settings.get_address()
        await self.set_node_value(
            ["0:Address", "0:NetworkInterface"], con_addr.NetworkInterface
        )
        await self.set_node_value(["0:Address", "0:Url"], con_addr.Url)
        meth = await instantiate(
            con_var,
            server.get_node(NodeId(ObjectIds.PubSubConnectionType_AddReaderGroup)),
            idx=1,
            bname="0:AddReaderGroup",
            dname=LocalizedText("AddReaderGroup"),
        )
        server.link_method(meth[0], self._add_reader_group)
        meth = await instantiate(
            con_var,
            server.get_node(NodeId(ObjectIds.PubSubConnectionType_AddWriterGroup)),
            idx=1,
            bname="0:AddWriterGroup",
            dname=LocalizedText("AddWriterGroup"),
        )
        server.link_method(meth[0], self._add_writer_group)
        meth = await instantiate(
            con_var,
            server.get_node(NodeId(ObjectIds.PubSubConnectionType_RemoveGroup)),
            idx=1,
            bname="0:RemoveGroup",
            dname=LocalizedText("RemoveGroup"),
        )
        server.link_method(meth[0], self._remove_group)
        for wg in self._writer_groups:
            await wg._init_information_model(self._node, self._server, self._app)
        for rg in self._reader_groups:
            await rg._init_information_model(self._node, self._server)
