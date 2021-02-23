"""
Binary protocol specific functions and constants
"""

import struct
import logging
import uuid
from enum import IntEnum, Enum
from typing import get_origin, Union, get_args
from dataclasses import is_dataclass, fields

from .uaerrors import UaError
from ..common.utils import Buffer
from asyncua import ua

logger = logging.getLogger('__name__')


def _is_union(uatype):
    return get_origin(uatype) == Union


def _is_list(uatype):
    return get_origin(uatype) == list


def _from_union(uatype, origin=None):
    if origin is None:
        origin = get_origin(uatype)
    if origin == Union:
        # need to find out what real type is
        for subtype in get_args(uatype):
            if subtype is not None.__class__:  # FIXME: strange comparison...
                return subtype
        else:
            ValueError(f"Union {uatype} seems to only contain None")


def _from_list(uatype):
    return get_args(uatype)[0]


def test_bit(data, offset):
    mask = 1 << offset
    return data & mask


def set_bit(data, offset):
    mask = 1 << offset
    return data | mask


def unset_bit(data, offset):
    mask = 1 << offset
    return data & ~mask


class _DateTime(object):
    @staticmethod
    def pack(dt):
        epch = ua.datetime_to_win_epoch(dt)
        return Primitives.Int64.pack(epch)

    @staticmethod
    def unpack(data):
        epch = Primitives.Int64.unpack(data)
        return ua.win_epoch_to_datetime(epch)


class _Bytes(object):
    @staticmethod
    def pack(data):
        if data is None:
            return Primitives.Int32.pack(-1)
        length = len(data)
        return Primitives.Int32.pack(length) + data

    @staticmethod
    def unpack(data):
        length = Primitives.Int32.unpack(data)
        if length == -1:
            return None
        return data.read(length)


class _String(object):
    @staticmethod
    def pack(string):
        if string is not None:
            string = string.encode('utf-8')
        return _Bytes.pack(string)

    @staticmethod
    def unpack(data):
        b = _Bytes.unpack(data)
        if b is None:
            return b
        return b.decode('utf-8')


class _Null(object):
    @staticmethod
    def pack(data):
        return b''

    @staticmethod
    def unpack(data):
        return None


class _Guid(object):
    @staticmethod
    def pack(guid):
        # convert python UUID 6 field format to OPC UA 4 field format
        f1 = Primitives.UInt32.pack(guid.time_low)
        f2 = Primitives.UInt16.pack(guid.time_mid)
        f3 = Primitives.UInt16.pack(guid.time_hi_version)
        f4a = Primitives.Byte.pack(guid.clock_seq_hi_variant)
        f4b = Primitives.Byte.pack(guid.clock_seq_low)
        f4c = struct.pack('>Q', guid.node)[2:8]  # no primitive .pack available for 6 byte int
        f4 = f4a + f4b + f4c
        # concat byte fields
        b = f1 + f2 + f3 + f4

        return b

    @staticmethod
    def unpack(data):
        # convert OPC UA 4 field format to python UUID bytes
        f1 = struct.pack('>I', Primitives.UInt32.unpack(data))
        f2 = struct.pack('>H', Primitives.UInt16.unpack(data))
        f3 = struct.pack('>H', Primitives.UInt16.unpack(data))
        f4 = data.read(8)
        # concat byte fields
        b = f1 + f2 + f3 + f4

        return uuid.UUID(bytes=b)


class _Primitive1(object):
    def __init__(self, fmt):
        self._fmt = fmt
        st = struct.Struct(fmt.format(1))
        self.size = st.size
        self.format = st.format

    def pack(self, data):
        return struct.pack(self.format, data)

    def unpack(self, data):
        return struct.unpack(self.format, data.read(self.size))[0]

    def pack_array(self, data):
        if data is None:
            return Primitives.Int32.pack(-1)
        if not isinstance(data, list):
            logger.warning(f'ua_binary.py > _Primitive1 > pack_array > data: {data} is not a instance of "list"!')
            return Primitives.Int32.pack(-1) # to prevent crashing while runtime
        size_data = Primitives.Int32.pack(len(data))
        return size_data + struct.pack(self._fmt.format(len(data)), *data)

    def unpack_array(self, data, length):
        if length == -1:
            return None
        if length == 0:
            return ()
        return struct.unpack(self._fmt.format(length), data.read(self.size * length))


