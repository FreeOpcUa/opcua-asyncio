import hashlib
from datetime import datetime, timedelta
import logging
import copy

from asyncua import ua
from ..ua.ua_binary import struct_from_binary, struct_to_binary, header_from_binary, header_to_binary

logger = logging.getLogger('asyncua.uaprotocol')


class MessageChunk(ua.FrozenClass):
    """
    Message Chunk, as described in OPC UA specs Part 6, 6.7.2.
    """
    def __init__(self, security_policy, body=b'', msg_type=ua.MessageType.SecureMessage, chunk_type=ua.ChunkType.Single):
        self.MessageHeader = ua.Header(msg_type, chunk_type)
        if msg_type in (ua.MessageType.SecureMessage, ua.MessageType.SecureClose):
            self.SecurityHeader = ua.SymmetricAlgorithmHeader()
        elif msg_type == ua.MessageType.SecureOpen:
            self.SecurityHeader = ua.AsymmetricAlgorithmHeader()
        else:
            raise ua.UaError("Unsupported message type: {0}".format(msg_type))
        self.SequenceHeader = ua.SequenceHeader()
        self.Body = body
        self.security_policy = security_policy

    @staticmethod
    def from_binary(security_policy, data):
        h = header_from_binary(data)
        return MessageChunk.from_header_and_body(security_policy, h, data)

    @staticmethod
    def from_header_and_body(security_policy, header, buf):
        if not len(buf) >= header.body_size:
            raise ValueError('Full body expected here')
        data = buf.copy(header.body_size)
        buf.skip(header.body_size)
        if header.MessageType in (ua.MessageType.SecureMessage, ua.MessageType.SecureClose):
            security_header = struct_from_binary(ua.SymmetricAlgorithmHeader, data)
            crypto = security_policy.symmetric_cryptography
        elif header.MessageType == ua.MessageType.SecureOpen:
            security_header = struct_from_binary(ua.AsymmetricAlgorithmHeader, data)
            crypto = security_policy.asymmetric_cryptography
        else:
            raise ua.UaError("Unsupported message type: {0}".format(header.MessageType))
        obj = MessageChunk(crypto)
        obj.MessageHeader = header
        obj.SecurityHeader = security_header
        decrypted = crypto.decrypt(data.read(len(data)))
        signature_size = crypto.vsignature_size()
        if signature_size > 0:
            signature = decrypted[-signature_size:]
            decrypted = decrypted[:-signature_size]
            crypto.verify(header_to_binary(obj.MessageHeader) + struct_to_binary(obj.SecurityHeader) + decrypted, signature)
        data = ua.utils.Buffer(crypto.remove_padding(decrypted))
        obj.SequenceHeader = struct_from_binary(ua.SequenceHeader, data)
        obj.Body = data.read(len(data))
        return obj

    def encrypted_size(self, plain_size):
        size = plain_size + self.security_policy.signature_size()
        pbs = self.security_policy.plain_block_size()
        if size % pbs != 0:
            raise ua.UaError("Encryption error")
        return size // pbs * self.security_policy.encrypted_block_size()

    def to_binary(self):
        security = struct_to_binary(self.SecurityHeader)
        encrypted_part = struct_to_binary(self.SequenceHeader) + self.Body
        encrypted_part += self.security_policy.padding(len(encrypted_part))
        self.MessageHeader.body_size = len(security) + self.encrypted_size(len(encrypted_part))
        header = header_to_binary(self.MessageHeader)
        encrypted_part += self.security_policy.signature(header + security + encrypted_part)
        return header + security + self.security_policy.encrypt(encrypted_part)

    @staticmethod
    def max_body_size(crypto, max_chunk_size):
        max_encrypted_size = max_chunk_size - ua.Header.max_size() - ua.SymmetricAlgorithmHeader.max_size()
        max_plain_size = (max_encrypted_size // crypto.encrypted_block_size()) * crypto.plain_block_size()
        return max_plain_size - ua.SequenceHeader.max_size() - crypto.signature_size() - crypto.min_padding_size()

    @staticmethod
    def message_to_chunks(security_policy, body, max_chunk_size, message_type=ua.MessageType.SecureMessage, channel_id=1, request_id=1, token_id=1):
        """
        Pack message body (as binary string) into one or more chunks.
        Size of each chunk will not exceed max_chunk_size.
        Returns a list of MessageChunks. SequenceNumber is not initialized here,
        it must be set by Secure Channel driver.
        """
        if message_type == ua.MessageType.SecureOpen:
            # SecureOpen message must be in a single chunk (specs, Part 6, 6.7.2)
            chunk = MessageChunk(security_policy.asymmetric_cryptography, body, message_type, ua.ChunkType.Single)
            chunk.SecurityHeader.SecurityPolicyURI = security_policy.URI
            if security_policy.client_certificate:
                chunk.SecurityHeader.SenderCertificate = security_policy.client_certificate
            if security_policy.server_certificate:
                chunk.SecurityHeader.ReceiverCertificateThumbPrint =\
                    hashlib.sha1(security_policy.server_certificate).digest()
            chunk.MessageHeader.ChannelId = channel_id
            chunk.SequenceHeader.RequestId = request_id
            return [chunk]

        crypto = security_policy.symmetric_cryptography
        max_size = MessageChunk.max_body_size(crypto, max_chunk_size)

        chunks = []
        for i in range(0, len(body), max_size):
            part = body[i:i + max_size]
            if i + max_size >= len(body):
                chunk_type = ua.ChunkType.Single
            else:
                chunk_type = ua.ChunkType.Intermediate
            chunk = MessageChunk(crypto, part, message_type, chunk_type)
            chunk.SecurityHeader.TokenId = token_id
            chunk.MessageHeader.ChannelId = channel_id
            chunk.SequenceHeader.RequestId = request_id
            chunks.append(chunk)
        return chunks

    def __str__(self):
        return "{0}({1}, {2}, {3}, {4} bytes)".format(self.__class__.__name__, self.MessageHeader, self.SequenceHeader, self.SecurityHeader, len(self.Body))

    __repr__ = __str__


class SecureConnection:
    """
    Common logic for client and server
    """
    def __init__(self, security_policy):
        self._sequence_number = 0
        self._peer_sequence_number = None
        self._incoming_parts = []
        self.security_policy = security_policy
        self._policies = []
        self._open = False
        self.security_token = ua.ChannelSecurityToken()
        self.next_security_token = ua.ChannelSecurityToken()
        self.prev_security_token = ua.ChannelSecurityToken()
        self.local_nonce = 0
        self.remote_nonce = 0
        self._allow_prev_token = False
        self._max_chunk_size = 65536

    def set_channel(self, params, request_type, client_nonce):
        """
        Called on client side when getting secure channel data from server.
        """
        if request_type == ua.SecurityTokenRequestType.Issue:
            self.security_token = params.SecurityToken
            self.local_nonce = client_nonce
            self.remote_nonce = params.ServerNonce
            self.security_policy.make_local_symmetric_key(self.remote_nonce, self.local_nonce)
            self.security_policy.make_remote_symmetric_key(self.local_nonce, self.remote_nonce)
            self._open = True
        else:
            self.next_security_token = params.SecurityToken
            self.local_nonce = client_nonce
            self.remote_nonce = params.ServerNonce

        self._allow_prev_token = True

    def open(self, params, server):
        """
        Called on server side to open secure channel.
        """

        self.local_nonce = ua.utils.create_nonce(self.security_policy.symmetric_key_size)
        self.remote_nonce = params.ClientNonce
        response = ua.OpenSecureChannelResult()
        response.ServerNonce = self.local_nonce

        if not self._open or params.RequestType == ua.SecurityTokenRequestType.Issue:
            self._open = True
            self.security_token.TokenId = 13  # random value
            self.security_token.ChannelId = server.get_new_channel_id()
            self.security_token.RevisedLifetime = params.RequestedLifetime
            self.security_token.CreatedAt = datetime.utcnow()

            response.SecurityToken = self.security_token

            self.security_policy.make_local_symmetric_key(self.remote_nonce, self.local_nonce)
            self.security_policy.make_remote_symmetric_key(self.local_nonce, self.remote_nonce)
        else:
            self.next_security_token = copy.deepcopy(self.security_token)
            self.next_security_token.TokenId += 1
            self.next_security_token.RevisedLifetime = params.RequestedLifetime
            self.next_security_token.CreatedAt = datetime.utcnow()

            response.SecurityToken = self.next_security_token

        return response

    def close(self):
        self._open = False

    def is_open(self):
        return self._open

    def set_policy_factories(self, policies):
        """
        Set a list of available security policies.
        Use this in servers with multiple endpoints with different security.
        """
        self._policies = policies

    @staticmethod
    def _policy_matches(policy, uri, mode=None):
        return policy.URI == uri and (mode is None or policy.Mode == mode)

    def select_policy(self, uri, peer_certificate, mode=None):
        for policy in self._policies:
            if policy.matches(uri, mode):
                self.security_policy = policy.create(peer_certificate)
                return
        if self.security_policy.URI != uri or (mode is not None and self.security_policy.Mode != mode):
            raise ua.UaError("No matching policy: {0}, {1}".format(uri, mode))

    def revolve_tokens(self):
        """
        Revolve security tokens of the security channel. Start using the
        next security token negotiated during the renewal of the channel and
        remember the previous token until the other communication party
        """
        self.prev_security_token = self.security_token
        self.security_token = self.next_security_token
        self.next_security_token = ua.ChannelSecurityToken()
        self.security_policy.make_local_symmetric_key(self.remote_nonce, self.local_nonce)
        self.security_policy.make_remote_symmetric_key(self.local_nonce, self.remote_nonce)

    def message_to_binary(self, message, message_type=ua.MessageType.SecureMessage, request_id=0):
        """
        Convert OPC UA secure message to binary.
        The only supported types are SecureOpen, SecureMessage, SecureClose.
        If message_type is SecureMessage, the AlgorithmHeader should be passed as arg.
        """
        chunks = MessageChunk.message_to_chunks(self.security_policy, message, self._max_chunk_size, message_type=message_type, channel_id=self.security_token.ChannelId, request_id=request_id, token_id=self.security_token.TokenId)
        for chunk in chunks:
            self._sequence_number += 1
            if self._sequence_number >= (1 << 32):
                logger.debug("Wrapping sequence number: %d -> 1", self._sequence_number)
                self._sequence_number = 1
            chunk.SequenceHeader.SequenceNumber = self._sequence_number
        return b"".join([chunk.to_binary() for chunk in chunks])

    def _check_sym_header(self, security_hdr):
        """
        Validates the symmetric header of the message chunk and revolves the
        security token if needed.
        """
        assert isinstance(security_hdr, ua.SymmetricAlgorithmHeader), "Expected SymAlgHeader, got: {0}".format(security_hdr)

        if security_hdr.TokenId == self.security_token.TokenId:
            return

        if security_hdr.TokenId == self.next_security_token.TokenId:
            self.revolve_tokens()
            return

        if self._allow_prev_token and security_hdr.TokenId == self.prev_security_token.TokenId:
            # From spec, part 4, section 5.5.2.1: Clients should accept Messages secured by an
            # expired SecurityToken for up to 25 % of the token lifetime. This should ensure that
            # Messages sent by the Server before the token expired are not rejected because of
            # network delays.
            timeout = self.prev_security_token.CreatedAt + timedelta(milliseconds=self.prev_security_token.RevisedLifetime * 1.25)
            if timeout < datetime.utcnow():
                raise ua.UaError("Security token id {} has timed out ({} < {})".format(security_hdr.TokenId, timeout, datetime.utcnow()))
            return

        expected_tokens = [self.security_token.TokenId, self.next_security_token.TokenId]
        if self._allow_prev_token:
            expected_tokens.insert(0, self.prev_security_token.TokenId)
        raise ua.UaError("Invalid security token id {}, expected one of: {}".format(security_hdr.TokenId, expected_tokens))

    def _check_incoming_chunk(self, chunk):
        if not isinstance(chunk, MessageChunk):
            raise ValueError(f'Expected chunk, got: {chunk}')
        if chunk.MessageHeader.MessageType != ua.MessageType.SecureOpen:
            if chunk.MessageHeader.ChannelId != self.security_token.ChannelId:
                raise ua.UaError('Wrong channel id {0}, expected {1}'.format(chunk.MessageHeader.ChannelId, self.security_token.ChannelId))
        if self._incoming_parts:
            if self._incoming_parts[0].SequenceHeader.RequestId != chunk.SequenceHeader.RequestId:
                raise ua.UaError('Wrong request id {0}, expected {1}'.format(chunk.SequenceHeader.RequestId, self._incoming_parts[0].SequenceHeader.RequestId))
        # The sequence number must monotonically increase (but it can wrap around)
        seq_num = chunk.SequenceHeader.SequenceNumber
        if self._peer_sequence_number is not None:
            if seq_num != self._peer_sequence_number + 1:
                wrap_limit = (1 << 32) - 1024
                if seq_num < 1024 and self._peer_sequence_number >= wrap_limit:
                    # The sequence number has wrapped around. See spec. part 6, 6.7.2
                    logger.debug('Sequence number wrapped: %d -> %d', self._peer_sequence_number, seq_num)
                else:
                    # Condition for monotonically increase is not met
                    raise ua.UaError("Received chunk: {0} with wrong sequence expecting: {1}, received: {2}, spec says to close connection".format(chunk, self._peer_sequence_number, seq_num))
        self._peer_sequence_number = seq_num

    def receive_from_header_and_body(self, header, body):
        """
        Convert MessageHeader and binary body to OPC UA TCP message (see OPC UA
        specs Part 6, 7.1: Hello, Acknowledge or ErrorMessage), or a Message
        object, or None (if intermediate chunk is received)
        """
        if header.MessageType == ua.MessageType.SecureOpen:
            data = body.copy(header.body_size)
            security_header = struct_from_binary(ua.AsymmetricAlgorithmHeader, data)
            self.select_policy(security_header.SecurityPolicyURI, security_header.SenderCertificate)
        elif header.MessageType in (ua.MessageType.SecureMessage, ua.MessageType.SecureClose):
            data = body.copy(header.body_size)
            security_header = struct_from_binary(ua.SymmetricAlgorithmHeader, data)
            self._check_sym_header(security_header)

        if header.MessageType in (ua.MessageType.SecureMessage, ua.MessageType.SecureOpen, ua.MessageType.SecureClose):
            chunk = MessageChunk.from_header_and_body(self.security_policy, header, body)
            return self._receive(chunk)
        if header.MessageType == ua.MessageType.Hello:
            msg = struct_from_binary(ua.Hello, body)
            self._max_chunk_size = msg.ReceiveBufferSize
            return msg
        if header.MessageType == ua.MessageType.Acknowledge:
            msg = struct_from_binary(ua.Acknowledge, body)
            self._max_chunk_size = msg.SendBufferSize
            return msg
        if header.MessageType == ua.MessageType.Error:
            msg = struct_from_binary(ua.ErrorMessage, body)
            logger.warning("Received an error: %s", msg)
            return msg
        raise ua.UaError("Unsupported message type {0}".format(header.MessageType))

    def _receive(self, msg):
        self._check_incoming_chunk(msg)
        self._incoming_parts.append(msg)
        if msg.MessageHeader.ChunkType == ua.ChunkType.Intermediate:
            return None
        if msg.MessageHeader.ChunkType == ua.ChunkType.Abort:
            err = struct_from_binary(ua.ErrorMessage, ua.utils.Buffer(msg.Body))
            logger.warning("Message %s aborted: %s", msg, err)
            # specs Part 6, 6.7.3 say that aborted message shall be ignored
            # and SecureChannel should not be closed
            self._incoming_parts = []
            return None
        if msg.MessageHeader.ChunkType == ua.ChunkType.Single:
            message = ua.Message(self._incoming_parts)
            self._incoming_parts = []
            return message
        raise ua.UaError("Unsupported chunk type: {0}".format(msg))
