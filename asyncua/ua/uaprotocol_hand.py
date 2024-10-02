import struct
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Optional

from asyncua.common.connection import MessageChunk
from asyncua.ua import uaprotocol_auto as auto
from asyncua.ua import uatypes
from asyncua.common import utils

if TYPE_CHECKING:
    from asyncua.common.connection import MessageChunk
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

OPC_TCP_SCHEME = 'opc.tcp'


@dataclass
class Hello:
    ProtocolVersion: uatypes.UInt32 = 0
    # the following values could be set to 0 (meaning no limits)
    # unfortunately many servers do not support it
    # even newer version of prosys is broken,
    # so we set then to a high value known to work most places
    ReceiveBufferSize: uatypes.UInt32 = 2**31 - 1
    SendBufferSize: uatypes.UInt32 = 2**31 - 1
    MaxMessageSize: uatypes.UInt32 = 2**31 - 1
    MaxChunkCount: uatypes.UInt32 = 2**31 - 1
    EndpointUrl: uatypes.String = ""


@dataclass
class MessageType:
    Invalid: bytes = b'INV'  # FIXME: check value
    Hello: bytes = b'HEL'
    Acknowledge: bytes = b'ACK'
    Error: bytes = b'ERR'
    SecureOpen: bytes = b'OPN'
    SecureClose: bytes = b'CLO'
    SecureMessage: bytes = b'MSG'


@dataclass
class ChunkType:
    Invalid: bytes = b'0'  # FIXME check
    Single: bytes = b'F'
    Intermediate: bytes = b'C'
    Abort: bytes = b'A'  # when an error occurred and the Message is aborted (body is ErrorMessage)


@dataclass
class Header:
    MessageType: MessageType = None
    ChunkType: ChunkType = None
    ChannelId: int = 0
    body_size = 0
    packet_size = 0
    header_size = 8

    def add_size(self, size):
        self.body_size += size

    @staticmethod
    def max_size():
        return struct.calcsize("<3scII")


@dataclass
class ErrorMessage:
    Error: uatypes.StatusCode = uatypes.StatusCode()
    Reason: uatypes.String = ""


@dataclass
class Acknowledge:
    ProtocolVersion: uatypes.UInt32 = 0
    ReceiveBufferSize: uatypes.UInt32 = 65536
    SendBufferSize: uatypes.UInt32 = 65536
    MaxMessageSize: uatypes.UInt32 = 0  # No limits
    MaxChunkCount: uatypes.UInt32 = 0  # No limits


@dataclass
class AsymmetricAlgorithmHeader:
    SecurityPolicyURI: uatypes.String = 'http://opcfoundation.org/UA/SecurityPolicy#None'
    SenderCertificate: uatypes.ByteString = None
    ReceiverCertificateThumbPrint: uatypes.ByteString = None

    def __str__(self):
        len(self.SenderCertificate) if self.SenderCertificate is not None else None
        size2 = len(self.ReceiverCertificateThumbPrint) if self.ReceiverCertificateThumbPrint is not None else None
        return f'{self.__class__.__name__}(SecurityPolicy:{self.SecurityPolicyURI},' \
               f' certificatesize:{size2}, receiverCertificatesize:{size2} )'

    __repr__ = __str__


@dataclass
class SymmetricAlgorithmHeader:
    TokenId: uatypes.UInt32 = 0

    @staticmethod
    def max_size():
        return struct.calcsize('<I')


@dataclass
class SequenceHeader:
    SequenceNumber: uatypes.UInt32 = None
    RequestId: uatypes.UInt32 = None

    @staticmethod
    def max_size():
        return struct.calcsize('<II')


class CryptographyNone:
    """
    Base class for symmetric/asymmetric cryptography
    """
    def __init__(self):
        pass

    def plain_block_size(self):
        """
        Size of plain text block for block cipher.
        """
        return 1

    def encrypted_block_size(self):
        """
        Size of encrypted text block for block cipher.
        """
        return 1

    def padding(self, size):
        """
        Create padding for a block of given size.
        plain_size = size + len(padding) + signature_size()
        plain_size = N * plain_block_size()
        """
        return b''

    def min_padding_size(self):
        return 0

    def signature_size(self):
        return 0

    def signature(self, data):
        return b''

    def encrypt(self, data):
        return data

    def decrypt(self, data):
        return data

    def vsignature_size(self):
        return 0

    def verify(self, data, signature):
        """
        Verify signature and raise exception if signature is invalid
        """
        pass

    def remove_padding(self, data):
        return data


class SecurityPolicy:
    """
    Base class for security policy
    """
    URI = 'http://opcfoundation.org/UA/SecurityPolicy#None'
    AsymmetricSignatureURI: str = ''
    signature_key_size: int = 0
    symmetric_key_size: int = 0
    secure_channel_nonce_length: int = 0

    def __init__(self, permissions=None):
        self.asymmetric_cryptography = CryptographyNone()
        self.symmetric_cryptography = CryptographyNone()
        self.Mode = auto.MessageSecurityMode.None_
        self.peer_certificate = None
        self.host_certificate = None
        self.user = None
        self.permissions = permissions

    def make_local_symmetric_key(self, secret, seed):
        pass

    def make_remote_symmetric_key(self, secret, seed, lifetime):
        pass


