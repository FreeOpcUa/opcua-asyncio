import struct

from asyncua.ua import uaprotocol_auto as auto
from asyncua.ua import uatypes
from asyncua.common import utils
from asyncua.ua.uatypes import AccessLevel, FrozenClass

OPC_TCP_SCHEME = 'opc.tcp'


class Hello(uatypes.FrozenClass):
    ua_types = (
        ('ProtocolVersion', 'UInt32'), ('ReceiveBufferSize', 'UInt32'), ('SendBufferSize', 'UInt32'),
        ('MaxMessageSize', 'UInt32'), ('MaxChunkCount', 'UInt32'), ('EndpointUrl', 'String'),
    )

    def __init__(self):
        self.ProtocolVersion = 0
        self.ReceiveBufferSize = 65536
        self.SendBufferSize = 65536
        self.MaxMessageSize = 0  # No limits
        self.MaxChunkCount = 0  # No limits
        self.EndpointUrl = ""
        self._freeze = True


class MessageType:
    Invalid = b'INV'  # FIXME: check value
    Hello = b'HEL'
    Acknowledge = b'ACK'
    Error = b'ERR'
    SecureOpen = b'OPN'
    SecureClose = b'CLO'
    SecureMessage = b'MSG'


class ChunkType:
    Invalid = b'0'  # FIXME check
    Single = b'F'
    Intermediate = b'C'
    Abort = b'A'  # when an error occurred and the Message is aborted (body is ErrorMessage)


class Header(uatypes.FrozenClass):
    def __init__(self, msgType=None, chunkType=None, channelid=0):
        self.MessageType = msgType
        self.ChunkType = chunkType
        self.ChannelId = channelid
        self.body_size = 0
        self.packet_size = 0
        self.header_size = 8
        self._freeze = True

    def add_size(self, size):
        self.body_size += size

    @staticmethod
    def max_size():
        return struct.calcsize("<3scII")

    def __str__(self):
        return f'Header(type:{self.MessageType}, chunk_type:{self.ChunkType}, body_size:{self.body_size}, channel:{self.ChannelId})'

    __repr__ = __str__


class ErrorMessage(uatypes.FrozenClass):
    ua_types = (('Error', 'StatusCode'), ('Reason', 'String'),)

    def __init__(self):
        self.Error = uatypes.StatusCode()
        self.Reason = ""
        self._freeze = True

    def __str__(self):
        return f'MessageAbort(error:{self.Error}, reason:{self.Reason})'

    __repr__ = __str__


class Acknowledge(uatypes.FrozenClass):
    ua_types = [
        ('ProtocolVersion', 'UInt32'),
        ('ReceiveBufferSize', 'UInt32'),
        ('SendBufferSize', 'UInt32'),
        ('MaxMessageSize', 'UInt32'),
        ('MaxChunkCount', 'UInt32'),
    ]

    def __init__(self):
        self.ProtocolVersion = 0
        self.ReceiveBufferSize = 65536
        self.SendBufferSize = 65536
        self.MaxMessageSize = 0  # No limits
        self.MaxChunkCount = 0  # No limits
        self._freeze = True


class AsymmetricAlgorithmHeader(uatypes.FrozenClass):
    ua_types = [
        ('SecurityPolicyURI', 'String'),
        ('SenderCertificate', 'ByteString'),
        ('ReceiverCertificateThumbPrint', 'ByteString'),
    ]

    def __init__(self):
        self.SecurityPolicyURI = 'http://opcfoundation.org/UA/SecurityPolicy#None'
        self.SenderCertificate = None
        self.ReceiverCertificateThumbPrint = None
        self._freeze = True

    def __str__(self):
        size1 = len(self.SenderCertificate) if self.SenderCertificate is not None else None
        size2 = len(self.ReceiverCertificateThumbPrint) if self.ReceiverCertificateThumbPrint is not None else None
        return f'{self.__class__.__name__}(SecurityPolicy:{self.SecurityPolicyURI}, certificatesize:{size2}, receiverCertificatesize:{size2} )'

    __repr__ = __str__


class SymmetricAlgorithmHeader(uatypes.FrozenClass):
    ua_types = [
        ('TokenId', 'UInt32'),
    ]

    def __init__(self):
        self.TokenId = 0
        self._freeze = True

    @staticmethod
    def max_size():
        return struct.calcsize('<I')

    def __str__(self):
        return f'{self.__class__.__name__}(TokenId:{self.TokenId} )'

    __repr__ = __str__