class Primitives1:
    SByte = _Primitive1('<{:d}b')
    Int16 = _Primitive1('<{:d}h')
    Int32 = _Primitive1('<{:d}i')
    Int64 = _Primitive1('<{:d}q')
    Byte = _Primitive1('<{:d}B')
    Char = Byte
    UInt16 = _Primitive1('<{:d}H')
    UInt32 = _Primitive1('<{:d}I')
    UInt64 = _Primitive1('<{:d}Q')
    Boolean = _Primitive1('<{:d}?')
    Double = _Primitive1('<{:d}d')
    Float = _Primitive1('<{:d}f')


class Primitives(Primitives1):
    Null = _Null()
    String = _String()
    Bytes = _Bytes()
    ByteString = _Bytes()
    CharArray = _String()
    DateTime = _DateTime()
    Guid = _Guid()


def pack_uatype(vtype, value):
    if hasattr(Primitives, vtype.name):
        return getattr(Primitives, vtype.name).pack(value)
    elif vtype.value > 25:
        return Primitives.Bytes.pack(value)
    elif vtype == ua.VariantType.ExtensionObject:
        return extensionobject_to_binary(value)
    elif vtype in (ua.VariantType.NodeId, ua.VariantType.ExpandedNodeId):
        return nodeid_to_binary(value)
    elif vtype == ua.VariantType.Variant:
        return variant_to_binary(value)
    else:
        return struct_to_binary(value)


def unpack_uatype(vtype, data):
    if hasattr(Primitives, vtype.name):
        st = getattr(Primitives, vtype.name)
        return st.unpack(data)
    elif vtype.value > 25:
        return Primitives.Bytes.unpack(data)
    elif vtype == ua.VariantType.ExtensionObject:
        return extensionobject_from_binary(data)
    elif vtype in (ua.VariantType.NodeId, ua.VariantType.ExpandedNodeId):
        return nodeid_from_binary(data)
    elif vtype == ua.VariantType.Variant:
        return variant_from_binary(data)
    else:
        if hasattr(ua, vtype.name):
            cls = getattr(ua, vtype.name)
            return struct_from_binary(cls, data)
        else:
            raise UaError(f'Cannot unpack unknown variant type {vtype}')


def pack_uatype_array(vtype, array):
    if hasattr(Primitives1, vtype.name):
        data_type = getattr(Primitives1, vtype.name)
        return data_type.pack_array(array)
    if array is None:
        return b'\xff\xff\xff\xff'
    length = len(array)
    b = [pack_uatype(vtype, val) for val in array]
    b.insert(0, Primitives.Int32.pack(length))
    return b"".join(b)


def unpack_uatype_array(vtype, data):
    length = Primitives.Int32.unpack(data)
    if length == -1:
        return None
    elif hasattr(Primitives1, vtype.name):
        data_type = getattr(Primitives1, vtype.name)
        # Remark: works without tuple conversion to list.
        return list(data_type.unpack_array(data, length))
    else:
        # Revert to slow serial unpacking.
        return [unpack_uatype(vtype, data) for _ in range(length)]


def struct_to_binary(obj):
    packet = []
    has_switch = hasattr(obj, 'ua_switches')
    if has_switch:
        container_val = 0
        for name, switch in obj.ua_switches.items():
            member = getattr(obj, name)
            container_name, idx = switch
            if member is not None:
                container_val = container_val | 1 << idx
        setattr(obj, container_name, container_val)
    for field in fields(obj):
        uatype = field.type
        if field.name == "Encoding":
            packet.append(Primitives.Byte.pack(obj.Encoding))
            continue
        val = getattr(obj, field.name)
        if _is_union(uatype):
            uatype = _from_union(uatype)
        if _is_list(uatype):
            packet.append(list_to_binary(_from_list(uatype), val))
        else:
            if has_switch and val is None and field.name in obj.ua_switches:
                pass
            else:
                packet.append(to_binary(uatype, val))
    return b''.join(packet)