class SecurityPolicyFactory:
    """
    Helper class for creating server-side SecurityPolicy.
    Server has one certificate and private key, but needs a separate
    SecurityPolicy for every client and client's certificate
    """
    def __init__(self,
                 cls=SecurityPolicy,
                 mode=auto.MessageSecurityMode.None_,
                 certificate: "Optional[x509.Certificate]"=None,
                 private_key: "Optional[PrivateKeyTypes]"=None,
                 permission_ruleset=None
    ) -> None:
        self.cls = cls
        self.mode: auto.MessageSecurityMode = mode
        self.certificate: Optional[x509.Certificate] = certificate
        self.private_key: Optional[PrivateKeyTypes] = private_key
        self.permission_ruleset = permission_ruleset

    def matches(self, uri: str, mode=None) -> bool:
        return self.cls.URI == uri and (mode is None or self.mode == mode)

    def create(self, peer_certificate) -> SecurityPolicy:
        if self.cls is SecurityPolicy:
            return self.cls(permissions=self.permission_ruleset)
        else:
            return self.cls(peer_certificate, self.certificate, self.private_key, self.mode, permission_ruleset=self.permission_ruleset)


class Message:
    def __init__(self, chunks: "List[MessageChunk]") -> None:
        self._chunks: List[MessageChunk] = chunks

    def request_id(self) -> auto.UInt32:
        return self._chunks[0].SequenceHeader.RequestId

    def SequenceHeader(self) -> SequenceHeader:
        return self._chunks[0].SequenceHeader

    def SecurityHeader(self) -> SymmetricAlgorithmHeader | AsymmetricAlgorithmHeader:
        return self._chunks[0].SecurityHeader

    def body(self) -> utils.Buffer:
        body = b"".join([c.Body for c in self._chunks])
        return utils.Buffer(body)


# FIXES for missing switchfield in NodeAttributes classes
ana = auto.NodeAttributesMask


@dataclass
class ObjectAttributes(auto.ObjectAttributes):
    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.EventNotifier


@dataclass
class ObjectTypeAttributes(auto.ObjectTypeAttributes):
    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract


@dataclass
class VariableAttributes(auto.VariableAttributes):
    ArrayDimensions: List[uatypes.UInt32] = None
    Historizing: uatypes.Boolean = True
    AccessLevel: uatypes.Byte = auto.AccessLevel.CurrentRead.mask
    UserAccessLevel: uatypes.Byte = auto.AccessLevel.CurrentRead.mask
    SpecifiedAttributes: uatypes.UInt32 = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Value | ana.DataType | ana.ValueRank | ana.ArrayDimensions | ana.AccessLevel | ana.UserAccessLevel | ana.MinimumSamplingInterval | ana.Historizing


@dataclass
class VariableTypeAttributes(auto.VariableTypeAttributes):
    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Value | ana.DataType | ana.ValueRank | ana.ArrayDimensions | ana.IsAbstract


@dataclass
class MethodAttributes(auto.MethodAttributes):
    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Executable | ana.UserExecutable


@dataclass
class ReferenceTypeAttributes(auto.ReferenceTypeAttributes):
    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract | ana.Symmetric | ana.InverseName


# FIXME: changes in that class donnot seem to be part of spec as of 1.04
# not sure what the spec expect, maybe DataTypeDefinition must be set using an extra call...
# maybe it will be part of spec in 1.05??? no ideas
@dataclass
class DataTypeAttributes(auto.DataTypeAttributes):
    DataTypeDefinition: uatypes.ExtensionObject = field(default_factory=auto.ExtensionObject)

    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract | ana.DataTypeDefinition


# we now need to register DataTypeAttributes since we added a new attribute
nid = uatypes.FourByteNodeId(auto.ObjectIds.DataTypeAttributes_Encoding_DefaultBinary)
uatypes.extension_objects_by_typeid[nid] = DataTypeAttributes
uatypes.extension_object_typeids['DataTypeAttributes'] = nid


@dataclass
class ViewAttributes(auto.ViewAttributes):
    def __post_init__(self):
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.ContainsNoLoops | ana.EventNotifier


@dataclass
class Argument(auto.Argument):
    ValueRank: auto.Int32 = -1


@dataclass
class XmlElement:
    """
    An XML element encoded as a UTF-8 string.
    :ivar Value:
    :vartype Value: String
    """

    Value: uatypes.String = ""


# Default is StatusValue -> https://reference.opcfoundation.org/Core/Part4/v105/docs/7.10#Table134
@dataclass
class DataChangeFilter(auto.DataChangeFilter):
    Trigger = auto.DataChangeTrigger.StatusValue
