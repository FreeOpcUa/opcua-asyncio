"""
NetworkLayer for udp
"""

import asyncio
import logging
import struct
import socket
from dataclasses import InitVar, dataclass
from ipaddress import ip_address
from typing import List, Tuple, Union
from urllib.parse import urlparse

from ..ua import KeyValuePair
from ..ua.uaprotocol_auto import (
    NetworkAddressUrlDataType,
    PubSubConnectionDataType,
)
from ..ua.uatypes import (
    Byte,
    QualifiedName,
    String,
    UInt16,
    UInt32,
    UInt64,
    Variant,
    VariantType,
)
from ..common.utils import Buffer

from .connection import PubSubReceiver
from .uadp import UadpNetworkMessage

logger = logging.getLogger(__name__)


def _get_address_adapter(address: NetworkAddressUrlDataType):
    addr = None
    if address.NetworkInterface is not None:
        addr = address.NetworkInterface
    url = urlparse(str(address.Url))
    return (url.hostname, url.port), addr


@dataclass
class UdpSettings:
    """
    settings for the udp layer
    """

    Addr: Tuple[str, int] = None  # Address, Port
    Reuse: bool = True  # Reuse Port
    TTL: int | None = None  # Sets the time to live for UDP
    Loopback: bool = True  # Sends Messages to loopback
    Adapter: Tuple[str | None, int] = None  # Listening address
    Url: InitVar[str] = None  # Url to generate the addr

    def __post_init__(self, Url: str):
        if Url is not None:
            url = urlparse(Url)
            port = url.port if url.port is not None else 4840
            self.Addr = (url.hostname, port)
        if self.Adapter is None:
            self.Adapter = (None, self.Addr[1])

    @classmethod
    def from_cfg(cls, cfg: PubSubConnectionDataType):
        addr, adpater = _get_address_adapter(cfg.Address)
        s = cls(addr, Adapter=(adpater, addr[1]))
        s.set_key_value(cfg.ConnectionProperties)
        return s

    def get_address(self) -> NetworkAddressUrlDataType:
        adapter = "" if self.Adapter[0] is None else self.Adapter[0]
        return NetworkAddressUrlDataType(adapter, f"opc.udp://{self.Addr[0]}:{self.Addr[1]}")

    def set_key_value(self, kvs: List[KeyValuePair] | None) -> None:
        if kvs is not None:
            for kv in kvs:
                key = kv.Key.Name
                value = kv.Value
                if key == "ttl" and value.VariantType == VariantType.Boolean:
                    self.TTL = value.Value
                if key == "loopback" and value.VariantType == VariantType.Boolean:
                    self.Loopback = value.Value
                if key == "reuse" and value.VariantType == VariantType.Boolean:
                    self.Reuse = value.Value

    def get_key_value(self) -> List[KeyValuePair]:
        kvs = []
        if self.TTL is not None:
            kvs.append(KeyValuePair(QualifiedName("ttl"), Variant(self.TTL)))
        kvs.append(KeyValuePair(QualifiedName("reuse"), Variant(self.Reuse)))
        kvs.append(KeyValuePair(QualifiedName("Loopback"), Variant(self.Loopback)))
        return kvs

    def create_socket(self) -> Tuple[socket.socket, Union[Tuple[str, int], Tuple[str, int, int, int]], Tuple[str, int]]:
        family, typ, proto, _, addr = socket.getaddrinfo(self.Addr[0], self.Addr[1], 0, socket.SOCK_DGRAM)[0]
        sock = socket.socket(family, typ, proto)
        if self.Reuse:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if sock.family == socket.AF_INET:
            if self.Adapter[0] is None:
                local = ("0.0.0.0", self.Adapter[1])
            else:
                local = self.Adapter
            if self.Loopback:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, self.Loopback)
            if self.TTL is not None:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.TTL)
            try:
                if ip_address(addr[0]).is_multicast:
                    req = struct.pack("=4sl", socket.inet_aton(addr[0]), socket.INADDR_ANY)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
            except ValueError:
                # Invalid IPAddress => no multicast
                pass
        elif sock.family == socket.AF_INET6:
            if self.Adapter[0] is None:
                local = ("::", self.Adapter[1])
            else:
                local = self.Adapter
            if self.Loopback:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, int(self.Loopback))
            if self.TTL is not None:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, self.TTL)
            try:
                if ip_address(addr[0]).is_multicast:
                    req = struct.pack("=16si", socket.inet_pton(socket.AF_INET6, addr[0]), 0)
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, req)
            except ValueError:
                # Invalid IPAddress => no multicast
                pass
        else:
            raise NotImplementedError("Unsupported socket family f{sock.family}")
        sock.setblocking(False)
        sock.bind(local)
        return (sock, addr, local)


class OpcUdp(asyncio.DatagramProtocol):
    def __init__(self, cfg: UdpSettings, receiver: PubSubReceiver | None, publisher_id: Variant) -> None:
        super().__init__()
        self.cfg = cfg
        self.receiver = receiver
        self.publisher_id = publisher_id.Value

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        self.transport: asyncio.transports.DatagramTransport = transport

    def datagram_received(self, data: bytes, source: Tuple[str, int]) -> None:
        try:
            logger.debug("Received Datagram from %s - %s", source, data)
            buffer = Buffer(data)
            msg = UadpNetworkMessage.from_binary(buffer)
            logger.debug(msg)
            if self.receiver is not None:
                asyncio.ensure_future(self.receiver.got_uadp(msg))
            else:
                logger.warning("No receiver set — dropping UADP message")
        except Exception:
            logging.exception("Received Invalid UadpPacket")

    def send_uadp(self, msgs: List[UadpNetworkMessage]) -> None:
        for msg in msgs:
            logger.debug("Sending UadpMsg %s", msg)
            self.transport.sendto(msg.to_binary(), self.cfg.Addr)

    def set_receiver(self, receiver: PubSubReceiver) -> None:
        self.receiver = receiver

    def get_publisher_id(self) -> Union[Byte, UInt16, UInt32, UInt64, String]:
        """
        Returns the publisher id for creating messages
        """
        return self.publisher_id
