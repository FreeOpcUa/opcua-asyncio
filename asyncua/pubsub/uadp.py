"""
Implements Uadp Network Encoding defined in Part14 7.2
    Missing: RawDeltaFrame read
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import Protocol

from ..common.utils import Buffer
from ..ua import VariantType
from ..ua.status_codes import StatusCodes
from ..ua.ua_binary import (
    Primitives,
    from_binary,
    pack_uatype,
    struct_from_binary,
    struct_to_binary,
    to_binary,
    unpack_uatype,
)
from ..ua.uaprotocol_auto import (
    DataSetMetaDataType,
    EndpointDescription,
    VersionTime,
    WriterGroupDataType,
)
from ..ua.uatypes import (
    Byte,
    Bytes,
    DataValue,
    DateTime,
    Guid,
    StatusCode,
    String,
    UInt16,
    UInt32,
    UInt64,
    Variant,
)

logger = logging.getLogger(__name__)


class MessageHeaderFlags(IntFlag):
    """
    Uadp Message flags See OPC Unified Architecture, Part 14 7.2.2.2.2
    """

    NONE = 0
    UADP_VERSION_BIT0 = 0b1  # 1.04 and 1.05 only define version 1.
    PUBLISHER_ID = (
        0b00010000  # If the PublisherId is enabled, the type of PublisherId is indicated in the ExtendedFlags1 field.
    )
    GROUP_HEADER = 0b00100000
    PAYLOAD_HEADER = 0b01000000
    EXTENDED_FLAGS_1 = 0b10000000
    # FlagsExtend1
    # When No PublisherId is set then Id is Byte!
    PUBLISHER_ID_UINT16 = 0b0000000100000000
    PUBLISHER_ID_UINT32 = 0b0000001000000000
    PUBLISHER_ID_UINT64 = 0b0000011000000000
    PUBLISHER_ID_STRING = 0b0000010000000000
    DATACLASS_SET = 0b0000100000000000
    SECURITY_MODE = 0b0001000000000000
    TIMESTAMP = 0b0010000000000000
    PICO_SECONDS = 0b0100000000000000
    EXTENDED_FLAGS_2 = 0b1000000000000000
    # FlagsExtend2
    CHUNK = 0b000010000000000000000
    PROMOTEDFIELDS = 0b000100000000000000000  # Promoted fields can only be sent if the NetworkMessage contains only one DataSetMessage.
    DISCOVERYREQUEST = 0b001000000000000000000
    DISCOVERYRESPONSE = 0b010000000000000000000


class MessageGroupHeaderFlags(IntFlag):
    """
    Uadp group header flags See OPC Unified Architecture, Part 14 7.2.2.2.2
    """

    WRITER_GROUP_ID = 0b0001
    GROUP_VERSION = 0b0010
    NETWORK_MESSAGE_NUMBER = 0b0100
    SEQUENCE_NUMBER = 0b1000


class MessageDataSetFlags(IntFlag):
    """
    Uadp dataset header flags See OPC Unified Architecture, Part 14 7.2.2.3.2
    """

    # Byte 1
    VALID = 0b00000001
    RAW_DATA = 0b00000010
    DATA_VALUE = 0b00000100
    SEQUENCE_NUMBER = 0b00001000
    STATUS = 0b00010000
    CFG_MAJOR_VERSION = 0b00100000
    CFG_MINOR_VERSION = 0b01000000
    FLAGS2 = 0b10000000
    # Byte 2
    DELTA_FRAME = 0b0000000100000000
    EVENT = 0b0000001000000000
    KEEP_ALIVE = 0b0000001100000000
    TIMESTAMP = 0b0001000000000000
    PICOSECONDS = 0b0010000000000000


class InformationType(IntEnum):
    # Type of information to be send
    PublisherEndpoints = 1
    DataSetMetaData = 2
    DataSetWriter = 3


@dataclass
class UadpHeader:
    """
    Header of an Uadp  Message
    """

    PublisherId: Byte | UInt16 | UInt32 | UInt64 | String | None = None
    DataSetClassId: Guid | None = None

    def to_binary(self, flags: MessageHeaderFlags) -> bytes:
        b = []
        if self.PublisherId is not None:
            flags |= MessageHeaderFlags.PUBLISHER_ID
            if isinstance(self.PublisherId, UInt16):
                flags |= MessageHeaderFlags.PUBLISHER_ID_UINT16
            elif isinstance(self.PublisherId, UInt32):
                flags |= MessageHeaderFlags.PUBLISHER_ID_UINT32
            elif isinstance(self.PublisherId, UInt64):
                flags |= MessageHeaderFlags.PUBLISHER_ID_UINT64
            elif isinstance(self.PublisherId, String):
                flags |= MessageHeaderFlags.PUBLISHER_ID_STRING
        if self.DataSetClassId is not None:
            flags |= MessageHeaderFlags.DATACLASS_SET
        if flags > 0xFF:
            flags |= MessageHeaderFlags.EXTENDED_FLAGS_1
            if flags > 0xFFFF:
                flags |= MessageHeaderFlags.EXTENDED_FLAGS_2
                b.append(Primitives.UInt16.pack(flags & 0xFFFF))
                b.append(Primitives.Byte.pack(flags >> 16))
            else:
                b.append(Primitives.UInt16.pack(flags))
        else:
            b.append(Primitives.Byte.pack(flags))
        if self.PublisherId is not None:
            if isinstance(self.PublisherId, UInt16):
                b.append(Primitives.UInt16.pack(self.PublisherId))
            elif isinstance(self.PublisherId, UInt32):
                b.append(Primitives.UInt32.pack(self.PublisherId))
            elif isinstance(self.PublisherId, UInt64):
                b.append(Primitives.UInt64.pack(self.PublisherId))
            elif isinstance(self.PublisherId, String):
                b.append(Primitives.String.pack(self.PublisherId))
            else:
                b.append(Primitives.Byte.pack(self.PublisherId))
        if self.DataSetClassId is not None:
            b.append(Primitives.Guid.pack(self.DataSetClassId))
        return b"".join(b)

    @staticmethod
    def from_binary(data) -> tuple[MessageHeaderFlags, UadpHeader]:
        header = UadpHeader()
        flags = MessageHeaderFlags(Primitives.Byte.unpack(data))
        if MessageHeaderFlags.EXTENDED_FLAGS_1 in flags:
            flags |= MessageHeaderFlags(Primitives.Byte.unpack(data) << 8)
            if MessageHeaderFlags.EXTENDED_FLAGS_2 in flags:
                flags |= MessageHeaderFlags(Primitives.Byte.unpack(data) << 16)
        if MessageHeaderFlags.PUBLISHER_ID in flags:
            if MessageHeaderFlags.PUBLISHER_ID_STRING in flags:
                header.PublisherId = Primitives.String.unpack(data)
            elif MessageHeaderFlags.PUBLISHER_ID_UINT16 in flags:
                header.PublisherId = UInt16(Primitives.UInt16.unpack(data))
            elif MessageHeaderFlags.PUBLISHER_ID_UINT32 in flags:
                header.PublisherId = UInt32(Primitives.UInt32.unpack(data))
            elif MessageHeaderFlags.PUBLISHER_ID_UINT64 in flags:
                header.PublisherId = UInt64(Primitives.UInt64.unpack(data))
            else:
                header.PublisherId = Byte(Primitives.Byte.unpack(data))
        if MessageHeaderFlags.DATACLASS_SET in flags:
            header.DataSetClassId = Primitives.Guid.unpack(data)
        return flags, header


@dataclass
class UadpChunk:
    MessageSequenceNo: UInt16 = field(default_factory=lambda: UInt16(0))
    ChunkOffset: UInt32 = field(default_factory=lambda: UInt32(0))
    TotalSize: UInt32 = field(default_factory=lambda: UInt32(0))
    ChunkData: Bytes = field(default_factory=lambda: Bytes(b""))

    def to_binary(self) -> bytes:
        b: list[bytes] = []
        b.append(Primitives.UInt16.pack(self.MessageSequenceNo))
        b.append(Primitives.UInt32.pack(self.ChunkOffset))
        b.append(Primitives.UInt32.pack(self.TotalSize))
        b.append(self.ChunkData)
        return b"".join(b)

    @staticmethod
    def from_binary(data) -> UadpChunk:
        chunk = UadpChunk()
        chunk.MessageSequenceNo = Primitives.UInt16.unpack(data)
        chunk.ChunkOffset = Primitives.UInt32.unpack(data)
        chunk.TotalSize = Primitives.UInt32.unpack(data)
        chunk.ChunkData = data.read()
        return chunk


@dataclass
class UadpGroupHeader:
    """
    Header of group part of an uadp message
    """

    WriterGroupId: UInt16 | None = None
    GroupVersion: VersionTime | None = None
    NetworkMessageNo: UInt16 | None = None
    SequenceNo: UInt16 | None = None

    def to_bytes(self) -> bytes:
        flags = MessageGroupHeaderFlags(0)
        if self.WriterGroupId is not None:
            flags |= MessageGroupHeaderFlags.WRITER_GROUP_ID
        if self.GroupVersion is not None:
            flags |= MessageGroupHeaderFlags.GROUP_VERSION
        if self.NetworkMessageNo is not None:
            flags |= MessageGroupHeaderFlags.NETWORK_MESSAGE_NUMBER
        if self.SequenceNo is not None:
            flags |= MessageGroupHeaderFlags.SEQUENCE_NUMBER
        b = []
        b.append(Primitives.Byte.pack(flags))
        if self.WriterGroupId is not None:
            b.append(Primitives.UInt16.pack(self.WriterGroupId))
        if self.GroupVersion is not None:
            b.append(Primitives.UInt32.pack(self.GroupVersion))
        if self.NetworkMessageNo is not None:
            b.append(Primitives.UInt16.pack(self.NetworkMessageNo))
        if self.SequenceNo is not None:
            b.append(Primitives.UInt16.pack(self.SequenceNo))
        return b"".join(b)

    @staticmethod
    def from_binary(data) -> UadpGroupHeader:
        gp = UadpGroupHeader()
        flags = MessageGroupHeaderFlags(Primitives.Byte.unpack(data))
        if MessageGroupHeaderFlags.WRITER_GROUP_ID in flags:
            gp.WriterGroupId = Primitives.UInt16.unpack(data)
        if MessageGroupHeaderFlags.GROUP_VERSION in flags:
            gp.GroupVersion = Primitives.UInt32.unpack(data)
        if MessageGroupHeaderFlags.NETWORK_MESSAGE_NUMBER in flags:
            gp.NetworkMessageNo = Primitives.UInt16.unpack(data)
        if MessageGroupHeaderFlags.SEQUENCE_NUMBER in flags:
            gp.SequenceNo = Primitives.UInt16.unpack(data)
        return gp


@dataclass
class UadpDataSetMessageHeader:
    Valid: bool = True
    SequenceNo: UInt16 | None = None
    Timestamp: DateTime | None = None
    PicoSeconds: UInt16 | None = None
    Status: UInt16 | None = None
    CfgMajorVersion: VersionTime | None = None
    CfgMinorVersion: VersionTime | None = None

    def to_binary(self, flags: MessageDataSetFlags) -> bytes:
        if self.Valid:
            flags |= MessageDataSetFlags.VALID
        if self.SequenceNo is not None:
            flags |= MessageDataSetFlags.SEQUENCE_NUMBER
        if self.Timestamp is not None:
            flags |= MessageDataSetFlags.TIMESTAMP
        if self.PicoSeconds is not None:
            flags |= MessageDataSetFlags.PICOSECONDS
        if self.Status is not None:
            flags |= MessageDataSetFlags.STATUS
        if self.CfgMajorVersion is not None:
            flags |= MessageDataSetFlags.CFG_MAJOR_VERSION
        if self.CfgMinorVersion is not None:
            flags |= MessageDataSetFlags.CFG_MINOR_VERSION
        b = []
        if flags > 0xFF:
            flags |= MessageDataSetFlags.FLAGS2
            b.append(Primitives.UInt16.pack(flags))
        else:
            b.append(Primitives.Byte.pack(flags))
        if self.SequenceNo is not None:
            b.append(Primitives.UInt16.pack(self.SequenceNo))
        if self.Timestamp is not None:
            b.append(Primitives.DateTime.pack(self.Timestamp))
        if self.PicoSeconds is not None:
            b.append(Primitives.UInt16.pack(self.PicoSeconds))
        if self.Status is not None:
            b.append(Primitives.UInt16.pack(self.Status))
        if self.CfgMajorVersion is not None:
            b.append(Primitives.UInt32.pack(self.CfgMajorVersion))
        if self.CfgMinorVersion is not None:
            b.append(Primitives.UInt32.pack(self.CfgMinorVersion))
        return b"".join(b)

    @staticmethod
    def from_binary(data) -> tuple[MessageDataSetFlags, UadpDataSetMessageHeader]:
        header = UadpDataSetMessageHeader()
        flags = MessageDataSetFlags(Primitives.Byte.unpack(data))
        if MessageDataSetFlags.FLAGS2 in flags:
            flags |= MessageDataSetFlags(Primitives.Byte.unpack(data) << 8)
        if MessageDataSetFlags.VALID in flags:
            header.Valid = True
        if MessageDataSetFlags.SEQUENCE_NUMBER in flags:
            header.SequenceNo = Primitives.UInt16.unpack(data)
        if MessageDataSetFlags.TIMESTAMP in flags:
            d = Primitives.DateTime.unpack(data)
            header.Timestamp = DateTime(
                d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, d.tzinfo, fold=d.fold
            )
        if MessageDataSetFlags.PICOSECONDS in flags:
            header.PicoSeconds = Primitives.UInt16.unpack(data)
        if MessageDataSetFlags.STATUS in flags:
            header.Status = Primitives.UInt16.unpack(data)
        if MessageDataSetFlags.CFG_MAJOR_VERSION in flags:
            header.CfgMajorVersion = Primitives.UInt32.unpack(data)
        if MessageDataSetFlags.CFG_MINOR_VERSION in flags:
            header.CfgMinorVersion = Primitives.UInt32.unpack(data)
        return flags, header


@dataclass
class UadpPublisherEndpointsResp:
    """
    Response with the Endpoint of the publisher
    """

    Endpoints: list[EndpointDescription] = field(default_factory=list)
    Status: StatusCode = field(default_factory=lambda: StatusCode(UInt32(StatusCodes.Good)))


@dataclass
class UadpDataSetMetaDataResp:
    """
    Response with the MetaData of an DataSetWriter
    """

    DataSetWriterId: UInt16 = field(default_factory=lambda: UInt16(0))
    MetaData: DataSetMetaDataType = field(default_factory=DataSetMetaDataType)
    Status: StatusCode = field(default_factory=lambda: StatusCode(UInt32(StatusCodes.Good)))


@dataclass
class UadpDataSetWriterResp:
    """
    Response with the DataSetWriters of a Writer Group
    """

    DataSetWriterIds: list[UInt16] = field(default_factory=list)
    DataSetWriterConfig: WriterGroupDataType = field(default_factory=WriterGroupDataType)
    Status: list[StatusCode] = field(default_factory=list)


@dataclass
class UadpDiscoveryRequest:
    Type: InformationType = 0
    DataSetWriterIds: list[UInt16] = field(default_factory=list)


@dataclass
class UadpDiscoveryResponse:
    Type: InformationType  # Which type of discovery message
    SequenceNumber: (
        UInt16  # Sequence number for responses, should be incremented for each discovery response from the connection
    )
    Response: UadpPublisherEndpointsResp | UadpDataSetMetaDataResp | UadpDataSetWriterResp


@dataclass
class DeltaVariant:
    No: UInt16 = field(default_factory=lambda: UInt16(0))
    Value: Variant = field(default_factory=lambda: Variant)


@dataclass
class DeltaDataValue:
    No: UInt16 = field(default_factory=lambda: UInt16(0))
    Value: DataValue = field(default_factory=DataValue)


@dataclass
class DeltaRaw:
    No: UInt16 = field(default_factory=lambda: UInt16(0))
    Value: bytes = b""


@dataclass
class UadpDataSetDeltaVariant:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)
    Data: list[DeltaVariant] = field(default_factory=list)

    def message_to_binary(self) -> bytes:
        b = []
        b.append(self.Header.to_binary(MessageDataSetFlags.DELTA_FRAME))
        b.append(Primitives.UInt16.pack(len(self.Data)))
        for value in self.Data:
            b.append(struct_to_binary(value))
        return b"".join(b)

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        Data = [struct_from_binary(DeltaVariant, data) for _ in range(Primitives.UInt16.unpack(data))]
        return UadpDataSetDeltaVariant(header, Data)


@dataclass
class UadpDataSetDeltaDataValue:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)
    Data: list[DeltaDataValue] = field(default_factory=list)

    def message_to_binary(self) -> bytes:
        b = []
        b.append(self.Header.to_binary(MessageDataSetFlags.DELTA_FRAME | MessageDataSetFlags.DATA_VALUE))
        b.append(Primitives.UInt16.pack(len(self.Data)))
        for value in self.Data:
            b.append(struct_to_binary(value))
        return b"".join(b)

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        Data = [struct_from_binary(DeltaDataValue, data) for _ in range(Primitives.UInt16.unpack(data))]
        return UadpDataSetDeltaDataValue(header, Data)


@dataclass
class UadpDataSetDeltaRaw:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)
    Data: list[DeltaRaw] = field(default_factory=bytes)

    def message_to_binary(self) -> bytes:
        raise NotImplementedError("Raw Message is not implemented!")

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        raise NotImplementedError("Raw Message is not implemented!")


@dataclass
class UadpDataSetVariant:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)
    Data: list[Variant] = field(default_factory=list)

    def message_to_binary(self) -> bytes:
        b = []
        b.append(self.Header.to_binary(MessageDataSetFlags(0)))
        b.append(Primitives.UInt16.pack(len(self.Data)))
        for value in self.Data:
            b.append(pack_uatype(VariantType.Variant, value))
        return b"".join(b)

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        Data = [unpack_uatype(VariantType.Variant, data) for _ in range(Primitives.UInt16.unpack(data))]
        return UadpDataSetVariant(header, Data)


@dataclass
class UadpDataSetDataValue:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)
    Data: list[DataValue] = field(default_factory=list)

    def message_to_binary(self) -> bytes:
        b = []
        b.append(self.Header.to_binary(MessageDataSetFlags.DATA_VALUE))
        b.append(Primitives.UInt16.pack(len(self.Data)))
        for value in self.Data:
            b.append(to_binary(DataValue, value))
        return b"".join(b)

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        Data = [struct_from_binary(DataValue, data) for _ in range(Primitives.UInt16.unpack(data))]
        return UadpDataSetDataValue(header, Data)


@dataclass
class UadpDataSetRaw:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)
    Data: bytes = b""  # NOTE: could use field(default_factory=list) if we knew the field layout

    def message_to_binary(self) -> bytes:
        return b"".join([self.Header.to_binary(MessageDataSetFlags.RAW_DATA), self.Data])

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        return UadpDataSetRaw(header, data.read(size))


@dataclass
class UadpDataSetKeepAlive:
    Header: UadpDataSetMessageHeader = field(default_factory=UadpDataSetMessageHeader)

    def message_to_binary(self) -> bytes:
        return self.Header.to_binary(MessageDataSetFlags.KEEP_ALIVE)

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        return UadpDataSetKeepAlive(header)


# @dataclass
class UadpDataSetMessage(Protocol):
    def message_to_binary(self) -> bytes:
        raise NotImplementedError("UadpDataSetMessage is a abstract class")

    @staticmethod
    def message_from_binary(header: UadpDataSetMessageHeader, data: Buffer, size: int) -> UadpDataSetMessage:
        raise NotImplementedError("UadpDataSetMessage is a abstract class")


def _pack_payload(msgs: list[UadpDataSetMessage], has_payload_header: bool) -> bytes:
    b = []
    for msg in msgs:
        b.append(msg.message_to_binary())
    if has_payload_header and len(msgs) > 1:
        # Sizes is omitted if count is 1 *OR* payload header was omitted.
        sizes = [len(m.message_to_binary()) for m in msgs]
        b_sizes = [Primitives.UInt16.pack(sz) for sz in sizes]
        b = b_sizes + b
    return b"".join(b)


def _unpack_payload(data: Buffer, payload_header_count: int | None) -> list[UadpDataSetMessage]:
    """
    Unpack (at least one) DataSet payload.
    """
    sizes: list[int] = []
    payload: list[UadpDataSetMessage] = []
    if payload_header_count and payload_header_count > 1:
        # Sizes is omitted if count is 1 *OR* payload header was omitted.
        for _ in range(payload_header_count):
            sizes.append(Primitives.UInt16.unpack(data))
    else:
        # FIXME: For now, we assume one DataSetMessage if payload header was omitted.
        sizes.append(len(data))
    for size in sizes:
        header_len = len(data)
        flags, header = UadpDataSetMessageHeader.from_binary(data)
        header_len -= len(data)
        # HACK because RawData-encoded Data Key frames are not self-describing
        # This is only required for UadpDataSetRaw (I think), but we do it for all for the Protocol
        data_size = size - header_len
        if MessageDataSetFlags.KEEP_ALIVE in flags:
            payload.append(UadpDataSetKeepAlive.message_from_binary(header, data, data_size))
        elif MessageDataSetFlags.RAW_DATA in flags:
            if MessageDataSetFlags.DELTA_FRAME in flags:
                payload.append(UadpDataSetDeltaRaw.message_from_binary(header, data, data_size))
            else:
                payload.append(UadpDataSetRaw.message_from_binary(header, data, data_size))
        elif MessageDataSetFlags.DATA_VALUE in flags:
            if MessageDataSetFlags.DELTA_FRAME in flags:
                payload.append(UadpDataSetDeltaDataValue.message_from_binary(header, data, data_size))
            else:
                payload.append(UadpDataSetDataValue.message_from_binary(header, data, data_size))
        else:
            if MessageDataSetFlags.DELTA_FRAME in flags:
                payload.append(UadpDataSetDeltaVariant.message_from_binary(header, data, data_size))
            else:
                payload.append(UadpDataSetVariant.message_from_binary(header, data, data_size))
    return payload


@dataclass
class UadpNetworkMessage:
    """
    Network Message for UADP
    """

    Header: UadpHeader = field(default_factory=UadpHeader)
    GroupHeader: UadpGroupHeader | None = None
    DataSetPayloadHeader: list[UInt16] = field(default_factory=list)
    Timestamp: DateTime | None = None
    PicoSeconds: UInt16 | None = None
    PromotedFields: list[Variant] = field(default_factory=list)
    Payload: list[UadpDataSetMessage] | UadpDiscoveryRequest | UadpDiscoveryResponse | UadpChunk = None

    def to_binary(self) -> bytes:
        flags = MessageHeaderFlags.NONE
        flags |= MessageHeaderFlags.UADP_VERSION_BIT0
        if self.GroupHeader is not None:
            flags |= MessageHeaderFlags.GROUP_HEADER
        if self.DataSetPayloadHeader:
            flags |= MessageHeaderFlags.PAYLOAD_HEADER
        if self.Timestamp is not None:
            flags |= MessageHeaderFlags.TIMESTAMP
        if self.PicoSeconds is not None:
            flags |= MessageHeaderFlags.PICO_SECONDS
        if self.PromotedFields:
            flags |= MessageHeaderFlags.PROMOTEDFIELDS
        if isinstance(self.Payload, UadpDiscoveryRequest):
            flags |= MessageHeaderFlags.DISCOVERYREQUEST
        elif isinstance(self.Payload, UadpDiscoveryResponse):
            flags |= MessageHeaderFlags.DISCOVERYRESPONSE
        elif isinstance(self.Payload, UadpChunk):
            flags |= MessageHeaderFlags.CHUNK
        b = []
        b.append(self.Header.to_binary(flags))
        if self.GroupHeader is not None:
            b.append(self.GroupHeader.to_bytes())
        if self.DataSetPayloadHeader:
            b.append(Primitives.Byte.pack(len(self.DataSetPayloadHeader)))
            for ds in self.DataSetPayloadHeader:
                b.append(Primitives.UInt16.pack(ds))
        if self.Timestamp is not None:
            b.append(Primitives.DateTime.pack(self.Timestamp))
        if self.PicoSeconds is not None:
            b.append(Primitives.UInt16.pack(self.PicoSeconds))
        if self.PromotedFields:
            b.append(Primitives.UInt16.pack(len(self.PromotedFields)))
            for promoted in self.PromotedFields:
                b.append(pack_uatype(VariantType.Variant, promoted))
        if isinstance(self.Payload, UadpDiscoveryRequest):
            b.append(to_binary(UadpDiscoveryRequest, self.Payload))
        elif isinstance(self.Payload, UadpDiscoveryResponse):
            b.append(to_binary(UadpDiscoveryResponse, self.Payload))
        elif isinstance(self.Payload, UadpChunk):
            b.append(self.Payload.to_binary())
        else:
            b.append(_pack_payload(self.Payload, bool(self.DataSetPayloadHeader)))
        return b"".join(b)

    @staticmethod
    def from_binary(data: Buffer) -> UadpNetworkMessage:
        msg = UadpNetworkMessage()
        flags, msg.Header = UadpHeader.from_binary(data)
        if MessageHeaderFlags.GROUP_HEADER in flags:
            msg.GroupHeader = UadpGroupHeader.from_binary(data)
        if MessageHeaderFlags.PAYLOAD_HEADER in flags:
            sz = Primitives.Byte.unpack(data)
            msg.DataSetPayloadHeader = [Primitives.UInt16.unpack(data) for _ in range(sz)]
        if MessageHeaderFlags.TIMESTAMP in flags:
            d = Primitives.DateTime.unpack(data)
            msg.Timestamp = DateTime(
                d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, d.tzinfo, fold=d.fold
            )
        if MessageHeaderFlags.PICO_SECONDS in flags:
            msg.PicoSeconds = Primitives.UInt16.unpack(data)
        if MessageHeaderFlags.PROMOTEDFIELDS in flags:
            promoted_sz = Primitives.UInt16.unpack(data)
            msg.PromotedFields = [unpack_uatype(VariantType.Variant, data) for _ in range(promoted_sz)]
            # the count of DataSetMessages must be = 1
        if MessageHeaderFlags.CHUNK in flags:
            msg.Payload = UadpChunk.from_binary(data)
        elif MessageHeaderFlags.DISCOVERYREQUEST in flags:
            msg.Payload = from_binary(UadpDiscoveryRequest, data)
        elif MessageHeaderFlags.DISCOVERYRESPONSE in flags:
            msg.Payload = from_binary(UadpDiscoveryResponse, data)
        else:
            # NetworkMessage type defaults to DataSetMessage payload.
            # Per OPC Unified Architecture, Part 14 7.2.2.3.2, field Count,
            # such a "NetworkMessage shall contain at least one DataSetMessages."
            count = len(msg.DataSetPayloadHeader)
            # But, if there was no payload header, the subscriber must know the count and sizes
            # from the DataSetReader configuration; the GroupHeader is the default way
            # to reference that configuration (via WriterGroupId/NetworkMessageNumber).
            # We do not support this yet, and assume count=1.
            msg.Payload = _unpack_payload(data, count)
        return msg
