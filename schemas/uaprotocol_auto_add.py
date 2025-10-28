def extensionobject_from_binary(data):
    """
    Convert binary-coded ExtensionObject to a Python object.
    Returns an object, or None if TypeId is zero
    """
    TypeId = NodeId.from_binary(data)
    Encoding = ord(data.read(1))
    body = None
    if Encoding & (1 << 0):
        length = uabin.Primitives.Int32.unpack(data)
        if length < 1:
            body = Buffer(b"")
        else:
            body = data.copy(length)
            data.skip(length)
    if TypeId.Identifier == 0:
        return None
    elif TypeId.Identifier not in ExtensionClasses:
        e = ExtensionObject()
        e.TypeId = TypeId
        e.Encoding = Encoding
        if body is not None:
            e.Body = body.read(len(body))
        return e
    klass = ExtensionClasses[TypeId.Identifier]
    if body is None:
        raise UaError(f"parsing ExtensionObject {klass.__name__} without data")
    return klass.from_binary(body)


def extensionobject_to_binary(obj):
    """
    Convert Python object to binary-coded ExtensionObject.
    If obj is None, convert to empty ExtensionObject (TypeId = 0, no Body).
    Returns a binary string
    """
    if isinstance(obj, ExtensionObject):
        return obj.to_binary()
    TypeId = NodeId()
    Encoding = 0
    Body = None
    if obj is not None:
        TypeId = FourByteNodeId(getattr(ObjectIds, f"{obj.__class__.__name__}_Encoding_DefaultBinary"))
        Encoding |= 1 << 0
        Body = obj.to_binary()
    packet = []
    packet.append(TypeId.to_binary())
    packet.append(uabin.Primitives.UInt8.pack(Encoding))
    if Body:
        packet.append(uabin.Primitives.Bytes.pack(Body))
    return b"".join(packet)