def to_binary(uatype, val):
    """
    Pack a python object to binary given a type hint
    """
    if _is_list(uatype):
        return list_to_binary(_from_list(uatype), val)
    elif hasattr(Primitives, uatype.__name__):
        return getattr(Primitives, uatype.__name__).pack(val)
    elif isinstance(val, (IntEnum, Enum)):
        return Primitives.UInt32.pack(val.value)
    elif hasattr(ua.VariantType, uatype.__name__):
        vtype = getattr(ua.VariantType, uatype.__name__)
        return pack_uatype(vtype, val)
    elif isinstance(val, ua.NodeId):
        return nodeid_to_binary(val)
    elif isinstance(val, ua.Variant):
        return variant_to_binary(val)
    elif is_dataclass(val):
        return struct_to_binary(val)
    else:
        raise UaError(f'No known way to pack {val} of type {uatype} to ua binary')


def list_to_binary(uatype, val):
    if val is None:
        return Primitives.Int32.pack(-1)
    if hasattr(Primitives1, uatype.__name__):
        data_type = getattr(Primitives1, uatype.__name__)
        return data_type.pack_array(val)
    data_size = Primitives.Int32.pack(len(val))
    pack = [to_binary(uatype, el) for el in val]
    pack.insert(0, data_size)
    return b''.join(pack)


def nodeid_to_binary(nodeid):
    if nodeid.NodeIdType == ua.NodeIdType.TwoByte:
        return struct.pack('<BB', nodeid.NodeIdType.value, nodeid.Identifier)
    elif nodeid.NodeIdType == ua.NodeIdType.FourByte:
        data = struct.pack('<BBH', nodeid.NodeIdType.value, nodeid.NamespaceIndex, nodeid.Identifier)
    elif nodeid.NodeIdType == ua.NodeIdType.Numeric:
        data = struct.pack('<BHI', nodeid.NodeIdType.value, nodeid.NamespaceIndex, nodeid.Identifier)
    elif nodeid.NodeIdType == ua.NodeIdType.String:
        data = struct.pack('<BH', nodeid.NodeIdType.value, nodeid.NamespaceIndex) + \
            Primitives.String.pack(nodeid.Identifier)
    elif nodeid.NodeIdType == ua.NodeIdType.ByteString:
        data = struct.pack('<BH', nodeid.NodeIdType.value, nodeid.NamespaceIndex) + \
            Primitives.Bytes.pack(nodeid.Identifier)
    elif nodeid.NodeIdType == ua.NodeIdType.Guid:
        data = struct.pack('<BH', nodeid.NodeIdType.value, nodeid.NamespaceIndex) + \
               Primitives.Guid.pack(nodeid.Identifier)
    else:
        raise UaError(f'Unknown NodeIdType: {nodeid.NodeIdType} for NodeId: {nodeid}')
    # Add NamespaceUri and ServerIndex in case we have an ExpandedNodeId
    if hasattr(nodeid, "NamespaceUri") and nodeid.NamespaceUri:
        data = bytearray(data)
        data[0] = set_bit(data[0], 7)
        data.extend(Primitives.String.pack(nodeid.NamespaceUri))
    if hasattr(nodeid, "ServerIndex") and nodeid.ServerIndex:
        if not isinstance(data, bytearray):
            data = bytearray(data)
        data[0] = set_bit(data[0], 6)
        data.extend(Primitives.UInt32.pack(nodeid.ServerIndex))
    return data


