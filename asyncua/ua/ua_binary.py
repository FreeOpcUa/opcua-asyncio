"""
Binary protocol specific functions and constants
"""

import functools
import struct
import logging
from typing import Any, Callable
import typing
import uuid
from enum import Enum, IntFlag
from dataclasses import is_dataclass, fields
from asyncua import ua
from .uaerrors import UaError
from ..common.utils import Buffer
from .uatypes import type_is_list, type_is_union, type_from_list, types_from_union, type_allow_subclass

logger = logging.getLogger('__name__')


def test_bit(data, offset):
    mask = 1 << offset
    return data & mask


def set_bit(data, offset):
    mask = 1 << offset
    return data | mask


def unset_bit(data, offset):
    mask = 1 << offset
    return data & ~mask


class _DateTime:
    @staticmethod
    def pack(dt):
        epch = ua.datetime_to_win_epoch(dt)
        return Primitives.Int64.pack(epch)

    @staticmethod
    def unpack(data):
        epch = Primitives.Int64.unpack(data)
        return ua.win_epoch_to_datetime(epch)


class _Bytes:
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


class _String:
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
        return b.decode('utf-8', errors="replace")  # not need to be strict here, this is user data


class _Null:
    @staticmethod
    def pack(data):
        return b''

    @staticmethod
    def unpack(data):
        return None


class _Guid:
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


class _Primitive1:
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
            logger.warning('ua_binary.py > _Primitive1 > pack_array > data: %s is not a instance of "list"!', data)
            return Primitives.Int32.pack(-1)  # to prevent crashing while runtime
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


@functools.lru_cache(maxsize=None)
def create_uatype_serializer(vtype):
    if hasattr(Primitives, vtype.name):
        return getattr(Primitives, vtype.name).pack
    if vtype.value > 25:
        return Primitives.Bytes.pack
    if vtype == ua.VariantType.ExtensionObject:
        return extensionobject_to_binary
    if vtype in (ua.VariantType.NodeId, ua.VariantType.ExpandedNodeId):
        return nodeid_to_binary
    if vtype == ua.VariantType.Variant:
        return variant_to_binary
    return struct_to_binary


def pack_uatype(vtype, value):
    return create_uatype_serializer(vtype)(value)


@functools.lru_cache(maxsize=None)
def _create_uatype_deserializer(vtype):
    if hasattr(Primitives, vtype.name):
        return getattr(Primitives, vtype.name).unpack
    if vtype.value > 25:
        return Primitives.Bytes.unpack
    if vtype == ua.VariantType.ExtensionObject:
        return extensionobject_from_binary
    if vtype in (ua.VariantType.NodeId, ua.VariantType.ExpandedNodeId):
        return nodeid_from_binary
    if vtype == ua.VariantType.Variant:
        return variant_from_binary
    if hasattr(ua, vtype.name):
        cls = getattr(ua, vtype.name)
        return _create_dataclass_deserializer(cls)
    raise UaError(f'Cannot unpack unknown variant type {vtype}')


def unpack_uatype(vtype, data):
    return _create_uatype_deserializer(vtype)(data)


@functools.lru_cache(maxsize=None)
def create_uatype_array_serializer(vtype):
    if hasattr(Primitives1, vtype.name):
        data_type = getattr(Primitives1, vtype.name)
        return data_type.pack_array
    serializer = create_uatype_serializer(vtype)

    def serialize(array):
        if array is None:
            return b'\xff\xff\xff\xff'
        length = Primitives.Int32.pack(len(array))
        return length + b"".join(serializer(val) for val in array)
    return serialize


def pack_uatype_array(vtype, array):
    return create_uatype_array_serializer(vtype)(array)


def unpack_uatype_array(vtype, data):
    return _create_uatype_array_deserializer(vtype)(data)


@functools.lru_cache(maxsize=None)
def _create_uatype_array_deserializer(vtype):
    if hasattr(Primitives1, vtype.name):  # Fast primitive array deserializer
        unpack_array = getattr(Primitives1, vtype.name).unpack_array
    else:  # Revert to slow serial unpacking.
        deserialize_element = _create_uatype_deserializer(vtype)

        def unpack_array(data, length):
            return (deserialize_element(data) for _ in range(length))

    def deserialize(data):
        length = Primitives.Int32.unpack(data)
        if length == -1:
            return None
        # Remark: works without tuple conversion to list.
        return list(unpack_array(data, length))
    return deserialize


def field_serializer(ftype) -> Callable[[Any], bytes]:
    is_optional = type_is_union(ftype)
    uatype = ftype
    if is_optional:
        uatype = types_from_union(uatype)[0]
    if type_is_list(uatype):
        return create_list_serializer(type_from_list(uatype))
    else:
        serializer = create_type_serializer(uatype)
        if is_optional:
            return lambda val: b'' if val is None else serializer(val)
        else:
            return serializer


