'''
    NetworkLayer for udp
'''

from urllib.parse import urlparse
from asyncua.ua.ua_binary import struct_from_binary
from asyncua.ua.uaprotocol_auto import NetworkAddressUrlDataType, PubSubConnectionDataType
from .connection import PubSubReciver
from asyncua.ua import KeyValuePair
import asyncio
from dataclasses import InitVar, dataclass
from ipaddress import ip_address
import socket
from typing import List, Optional, Tuple, Union
import struct
from asyncua.ua.uatypes import Byte, QualifiedName, String, UInt16, UInt32, UInt64, Variant, VariantType
from asyncua.common.utils import Buffer
import logging
from .uadp import UadpNetworkMessage

logger = logging.getLogger(__name__)


def _get_address_adatper(address: NetworkAddressUrlDataType):
    addr = None
    if address.NetworkInterface is not None:
        addr = address.NetworkInterface
    url = urlparse(address.Url)
    return (url.hostname, url.port), addr


@dataclass
class UdpSettings:
    '''
        settings for the udp layer
    '''
    Addr: Tuple[str, int] = None  # Address, Port
    Reuse: bool = True  # Resuse Port
    TTL: Optional[int] = None  # Sets the time to live for UDP
    Loopback: bool = True  # Sends Messages to loopback
    Adapter: Tuple[Optional[str], int] = None  # Listening address
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
        addr, adpater = _get_address_adatper(struct_from_binary(NetworkAddressUrlDataType, Buffer(cfg.Address.Body)))
        s = cls(addr, Adapter=(adpater, addr[1]))
        s.set_key_value(cfg.ConnectionProperties)
        return s

    def get_address(self) -> NetworkAddressUrlDataType:
        return NetworkAddressUrlDataType(self.Adapter[0], f"opc.udp://{self.Addr[0]}:{self.Addr[1]}")

    def set_key_value(self, kvs: Optional[List[KeyValuePair]]) -> None:
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

    def create_socket(self) -> Tuple[socket.socket, Tuple[str, int], Tuple[str, int]]:
        family, type, proto, _, addr = socket.getaddrinfo(self.Addr[0], self.Addr[1], 0, socket.SOCK_DGRAM)[0]
        sock = socket.socket(family, type, proto)
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
            raise NotImplementedError("Unsupporte socket family f{sock.family}")
        sock.setblocking(False)
        sock.bind(local)
        return (sock, addr, local)


class OpcUdp(asyncio.DatagramProtocol):
    def __init__(
        self, cfg: UdpSettings, reciver: Optional[PubSubReciver], publisher_id: Variant
    ) -> None:
        super().__init__()
        self.cfg = cfg
        self.reciver = reciver
        self.publisher_id = publisher_id.Value

    def connection_made(self, transport: asyncio.transports.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, source: Tuple[str, int]) -> None:
        try:
            logger.debug(f"Recived Datagramm from {source} - {data}")
            buffer = Buffer(data)
            msg = UadpNetworkMessage.from_binary(buffer)
            logger.debug(msg)
            asyncio.ensure_future(self.reciver.got_uadp(msg))
        except Exception:
            logging.exception("Recived Invalid UadpPacket")

    def send_uadp(self, msgs: List[UadpNetworkMessage]) -> None:
        for msg in msgs:
            logger.debug(f"Sending UadpMsg {msg}")
            self.transport.sendto(msg.to_binary(), self.cfg.Addr)

    def set_receiver(self, reciver: PubSubReciver) -> None:
        self.reciver = reciver

    def get_publisher_id(self) -> Union[Byte, UInt16, UInt32, UInt64, String]:
        '''
        Returns the publisher id for creating messages
        '''
        return self.publisher_id