def nodeid_from_binary(data):
    encoding = ord(data.read(1))
    nidtype = ua.NodeIdType(encoding & 0b00111111)
    expanded = False

    if nidtype == ua.NodeIdType.TwoByte:
        identifier = ord(data.read(1))
        return ua.TwoByteNodeId(identifier)
    if nidtype == ua.NodeIdType.FourByte:
        nidx, identifier = struct.unpack("<BH", data.read(3))
    elif nidtype == ua.NodeIdType.Numeric:
        nidx, identifier = struct.unpack("<HI", data.read(6))
    elif nidtype == ua.NodeIdType.String:
        nidx = Primitives.UInt16.unpack(data)
        identifier = Primitives.String.unpack(data)
    elif nidtype == ua.NodeIdType.ByteString:
        nidx = Primitives.UInt16.unpack(data)
        identifier = Primitives.Bytes.unpack(data)
    elif nidtype == ua.NodeIdType.Guid:
        nidx = Primitives.UInt16.unpack(data)
        identifier = Primitives.Guid.unpack(data)
    else:
        raise UaError(f'Unknown NodeId encoding: {nidtype}')

    if test_bit(encoding, 7):
        uri = Primitives.String.unpack(data)
        expanded = True
    if test_bit(encoding, 6):
        server_idx = Primitives.UInt32.unpack(data)
        expanded = True

    if expanded:
        return ua.ExpandedNodeId(identifier, nidx, nidtype, uri, server_idx)
    return ua.NodeId(identifier, nidx, nidtype)


def variant_to_binary(var):
    b = []
    encoding = var.VariantType.value & 0b111111
    if var.is_array or isinstance(var.Value, (list, tuple)):
        var.is_array = True
        encoding = set_bit(encoding, 7)
        if var.Dimensions is not None:
            encoding = set_bit(encoding, 6)
        b.append(Primitives.Byte.pack(encoding))
        b.append(pack_uatype_array(var.VariantType, ua.flatten(var.Value)))
        if var.Dimensions is not None:
            b.append(pack_uatype_array(ua.VariantType.Int32, var.Dimensions))
    else:
        b.append(Primitives.Byte.pack(encoding))
        b.append(pack_uatype(var.VariantType, var.Value))

    return b"".join(b)


def variant_from_binary(data):
    dimensions = None
    array = False
    encoding = ord(data.read(1))
    int_type = encoding & 0b00111111
    vtype = ua.datatype_to_varianttype(int_type)
    if test_bit(encoding, 7):
        value = unpack_uatype_array(vtype, data)
        array = True
    else:
        value = unpack_uatype(vtype, data)
    if test_bit(encoding, 6):
        dimensions = unpack_uatype_array(ua.VariantType.Int32, data)
        value = _reshape(value, dimensions)
    return ua.Variant(value, vtype, dimensions, is_array=array)


def _reshape(flat, dims):
    subdims = dims[1:]
    subsize = 1
    for i in subdims:
        if i == 0:
            i = 1
        subsize *= i
    while dims[0] * subsize > len(flat):
        flat.append([])
    if not subdims or subdims == [0]:
        return flat
    return [_reshape(flat[i:i + subsize], subdims) for i in range(0, len(flat), subsize)]


def extensionobject_from_binary(data):
    """
    Convert binary-coded ExtensionObject to a Python object.
    Returns an object, or None if TypeId is zero
    """
    typeid = nodeid_from_binary(data)
    encoding = ord(data.read(1))
    body = None
    if encoding & (1 << 0):
        length = Primitives.Int32.unpack(data)
        if length < 1:
            body = Buffer(b"")
        else:
            body = data.copy(length)
            data.skip(length)
    if typeid.Identifier == 0:
        return None
    elif typeid in ua.extension_objects_by_typeid:
        cls = ua.extension_objects_by_typeid[typeid]
        if body is None:
            raise UaError(f'parsing ExtensionObject {cls.__name__} without data')
        return from_binary(cls, body)
    else:
        e = ua.ExtensionObject()
        e.TypeId = typeid
        e.Encoding = encoding
        if body is not None:
            e.Body = body.read(len(body))
        return e