@functools.lru_cache(maxsize=None)
def create_dataclass_serializer(dataclazz):
    """Given a dataclass, return a function that serializes instances of this dataclass"""
    data_fields = fields(dataclazz)
    # TODO: adding the 'ua' module to the globals to resolve the type hints might not be enough.
    #       its possible that the type annotations also refere to classes defined in other modules.
    resolved_fieldtypes = typing.get_type_hints(dataclazz, {'ua': ua})
    for f in data_fields:
        f.type = resolved_fieldtypes[f.name]

    if issubclass(dataclazz, ua.UaUnion):
        # Union is a class with Encoding and Value field
        # the value is depended of encoding
        union_field = next(filter(lambda f: type_is_union(f.type), data_fields))
        encoding_funcs = [field_serializer(types) for types in types_from_union(union_field.type)]

        def union_serialize(obj):
            bin = Primitives.UInt32.pack(obj.Encoding)
            # 0 => None
            # 1.. => union fields
            if obj.Encoding > 0 and obj.Encoding <= len(encoding_funcs):
                serialize = encoding_funcs[obj.Encoding - 1]
                return b"".join([bin, serialize(obj.Value)])
            return bin
        return union_serialize
    option_fields_encodings = [  # Name and binary encoding of optional fields
        (field.name, 1 << enc_count)
        for enc_count, field
        in enumerate(filter(lambda f: type_is_union(f.type), data_fields))
    ]

    def enc_value(obj):
        enc = 0
        for name, enc_val in option_fields_encodings:
            if obj.__dict__[name] is not None:
                enc |= enc_val
        return enc

    encoding_functions = [(f.name, field_serializer(f.type)) for f in data_fields]

    def serialize(obj):
        return b''.join(
            serializer(enc_value(obj)) if name == 'Encoding'
            else serializer(obj.__dict__[name])
            for name, serializer in encoding_functions
        )

    return serialize


def struct_to_binary(obj):
    serializer = create_dataclass_serializer(obj.__class__)
    return serializer(obj)


def create_enum_serializer(uatype):
    if issubclass(uatype, IntFlag):
        typename = 'UInt32'
        if hasattr(uatype, 'datatype'):
            typename = uatype.datatype()
        return getattr(Primitives, typename).pack
    elif isinstance(uatype, Enum):
        return lambda val: Primitives.Int32.pack(val.value)
    return Primitives.Int32.pack


@functools.lru_cache(maxsize=None)
def create_type_serializer(uatype):
    """Create a binary serialization function for the given UA type"""
    if type_allow_subclass(uatype):
        return extensionobject_to_binary
    if type_is_list(uatype):
        return create_list_serializer(type_from_list(uatype))
    if hasattr(Primitives, uatype.__name__):
        return getattr(Primitives, uatype.__name__).pack
    if issubclass(uatype, Enum):
        return create_enum_serializer(uatype)
    if hasattr(ua.VariantType, uatype.__name__):
        vtype = getattr(ua.VariantType, uatype.__name__)
        return create_uatype_serializer(vtype)
    if issubclass(uatype, ua.NodeId):
        return nodeid_to_binary
    if issubclass(uatype, ua.Variant):
        return variant_to_binary
    if is_dataclass(uatype):
        return create_dataclass_serializer(uatype)
    raise UaError(f'No known way to pack value of type {uatype} to ua binary')


def to_binary(uatype, val):
    return create_type_serializer(uatype)(val)


@functools.lru_cache(maxsize=None)
def create_list_serializer(uatype) -> Callable[[Any], bytes]:
    """
    Given a type, return a function that takes a list of instances
    of that type and serializes it.
    """
    if hasattr(Primitives1, uatype.__name__):
        data_type = getattr(Primitives1, uatype.__name__)
        return data_type.pack_array
    type_serializer = create_type_serializer(uatype)
    none_val = Primitives.Int32.pack(-1)

    def serialize(val):
        if val is None:
            return none_val
        data_size = Primitives.Int32.pack(len(val))
        return data_size + b''.join(type_serializer(el) for el in val)
    return serialize


def list_to_binary(uatype, val):
    return create_list_serializer(uatype)(val)


def nodeid_to_binary(nodeid):
    if nodeid.NodeIdType == ua.NodeIdType.TwoByte:
        data = struct.pack('<BB', nodeid.NodeIdType.value, nodeid.Identifier)
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
    uri = None
    server_idx = None

    if nidtype == ua.NodeIdType.TwoByte:
        identifier = ord(data.read(1))
        nidx = 0
    elif nidtype == ua.NodeIdType.FourByte:
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
    if test_bit(encoding, 6):
        server_idx = Primitives.UInt32.unpack(data)

    if uri is not None or server_idx is not None:
        return ua.ExpandedNodeId(identifier, nidx, nidtype, uri, server_idx)
    return ua.NodeId(identifier, nidx, nidtype)