class SequenceHeader(uatypes.FrozenClass):
    ua_types = [
        ('SequenceNumber', 'UInt32'),
        ('RequestId', 'UInt32'),
    ]

    def __init__(self):
        self.SequenceNumber = None
        self.RequestId = None
        self._freeze = True

    @staticmethod
    def max_size():
        return struct.calcsize('<II')

    def __str__(self):
        return f'{self.__class__.__name__}(SequenceNumber:{self.SequenceNumber}, RequestId:{self.RequestId} )'

    __repr__ = __str__


class CryptographyNone:
    """
    Base class for symmetric/asymmetric cryprography
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
    AsymmetricSignatureURI = ''
    signature_key_size = 0
    symmetric_key_size = 0

    def __init__(self):
        self.asymmetric_cryptography = CryptographyNone()
        self.symmetric_cryptography = CryptographyNone()
        self.Mode = auto.MessageSecurityMode.None_
        self.server_certificate = None
        self.client_certificate = None

    def make_local_symmetric_key(self, secret, seed):
        pass

    def make_remote_symmetric_key(self, secret, seed):
        pass


class SecurityPolicyFactory:
    """
    Helper class for creating server-side SecurityPolicy.
    Server has one certificate and private key, but needs a separate
    SecurityPolicy for every client and client's certificate
    """

    def __init__(self, cls=SecurityPolicy, mode=auto.MessageSecurityMode.None_, certificate=None, private_key=None):
        self.cls = cls
        self.mode = mode
        self.certificate = certificate
        self.private_key = private_key

    def matches(self, uri, mode=None):
        return self.cls.URI == uri and (mode is None or self.mode == mode)

    def create(self, peer_certificate):
        if self.cls is SecurityPolicy:
            return self.cls()
        else:
            return self.cls(peer_certificate, self.certificate, self.private_key, self.mode)


class Message:
    def __init__(self, chunks):
        self._chunks = chunks

    def request_id(self):
        return self._chunks[0].SequenceHeader.RequestId

    def SequenceHeader(self):
        return self._chunks[0].SequenceHeader

    def SecurityHeader(self):
        return self._chunks[0].SecurityHeader

    def body(self):
        body = b"".join([c.Body for c in self._chunks])
        return utils.Buffer(body)


# FIXES for missing switchfield in NodeAttributes classes
ana = auto.NodeAttributesMask


class ObjectAttributes(auto.ObjectAttributes):
    def __init__(self):
        auto.ObjectAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.EventNotifier


class ObjectTypeAttributes(auto.ObjectTypeAttributes):
    def __init__(self):
        auto.ObjectTypeAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract


class VariableAttributes(auto.VariableAttributes):
    def __init__(self):
        auto.VariableAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Value | ana.DataType | ana.ValueRank | ana.ArrayDimensions | ana.AccessLevel | ana.UserAccessLevel | ana.MinimumSamplingInterval | ana.Historizing
        self.Historizing = False
        self.AccessLevel = AccessLevel.CurrentRead.mask
        self.UserAccessLevel = AccessLevel.CurrentRead.mask


class VariableTypeAttributes(auto.VariableTypeAttributes):
    def __init__(self):
        auto.VariableTypeAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Value | ana.DataType | ana.ValueRank | ana.ArrayDimensions | ana.IsAbstract


class MethodAttributes(auto.MethodAttributes):
    def __init__(self):
        auto.MethodAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Executable | ana.UserExecutable


class ReferenceTypeAttributes(auto.ReferenceTypeAttributes):
    def __init__(self):
        auto.ReferenceTypeAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract | ana.Symmetric | ana.InverseName


class DataTypeAttributes(auto.DataTypeAttributes):
    def __init__(self):
        auto.DataTypeAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract


class ViewAttributes(auto.ViewAttributes):
    def __init__(self):
        auto.ViewAttributes.__init__(self)
        self.SpecifiedAttributes = ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.ContainsNoLoops | ana.EventNotifier


class Argument(auto.Argument):
    def __init__(self):
        auto.Argument.__init__(self)
        self.ValueRank = -2


class XmlElement(FrozenClass):
    '''
    An XML element encoded as a UTF-8 string.
    :ivar Value:
    :vartype Value: String
    '''

    ua_types = [
        ('Value', 'String'),
    ]

    def __init__(self, xml=""):
        self.Value = xml
        self._freeze = True

    def __str__(self):
        return f'XmlElement(Value:{self.Value})'

    __repr__ = __str__

    def __eq__(self, el):
        return isinstance(el, XmlElement) and self.Value == el.Value