def extensionobject_to_binary(obj):
    """
    Convert Python object to binary-coded ExtensionObject.
    If obj is None, convert to empty ExtensionObject (TypeId=0, no Body).
    Returns a binary string
    """
    if isinstance(obj, ua.ExtensionObject):
        return struct_to_binary(obj)
    if obj is None:
        type_id = ua.NodeId()
        encoding = 0
        body = None
    else:
        type_id = ua.extension_object_typeids[obj.__class__.__name__]
        encoding = 0x01
        body = struct_to_binary(obj)
    packet = [
        nodeid_to_binary(type_id),
        Primitives.Byte.pack(encoding),
    ]
    if body:
        packet.append(Primitives.Bytes.pack(body))
    return b''.join(packet)


def from_binary(uatype, data):
    """
    unpack data given an uatype as a string or a python class having a ua_types member
    """
    if _is_union(uatype):
        uatype = _from_union(uatype)
    if _is_list(uatype):
        utype = _from_list(uatype)
        if hasattr(ua.VariantType, utype.__name__):
            vtype = getattr(ua.VariantType, utype.__name__)
            return unpack_uatype_array(vtype, data)
        size = Primitives.Int32.unpack(data)
        return [from_binary(utype, data) for _ in range(size)]
    elif hasattr(ua.VariantType, uatype.__name__):
        vtype = getattr(ua.VariantType, uatype.__name__)
        return unpack_uatype(vtype, data)
    elif hasattr(Primitives, uatype.__name__):
        return getattr(Primitives, uatype.__name__).unpack(data)
    else:
        return struct_from_binary(uatype, data)


def struct_from_binary(objtype, data):
    """
    unpack an ua struct. Arguments are an objtype as Python class or string
    """
    if isinstance(objtype, str):
        objtype = getattr(ua, objtype)
    if issubclass(objtype, Enum):
        return objtype(Primitives.UInt32.unpack(data))
    obj = objtype()
    for field in fields(obj):
        # if our member has a switch and it is not set we skip it
        if hasattr(obj, "ua_switches") and field.name in obj.ua_switches:
            container_name, idx = obj.ua_switches[field.name]
            val = getattr(obj, container_name)
            if not test_bit(val, idx):
                continue
        val = from_binary(field.type, data)
        setattr(obj, field.name, val)
    return obj


def header_to_binary(hdr):
    b = [struct.pack("<3ss", hdr.MessageType, hdr.ChunkType)]
    size = hdr.body_size + 8
    if hdr.MessageType in (ua.MessageType.SecureOpen, ua.MessageType.SecureClose, ua.MessageType.SecureMessage):
        size += 4
    b.append(Primitives.UInt32.pack(size))
    if hdr.MessageType in (ua.MessageType.SecureOpen, ua.MessageType.SecureClose, ua.MessageType.SecureMessage):
        b.append(Primitives.UInt32.pack(hdr.ChannelId))
    return b"".join(b)


def header_from_binary(data):
    hdr = ua.Header()
    hdr.MessageType, hdr.ChunkType, hdr.packet_size = struct.unpack("<3scI", data.read(8))
    hdr.body_size = hdr.packet_size - 8
    if hdr.MessageType in (ua.MessageType.SecureOpen, ua.MessageType.SecureClose, ua.MessageType.SecureMessage):
        hdr.body_size -= 4
        hdr.ChannelId = Primitives.UInt32.unpack(data)
        hdr.header_size = 12
    return hdr


def uatcp_to_binary(message_type, message):
    """
    Convert OPC UA TCP message (see OPC UA specs Part 6, 7.1) to binary.
    The only supported types are Hello, Acknowledge and ErrorMessage
    """
    header = ua.Header(message_type, ua.ChunkType.Single)
    binmsg = struct_to_binary(message)
    header.body_size = len(binmsg)
    return header_to_binary(header) + binmsg