def variant_to_binary(var):
    encoding = var.VariantType.value & 0b0011_1111
    if var.is_array or isinstance(var.Value, (list, tuple)):
        body = pack_uatype_array(var.VariantType, ua.flatten(var.Value))
        if var.Dimensions is None:
            encoding |= 0b1000_0000
        else:
            encoding |= 0b1100_0000
            body += pack_uatype_array(ua.VariantType.Int32, var.Dimensions)
    else:
        body = pack_uatype(var.VariantType, var.Value)
    return Primitives.Byte.pack(encoding) + body


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
        if value is not None:
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
        return ua.ExtensionObject()
    if typeid in ua.extension_objects_by_typeid:
        cls = ua.extension_objects_by_typeid[typeid]
        if body is None:
            raise UaError(f'parsing ExtensionObject {cls.__name__} without data')
        return from_binary(cls, body)
    if body is not None:
        body_data = body.read(len(body))
    else:
        body_data = None
    e = ua.ExtensionObject(
        TypeId=typeid,
        Body=body_data,
    )
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


def _create_list_deserializer(uatype):
    element_deserializer = _create_type_deserializer(uatype)

    def _deserialize(data):
        size = Primitives.Int32.unpack(data)
        return [element_deserializer(data) for _ in range(size)]
    return _deserialize


@functools.lru_cache(maxsize=None)
def _create_type_deserializer(uatype):
    if type_is_union(uatype):
        return _create_type_deserializer(types_from_union(uatype)[0])
    if type_is_list(uatype):
        utype = type_from_list(uatype)
        if hasattr(ua.VariantType, utype.__name__):
            vtype = getattr(ua.VariantType, utype.__name__)
            return _create_uatype_array_deserializer(vtype)
        else:
            return _create_list_deserializer(utype)
    if hasattr(ua.VariantType, uatype.__name__):
        vtype = getattr(ua.VariantType, uatype.__name__)
        return _create_uatype_deserializer(vtype)
    if hasattr(Primitives, uatype.__name__):
        return getattr(Primitives, uatype.__name__).unpack
    return _create_dataclass_deserializer(uatype)


def create_enum_deserializer(uatype):
    if issubclass(uatype, IntFlag):
        typename = 'UInt32'
        if hasattr(uatype, 'datatype'):
            typename = uatype.datatype()
        unpack = getattr(Primitives, typename).unpack
        return lambda val: uatype(unpack(val))
    return lambda val: uatype(Primitives.Int32.unpack(val))


def from_binary(uatype, data):
    """
    unpack data given an uatype as a string or a python dataclass using ua types
    """
    return _create_type_deserializer(uatype)(data)


@functools.lru_cache(maxsize=None)
def _create_dataclass_deserializer(objtype):
    if isinstance(objtype, str):
        objtype = getattr(ua, objtype)
    if issubclass(objtype, Enum):
        return create_enum_deserializer(objtype)
    if issubclass(objtype, ua.UaUnion):
        # unions are just objects with encoding and value field
        typefields = fields(objtype)
        union_types = next(types_from_union(f.type) for f in typefields if f.name == "Value")
        field_deserializers = [_create_type_deserializer(type) for type in union_types]
        byte_decode = next(_create_type_deserializer(f.type) for f in typefields if f.name == "Encoding")

        def decode_union(data):
            enc = byte_decode(data)
            obj = objtype()
            obj.Encoding = enc
            # encoding value
            # 0 => empty union
            # 1..union_fiels => index of the
            if enc > 0 and enc <= len(field_deserializers):
                obj.Value = field_deserializers[enc - 1](data)
            else:
                obj.Value = None
            return obj
        return decode_union
    enc_count = 0
    field_deserializers = []
    # TODO: adding the 'ua' module to the globals to resolve the type hints might not be enough.
    #       its possible that the type annotations also refere to classes defined in other modules.
    resolved_fieldtypes = typing.get_type_hints(objtype, {'ua': ua})
    for field in fields(objtype):
        optional_enc_bit = 0
        field_type = resolved_fieldtypes[field.name]
        subtypes = type_allow_subclass(field.type)
        # if our member has a switch and it is not set we will need to skip it
        if type_is_union(field_type):
            optional_enc_bit = 1 << enc_count
            enc_count += 1
        if subtypes:
            deserialize_field = extensionobject_from_binary
        else:
            deserialize_field = _create_type_deserializer(field_type)
        field_deserializers.append((field, optional_enc_bit, deserialize_field))

    def decode(data):
        kwargs = {}
        enc = 0
        for field, optional_enc_bit, deserialize_field in field_deserializers:
            if field.name == "Encoding":
                enc = deserialize_field(data)
            elif optional_enc_bit == 0 or enc & optional_enc_bit:
                kwargs[field.name] = deserialize_field(data)
        return objtype(**kwargs)
    return decode


def struct_from_binary(objtype, data):
    """
    unpack an ua struct. Arguments are an objtype as Python dataclass or string
    """
    return _create_dataclass_deserializer(objtype)(data)


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
