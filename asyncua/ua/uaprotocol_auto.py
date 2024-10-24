"""
Autogenerate code from xml spec
Date:2024-04-25 11:57:44.365871
"""

from datetime import datetime, timezone
from enum import IntEnum, IntFlag
from typing import List, Optional, Type
from dataclasses import dataclass, field

from asyncua.ua.uatypes import FROZEN
from asyncua.ua.uatypes import SByte, Byte, Bytes, ByteString, Int16, Int32, Int64, UInt16, UInt32
from asyncua.ua.uatypes import UInt64, Boolean, Float, Double, Null, String, CharArray, DateTime, Guid
from asyncua.ua.uatypes import AccessLevel, EventNotifier
from asyncua.ua.uatypes import LocalizedText, Variant, QualifiedName, StatusCode, DataValue
from asyncua.ua.uatypes import RelativePath, RelativePathElement
from asyncua.ua.uatypes import NodeId, FourByteNodeId, ExpandedNodeId, ExtensionObject, DiagnosticInfo
from asyncua.ua.uatypes import extension_object_typeids, extension_objects_by_typeid
from asyncua.ua.object_ids import ObjectIds


Image = ByteString


ImageBMP = ByteString


ImageGIF = ByteString


ImageJPG = ByteString


ImagePNG = ByteString


AudioDataType = ByteString


UriString = String


BitFieldMaskDataType = UInt64


SemanticVersionString = String


Handle = UInt32


TrimmedString = String


EncodedTicket = String


NormalizedString = String


DecimalString = String


DurationString = String


TimeString = String


DateString = String


Duration = Double


UtcTime = DateTime


LocaleId = String


Index = UInt32


IntegerId = UInt32


VersionTime = UInt32


ApplicationInstanceCertificate = ByteString


SessionAuthenticationToken = NodeId


ContinuationPoint = ByteString


Counter = UInt32


NumericRange = String


class NamingRuleType(IntEnum):
    """
    https://reference.opcfoundation.org/v104/Core/docs/Part3/8.29

    :ivar Mandatory:
    :vartype Mandatory: 1
    :ivar Optional:
    :vartype Optional: 2
    :ivar Constraint:
    :vartype Constraint: 3
    """
    Mandatory = 1
    Optional = 2
    Constraint = 3


class RedundantServerMode(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.44

    :ivar PrimaryWithBackup:
    :vartype PrimaryWithBackup: 0
    :ivar PrimaryOnly:
    :vartype PrimaryOnly: 1
    :ivar BackupReady:
    :vartype BackupReady: 2
    :ivar BackupNotReady:
    :vartype BackupNotReady: 3
    """
    PrimaryWithBackup = 0
    PrimaryOnly = 1
    BackupReady = 2
    BackupNotReady = 3


class OpenFileMode(IntEnum):
    """
    :ivar Read:
    :vartype Read: 1
    :ivar Write:
    :vartype Write: 2
    :ivar EraseExisting:
    :vartype EraseExisting: 4
    :ivar Append:
    :vartype Append: 8
    """
    Read = 1
    Write = 2
    EraseExisting = 4
    Append = 8


class IdentityCriteriaType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part18/4.4.4

    :ivar UserName:
    :vartype UserName: 1
    :ivar Thumbprint:
    :vartype Thumbprint: 2
    :ivar Role:
    :vartype Role: 3
    :ivar GroupId:
    :vartype GroupId: 4
    :ivar Anonymous:
    :vartype Anonymous: 5
    :ivar AuthenticatedUser:
    :vartype AuthenticatedUser: 6
    :ivar Application:
    :vartype Application: 7
    :ivar X509Subject:
    :vartype X509Subject: 8
    """
    UserName = 1
    Thumbprint = 2
    Role = 3
    GroupId = 4
    Anonymous = 5
    AuthenticatedUser = 6
    Application = 7
    X509Subject = 8


class ConversionLimitEnum(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/6.6.3

    :ivar NoConversion:
    :vartype NoConversion: 0
    :ivar Limited:
    :vartype Limited: 1
    :ivar Unlimited:
    :vartype Unlimited: 2
    """
    NoConversion = 0
    Limited = 1
    Unlimited = 2


class AlarmMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part9/8.3

    :ivar Active:
    :vartype Active: Bit: 0
    :ivar Unacknowledged:
    :vartype Unacknowledged: Bit: 1
    :ivar Unconfirmed:
    :vartype Unconfirmed: Bit: 2
    """
    Active = 1<<0
    Unacknowledged = 1<<1
    Unconfirmed = 1<<2

    @staticmethod
    def datatype() -> str:
        return "UInt16"


class TrustListValidationOptions(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part12/7.8.2/#7.8.2.8

    :ivar SuppressCertificateExpired:
    :vartype SuppressCertificateExpired: Bit: 0
    :ivar SuppressHostNameInvalid:
    :vartype SuppressHostNameInvalid: Bit: 1
    :ivar SuppressRevocationStatusUnknown:
    :vartype SuppressRevocationStatusUnknown: Bit: 2
    :ivar SuppressIssuerCertificateExpired:
    :vartype SuppressIssuerCertificateExpired: Bit: 3
    :ivar SuppressIssuerRevocationStatusUnknown:
    :vartype SuppressIssuerRevocationStatusUnknown: Bit: 4
    :ivar CheckRevocationStatusOnline:
    :vartype CheckRevocationStatusOnline: Bit: 5
    :ivar CheckRevocationStatusOffline:
    :vartype CheckRevocationStatusOffline: Bit: 6
    """
    SuppressCertificateExpired = 1<<0
    SuppressHostNameInvalid = 1<<1
    SuppressRevocationStatusUnknown = 1<<2
    SuppressIssuerCertificateExpired = 1<<3
    SuppressIssuerRevocationStatusUnknown = 1<<4
    CheckRevocationStatusOnline = 1<<5
    CheckRevocationStatusOffline = 1<<6

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class TrustListMasks(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part12/7.8.2/#7.8.2.7

    :ivar None_:
    :vartype None_: 0
    :ivar TrustedCertificates:
    :vartype TrustedCertificates: 1
    :ivar TrustedCrls:
    :vartype TrustedCrls: 2
    :ivar IssuerCertificates:
    :vartype IssuerCertificates: 4
    :ivar IssuerCrls:
    :vartype IssuerCrls: 8
    :ivar All:
    :vartype All: 15
    """
    None_ = 0
    TrustedCertificates = 1
    TrustedCrls = 2
    IssuerCertificates = 4
    IssuerCrls = 8
    All = 15


class PubSubState(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.1

    :ivar Disabled:
    :vartype Disabled: 0
    :ivar Paused:
    :vartype Paused: 1
    :ivar Operational:
    :vartype Operational: 2
    :ivar Error:
    :vartype Error: 3
    :ivar PreOperational:
    :vartype PreOperational: 4
    """
    Disabled = 0
    Paused = 1
    Operational = 2
    Error = 3
    PreOperational = 4


class DataSetFieldFlags(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.2.5

    :ivar PromotedField:
    :vartype PromotedField: Bit: 0
    """
    PromotedField = 1<<0

    @staticmethod
    def datatype() -> str:
        return "UInt16"


class DataSetFieldContentMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.4/#6.2.4.2

    :ivar StatusCode:
    :vartype StatusCode: Bit: 0
    :ivar SourceTimestamp:
    :vartype SourceTimestamp: Bit: 1
    :ivar ServerTimestamp:
    :vartype ServerTimestamp: Bit: 2
    :ivar SourcePicoSeconds:
    :vartype SourcePicoSeconds: Bit: 3
    :ivar ServerPicoSeconds:
    :vartype ServerPicoSeconds: Bit: 4
    :ivar RawData:
    :vartype RawData: Bit: 5
    """
    StatusCode = 1<<0
    SourceTimestamp = 1<<1
    ServerTimestamp = 1<<2
    SourcePicoSeconds = 1<<3
    ServerPicoSeconds = 1<<4
    RawData = 1<<5

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class OverrideValueHandling(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.2.4

    :ivar Disabled:
    :vartype Disabled: 0
    :ivar LastUsableValue:
    :vartype LastUsableValue: 1
    :ivar OverrideValue:
    :vartype OverrideValue: 2
    """
    Disabled = 0
    LastUsableValue = 1
    OverrideValue = 2


class DataSetOrderingType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.1/#6.3.1.1.3

    :ivar Undefined:
    :vartype Undefined: 0
    :ivar AscendingWriterId:
    :vartype AscendingWriterId: 1
    :ivar AscendingWriterIdSingle:
    :vartype AscendingWriterIdSingle: 2
    """
    Undefined = 0
    AscendingWriterId = 1
    AscendingWriterIdSingle = 2


class UadpNetworkMessageContentMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.1/#6.3.1.1.4

    :ivar PublisherId:
    :vartype PublisherId: Bit: 0
    :ivar GroupHeader:
    :vartype GroupHeader: Bit: 1
    :ivar WriterGroupId:
    :vartype WriterGroupId: Bit: 2
    :ivar GroupVersion:
    :vartype GroupVersion: Bit: 3
    :ivar NetworkMessageNumber:
    :vartype NetworkMessageNumber: Bit: 4
    :ivar SequenceNumber:
    :vartype SequenceNumber: Bit: 5
    :ivar PayloadHeader:
    :vartype PayloadHeader: Bit: 6
    :ivar Timestamp:
    :vartype Timestamp: Bit: 7
    :ivar PicoSeconds:
    :vartype PicoSeconds: Bit: 8
    :ivar DataSetClassId:
    :vartype DataSetClassId: Bit: 9
    :ivar PromotedFields:
    :vartype PromotedFields: Bit: 10
    """
    PublisherId = 1<<0
    GroupHeader = 1<<1
    WriterGroupId = 1<<2
    GroupVersion = 1<<3
    NetworkMessageNumber = 1<<4
    SequenceNumber = 1<<5
    PayloadHeader = 1<<6
    Timestamp = 1<<7
    PicoSeconds = 1<<8
    DataSetClassId = 1<<9
    PromotedFields = 1<<10

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class UadpDataSetMessageContentMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.1/#6.3.1.3.2

    :ivar Timestamp:
    :vartype Timestamp: Bit: 0
    :ivar PicoSeconds:
    :vartype PicoSeconds: Bit: 1
    :ivar Status:
    :vartype Status: Bit: 2
    :ivar MajorVersion:
    :vartype MajorVersion: Bit: 3
    :ivar MinorVersion:
    :vartype MinorVersion: Bit: 4
    :ivar SequenceNumber:
    :vartype SequenceNumber: Bit: 5
    """
    Timestamp = 1<<0
    PicoSeconds = 1<<1
    Status = 1<<2
    MajorVersion = 1<<3
    MinorVersion = 1<<4
    SequenceNumber = 1<<5

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class JsonNetworkMessageContentMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.2/#6.3.2.1.1

    :ivar NetworkMessageHeader:
    :vartype NetworkMessageHeader: Bit: 0
    :ivar DataSetMessageHeader:
    :vartype DataSetMessageHeader: Bit: 1
    :ivar SingleDataSetMessage:
    :vartype SingleDataSetMessage: Bit: 2
    :ivar PublisherId:
    :vartype PublisherId: Bit: 3
    :ivar DataSetClassId:
    :vartype DataSetClassId: Bit: 4
    :ivar ReplyTo:
    :vartype ReplyTo: Bit: 5
    :ivar WriterGroupName:
    :vartype WriterGroupName: Bit: 6
    """
    NetworkMessageHeader = 1<<0
    DataSetMessageHeader = 1<<1
    SingleDataSetMessage = 1<<2
    PublisherId = 1<<3
    DataSetClassId = 1<<4
    ReplyTo = 1<<5
    WriterGroupName = 1<<6

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class JsonDataSetMessageContentMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.2/#6.3.2.3.1

    :ivar DataSetWriterId:
    :vartype DataSetWriterId: Bit: 0
    :ivar MetaDataVersion:
    :vartype MetaDataVersion: Bit: 1
    :ivar SequenceNumber:
    :vartype SequenceNumber: Bit: 2
    :ivar Timestamp:
    :vartype Timestamp: Bit: 3
    :ivar Status:
    :vartype Status: Bit: 4
    :ivar MessageType:
    :vartype MessageType: Bit: 5
    :ivar DataSetWriterName:
    :vartype DataSetWriterName: Bit: 6
    :ivar ReversibleFieldEncoding:
    :vartype ReversibleFieldEncoding: Bit: 7
    :ivar PublisherId:
    :vartype PublisherId: Bit: 8
    :ivar WriterGroupName:
    :vartype WriterGroupName: Bit: 9
    :ivar MinorVersion:
    :vartype MinorVersion: Bit: 10
    """
    DataSetWriterId = 1<<0
    MetaDataVersion = 1<<1
    SequenceNumber = 1<<2
    Timestamp = 1<<3
    Status = 1<<4
    MessageType = 1<<5
    DataSetWriterName = 1<<6
    ReversibleFieldEncoding = 1<<7
    PublisherId = 1<<8
    WriterGroupName = 1<<9
    MinorVersion = 1<<10

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class BrokerTransportQualityOfService(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.2/#6.4.2.1

    :ivar NotSpecified:
    :vartype NotSpecified: 0
    :ivar BestEffort:
    :vartype BestEffort: 1
    :ivar AtLeastOnce:
    :vartype AtLeastOnce: 2
    :ivar AtMostOnce:
    :vartype AtMostOnce: 3
    :ivar ExactlyOnce:
    :vartype ExactlyOnce: 4
    """
    NotSpecified = 0
    BestEffort = 1
    AtLeastOnce = 2
    AtMostOnce = 3
    ExactlyOnce = 4


class PubSubConfigurationRefMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/9.1.3/#9.1.3.7.2

    :ivar ElementAdd:
    :vartype ElementAdd: Bit: 0
    :ivar ElementMatch:
    :vartype ElementMatch: Bit: 1
    :ivar ElementModify:
    :vartype ElementModify: Bit: 2
    :ivar ElementRemove:
    :vartype ElementRemove: Bit: 3
    :ivar ReferenceWriter:
    :vartype ReferenceWriter: Bit: 4
    :ivar ReferenceReader:
    :vartype ReferenceReader: Bit: 5
    :ivar ReferenceWriterGroup:
    :vartype ReferenceWriterGroup: Bit: 6
    :ivar ReferenceReaderGroup:
    :vartype ReferenceReaderGroup: Bit: 7
    :ivar ReferenceConnection:
    :vartype ReferenceConnection: Bit: 8
    :ivar ReferencePubDataset:
    :vartype ReferencePubDataset: Bit: 9
    :ivar ReferenceSubDataset:
    :vartype ReferenceSubDataset: Bit: 10
    :ivar ReferenceSecurityGroup:
    :vartype ReferenceSecurityGroup: Bit: 11
    :ivar ReferencePushTarget:
    :vartype ReferencePushTarget: Bit: 12
    """
    ElementAdd = 1<<0
    ElementMatch = 1<<1
    ElementModify = 1<<2
    ElementRemove = 1<<3
    ReferenceWriter = 1<<4
    ReferenceReader = 1<<5
    ReferenceWriterGroup = 1<<6
    ReferenceReaderGroup = 1<<7
    ReferenceConnection = 1<<8
    ReferencePubDataset = 1<<9
    ReferenceSubDataset = 1<<10
    ReferenceSecurityGroup = 1<<11
    ReferencePushTarget = 1<<12

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class DiagnosticsLevel(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/9.1.11/#9.1.11.4

    :ivar Basic:
    :vartype Basic: 0
    :ivar Advanced:
    :vartype Advanced: 1
    :ivar Info:
    :vartype Info: 2
    :ivar Log:
    :vartype Log: 3
    :ivar Debug:
    :vartype Debug: 4
    """
    Basic = 0
    Advanced = 1
    Info = 2
    Log = 3
    Debug = 4


class PubSubDiagnosticsCounterClassification(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/9.1.11/#9.1.11.6

    :ivar Information:
    :vartype Information: 0
    :ivar Error:
    :vartype Error: 1
    """
    Information = 0
    Error = 1


class PasswordOptionsMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part18/5.2.2

    :ivar SupportInitialPasswordChange:
    :vartype SupportInitialPasswordChange: Bit: 0
    :ivar SupportDisableUser:
    :vartype SupportDisableUser: Bit: 1
    :ivar SupportDisableDeleteForUser:
    :vartype SupportDisableDeleteForUser: Bit: 2
    :ivar SupportNoChangeForUser:
    :vartype SupportNoChangeForUser: Bit: 3
    :ivar SupportDescriptionForUser:
    :vartype SupportDescriptionForUser: Bit: 4
    :ivar RequiresUpperCaseCharacters:
    :vartype RequiresUpperCaseCharacters: Bit: 5
    :ivar RequiresLowerCaseCharacters:
    :vartype RequiresLowerCaseCharacters: Bit: 6
    :ivar RequiresDigitCharacters:
    :vartype RequiresDigitCharacters: Bit: 7
    :ivar RequiresSpecialCharacters:
    :vartype RequiresSpecialCharacters: Bit: 8
    """
    SupportInitialPasswordChange = 1<<0
    SupportDisableUser = 1<<1
    SupportDisableDeleteForUser = 1<<2
    SupportNoChangeForUser = 1<<3
    SupportDescriptionForUser = 1<<4
    RequiresUpperCaseCharacters = 1<<5
    RequiresLowerCaseCharacters = 1<<6
    RequiresDigitCharacters = 1<<7
    RequiresSpecialCharacters = 1<<8

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class UserConfigurationMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part18/5.2.3

    :ivar NoDelete:
    :vartype NoDelete: Bit: 0
    :ivar Disabled:
    :vartype Disabled: Bit: 1
    :ivar NoChangeByUser:
    :vartype NoChangeByUser: Bit: 2
    :ivar MustChangePassword:
    :vartype MustChangePassword: Bit: 3
    """
    NoDelete = 1<<0
    Disabled = 1<<1
    NoChangeByUser = 1<<2
    MustChangePassword = 1<<3

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class Duplex(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.1

    :ivar Full:
    :vartype Full: 0
    :ivar Half:
    :vartype Half: 1
    :ivar Unknown:
    :vartype Unknown: 2
    """
    Full = 0
    Half = 1
    Unknown = 2


class InterfaceAdminStatus(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.2

    :ivar Up:
    :vartype Up: 0
    :ivar Down:
    :vartype Down: 1
    :ivar Testing:
    :vartype Testing: 2
    """
    Up = 0
    Down = 1
    Testing = 2


class InterfaceOperStatus(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.3

    :ivar Up:
    :vartype Up: 0
    :ivar Down:
    :vartype Down: 1
    :ivar Testing:
    :vartype Testing: 2
    :ivar Unknown:
    :vartype Unknown: 3
    :ivar Dormant:
    :vartype Dormant: 4
    :ivar NotPresent:
    :vartype NotPresent: 5
    :ivar LowerLayerDown:
    :vartype LowerLayerDown: 6
    """
    Up = 0
    Down = 1
    Testing = 2
    Unknown = 3
    Dormant = 4
    NotPresent = 5
    LowerLayerDown = 6


class NegotiationStatus(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.4

    :ivar InProgress:
    :vartype InProgress: 0
    :ivar Complete:
    :vartype Complete: 1
    :ivar Failed:
    :vartype Failed: 2
    :ivar Unknown:
    :vartype Unknown: 3
    :ivar NoNegotiation:
    :vartype NoNegotiation: 4
    """
    InProgress = 0
    Complete = 1
    Failed = 2
    Unknown = 3
    NoNegotiation = 4


class TsnFailureCode(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.5

    :ivar NoFailure:
    :vartype NoFailure: 0
    :ivar InsufficientBandwidth:
    :vartype InsufficientBandwidth: 1
    :ivar InsufficientResources:
    :vartype InsufficientResources: 2
    :ivar InsufficientTrafficClassBandwidth:
    :vartype InsufficientTrafficClassBandwidth: 3
    :ivar StreamIdInUse:
    :vartype StreamIdInUse: 4
    :ivar StreamDestinationAddressInUse:
    :vartype StreamDestinationAddressInUse: 5
    :ivar StreamPreemptedByHigherRank:
    :vartype StreamPreemptedByHigherRank: 6
    :ivar LatencyHasChanged:
    :vartype LatencyHasChanged: 7
    :ivar EgressPortNotAvbCapable:
    :vartype EgressPortNotAvbCapable: 8
    :ivar UseDifferentDestinationAddress:
    :vartype UseDifferentDestinationAddress: 9
    :ivar OutOfMsrpResources:
    :vartype OutOfMsrpResources: 10
    :ivar OutOfMmrpResources:
    :vartype OutOfMmrpResources: 11
    :ivar CannotStoreDestinationAddress:
    :vartype CannotStoreDestinationAddress: 12
    :ivar PriorityIsNotAnSrcClass:
    :vartype PriorityIsNotAnSrcClass: 13
    :ivar MaxFrameSizeTooLarge:
    :vartype MaxFrameSizeTooLarge: 14
    :ivar MaxFanInPortsLimitReached:
    :vartype MaxFanInPortsLimitReached: 15
    :ivar FirstValueChangedForStreamId:
    :vartype FirstValueChangedForStreamId: 16
    :ivar VlanBlockedOnEgress:
    :vartype VlanBlockedOnEgress: 17
    :ivar VlanTaggingDisabledOnEgress:
    :vartype VlanTaggingDisabledOnEgress: 18
    :ivar SrClassPriorityMismatch:
    :vartype SrClassPriorityMismatch: 19
    :ivar FeatureNotPropagated:
    :vartype FeatureNotPropagated: 20
    :ivar MaxLatencyExceeded:
    :vartype MaxLatencyExceeded: 21
    :ivar BridgeDoesNotProvideNetworkId:
    :vartype BridgeDoesNotProvideNetworkId: 22
    :ivar StreamTransformNotSupported:
    :vartype StreamTransformNotSupported: 23
    :ivar StreamIdTypeNotSupported:
    :vartype StreamIdTypeNotSupported: 24
    :ivar FeatureNotSupported:
    :vartype FeatureNotSupported: 25
    """
    NoFailure = 0
    InsufficientBandwidth = 1
    InsufficientResources = 2
    InsufficientTrafficClassBandwidth = 3
    StreamIdInUse = 4
    StreamDestinationAddressInUse = 5
    StreamPreemptedByHigherRank = 6
    LatencyHasChanged = 7
    EgressPortNotAvbCapable = 8
    UseDifferentDestinationAddress = 9
    OutOfMsrpResources = 10
    OutOfMmrpResources = 11
    CannotStoreDestinationAddress = 12
    PriorityIsNotAnSrcClass = 13
    MaxFrameSizeTooLarge = 14
    MaxFanInPortsLimitReached = 15
    FirstValueChangedForStreamId = 16
    VlanBlockedOnEgress = 17
    VlanTaggingDisabledOnEgress = 18
    SrClassPriorityMismatch = 19
    FeatureNotPropagated = 20
    MaxLatencyExceeded = 21
    BridgeDoesNotProvideNetworkId = 22
    StreamTransformNotSupported = 23
    StreamIdTypeNotSupported = 24
    FeatureNotSupported = 25


class TsnStreamState(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.6

    :ivar Disabled:
    :vartype Disabled: 0
    :ivar Configuring:
    :vartype Configuring: 1
    :ivar Ready:
    :vartype Ready: 2
    :ivar Operational:
    :vartype Operational: 3
    :ivar Error:
    :vartype Error: 4
    """
    Disabled = 0
    Configuring = 1
    Ready = 2
    Operational = 3
    Error = 4


class TsnTalkerStatus(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.7

    :ivar None_:
    :vartype None_: 0
    :ivar Ready:
    :vartype Ready: 1
    :ivar Failed:
    :vartype Failed: 2
    """
    None_ = 0
    Ready = 1
    Failed = 2


class TsnListenerStatus(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.1/#5.3.1.8

    :ivar None_:
    :vartype None_: 0
    :ivar Ready:
    :vartype Ready: 1
    :ivar PartialFailed:
    :vartype PartialFailed: 2
    :ivar Failed:
    :vartype Failed: 3
    """
    None_ = 0
    Ready = 1
    PartialFailed = 2
    Failed = 3


class IdType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.5/#12.2.5.1

    :ivar Numeric:
    :vartype Numeric: 0
    :ivar String:
    :vartype String: 1
    :ivar Guid:
    :vartype Guid: 2
    :ivar Opaque:
    :vartype Opaque: 3
    """
    Numeric = 0
    String = 1
    Guid = 2
    Opaque = 3


class NodeClass(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.5/#12.2.5.2

    :ivar Unspecified:
    :vartype Unspecified: 0
    :ivar Object:
    :vartype Object: 1
    :ivar Variable:
    :vartype Variable: 2
    :ivar Method:
    :vartype Method: 4
    :ivar ObjectType:
    :vartype ObjectType: 8
    :ivar VariableType:
    :vartype VariableType: 16
    :ivar ReferenceType:
    :vartype ReferenceType: 32
    :ivar DataType:
    :vartype DataType: 64
    :ivar View:
    :vartype View: 128
    """
    Unspecified = 0
    Object = 1
    Variable = 2
    Method = 4
    ObjectType = 8
    VariableType = 16
    ReferenceType = 32
    DataType = 64
    View = 128


class PermissionType(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part3/8.55

    :ivar Browse:
    :vartype Browse: Bit: 0
    :ivar ReadRolePermissions:
    :vartype ReadRolePermissions: Bit: 1
    :ivar WriteAttribute:
    :vartype WriteAttribute: Bit: 2
    :ivar WriteRolePermissions:
    :vartype WriteRolePermissions: Bit: 3
    :ivar WriteHistorizing:
    :vartype WriteHistorizing: Bit: 4
    :ivar Read:
    :vartype Read: Bit: 5
    :ivar Write:
    :vartype Write: Bit: 6
    :ivar ReadHistory:
    :vartype ReadHistory: Bit: 7
    :ivar InsertHistory:
    :vartype InsertHistory: Bit: 8
    :ivar ModifyHistory:
    :vartype ModifyHistory: Bit: 9
    :ivar DeleteHistory:
    :vartype DeleteHistory: Bit: 10
    :ivar ReceiveEvents:
    :vartype ReceiveEvents: Bit: 11
    :ivar Call:
    :vartype Call: Bit: 12
    :ivar AddReference:
    :vartype AddReference: Bit: 13
    :ivar RemoveReference:
    :vartype RemoveReference: Bit: 14
    :ivar DeleteNode:
    :vartype DeleteNode: Bit: 15
    :ivar AddNode:
    :vartype AddNode: Bit: 16
    """
    Browse = 1<<0
    ReadRolePermissions = 1<<1
    WriteAttribute = 1<<2
    WriteRolePermissions = 1<<3
    WriteHistorizing = 1<<4
    Read = 1<<5
    Write = 1<<6
    ReadHistory = 1<<7
    InsertHistory = 1<<8
    ModifyHistory = 1<<9
    DeleteHistory = 1<<10
    ReceiveEvents = 1<<11
    Call = 1<<12
    AddReference = 1<<13
    RemoveReference = 1<<14
    DeleteNode = 1<<15
    AddNode = 1<<16

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class AccessLevelType(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part3/8.57

    :ivar CurrentRead:
    :vartype CurrentRead: Bit: 0
    :ivar CurrentWrite:
    :vartype CurrentWrite: Bit: 1
    :ivar HistoryRead:
    :vartype HistoryRead: Bit: 2
    :ivar HistoryWrite:
    :vartype HistoryWrite: Bit: 3
    :ivar SemanticChange:
    :vartype SemanticChange: Bit: 4
    :ivar StatusWrite:
    :vartype StatusWrite: Bit: 5
    :ivar TimestampWrite:
    :vartype TimestampWrite: Bit: 6
    """
    CurrentRead = 1<<0
    CurrentWrite = 1<<1
    HistoryRead = 1<<2
    HistoryWrite = 1<<3
    SemanticChange = 1<<4
    StatusWrite = 1<<5
    TimestampWrite = 1<<6

    @staticmethod
    def datatype() -> str:
        return "Byte"


class AccessLevelExType(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part3/8.58

    :ivar CurrentRead:
    :vartype CurrentRead: Bit: 0
    :ivar CurrentWrite:
    :vartype CurrentWrite: Bit: 1
    :ivar HistoryRead:
    :vartype HistoryRead: Bit: 2
    :ivar HistoryWrite:
    :vartype HistoryWrite: Bit: 3
    :ivar SemanticChange:
    :vartype SemanticChange: Bit: 4
    :ivar StatusWrite:
    :vartype StatusWrite: Bit: 5
    :ivar TimestampWrite:
    :vartype TimestampWrite: Bit: 6
    :ivar NonatomicRead:
    :vartype NonatomicRead: Bit: 8
    :ivar NonatomicWrite:
    :vartype NonatomicWrite: Bit: 9
    :ivar WriteFullArrayOnly:
    :vartype WriteFullArrayOnly: Bit: 10
    :ivar NoSubDataTypes:
    :vartype NoSubDataTypes: Bit: 11
    :ivar NonVolatile:
    :vartype NonVolatile: Bit: 12
    :ivar Constant:
    :vartype Constant: Bit: 13
    """
    CurrentRead = 1<<0
    CurrentWrite = 1<<1
    HistoryRead = 1<<2
    HistoryWrite = 1<<3
    SemanticChange = 1<<4
    StatusWrite = 1<<5
    TimestampWrite = 1<<6
    NonatomicRead = 1<<8
    NonatomicWrite = 1<<9
    WriteFullArrayOnly = 1<<10
    NoSubDataTypes = 1<<11
    NonVolatile = 1<<12
    Constant = 1<<13

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class EventNotifierType(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part3/8.59

    :ivar SubscribeToEvents:
    :vartype SubscribeToEvents: Bit: 0
    :ivar HistoryRead:
    :vartype HistoryRead: Bit: 2
    :ivar HistoryWrite:
    :vartype HistoryWrite: Bit: 3
    """
    SubscribeToEvents = 1<<0
    HistoryRead = 1<<2
    HistoryWrite = 1<<3

    @staticmethod
    def datatype() -> str:
        return "Byte"


class AccessRestrictionType(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.9/#12.2.9.13

    :ivar SigningRequired:
    :vartype SigningRequired: Bit: 0
    :ivar EncryptionRequired:
    :vartype EncryptionRequired: Bit: 1
    :ivar SessionRequired:
    :vartype SessionRequired: Bit: 2
    :ivar ApplyRestrictionsToBrowse:
    :vartype ApplyRestrictionsToBrowse: Bit: 3
    """
    SigningRequired = 1<<0
    EncryptionRequired = 1<<1
    SessionRequired = 1<<2
    ApplyRestrictionsToBrowse = 1<<3

    @staticmethod
    def datatype() -> str:
        return "UInt16"


class StructureType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.5/#12.2.5.3

    :ivar Structure:
    :vartype Structure: 0
    :ivar StructureWithOptionalFields:
    :vartype StructureWithOptionalFields: 1
    :ivar Union:
    :vartype Union: 2
    :ivar StructureWithSubtypedValues:
    :vartype StructureWithSubtypedValues: 3
    :ivar UnionWithSubtypedValues:
    :vartype UnionWithSubtypedValues: 4
    """
    Structure = 0
    StructureWithOptionalFields = 1
    Union = 2
    StructureWithSubtypedValues = 3
    UnionWithSubtypedValues = 4


class ApplicationType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.4

    :ivar Server:
    :vartype Server: 0
    :ivar Client:
    :vartype Client: 1
    :ivar ClientAndServer:
    :vartype ClientAndServer: 2
    :ivar DiscoveryServer:
    :vartype DiscoveryServer: 3
    """
    Server = 0
    Client = 1
    ClientAndServer = 2
    DiscoveryServer = 3


class MessageSecurityMode(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.10

    :ivar Invalid:
    :vartype Invalid: 0
    :ivar None_:
    :vartype None_: 1
    :ivar Sign:
    :vartype Sign: 2
    :ivar SignAndEncrypt:
    :vartype SignAndEncrypt: 3
    """
    Invalid = 0
    None_ = 1
    Sign = 2
    SignAndEncrypt = 3


class UserTokenType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.43

    :ivar Anonymous:
    :vartype Anonymous: 0
    :ivar UserName:
    :vartype UserName: 1
    :ivar Certificate:
    :vartype Certificate: 2
    :ivar IssuedToken:
    :vartype IssuedToken: 3
    """
    Anonymous = 0
    UserName = 1
    Certificate = 2
    IssuedToken = 3


class SecurityTokenRequestType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.12

    :ivar Issue:
    :vartype Issue: 0
    :ivar Renew:
    :vartype Renew: 1
    """
    Issue = 0
    Renew = 1


class NodeAttributesMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar AccessLevel:
    :vartype AccessLevel: 1
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: 2
    :ivar BrowseName:
    :vartype BrowseName: 4
    :ivar ContainsNoLoops:
    :vartype ContainsNoLoops: 8
    :ivar DataType:
    :vartype DataType: 16
    :ivar Description:
    :vartype Description: 32
    :ivar DisplayName:
    :vartype DisplayName: 64
    :ivar EventNotifier:
    :vartype EventNotifier: 128
    :ivar Executable:
    :vartype Executable: 256
    :ivar Historizing:
    :vartype Historizing: 512
    :ivar InverseName:
    :vartype InverseName: 1024
    :ivar IsAbstract:
    :vartype IsAbstract: 2048
    :ivar MinimumSamplingInterval:
    :vartype MinimumSamplingInterval: 4096
    :ivar NodeClass:
    :vartype NodeClass: 8192
    :ivar NodeId:
    :vartype NodeId: 16384
    :ivar Symmetric:
    :vartype Symmetric: 32768
    :ivar UserAccessLevel:
    :vartype UserAccessLevel: 65536
    :ivar UserExecutable:
    :vartype UserExecutable: 131072
    :ivar UserWriteMask:
    :vartype UserWriteMask: 262144
    :ivar ValueRank:
    :vartype ValueRank: 524288
    :ivar WriteMask:
    :vartype WriteMask: 1048576
    :ivar Value:
    :vartype Value: 2097152
    :ivar DataTypeDefinition:
    :vartype DataTypeDefinition: 4194304
    :ivar RolePermissions:
    :vartype RolePermissions: 8388608
    :ivar AccessRestrictions:
    :vartype AccessRestrictions: 16777216
    :ivar All:
    :vartype All: 33554431
    :ivar BaseNode:
    :vartype BaseNode: 26501220
    :ivar Object:
    :vartype Object: 26501348
    :ivar ObjectType:
    :vartype ObjectType: 26503268
    :ivar Variable:
    :vartype Variable: 26571383
    :ivar VariableType:
    :vartype VariableType: 28600438
    :ivar Method:
    :vartype Method: 26632548
    :ivar ReferenceType:
    :vartype ReferenceType: 26537060
    :ivar View:
    :vartype View: 26501356
    """
    None_ = 0
    AccessLevel = 1
    ArrayDimensions = 2
    BrowseName = 4
    ContainsNoLoops = 8
    DataType = 16
    Description = 32
    DisplayName = 64
    EventNotifier = 128
    Executable = 256
    Historizing = 512
    InverseName = 1024
    IsAbstract = 2048
    MinimumSamplingInterval = 4096
    NodeClass = 8192
    NodeId = 16384
    Symmetric = 32768
    UserAccessLevel = 65536
    UserExecutable = 131072
    UserWriteMask = 262144
    ValueRank = 524288
    WriteMask = 1048576
    Value = 2097152
    DataTypeDefinition = 4194304
    RolePermissions = 8388608
    AccessRestrictions = 16777216
    All = 33554431
    BaseNode = 26501220
    Object = 26501348
    ObjectType = 26503268
    Variable = 26571383
    VariableType = 28600438
    Method = 26632548
    ReferenceType = 26537060
    View = 26501356


class AttributeWriteMask(IntFlag):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part3/8.60

    :ivar AccessLevel:
    :vartype AccessLevel: Bit: 0
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: Bit: 1
    :ivar BrowseName:
    :vartype BrowseName: Bit: 2
    :ivar ContainsNoLoops:
    :vartype ContainsNoLoops: Bit: 3
    :ivar DataType:
    :vartype DataType: Bit: 4
    :ivar Description:
    :vartype Description: Bit: 5
    :ivar DisplayName:
    :vartype DisplayName: Bit: 6
    :ivar EventNotifier:
    :vartype EventNotifier: Bit: 7
    :ivar Executable:
    :vartype Executable: Bit: 8
    :ivar Historizing:
    :vartype Historizing: Bit: 9
    :ivar InverseName:
    :vartype InverseName: Bit: 10
    :ivar IsAbstract:
    :vartype IsAbstract: Bit: 11
    :ivar MinimumSamplingInterval:
    :vartype MinimumSamplingInterval: Bit: 12
    :ivar NodeClass:
    :vartype NodeClass: Bit: 13
    :ivar NodeId:
    :vartype NodeId: Bit: 14
    :ivar Symmetric:
    :vartype Symmetric: Bit: 15
    :ivar UserAccessLevel:
    :vartype UserAccessLevel: Bit: 16
    :ivar UserExecutable:
    :vartype UserExecutable: Bit: 17
    :ivar UserWriteMask:
    :vartype UserWriteMask: Bit: 18
    :ivar ValueRank:
    :vartype ValueRank: Bit: 19
    :ivar WriteMask:
    :vartype WriteMask: Bit: 20
    :ivar ValueForVariableType:
    :vartype ValueForVariableType: Bit: 21
    :ivar DataTypeDefinition:
    :vartype DataTypeDefinition: Bit: 22
    :ivar RolePermissions:
    :vartype RolePermissions: Bit: 23
    :ivar AccessRestrictions:
    :vartype AccessRestrictions: Bit: 24
    :ivar AccessLevelEx:
    :vartype AccessLevelEx: Bit: 25
    """
    AccessLevel = 1<<0
    ArrayDimensions = 1<<1
    BrowseName = 1<<2
    ContainsNoLoops = 1<<3
    DataType = 1<<4
    Description = 1<<5
    DisplayName = 1<<6
    EventNotifier = 1<<7
    Executable = 1<<8
    Historizing = 1<<9
    InverseName = 1<<10
    IsAbstract = 1<<11
    MinimumSamplingInterval = 1<<12
    NodeClass = 1<<13
    NodeId = 1<<14
    Symmetric = 1<<15
    UserAccessLevel = 1<<16
    UserExecutable = 1<<17
    UserWriteMask = 1<<18
    ValueRank = 1<<19
    WriteMask = 1<<20
    ValueForVariableType = 1<<21
    DataTypeDefinition = 1<<22
    RolePermissions = 1<<23
    AccessRestrictions = 1<<24
    AccessLevelEx = 1<<25

    @staticmethod
    def datatype() -> str:
        return "UInt32"


class BrowseDirection(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.5

    :ivar Forward:
    :vartype Forward: 0
    :ivar Inverse:
    :vartype Inverse: 1
    :ivar Both:
    :vartype Both: 2
    :ivar Invalid:
    :vartype Invalid: 3
    """
    Forward = 0
    Inverse = 1
    Both = 2
    Invalid = 3


class BrowseResultMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: 1
    :ivar IsForward:
    :vartype IsForward: 2
    :ivar NodeClass:
    :vartype NodeClass: 4
    :ivar BrowseName:
    :vartype BrowseName: 8
    :ivar DisplayName:
    :vartype DisplayName: 16
    :ivar TypeDefinition:
    :vartype TypeDefinition: 32
    :ivar All:
    :vartype All: 63
    :ivar ReferenceTypeInfo:
    :vartype ReferenceTypeInfo: 3
    :ivar TargetInfo:
    :vartype TargetInfo: 60
    """
    None_ = 0
    ReferenceTypeId = 1
    IsForward = 2
    NodeClass = 4
    BrowseName = 8
    DisplayName = 16
    TypeDefinition = 32
    All = 63
    ReferenceTypeInfo = 3
    TargetInfo = 60


class FilterOperator(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.3

    :ivar Equals:
    :vartype Equals: 0
    :ivar IsNull:
    :vartype IsNull: 1
    :ivar GreaterThan:
    :vartype GreaterThan: 2
    :ivar LessThan:
    :vartype LessThan: 3
    :ivar GreaterThanOrEqual:
    :vartype GreaterThanOrEqual: 4
    :ivar LessThanOrEqual:
    :vartype LessThanOrEqual: 5
    :ivar Like:
    :vartype Like: 6
    :ivar Not:
    :vartype Not: 7
    :ivar Between:
    :vartype Between: 8
    :ivar InList:
    :vartype InList: 9
    :ivar And:
    :vartype And: 10
    :ivar Or:
    :vartype Or: 11
    :ivar Cast:
    :vartype Cast: 12
    :ivar InView:
    :vartype InView: 13
    :ivar OfType:
    :vartype OfType: 14
    :ivar RelatedTo:
    :vartype RelatedTo: 15
    :ivar BitwiseAnd:
    :vartype BitwiseAnd: 16
    :ivar BitwiseOr:
    :vartype BitwiseOr: 17
    """
    Equals = 0
    IsNull = 1
    GreaterThan = 2
    LessThan = 3
    GreaterThanOrEqual = 4
    LessThanOrEqual = 5
    Like = 6
    Not = 7
    Between = 8
    InList = 9
    And = 10
    Or = 11
    Cast = 12
    InView = 13
    OfType = 14
    RelatedTo = 15
    BitwiseAnd = 16
    BitwiseOr = 17


class TimestampsToReturn(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.40

    :ivar Source:
    :vartype Source: 0
    :ivar Server:
    :vartype Server: 1
    :ivar Both:
    :vartype Both: 2
    :ivar Neither:
    :vartype Neither: 3
    :ivar Invalid:
    :vartype Invalid: 4
    """
    Source = 0
    Server = 1
    Both = 2
    Neither = 3
    Invalid = 4


class HistoryUpdateType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.7

    :ivar Insert:
    :vartype Insert: 1
    :ivar Replace:
    :vartype Replace: 2
    :ivar Update:
    :vartype Update: 3
    :ivar Delete:
    :vartype Delete: 4
    """
    Insert = 1
    Replace = 2
    Update = 3
    Delete = 4


class PerformUpdateType(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.8

    :ivar Insert:
    :vartype Insert: 1
    :ivar Replace:
    :vartype Replace: 2
    :ivar Update:
    :vartype Update: 3
    :ivar Remove:
    :vartype Remove: 4
    """
    Insert = 1
    Replace = 2
    Update = 3
    Remove = 4


class MonitoringMode(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.23

    :ivar Disabled:
    :vartype Disabled: 0
    :ivar Sampling:
    :vartype Sampling: 1
    :ivar Reporting:
    :vartype Reporting: 2
    """
    Disabled = 0
    Sampling = 1
    Reporting = 2


class DataChangeTrigger(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.10

    :ivar Status:
    :vartype Status: 0
    :ivar StatusValue:
    :vartype StatusValue: 1
    :ivar StatusValueTimestamp:
    :vartype StatusValueTimestamp: 2
    """
    Status = 0
    StatusValue = 1
    StatusValueTimestamp = 2


class DeadbandType(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar Absolute:
    :vartype Absolute: 1
    :ivar Percent:
    :vartype Percent: 2
    """
    None_ = 0
    Absolute = 1
    Percent = 2


class RedundancySupport(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.5

    :ivar None_:
    :vartype None_: 0
    :ivar Cold:
    :vartype Cold: 1
    :ivar Warm:
    :vartype Warm: 2
    :ivar Hot:
    :vartype Hot: 3
    :ivar Transparent:
    :vartype Transparent: 4
    :ivar HotAndMirrored:
    :vartype HotAndMirrored: 5
    """
    None_ = 0
    Cold = 1
    Warm = 2
    Hot = 3
    Transparent = 4
    HotAndMirrored = 5


class ServerState(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.6

    :ivar Running:
    :vartype Running: 0
    :ivar Failed:
    :vartype Failed: 1
    :ivar NoConfiguration:
    :vartype NoConfiguration: 2
    :ivar Suspended:
    :vartype Suspended: 3
    :ivar Shutdown:
    :vartype Shutdown: 4
    :ivar Test:
    :vartype Test: 5
    :ivar CommunicationFault:
    :vartype CommunicationFault: 6
    :ivar Unknown:
    :vartype Unknown: 7
    """
    Running = 0
    Failed = 1
    NoConfiguration = 2
    Suspended = 3
    Shutdown = 4
    Test = 5
    CommunicationFault = 6
    Unknown = 7


class ModelChangeStructureVerbMask(IntEnum):
    """
    :ivar NodeAdded:
    :vartype NodeAdded: 1
    :ivar NodeDeleted:
    :vartype NodeDeleted: 2
    :ivar ReferenceAdded:
    :vartype ReferenceAdded: 4
    :ivar ReferenceDeleted:
    :vartype ReferenceDeleted: 8
    :ivar DataTypeChanged:
    :vartype DataTypeChanged: 16
    """
    NodeAdded = 1
    NodeDeleted = 2
    ReferenceAdded = 4
    ReferenceDeleted = 8
    DataTypeChanged = 16


class AxisScaleEnumeration(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.7

    :ivar Linear:
    :vartype Linear: 0
    :ivar Log:
    :vartype Log: 1
    :ivar Ln:
    :vartype Ln: 2
    """
    Linear = 0
    Log = 1
    Ln = 2


class ExceptionDeviationFormat(IntEnum):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/5.2.2

    :ivar AbsoluteValue:
    :vartype AbsoluteValue: 0
    :ivar PercentOfValue:
    :vartype PercentOfValue: 1
    :ivar PercentOfRange:
    :vartype PercentOfRange: 2
    :ivar PercentOfEURange:
    :vartype PercentOfEURange: 3
    :ivar Unknown:
    :vartype Unknown: 4
    """
    AbsoluteValue = 0
    PercentOfValue = 1
    PercentOfRange = 2
    PercentOfEURange = 3
    Unknown = 4


@dataclass(frozen=FROZEN)
class Union:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.12

    """

    data_type = NodeId(ObjectIds.Union)


@dataclass(frozen=FROZEN)
class KeyValuePair:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.21

    :ivar Key:
    :vartype Key: QualifiedName
    :ivar Value:
    :vartype Value: Variant
    """

    data_type = NodeId(ObjectIds.KeyValuePair)

    Key: QualifiedName = field(default_factory=QualifiedName)
    Value: Variant = field(default_factory=Variant)


@dataclass(frozen=FROZEN)
class AdditionalParametersType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.1

    :ivar Parameters:
    :vartype Parameters: KeyValuePair
    """

    data_type = NodeId(ObjectIds.AdditionalParametersType)

    Parameters: List[KeyValuePair] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class EphemeralKeyType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.15

    :ivar PublicKey:
    :vartype PublicKey: ByteString
    :ivar Signature:
    :vartype Signature: ByteString
    """

    data_type = NodeId(ObjectIds.EphemeralKeyType)

    PublicKey: ByteString = None
    Signature: ByteString = None


@dataclass(frozen=FROZEN)
class EndpointType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part18/4.4.2

    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    :ivar TransportProfileUri:
    :vartype TransportProfileUri: String
    """

    data_type = NodeId(ObjectIds.EndpointType)

    EndpointUrl: String = None
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityPolicyUri: String = None
    TransportProfileUri: String = None


@dataclass(frozen=FROZEN)
class BitFieldDefinition:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.45

    :ivar Name:
    :vartype Name: String
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar Reserved:
    :vartype Reserved: Boolean
    :ivar StartingBitPosition:
    :vartype StartingBitPosition: UInt32
    :ivar EndingBitPosition:
    :vartype EndingBitPosition: UInt32
    """

    data_type = NodeId(ObjectIds.BitFieldDefinition)

    Name: String = None
    Description: LocalizedText = field(default_factory=LocalizedText)
    Reserved: Boolean = True
    StartingBitPosition: UInt32 = 0
    EndingBitPosition: UInt32 = 0


@dataclass(frozen=FROZEN)
class RationalNumber:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.22

    :ivar Numerator:
    :vartype Numerator: Int32
    :ivar Denominator:
    :vartype Denominator: UInt32
    """

    data_type = NodeId(ObjectIds.RationalNumber)

    Numerator: Int32 = 0
    Denominator: UInt32 = 0


@dataclass(frozen=FROZEN)
class Vector:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.23

    """

    data_type = NodeId(ObjectIds.Vector)


@dataclass(frozen=FROZEN)
class ThreeDVector(Vector):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.24

    :ivar X:
    :vartype X: Double
    :ivar Y:
    :vartype Y: Double
    :ivar Z:
    :vartype Z: Double
    """

    data_type = NodeId(ObjectIds.ThreeDVector)

    X: Double = 0
    Y: Double = 0
    Z: Double = 0


@dataclass(frozen=FROZEN)
class CartesianCoordinates:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.25

    """

    data_type = NodeId(ObjectIds.CartesianCoordinates)


@dataclass(frozen=FROZEN)
class ThreeDCartesianCoordinates(CartesianCoordinates):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.26

    :ivar X:
    :vartype X: Double
    :ivar Y:
    :vartype Y: Double
    :ivar Z:
    :vartype Z: Double
    """

    data_type = NodeId(ObjectIds.ThreeDCartesianCoordinates)

    X: Double = 0
    Y: Double = 0
    Z: Double = 0


@dataclass(frozen=FROZEN)
class Orientation:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.27

    """

    data_type = NodeId(ObjectIds.Orientation)


@dataclass(frozen=FROZEN)
class ThreeDOrientation(Orientation):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.28

    :ivar A:
    :vartype A: Double
    :ivar B:
    :vartype B: Double
    :ivar C:
    :vartype C: Double
    """

    data_type = NodeId(ObjectIds.ThreeDOrientation)

    A: Double = 0
    B: Double = 0
    C: Double = 0


@dataclass(frozen=FROZEN)
class Frame:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.29

    """

    data_type = NodeId(ObjectIds.Frame)


@dataclass(frozen=FROZEN)
class ThreeDFrame(Frame):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.30

    :ivar CartesianCoordinates:
    :vartype CartesianCoordinates: ThreeDCartesianCoordinates
    :ivar Orientation:
    :vartype Orientation: ThreeDOrientation
    """

    data_type = NodeId(ObjectIds.ThreeDFrame)

    CartesianCoordinates: ThreeDCartesianCoordinates = field(default_factory=ThreeDCartesianCoordinates)
    Orientation: ThreeDOrientation = field(default_factory=ThreeDOrientation)


@dataclass(frozen=FROZEN)
class IdentityMappingRuleType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part18/4.4.3

    :ivar CriteriaType:
    :vartype CriteriaType: IdentityCriteriaType
    :ivar Criteria:
    :vartype Criteria: String
    """

    data_type = NodeId(ObjectIds.IdentityMappingRuleType)

    CriteriaType: IdentityCriteriaType = IdentityCriteriaType.UserName
    Criteria: String = None


@dataclass(frozen=FROZEN)
class CurrencyUnitType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.2

    :ivar NumericCode:
    :vartype NumericCode: Int16
    :ivar Exponent:
    :vartype Exponent: SByte
    :ivar AlphabeticCode:
    :vartype AlphabeticCode: String
    :ivar Currency:
    :vartype Currency: LocalizedText
    """

    data_type = NodeId(ObjectIds.CurrencyUnitType)

    NumericCode: Int16 = 0
    Exponent: SByte = field(default_factory=SByte)
    AlphabeticCode: String = None
    Currency: LocalizedText = field(default_factory=LocalizedText)


@dataclass(frozen=FROZEN)
class AnnotationDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/6.6.1

    :ivar Annotation:
    :vartype Annotation: String
    :ivar Discipline:
    :vartype Discipline: String
    :ivar Uri:
    :vartype Uri: String
    """

    data_type = NodeId(ObjectIds.AnnotationDataType)

    Annotation: String = None
    Discipline: String = None
    Uri: String = None


@dataclass(frozen=FROZEN)
class LinearConversionDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/6.6.2

    :ivar InitialAddend:
    :vartype InitialAddend: Float
    :ivar Multiplicand:
    :vartype Multiplicand: Float
    :ivar Divisor:
    :vartype Divisor: Float
    :ivar FinalAddend:
    :vartype FinalAddend: Float
    """

    data_type = NodeId(ObjectIds.LinearConversionDataType)

    InitialAddend: Float = 0
    Multiplicand: Float = 0
    Divisor: Float = 0
    FinalAddend: Float = 0


@dataclass(frozen=FROZEN)
class QuantityDimension:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/6.6.4

    :ivar MassExponent:
    :vartype MassExponent: SByte
    :ivar LengthExponent:
    :vartype LengthExponent: SByte
    :ivar TimeExponent:
    :vartype TimeExponent: SByte
    :ivar ElectricCurrentExponent:
    :vartype ElectricCurrentExponent: SByte
    :ivar AmountOfSubstanceExponent:
    :vartype AmountOfSubstanceExponent: SByte
    :ivar LuminousIntensityExponent:
    :vartype LuminousIntensityExponent: SByte
    :ivar AbsoluteTemperatureExponent:
    :vartype AbsoluteTemperatureExponent: SByte
    :ivar DimensionlessExponent:
    :vartype DimensionlessExponent: SByte
    """

    data_type = NodeId(ObjectIds.QuantityDimension)

    MassExponent: SByte = field(default_factory=SByte)
    LengthExponent: SByte = field(default_factory=SByte)
    TimeExponent: SByte = field(default_factory=SByte)
    ElectricCurrentExponent: SByte = field(default_factory=SByte)
    AmountOfSubstanceExponent: SByte = field(default_factory=SByte)
    LuminousIntensityExponent: SByte = field(default_factory=SByte)
    AbsoluteTemperatureExponent: SByte = field(default_factory=SByte)
    DimensionlessExponent: SByte = field(default_factory=SByte)


@dataclass(frozen=FROZEN)
class TrustListDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part12/7.8.2/#7.8.2.6

    :ivar SpecifiedLists:
    :vartype SpecifiedLists: UInt32
    :ivar TrustedCertificates:
    :vartype TrustedCertificates: ByteString
    :ivar TrustedCrls:
    :vartype TrustedCrls: ByteString
    :ivar IssuerCertificates:
    :vartype IssuerCertificates: ByteString
    :ivar IssuerCrls:
    :vartype IssuerCrls: ByteString
    """

    data_type = NodeId(ObjectIds.TrustListDataType)

    SpecifiedLists: UInt32 = 0
    TrustedCertificates: List[ByteString] = field(default_factory=list)
    TrustedCrls: List[ByteString] = field(default_factory=list)
    IssuerCertificates: List[ByteString] = field(default_factory=list)
    IssuerCrls: List[ByteString] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class TransactionErrorType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part12/7.10.12

    :ivar TargetId:
    :vartype TargetId: NodeId
    :ivar Error:
    :vartype Error: StatusCode
    :ivar Message:
    :vartype Message: LocalizedText
    """

    data_type = NodeId(ObjectIds.TransactionErrorType)

    TargetId: NodeId = field(default_factory=NodeId)
    Error: StatusCode = field(default_factory=StatusCode)
    Message: LocalizedText = field(default_factory=LocalizedText)


@dataclass(frozen=FROZEN)
class DecimalDataType:
    """
    :ivar Scale:
    :vartype Scale: Int16
    :ivar Value:
    :vartype Value: ByteString
    """

    data_type = NodeId(ObjectIds.DecimalDataType)

    Scale: Int16 = 0
    Value: ByteString = None


@dataclass(frozen=FROZEN)
class DataTypeDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.32

    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    """

    data_type = NodeId(ObjectIds.DataTypeDescription)

    DataTypeId: NodeId = field(default_factory=NodeId)
    Name: QualifiedName = field(default_factory=QualifiedName)


@dataclass(frozen=FROZEN)
class SimpleTypeDescription(DataTypeDescription):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.35

    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    :ivar BaseDataType:
    :vartype BaseDataType: NodeId
    :ivar BuiltInType:
    :vartype BuiltInType: Byte
    """

    data_type = NodeId(ObjectIds.SimpleTypeDescription)

    DataTypeId: NodeId = field(default_factory=NodeId)
    Name: QualifiedName = field(default_factory=QualifiedName)
    BaseDataType: NodeId = field(default_factory=NodeId)
    BuiltInType: Byte = 0


@dataclass(frozen=FROZEN)
class PortableQualifiedName:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.37

    :ivar NamespaceUri:
    :vartype NamespaceUri: String
    :ivar Name:
    :vartype Name: String
    """

    data_type = NodeId(ObjectIds.PortableQualifiedName)

    NamespaceUri: String = None
    Name: String = None


@dataclass(frozen=FROZEN)
class UnsignedRationalNumber:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.40

    :ivar Numerator:
    :vartype Numerator: UInt32
    :ivar Denominator:
    :vartype Denominator: UInt32
    """

    data_type = NodeId(ObjectIds.UnsignedRationalNumber)

    Numerator: UInt32 = 0
    Denominator: UInt32 = 0


@dataclass(frozen=FROZEN)
class FieldMetaData:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.2.4

    :ivar Name:
    :vartype Name: String
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar FieldFlags:
    :vartype FieldFlags: DataSetFieldFlags
    :ivar BuiltInType:
    :vartype BuiltInType: Byte
    :ivar DataType:
    :vartype DataType: NodeId
    :ivar ValueRank:
    :vartype ValueRank: Int32
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: UInt32
    :ivar MaxStringLength:
    :vartype MaxStringLength: UInt32
    :ivar DataSetFieldId:
    :vartype DataSetFieldId: Guid
    :ivar Properties:
    :vartype Properties: KeyValuePair
    """

    data_type = NodeId(ObjectIds.FieldMetaData)

    Name: String = None
    Description: LocalizedText = field(default_factory=LocalizedText)
    FieldFlags: DataSetFieldFlags = field(default_factory=lambda:DataSetFieldFlags(0))
    BuiltInType: Byte = 0
    DataType: NodeId = field(default_factory=NodeId)
    ValueRank: Int32 = 0
    ArrayDimensions: List[UInt32] = field(default_factory=list)
    MaxStringLength: UInt32 = 0
    DataSetFieldId: Guid = Guid(int=0)
    Properties: List[KeyValuePair] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class ConfigurationVersionDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.2.6

    :ivar MajorVersion:
    :vartype MajorVersion: VersionTime
    :ivar MinorVersion:
    :vartype MinorVersion: VersionTime
    """

    data_type = NodeId(ObjectIds.ConfigurationVersionDataType)

    MajorVersion: VersionTime = 0
    MinorVersion: VersionTime = 0


@dataclass(frozen=FROZEN)
class PublishedDataSetSourceDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.6

    """

    data_type = NodeId(ObjectIds.PublishedDataSetSourceDataType)


@dataclass(frozen=FROZEN)
class PublishedVariableDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.7.1

    :ivar PublishedVariable:
    :vartype PublishedVariable: NodeId
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar SamplingIntervalHint:
    :vartype SamplingIntervalHint: Duration
    :ivar DeadbandType:
    :vartype DeadbandType: UInt32
    :ivar DeadbandValue:
    :vartype DeadbandValue: Double
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    :ivar SubstituteValue:
    :vartype SubstituteValue: Variant
    :ivar MetaDataProperties:
    :vartype MetaDataProperties: QualifiedName
    """

    data_type = NodeId(ObjectIds.PublishedVariableDataType)

    PublishedVariable: NodeId = field(default_factory=NodeId)
    AttributeId: IntegerId = 0
    SamplingIntervalHint: Duration = 0
    DeadbandType: UInt32 = 0
    DeadbandValue: Double = 0
    IndexRange: NumericRange = None
    SubstituteValue: Variant = field(default_factory=Variant)
    MetaDataProperties: List[QualifiedName] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class PublishedDataItemsDataType(PublishedDataSetSourceDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.7.2

    :ivar PublishedData:
    :vartype PublishedData: PublishedVariableDataType
    """

    data_type = NodeId(ObjectIds.PublishedDataItemsDataType)

    PublishedData: List[PublishedVariableDataType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class PublishedDataSetCustomSourceDataType(PublishedDataSetSourceDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.9.2

    :ivar CyclicDataSet:
    :vartype CyclicDataSet: Boolean
    """

    data_type = NodeId(ObjectIds.PublishedDataSetCustomSourceDataType)

    CyclicDataSet: Boolean = True


@dataclass(frozen=FROZEN)
class DataSetWriterTransportDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.4/#6.2.4.5.2

    """

    data_type = NodeId(ObjectIds.DataSetWriterTransportDataType)


@dataclass(frozen=FROZEN)
class DataSetWriterMessageDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.4/#6.2.4.5.3

    """

    data_type = NodeId(ObjectIds.DataSetWriterMessageDataType)


@dataclass(frozen=FROZEN)
class DataSetWriterDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.4/#6.2.4.5.1

    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar DataSetWriterId:
    :vartype DataSetWriterId: UInt16
    :ivar DataSetFieldContentMask:
    :vartype DataSetFieldContentMask: DataSetFieldContentMask
    :ivar KeyFrameCount:
    :vartype KeyFrameCount: UInt32
    :ivar DataSetName:
    :vartype DataSetName: String
    :ivar DataSetWriterProperties:
    :vartype DataSetWriterProperties: KeyValuePair
    :ivar TransportSettings:
    :vartype TransportSettings: DataSetWriterTransportDataType
    :ivar MessageSettings:
    :vartype MessageSettings: DataSetWriterMessageDataType
    """

    data_type = NodeId(ObjectIds.DataSetWriterDataType)

    Name: String = None
    Enabled: Boolean = True
    DataSetWriterId: UInt16 = 0
    DataSetFieldContentMask_: DataSetFieldContentMask = field(default_factory=lambda:DataSetFieldContentMask(0))
    KeyFrameCount: UInt32 = 0
    DataSetName: String = None
    DataSetWriterProperties: List[KeyValuePair] = field(default_factory=list)
    TransportSettings: Type[DataSetWriterTransportDataType] = field(default_factory=DataSetWriterTransportDataType)
    MessageSettings: Type[DataSetWriterMessageDataType] = field(default_factory=DataSetWriterMessageDataType)

    @property
    def DataSetFieldContentMask(self):
        return self.DataSetFieldContentMask_

    @DataSetFieldContentMask.setter
    def DataSetFieldContentMask(self, val):
        self.DataSetFieldContentMask_ = val


@dataclass(frozen=FROZEN)
class WriterGroupTransportDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.6/#6.2.6.7.2

    """

    data_type = NodeId(ObjectIds.WriterGroupTransportDataType)


@dataclass(frozen=FROZEN)
class WriterGroupMessageDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.6/#6.2.6.7.3

    """

    data_type = NodeId(ObjectIds.WriterGroupMessageDataType)


@dataclass(frozen=FROZEN)
class ConnectionTransportDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.7/#6.2.7.5.2

    """

    data_type = NodeId(ObjectIds.ConnectionTransportDataType)


@dataclass(frozen=FROZEN)
class NetworkAddressDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.7/#6.2.7.5.3

    :ivar NetworkInterface:
    :vartype NetworkInterface: String
    """

    data_type = NodeId(ObjectIds.NetworkAddressDataType)

    NetworkInterface: String = None


@dataclass(frozen=FROZEN)
class NetworkAddressUrlDataType(NetworkAddressDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.7/#6.2.7.5.4

    :ivar NetworkInterface:
    :vartype NetworkInterface: String
    :ivar Url:
    :vartype Url: String
    """

    data_type = NodeId(ObjectIds.NetworkAddressUrlDataType)

    NetworkInterface: String = None
    Url: String = None


@dataclass(frozen=FROZEN)
class ReaderGroupTransportDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.8/#6.2.8.2.2

    """

    data_type = NodeId(ObjectIds.ReaderGroupTransportDataType)


@dataclass(frozen=FROZEN)
class ReaderGroupMessageDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.8/#6.2.8.2.3

    """

    data_type = NodeId(ObjectIds.ReaderGroupMessageDataType)


@dataclass(frozen=FROZEN)
class DataSetReaderTransportDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.9/#6.2.9.13.2

    """

    data_type = NodeId(ObjectIds.DataSetReaderTransportDataType)


@dataclass(frozen=FROZEN)
class DataSetReaderMessageDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.9/#6.2.9.13.3

    """

    data_type = NodeId(ObjectIds.DataSetReaderMessageDataType)


@dataclass(frozen=FROZEN)
class SubscribedDataSetDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.1

    """

    data_type = NodeId(ObjectIds.SubscribedDataSetDataType)


@dataclass(frozen=FROZEN)
class FieldTargetDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.2.3

    :ivar DataSetFieldId:
    :vartype DataSetFieldId: Guid
    :ivar ReceiverIndexRange:
    :vartype ReceiverIndexRange: NumericRange
    :ivar TargetNodeId:
    :vartype TargetNodeId: NodeId
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar WriteIndexRange:
    :vartype WriteIndexRange: NumericRange
    :ivar OverrideValueHandling:
    :vartype OverrideValueHandling: OverrideValueHandling
    :ivar OverrideValue:
    :vartype OverrideValue: Variant
    """

    data_type = NodeId(ObjectIds.FieldTargetDataType)

    DataSetFieldId: Guid = Guid(int=0)
    ReceiverIndexRange: NumericRange = None
    TargetNodeId: NodeId = field(default_factory=NodeId)
    AttributeId: IntegerId = 0
    WriteIndexRange: NumericRange = None
    OverrideValueHandling_: OverrideValueHandling = OverrideValueHandling.Disabled
    OverrideValue: Variant = field(default_factory=Variant)

    @property
    def OverrideValueHandling(self):
        return self.OverrideValueHandling_

    @OverrideValueHandling.setter
    def OverrideValueHandling(self, val):
        self.OverrideValueHandling_ = val


@dataclass(frozen=FROZEN)
class TargetVariablesDataType(SubscribedDataSetDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.2.2

    :ivar TargetVariables:
    :vartype TargetVariables: FieldTargetDataType
    """

    data_type = NodeId(ObjectIds.TargetVariablesDataType)

    TargetVariables: List[FieldTargetDataType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class StandaloneSubscribedDataSetRefDataType(SubscribedDataSetDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.4

    :ivar DataSetName:
    :vartype DataSetName: String
    """

    data_type = NodeId(ObjectIds.StandaloneSubscribedDataSetRefDataType)

    DataSetName: String = None


@dataclass(frozen=FROZEN)
class UadpWriterGroupMessageDataType(WriterGroupMessageDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.1/#6.3.1.1.7

    :ivar GroupVersion:
    :vartype GroupVersion: VersionTime
    :ivar DataSetOrdering:
    :vartype DataSetOrdering: DataSetOrderingType
    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: UadpNetworkMessageContentMask
    :ivar SamplingOffset:
    :vartype SamplingOffset: Duration
    :ivar PublishingOffset:
    :vartype PublishingOffset: Duration
    """

    data_type = NodeId(ObjectIds.UadpWriterGroupMessageDataType)

    GroupVersion: VersionTime = 0
    DataSetOrdering: DataSetOrderingType = DataSetOrderingType.Undefined
    NetworkMessageContentMask: UadpNetworkMessageContentMask = field(default_factory=lambda:UadpNetworkMessageContentMask(0))
    SamplingOffset: Duration = 0
    PublishingOffset: List[Duration] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class UadpDataSetWriterMessageDataType(DataSetWriterMessageDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.1/#6.3.1.3.6

    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: UadpDataSetMessageContentMask
    :ivar ConfiguredSize:
    :vartype ConfiguredSize: UInt16
    :ivar NetworkMessageNumber:
    :vartype NetworkMessageNumber: UInt16
    :ivar DataSetOffset:
    :vartype DataSetOffset: UInt16
    """

    data_type = NodeId(ObjectIds.UadpDataSetWriterMessageDataType)

    DataSetMessageContentMask: UadpDataSetMessageContentMask = field(default_factory=lambda:UadpDataSetMessageContentMask(0))
    ConfiguredSize: UInt16 = 0
    NetworkMessageNumber: UInt16 = 0
    DataSetOffset: UInt16 = 0


@dataclass(frozen=FROZEN)
class UadpDataSetReaderMessageDataType(DataSetReaderMessageDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.1/#6.3.1.4.10

    :ivar GroupVersion:
    :vartype GroupVersion: VersionTime
    :ivar NetworkMessageNumber:
    :vartype NetworkMessageNumber: UInt16
    :ivar DataSetOffset:
    :vartype DataSetOffset: UInt16
    :ivar DataSetClassId:
    :vartype DataSetClassId: Guid
    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: UadpNetworkMessageContentMask
    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: UadpDataSetMessageContentMask
    :ivar PublishingInterval:
    :vartype PublishingInterval: Duration
    :ivar ReceiveOffset:
    :vartype ReceiveOffset: Duration
    :ivar ProcessingOffset:
    :vartype ProcessingOffset: Duration
    """

    data_type = NodeId(ObjectIds.UadpDataSetReaderMessageDataType)

    GroupVersion: VersionTime = 0
    NetworkMessageNumber: UInt16 = 0
    DataSetOffset: UInt16 = 0
    DataSetClassId: Guid = Guid(int=0)
    NetworkMessageContentMask: UadpNetworkMessageContentMask = field(default_factory=lambda:UadpNetworkMessageContentMask(0))
    DataSetMessageContentMask: UadpDataSetMessageContentMask = field(default_factory=lambda:UadpDataSetMessageContentMask(0))
    PublishingInterval: Duration = 0
    ReceiveOffset: Duration = 0
    ProcessingOffset: Duration = 0


@dataclass(frozen=FROZEN)
class JsonWriterGroupMessageDataType(WriterGroupMessageDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.2/#6.3.2.1.2

    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: JsonNetworkMessageContentMask
    """

    data_type = NodeId(ObjectIds.JsonWriterGroupMessageDataType)

    NetworkMessageContentMask: JsonNetworkMessageContentMask = field(default_factory=lambda:JsonNetworkMessageContentMask(0))


@dataclass(frozen=FROZEN)
class JsonDataSetWriterMessageDataType(DataSetWriterMessageDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.2/#6.3.2.3.2

    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: JsonDataSetMessageContentMask
    """

    data_type = NodeId(ObjectIds.JsonDataSetWriterMessageDataType)

    DataSetMessageContentMask: JsonDataSetMessageContentMask = field(default_factory=lambda:JsonDataSetMessageContentMask(0))


@dataclass(frozen=FROZEN)
class JsonDataSetReaderMessageDataType(DataSetReaderMessageDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.3.2/#6.3.2.4.3

    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: JsonNetworkMessageContentMask
    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: JsonDataSetMessageContentMask
    """

    data_type = NodeId(ObjectIds.JsonDataSetReaderMessageDataType)

    NetworkMessageContentMask: JsonNetworkMessageContentMask = field(default_factory=lambda:JsonNetworkMessageContentMask(0))
    DataSetMessageContentMask: JsonDataSetMessageContentMask = field(default_factory=lambda:JsonDataSetMessageContentMask(0))


@dataclass(frozen=FROZEN)
class QosDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.1.2

    """

    data_type = NodeId(ObjectIds.QosDataType)


@dataclass(frozen=FROZEN)
class TransmitQosDataType(QosDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.1.3

    """

    data_type = NodeId(ObjectIds.TransmitQosDataType)


@dataclass(frozen=FROZEN)
class TransmitQosPriorityDataType(TransmitQosDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.1.4.2

    :ivar PriorityLabel:
    :vartype PriorityLabel: String
    """

    data_type = NodeId(ObjectIds.TransmitQosPriorityDataType)

    PriorityLabel: String = None


@dataclass(frozen=FROZEN)
class ReceiveQosDataType(QosDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.1.5

    """

    data_type = NodeId(ObjectIds.ReceiveQosDataType)


@dataclass(frozen=FROZEN)
class ReceiveQosPriorityDataType(ReceiveQosDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.1.6.2

    :ivar PriorityLabel:
    :vartype PriorityLabel: String
    """

    data_type = NodeId(ObjectIds.ReceiveQosPriorityDataType)

    PriorityLabel: String = None


@dataclass(frozen=FROZEN)
class DatagramConnectionTransportDataType(ConnectionTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.2.2

    :ivar DiscoveryAddress:
    :vartype DiscoveryAddress: NetworkAddressDataType
    """

    data_type = NodeId(ObjectIds.DatagramConnectionTransportDataType)

    DiscoveryAddress: Type[NetworkAddressDataType] = field(default_factory=NetworkAddressDataType)


@dataclass(frozen=FROZEN)
class DatagramConnectionTransport2DataType(DatagramConnectionTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.2.7

    :ivar DiscoveryAddress:
    :vartype DiscoveryAddress: NetworkAddressDataType
    :ivar DiscoveryAnnounceRate:
    :vartype DiscoveryAnnounceRate: UInt32
    :ivar DiscoveryMaxMessageSize:
    :vartype DiscoveryMaxMessageSize: UInt32
    :ivar QosCategory:
    :vartype QosCategory: String
    :ivar DatagramQos:
    :vartype DatagramQos: QosDataType
    """

    data_type = NodeId(ObjectIds.DatagramConnectionTransport2DataType)

    DiscoveryAddress: Type[NetworkAddressDataType] = field(default_factory=NetworkAddressDataType)
    DiscoveryAnnounceRate: UInt32 = 0
    DiscoveryMaxMessageSize: UInt32 = 0
    QosCategory: String = None
    DatagramQos: List[Type[QosDataType]] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DatagramWriterGroupTransportDataType(WriterGroupTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.3.3

    :ivar MessageRepeatCount:
    :vartype MessageRepeatCount: Byte
    :ivar MessageRepeatDelay:
    :vartype MessageRepeatDelay: Duration
    """

    data_type = NodeId(ObjectIds.DatagramWriterGroupTransportDataType)

    MessageRepeatCount: Byte = 0
    MessageRepeatDelay: Duration = 0


@dataclass(frozen=FROZEN)
class DatagramWriterGroupTransport2DataType(DatagramWriterGroupTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.3.9

    :ivar MessageRepeatCount:
    :vartype MessageRepeatCount: Byte
    :ivar MessageRepeatDelay:
    :vartype MessageRepeatDelay: Duration
    :ivar Address:
    :vartype Address: NetworkAddressDataType
    :ivar QosCategory:
    :vartype QosCategory: String
    :ivar DatagramQos:
    :vartype DatagramQos: TransmitQosDataType
    :ivar DiscoveryAnnounceRate:
    :vartype DiscoveryAnnounceRate: UInt32
    :ivar Topic:
    :vartype Topic: String
    """

    data_type = NodeId(ObjectIds.DatagramWriterGroupTransport2DataType)

    MessageRepeatCount: Byte = 0
    MessageRepeatDelay: Duration = 0
    Address: Type[NetworkAddressDataType] = field(default_factory=NetworkAddressDataType)
    QosCategory: String = None
    DatagramQos: List[Type[TransmitQosDataType]] = field(default_factory=list)
    DiscoveryAnnounceRate: UInt32 = 0
    Topic: String = None


@dataclass(frozen=FROZEN)
class DatagramDataSetReaderTransportDataType(DataSetReaderTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.1/#6.4.1.6.5

    :ivar Address:
    :vartype Address: NetworkAddressDataType
    :ivar QosCategory:
    :vartype QosCategory: String
    :ivar DatagramQos:
    :vartype DatagramQos: ReceiveQosDataType
    :ivar Topic:
    :vartype Topic: String
    """

    data_type = NodeId(ObjectIds.DatagramDataSetReaderTransportDataType)

    Address: Type[NetworkAddressDataType] = field(default_factory=NetworkAddressDataType)
    QosCategory: String = None
    DatagramQos: List[Type[ReceiveQosDataType]] = field(default_factory=list)
    Topic: String = None


@dataclass(frozen=FROZEN)
class BrokerConnectionTransportDataType(ConnectionTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.2/#6.4.2.2.3

    :ivar ResourceUri:
    :vartype ResourceUri: String
    :ivar AuthenticationProfileUri:
    :vartype AuthenticationProfileUri: String
    """

    data_type = NodeId(ObjectIds.BrokerConnectionTransportDataType)

    ResourceUri: String = None
    AuthenticationProfileUri: String = None


@dataclass(frozen=FROZEN)
class BrokerWriterGroupTransportDataType(WriterGroupTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.2/#6.4.2.3.5

    :ivar QueueName:
    :vartype QueueName: String
    :ivar ResourceUri:
    :vartype ResourceUri: String
    :ivar AuthenticationProfileUri:
    :vartype AuthenticationProfileUri: String
    :ivar RequestedDeliveryGuarantee:
    :vartype RequestedDeliveryGuarantee: BrokerTransportQualityOfService
    """

    data_type = NodeId(ObjectIds.BrokerWriterGroupTransportDataType)

    QueueName: String = None
    ResourceUri: String = None
    AuthenticationProfileUri: String = None
    RequestedDeliveryGuarantee: BrokerTransportQualityOfService = BrokerTransportQualityOfService.NotSpecified


@dataclass(frozen=FROZEN)
class BrokerDataSetWriterTransportDataType(DataSetWriterTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.2/#6.4.2.5.7

    :ivar QueueName:
    :vartype QueueName: String
    :ivar ResourceUri:
    :vartype ResourceUri: String
    :ivar AuthenticationProfileUri:
    :vartype AuthenticationProfileUri: String
    :ivar RequestedDeliveryGuarantee:
    :vartype RequestedDeliveryGuarantee: BrokerTransportQualityOfService
    :ivar MetaDataQueueName:
    :vartype MetaDataQueueName: String
    :ivar MetaDataUpdateTime:
    :vartype MetaDataUpdateTime: Duration
    """

    data_type = NodeId(ObjectIds.BrokerDataSetWriterTransportDataType)

    QueueName: String = None
    ResourceUri: String = None
    AuthenticationProfileUri: String = None
    RequestedDeliveryGuarantee: BrokerTransportQualityOfService = BrokerTransportQualityOfService.NotSpecified
    MetaDataQueueName: String = None
    MetaDataUpdateTime: Duration = 0


@dataclass(frozen=FROZEN)
class BrokerDataSetReaderTransportDataType(DataSetReaderTransportDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.4.2/#6.4.2.6.6

    :ivar QueueName:
    :vartype QueueName: String
    :ivar ResourceUri:
    :vartype ResourceUri: String
    :ivar AuthenticationProfileUri:
    :vartype AuthenticationProfileUri: String
    :ivar RequestedDeliveryGuarantee:
    :vartype RequestedDeliveryGuarantee: BrokerTransportQualityOfService
    :ivar MetaDataQueueName:
    :vartype MetaDataQueueName: String
    """

    data_type = NodeId(ObjectIds.BrokerDataSetReaderTransportDataType)

    QueueName: String = None
    ResourceUri: String = None
    AuthenticationProfileUri: String = None
    RequestedDeliveryGuarantee: BrokerTransportQualityOfService = BrokerTransportQualityOfService.NotSpecified
    MetaDataQueueName: String = None


@dataclass(frozen=FROZEN)
class PubSubConfigurationRefDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/9.1.3/#9.1.3.7.3

    :ivar ConfigurationMask:
    :vartype ConfigurationMask: PubSubConfigurationRefMask
    :ivar ElementIndex:
    :vartype ElementIndex: UInt16
    :ivar ConnectionIndex:
    :vartype ConnectionIndex: UInt16
    :ivar GroupIndex:
    :vartype GroupIndex: UInt16
    """

    data_type = NodeId(ObjectIds.PubSubConfigurationRefDataType)

    ConfigurationMask: PubSubConfigurationRefMask = field(default_factory=lambda:PubSubConfigurationRefMask(0))
    ElementIndex: UInt16 = 0
    ConnectionIndex: UInt16 = 0
    GroupIndex: UInt16 = 0


@dataclass(frozen=FROZEN)
class PubSubConfigurationValueDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/9.1.3/#9.1.3.7.4

    :ivar ConfigurationElement:
    :vartype ConfigurationElement: PubSubConfigurationRefDataType
    :ivar Name:
    :vartype Name: String
    :ivar Identifier:
    :vartype Identifier: Variant
    """

    data_type = NodeId(ObjectIds.PubSubConfigurationValueDataType)

    ConfigurationElement: PubSubConfigurationRefDataType = field(default_factory=PubSubConfigurationRefDataType)
    Name: String = None
    Identifier: Variant = field(default_factory=Variant)


@dataclass(frozen=FROZEN)
class AliasNameDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part17/7.2

    :ivar AliasName:
    :vartype AliasName: QualifiedName
    :ivar ReferencedNodes:
    :vartype ReferencedNodes: ExpandedNodeId
    """

    data_type = NodeId(ObjectIds.AliasNameDataType)

    AliasName: QualifiedName = field(default_factory=QualifiedName)
    ReferencedNodes: List[ExpandedNodeId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class UserManagementDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part18/5.2.4

    :ivar UserName:
    :vartype UserName: String
    :ivar UserConfiguration:
    :vartype UserConfiguration: UserConfigurationMask
    :ivar Description:
    :vartype Description: String
    """

    data_type = NodeId(ObjectIds.UserManagementDataType)

    UserName: String = None
    UserConfiguration: UserConfigurationMask = field(default_factory=lambda:UserConfigurationMask(0))
    Description: String = None


@dataclass(frozen=FROZEN)
class PriorityMappingEntryType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part22/5.3.2/#5.3.2.1

    :ivar MappingUri:
    :vartype MappingUri: String
    :ivar PriorityLabel:
    :vartype PriorityLabel: String
    :ivar PriorityValue_PCP:
    :vartype PriorityValue_PCP: Byte
    :ivar PriorityValue_DSCP:
    :vartype PriorityValue_DSCP: UInt32
    """

    data_type = NodeId(ObjectIds.PriorityMappingEntryType)

    MappingUri: String = None
    PriorityLabel: String = None
    PriorityValue_PCP: Byte = 0
    PriorityValue_DSCP: UInt32 = 0


@dataclass(frozen=FROZEN)
class ReferenceDescriptionDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part23/5.5.1

    :ivar SourceNode:
    :vartype SourceNode: NodeId
    :ivar ReferenceType:
    :vartype ReferenceType: NodeId
    :ivar IsForward:
    :vartype IsForward: Boolean
    :ivar TargetNode:
    :vartype TargetNode: ExpandedNodeId
    """

    data_type = NodeId(ObjectIds.ReferenceDescriptionDataType)

    SourceNode: NodeId = field(default_factory=NodeId)
    ReferenceType: NodeId = field(default_factory=NodeId)
    IsForward: Boolean = True
    TargetNode: ExpandedNodeId = field(default_factory=ExpandedNodeId)


@dataclass(frozen=FROZEN)
class ReferenceListEntryDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part23/5.5.2

    :ivar ReferenceType:
    :vartype ReferenceType: NodeId
    :ivar IsForward:
    :vartype IsForward: Boolean
    :ivar TargetNode:
    :vartype TargetNode: ExpandedNodeId
    """

    data_type = NodeId(ObjectIds.ReferenceListEntryDataType)

    ReferenceType: NodeId = field(default_factory=NodeId)
    IsForward: Boolean = True
    TargetNode: ExpandedNodeId = field(default_factory=ExpandedNodeId)


@dataclass(frozen=FROZEN)
class RolePermissionType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.9

    :ivar RoleId:
    :vartype RoleId: NodeId
    :ivar Permissions:
    :vartype Permissions: PermissionType
    """

    data_type = NodeId(ObjectIds.RolePermissionType)

    RoleId: NodeId = field(default_factory=NodeId)
    Permissions: PermissionType = field(default_factory=lambda:PermissionType(0))


@dataclass(frozen=FROZEN)
class SubscribedDataSetMirrorDataType(SubscribedDataSetDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.3.4

    :ivar ParentNodeName:
    :vartype ParentNodeName: String
    :ivar RolePermissions:
    :vartype RolePermissions: RolePermissionType
    """

    data_type = NodeId(ObjectIds.SubscribedDataSetMirrorDataType)

    ParentNodeName: String = None
    RolePermissions: List[RolePermissionType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SecurityGroupDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.12/#6.2.12.2

    :ivar Name:
    :vartype Name: String
    :ivar SecurityGroupFolder:
    :vartype SecurityGroupFolder: String
    :ivar KeyLifetime:
    :vartype KeyLifetime: Duration
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    :ivar MaxFutureKeyCount:
    :vartype MaxFutureKeyCount: UInt32
    :ivar MaxPastKeyCount:
    :vartype MaxPastKeyCount: UInt32
    :ivar SecurityGroupId:
    :vartype SecurityGroupId: String
    :ivar RolePermissions:
    :vartype RolePermissions: RolePermissionType
    :ivar GroupProperties:
    :vartype GroupProperties: KeyValuePair
    """

    data_type = NodeId(ObjectIds.SecurityGroupDataType)

    Name: String = None
    SecurityGroupFolder: List[String] = field(default_factory=list)
    KeyLifetime: Duration = 0
    SecurityPolicyUri: String = None
    MaxFutureKeyCount: UInt32 = 0
    MaxPastKeyCount: UInt32 = 0
    SecurityGroupId: String = None
    RolePermissions: List[RolePermissionType] = field(default_factory=list)
    GroupProperties: List[KeyValuePair] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DataTypeDefinition:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.3

    """

    data_type = NodeId(ObjectIds.DataTypeDefinition)


@dataclass(frozen=FROZEN)
class StructureField:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.10

    :ivar Name:
    :vartype Name: String
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar DataType:
    :vartype DataType: NodeId
    :ivar ValueRank:
    :vartype ValueRank: Int32
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: UInt32
    :ivar MaxStringLength:
    :vartype MaxStringLength: UInt32
    :ivar IsOptional:
    :vartype IsOptional: Boolean
    """

    data_type = NodeId(ObjectIds.StructureField)

    Name: String = None
    Description: LocalizedText = field(default_factory=LocalizedText)
    DataType: NodeId = field(default_factory=NodeId)
    ValueRank: Int32 = 0
    ArrayDimensions: List[UInt32] = field(default_factory=list)
    MaxStringLength: UInt32 = 0
    IsOptional: Boolean = True


@dataclass(frozen=FROZEN)
class StructureDefinition(DataTypeDefinition):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.5

    :ivar DefaultEncodingId:
    :vartype DefaultEncodingId: NodeId
    :ivar BaseDataType:
    :vartype BaseDataType: NodeId
    :ivar StructureType:
    :vartype StructureType: StructureType
    :ivar Fields:
    :vartype Fields: StructureField
    """

    data_type = NodeId(ObjectIds.StructureDefinition)

    DefaultEncodingId: NodeId = field(default_factory=NodeId)
    BaseDataType: NodeId = field(default_factory=NodeId)
    StructureType_: StructureType = StructureType.Structure
    Fields: List[StructureField] = field(default_factory=list)

    @property
    def StructureType(self):
        return self.StructureType_

    @StructureType.setter
    def StructureType(self, val):
        self.StructureType_ = val


@dataclass(frozen=FROZEN)
class StructureDescription(DataTypeDescription):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.33

    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    :ivar StructureDefinition:
    :vartype StructureDefinition: StructureDefinition
    """

    data_type = NodeId(ObjectIds.StructureDescription)

    DataTypeId: NodeId = field(default_factory=NodeId)
    Name: QualifiedName = field(default_factory=QualifiedName)
    StructureDefinition_: StructureDefinition = field(default_factory=StructureDefinition)

    @property
    def StructureDefinition(self):
        return self.StructureDefinition_

    @StructureDefinition.setter
    def StructureDefinition(self, val):
        self.StructureDefinition_ = val


@dataclass(frozen=FROZEN)
class Argument:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.1

    :ivar Name:
    :vartype Name: String
    :ivar DataType:
    :vartype DataType: NodeId
    :ivar ValueRank:
    :vartype ValueRank: Int32
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: UInt32
    :ivar Description:
    :vartype Description: LocalizedText
    """

    data_type = NodeId(ObjectIds.Argument)

    Name: String = None
    DataType: NodeId = field(default_factory=NodeId)
    ValueRank: Int32 = 0
    ArrayDimensions: List[UInt32] = field(default_factory=list)
    Description: LocalizedText = field(default_factory=LocalizedText)


@dataclass(frozen=FROZEN)
class EnumValueType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.6

    :ivar Value:
    :vartype Value: Int64
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    """

    data_type = NodeId(ObjectIds.EnumValueType)

    Value: Int64 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)


@dataclass(frozen=FROZEN)
class EnumField(EnumValueType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.7

    :ivar Value:
    :vartype Value: Int64
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar Name:
    :vartype Name: String
    """

    data_type = NodeId(ObjectIds.EnumField)

    Value: Int64 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    Name: String = None


@dataclass(frozen=FROZEN)
class EnumDefinition(DataTypeDefinition):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.4

    :ivar Fields:
    :vartype Fields: EnumField
    """

    data_type = NodeId(ObjectIds.EnumDefinition)

    Fields: List[EnumField] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class EnumDescription(DataTypeDescription):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.34

    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    :ivar EnumDefinition:
    :vartype EnumDefinition: EnumDefinition
    :ivar BuiltInType:
    :vartype BuiltInType: Byte
    """

    data_type = NodeId(ObjectIds.EnumDescription)

    DataTypeId: NodeId = field(default_factory=NodeId)
    Name: QualifiedName = field(default_factory=QualifiedName)
    EnumDefinition_: EnumDefinition = field(default_factory=EnumDefinition)
    BuiltInType: Byte = 0

    @property
    def EnumDefinition(self):
        return self.EnumDefinition_

    @EnumDefinition.setter
    def EnumDefinition(self, val):
        self.EnumDefinition_ = val


@dataclass(frozen=FROZEN)
class DataTypeSchemaHeader:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.31

    :ivar Namespaces:
    :vartype Namespaces: String
    :ivar StructureDataTypes:
    :vartype StructureDataTypes: StructureDescription
    :ivar EnumDataTypes:
    :vartype EnumDataTypes: EnumDescription
    :ivar SimpleDataTypes:
    :vartype SimpleDataTypes: SimpleTypeDescription
    """

    data_type = NodeId(ObjectIds.DataTypeSchemaHeader)

    Namespaces: List[String] = field(default_factory=list)
    StructureDataTypes: List[StructureDescription] = field(default_factory=list)
    EnumDataTypes: List[EnumDescription] = field(default_factory=list)
    SimpleDataTypes: List[SimpleTypeDescription] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class UABinaryFileDataType(DataTypeSchemaHeader):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.36

    :ivar Namespaces:
    :vartype Namespaces: String
    :ivar StructureDataTypes:
    :vartype StructureDataTypes: StructureDescription
    :ivar EnumDataTypes:
    :vartype EnumDataTypes: EnumDescription
    :ivar SimpleDataTypes:
    :vartype SimpleDataTypes: SimpleTypeDescription
    :ivar SchemaLocation:
    :vartype SchemaLocation: String
    :ivar FileHeader:
    :vartype FileHeader: KeyValuePair
    :ivar Body:
    :vartype Body: Variant
    """

    data_type = NodeId(ObjectIds.UABinaryFileDataType)

    Namespaces: List[String] = field(default_factory=list)
    StructureDataTypes: List[StructureDescription] = field(default_factory=list)
    EnumDataTypes: List[EnumDescription] = field(default_factory=list)
    SimpleDataTypes: List[SimpleTypeDescription] = field(default_factory=list)
    SchemaLocation: String = None
    FileHeader: List[KeyValuePair] = field(default_factory=list)
    Body: Variant = field(default_factory=Variant)


@dataclass(frozen=FROZEN)
class DataSetMetaDataType(DataTypeSchemaHeader):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.2.3

    :ivar Namespaces:
    :vartype Namespaces: String
    :ivar StructureDataTypes:
    :vartype StructureDataTypes: StructureDescription
    :ivar EnumDataTypes:
    :vartype EnumDataTypes: EnumDescription
    :ivar SimpleDataTypes:
    :vartype SimpleDataTypes: SimpleTypeDescription
    :ivar Name:
    :vartype Name: String
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar Fields:
    :vartype Fields: FieldMetaData
    :ivar DataSetClassId:
    :vartype DataSetClassId: Guid
    :ivar ConfigurationVersion:
    :vartype ConfigurationVersion: ConfigurationVersionDataType
    """

    data_type = NodeId(ObjectIds.DataSetMetaDataType)

    Namespaces: List[String] = field(default_factory=list)
    StructureDataTypes: List[StructureDescription] = field(default_factory=list)
    EnumDataTypes: List[EnumDescription] = field(default_factory=list)
    SimpleDataTypes: List[SimpleTypeDescription] = field(default_factory=list)
    Name: String = None
    Description: LocalizedText = field(default_factory=LocalizedText)
    Fields: List[FieldMetaData] = field(default_factory=list)
    DataSetClassId: Guid = Guid(int=0)
    ConfigurationVersion: ConfigurationVersionDataType = field(default_factory=ConfigurationVersionDataType)


@dataclass(frozen=FROZEN)
class PublishedDataSetDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.5

    :ivar Name:
    :vartype Name: String
    :ivar DataSetFolder:
    :vartype DataSetFolder: String
    :ivar DataSetMetaData:
    :vartype DataSetMetaData: DataSetMetaDataType
    :ivar ExtensionFields:
    :vartype ExtensionFields: KeyValuePair
    :ivar DataSetSource:
    :vartype DataSetSource: PublishedDataSetSourceDataType
    """

    data_type = NodeId(ObjectIds.PublishedDataSetDataType)

    Name: String = None
    DataSetFolder: List[String] = field(default_factory=list)
    DataSetMetaData: DataSetMetaDataType = field(default_factory=DataSetMetaDataType)
    ExtensionFields: List[KeyValuePair] = field(default_factory=list)
    DataSetSource: Type[PublishedDataSetSourceDataType] = field(default_factory=PublishedDataSetSourceDataType)


@dataclass(frozen=FROZEN)
class StandaloneSubscribedDataSetDataType(SubscribedDataSetDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.10/#6.2.10.5

    :ivar Name:
    :vartype Name: String
    :ivar DataSetFolder:
    :vartype DataSetFolder: String
    :ivar DataSetMetaData:
    :vartype DataSetMetaData: DataSetMetaDataType
    :ivar SubscribedDataSet:
    :vartype SubscribedDataSet: SubscribedDataSetDataType
    """

    data_type = NodeId(ObjectIds.StandaloneSubscribedDataSetDataType)

    Name: String = None
    DataSetFolder: List[String] = field(default_factory=list)
    DataSetMetaData: DataSetMetaDataType = field(default_factory=DataSetMetaDataType)
    SubscribedDataSet: Type[SubscribedDataSetDataType] = field(default_factory=SubscribedDataSetDataType)


@dataclass(frozen=FROZEN)
class OptionSet:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.8

    :ivar Value:
    :vartype Value: ByteString
    :ivar ValidBits:
    :vartype ValidBits: ByteString
    """

    data_type = NodeId(ObjectIds.OptionSet)

    Value: ByteString = None
    ValidBits: ByteString = None


@dataclass(frozen=FROZEN)
class TimeZoneDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.2.12/#12.2.12.11

    :ivar Offset:
    :vartype Offset: Int16
    :ivar DaylightSavingInOffset:
    :vartype DaylightSavingInOffset: Boolean
    """

    data_type = NodeId(ObjectIds.TimeZoneDataType)

    Offset: Int16 = 0
    DaylightSavingInOffset: Boolean = True


@dataclass(frozen=FROZEN)
class ApplicationDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.3

    :ivar ApplicationUri:
    :vartype ApplicationUri: String
    :ivar ProductUri:
    :vartype ProductUri: String
    :ivar ApplicationName:
    :vartype ApplicationName: LocalizedText
    :ivar ApplicationType:
    :vartype ApplicationType: ApplicationType
    :ivar GatewayServerUri:
    :vartype GatewayServerUri: String
    :ivar DiscoveryProfileUri:
    :vartype DiscoveryProfileUri: String
    :ivar DiscoveryUrls:
    :vartype DiscoveryUrls: String
    """

    data_type = NodeId(ObjectIds.ApplicationDescription)

    ApplicationUri: String = None
    ProductUri: String = None
    ApplicationName: LocalizedText = field(default_factory=LocalizedText)
    ApplicationType_: ApplicationType = ApplicationType.Server
    GatewayServerUri: String = None
    DiscoveryProfileUri: String = None
    DiscoveryUrls: List[String] = field(default_factory=list)

    @property
    def ApplicationType(self):
        return self.ApplicationType_

    @ApplicationType.setter
    def ApplicationType(self, val):
        self.ApplicationType_ = val


@dataclass(frozen=FROZEN)
class RequestHeader:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.33

    :ivar AuthenticationToken:
    :vartype AuthenticationToken: SessionAuthenticationToken
    :ivar Timestamp:
    :vartype Timestamp: UtcTime
    :ivar RequestHandle:
    :vartype RequestHandle: IntegerId
    :ivar ReturnDiagnostics:
    :vartype ReturnDiagnostics: UInt32
    :ivar AuditEntryId:
    :vartype AuditEntryId: String
    :ivar TimeoutHint:
    :vartype TimeoutHint: UInt32
    :ivar AdditionalHeader:
    :vartype AdditionalHeader: ExtensionObject
    """

    data_type = NodeId(ObjectIds.RequestHeader)

    AuthenticationToken: SessionAuthenticationToken = field(default_factory=NodeId)
    Timestamp: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    RequestHandle: IntegerId = 0
    ReturnDiagnostics: UInt32 = 0
    AuditEntryId: String = None
    TimeoutHint: UInt32 = 0
    AdditionalHeader: ExtensionObject = ExtensionObject()


@dataclass(frozen=FROZEN)
class ResponseHeader:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.34

    :ivar Timestamp:
    :vartype Timestamp: UtcTime
    :ivar RequestHandle:
    :vartype RequestHandle: IntegerId
    :ivar ServiceResult:
    :vartype ServiceResult: StatusCode
    :ivar ServiceDiagnostics:
    :vartype ServiceDiagnostics: DiagnosticInfo
    :ivar StringTable:
    :vartype StringTable: String
    :ivar AdditionalHeader:
    :vartype AdditionalHeader: ExtensionObject
    """

    data_type = NodeId(ObjectIds.ResponseHeader)

    Timestamp: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    RequestHandle: IntegerId = 0
    ServiceResult: StatusCode = field(default_factory=StatusCode)
    ServiceDiagnostics: DiagnosticInfo = field(default_factory=DiagnosticInfo)
    StringTable: List[String] = field(default_factory=list)
    AdditionalHeader: ExtensionObject = ExtensionObject()


@dataclass(frozen=FROZEN)
class ServiceFault:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.35

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = NodeId(ObjectIds.ServiceFault)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ServiceFault_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class SessionlessInvokeRequestType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/6.3.2

    :ivar UrisVersion:
    :vartype UrisVersion: VersionTime
    :ivar NamespaceUris:
    :vartype NamespaceUris: String
    :ivar ServerUris:
    :vartype ServerUris: String
    :ivar LocaleIds:
    :vartype LocaleIds: LocaleId
    :ivar ServiceId:
    :vartype ServiceId: UInt32
    """

    data_type = NodeId(ObjectIds.SessionlessInvokeRequestType)

    UrisVersion: VersionTime = 0
    NamespaceUris: List[String] = field(default_factory=list)
    ServerUris: List[String] = field(default_factory=list)
    LocaleIds: List[LocaleId] = field(default_factory=list)
    ServiceId: UInt32 = 0


@dataclass(frozen=FROZEN)
class SessionlessInvokeResponseType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/6.3.2

    :ivar NamespaceUris:
    :vartype NamespaceUris: String
    :ivar ServerUris:
    :vartype ServerUris: String
    :ivar ServiceId:
    :vartype ServiceId: UInt32
    """

    data_type = NodeId(ObjectIds.SessionlessInvokeResponseType)

    NamespaceUris: List[String] = field(default_factory=list)
    ServerUris: List[String] = field(default_factory=list)
    ServiceId: UInt32 = 0


@dataclass(frozen=FROZEN)
class FindServersParameters:
    """
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar LocaleIds:
    :vartype LocaleIds: LocaleId
    :ivar ServerUris:
    :vartype ServerUris: String
    """

    EndpointUrl: String = None
    LocaleIds: List[LocaleId] = field(default_factory=list)
    ServerUris: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class FindServersRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.2/#5.4.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: FindServersParameters
    """

    data_type = NodeId(ObjectIds.FindServersRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.FindServersRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: FindServersParameters = field(default_factory=FindServersParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class FindServersResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.2/#5.4.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Servers:
    :vartype Servers: ApplicationDescription
    """

    data_type = NodeId(ObjectIds.FindServersResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.FindServersResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Servers: List[ApplicationDescription] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class ServerOnNetwork:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.3/#5.4.3.2

    :ivar RecordId:
    :vartype RecordId: UInt32
    :ivar ServerName:
    :vartype ServerName: String
    :ivar DiscoveryUrl:
    :vartype DiscoveryUrl: String
    :ivar ServerCapabilities:
    :vartype ServerCapabilities: String
    """

    data_type = NodeId(ObjectIds.ServerOnNetwork)

    RecordId: UInt32 = 0
    ServerName: String = None
    DiscoveryUrl: String = None
    ServerCapabilities: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class FindServersOnNetworkParameters:
    """
    :ivar StartingRecordId:
    :vartype StartingRecordId: Counter
    :ivar MaxRecordsToReturn:
    :vartype MaxRecordsToReturn: UInt32
    :ivar ServerCapabilityFilter:
    :vartype ServerCapabilityFilter: String
    """

    StartingRecordId: Counter = 0
    MaxRecordsToReturn: UInt32 = 0
    ServerCapabilityFilter: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class FindServersOnNetworkRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.3/#5.4.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: FindServersOnNetworkParameters
    """

    data_type = NodeId(ObjectIds.FindServersOnNetworkRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.FindServersOnNetworkRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: FindServersOnNetworkParameters = field(default_factory=FindServersOnNetworkParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class FindServersOnNetworkResult:
    """
    :ivar LastCounterResetTime:
    :vartype LastCounterResetTime: UtcTime
    :ivar Servers:
    :vartype Servers: ServerOnNetwork
    """

    LastCounterResetTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    Servers: List[ServerOnNetwork] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class FindServersOnNetworkResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.3/#5.4.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: FindServersOnNetworkResult
    """

    data_type = NodeId(ObjectIds.FindServersOnNetworkResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.FindServersOnNetworkResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: FindServersOnNetworkResult = field(default_factory=FindServersOnNetworkResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class UserTokenPolicy:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.42

    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar TokenType:
    :vartype TokenType: UserTokenType
    :ivar IssuedTokenType:
    :vartype IssuedTokenType: String
    :ivar IssuerEndpointUrl:
    :vartype IssuerEndpointUrl: String
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    """

    data_type = NodeId(ObjectIds.UserTokenPolicy)

    PolicyId: String = None
    TokenType: UserTokenType = UserTokenType.Anonymous
    IssuedTokenType: String = None
    IssuerEndpointUrl: String = None
    SecurityPolicyUri: String = None


@dataclass(frozen=FROZEN)
class PubSubKeyPushTargetDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.12/#6.2.12.3

    :ivar ApplicationUri:
    :vartype ApplicationUri: String
    :ivar PushTargetFolder:
    :vartype PushTargetFolder: String
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    :ivar UserTokenType:
    :vartype UserTokenType: UserTokenPolicy
    :ivar RequestedKeyCount:
    :vartype RequestedKeyCount: UInt16
    :ivar RetryInterval:
    :vartype RetryInterval: Duration
    :ivar PushTargetProperties:
    :vartype PushTargetProperties: KeyValuePair
    :ivar SecurityGroups:
    :vartype SecurityGroups: String
    """

    data_type = NodeId(ObjectIds.PubSubKeyPushTargetDataType)

    ApplicationUri: String = None
    PushTargetFolder: List[String] = field(default_factory=list)
    EndpointUrl: String = None
    SecurityPolicyUri: String = None
    UserTokenType: UserTokenPolicy = field(default_factory=UserTokenPolicy)
    RequestedKeyCount: UInt16 = 0
    RetryInterval: Duration = 0
    PushTargetProperties: List[KeyValuePair] = field(default_factory=list)
    SecurityGroups: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class EndpointDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.14

    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar Server:
    :vartype Server: ApplicationDescription
    :ivar ServerCertificate:
    :vartype ServerCertificate: ApplicationInstanceCertificate
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    :ivar UserIdentityTokens:
    :vartype UserIdentityTokens: UserTokenPolicy
    :ivar TransportProfileUri:
    :vartype TransportProfileUri: String
    :ivar SecurityLevel:
    :vartype SecurityLevel: Byte
    """

    data_type = NodeId(ObjectIds.EndpointDescription)

    EndpointUrl: String = None
    Server: ApplicationDescription = field(default_factory=ApplicationDescription)
    ServerCertificate: ApplicationInstanceCertificate = None
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityPolicyUri: String = None
    UserIdentityTokens: List[UserTokenPolicy] = field(default_factory=list)
    TransportProfileUri: String = None
    SecurityLevel: Byte = 0


@dataclass(frozen=FROZEN)
class PubSubGroupDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.5/#6.2.5.7

    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityGroupId:
    :vartype SecurityGroupId: String
    :ivar SecurityKeyServices:
    :vartype SecurityKeyServices: EndpointDescription
    :ivar MaxNetworkMessageSize:
    :vartype MaxNetworkMessageSize: UInt32
    :ivar GroupProperties:
    :vartype GroupProperties: KeyValuePair
    """

    data_type = NodeId(ObjectIds.PubSubGroupDataType)

    Name: String = None
    Enabled: Boolean = True
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityGroupId: String = None
    SecurityKeyServices: List[EndpointDescription] = field(default_factory=list)
    MaxNetworkMessageSize: UInt32 = 0
    GroupProperties: List[KeyValuePair] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class WriterGroupDataType(PubSubGroupDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.6/#6.2.6.7.1

    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityGroupId:
    :vartype SecurityGroupId: String
    :ivar SecurityKeyServices:
    :vartype SecurityKeyServices: EndpointDescription
    :ivar MaxNetworkMessageSize:
    :vartype MaxNetworkMessageSize: UInt32
    :ivar GroupProperties:
    :vartype GroupProperties: KeyValuePair
    :ivar WriterGroupId:
    :vartype WriterGroupId: UInt16
    :ivar PublishingInterval:
    :vartype PublishingInterval: Duration
    :ivar KeepAliveTime:
    :vartype KeepAliveTime: Duration
    :ivar Priority:
    :vartype Priority: Byte
    :ivar LocaleIds:
    :vartype LocaleIds: LocaleId
    :ivar HeaderLayoutUri:
    :vartype HeaderLayoutUri: String
    :ivar TransportSettings:
    :vartype TransportSettings: WriterGroupTransportDataType
    :ivar MessageSettings:
    :vartype MessageSettings: WriterGroupMessageDataType
    :ivar DataSetWriters:
    :vartype DataSetWriters: DataSetWriterDataType
    """

    data_type = NodeId(ObjectIds.WriterGroupDataType)

    Name: String = None
    Enabled: Boolean = True
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityGroupId: String = None
    SecurityKeyServices: List[EndpointDescription] = field(default_factory=list)
    MaxNetworkMessageSize: UInt32 = 0
    GroupProperties: List[KeyValuePair] = field(default_factory=list)
    WriterGroupId: UInt16 = 0
    PublishingInterval: Duration = 0
    KeepAliveTime: Duration = 0
    Priority: Byte = 0
    LocaleIds: List[LocaleId] = field(default_factory=list)
    HeaderLayoutUri: String = None
    TransportSettings: Type[WriterGroupTransportDataType] = field(default_factory=WriterGroupTransportDataType)
    MessageSettings: Type[WriterGroupMessageDataType] = field(default_factory=WriterGroupMessageDataType)
    DataSetWriters: List[DataSetWriterDataType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DataSetReaderDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.9/#6.2.9.13.1

    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar PublisherId:
    :vartype PublisherId: Variant
    :ivar WriterGroupId:
    :vartype WriterGroupId: UInt16
    :ivar DataSetWriterId:
    :vartype DataSetWriterId: UInt16
    :ivar DataSetMetaData:
    :vartype DataSetMetaData: DataSetMetaDataType
    :ivar DataSetFieldContentMask:
    :vartype DataSetFieldContentMask: DataSetFieldContentMask
    :ivar MessageReceiveTimeout:
    :vartype MessageReceiveTimeout: Duration
    :ivar KeyFrameCount:
    :vartype KeyFrameCount: UInt32
    :ivar HeaderLayoutUri:
    :vartype HeaderLayoutUri: String
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityGroupId:
    :vartype SecurityGroupId: String
    :ivar SecurityKeyServices:
    :vartype SecurityKeyServices: EndpointDescription
    :ivar DataSetReaderProperties:
    :vartype DataSetReaderProperties: KeyValuePair
    :ivar TransportSettings:
    :vartype TransportSettings: DataSetReaderTransportDataType
    :ivar MessageSettings:
    :vartype MessageSettings: DataSetReaderMessageDataType
    :ivar SubscribedDataSet:
    :vartype SubscribedDataSet: SubscribedDataSetDataType
    """

    data_type = NodeId(ObjectIds.DataSetReaderDataType)

    Name: String = None
    Enabled: Boolean = True
    PublisherId: Variant = field(default_factory=Variant)
    WriterGroupId: UInt16 = 0
    DataSetWriterId: UInt16 = 0
    DataSetMetaData: DataSetMetaDataType = field(default_factory=DataSetMetaDataType)
    DataSetFieldContentMask_: DataSetFieldContentMask = field(default_factory=lambda:DataSetFieldContentMask(0))
    MessageReceiveTimeout: Duration = 0
    KeyFrameCount: UInt32 = 0
    HeaderLayoutUri: String = None
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityGroupId: String = None
    SecurityKeyServices: List[EndpointDescription] = field(default_factory=list)
    DataSetReaderProperties: List[KeyValuePair] = field(default_factory=list)
    TransportSettings: Type[DataSetReaderTransportDataType] = field(default_factory=DataSetReaderTransportDataType)
    MessageSettings: Type[DataSetReaderMessageDataType] = field(default_factory=DataSetReaderMessageDataType)
    SubscribedDataSet: Type[SubscribedDataSetDataType] = field(default_factory=SubscribedDataSetDataType)

    @property
    def DataSetFieldContentMask(self):
        return self.DataSetFieldContentMask_

    @DataSetFieldContentMask.setter
    def DataSetFieldContentMask(self, val):
        self.DataSetFieldContentMask_ = val


@dataclass(frozen=FROZEN)
class ReaderGroupDataType(PubSubGroupDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.8/#6.2.8.2.1

    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityGroupId:
    :vartype SecurityGroupId: String
    :ivar SecurityKeyServices:
    :vartype SecurityKeyServices: EndpointDescription
    :ivar MaxNetworkMessageSize:
    :vartype MaxNetworkMessageSize: UInt32
    :ivar GroupProperties:
    :vartype GroupProperties: KeyValuePair
    :ivar TransportSettings:
    :vartype TransportSettings: ReaderGroupTransportDataType
    :ivar MessageSettings:
    :vartype MessageSettings: ReaderGroupMessageDataType
    :ivar DataSetReaders:
    :vartype DataSetReaders: DataSetReaderDataType
    """

    data_type = NodeId(ObjectIds.ReaderGroupDataType)

    Name: String = None
    Enabled: Boolean = True
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityGroupId: String = None
    SecurityKeyServices: List[EndpointDescription] = field(default_factory=list)
    MaxNetworkMessageSize: UInt32 = 0
    GroupProperties: List[KeyValuePair] = field(default_factory=list)
    TransportSettings: Type[ReaderGroupTransportDataType] = field(default_factory=ReaderGroupTransportDataType)
    MessageSettings: Type[ReaderGroupMessageDataType] = field(default_factory=ReaderGroupMessageDataType)
    DataSetReaders: List[DataSetReaderDataType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class PubSubConnectionDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.7/#6.2.7.5.1

    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar PublisherId:
    :vartype PublisherId: Variant
    :ivar TransportProfileUri:
    :vartype TransportProfileUri: String
    :ivar Address:
    :vartype Address: NetworkAddressDataType
    :ivar ConnectionProperties:
    :vartype ConnectionProperties: KeyValuePair
    :ivar TransportSettings:
    :vartype TransportSettings: ConnectionTransportDataType
    :ivar WriterGroups:
    :vartype WriterGroups: WriterGroupDataType
    :ivar ReaderGroups:
    :vartype ReaderGroups: ReaderGroupDataType
    """

    data_type = NodeId(ObjectIds.PubSubConnectionDataType)

    Name: String = None
    Enabled: Boolean = True
    PublisherId: Variant = field(default_factory=Variant)
    TransportProfileUri: String = None
    Address: Type[NetworkAddressDataType] = field(default_factory=NetworkAddressDataType)
    ConnectionProperties: List[KeyValuePair] = field(default_factory=list)
    TransportSettings: Type[ConnectionTransportDataType] = field(default_factory=ConnectionTransportDataType)
    WriterGroups: List[WriterGroupDataType] = field(default_factory=list)
    ReaderGroups: List[ReaderGroupDataType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class PubSubConfigurationDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.12/#6.2.12.1

    :ivar PublishedDataSets:
    :vartype PublishedDataSets: PublishedDataSetDataType
    :ivar Connections:
    :vartype Connections: PubSubConnectionDataType
    :ivar Enabled:
    :vartype Enabled: Boolean
    """

    data_type = NodeId(ObjectIds.PubSubConfigurationDataType)

    PublishedDataSets: List[PublishedDataSetDataType] = field(default_factory=list)
    Connections: List[PubSubConnectionDataType] = field(default_factory=list)
    Enabled: Boolean = True


@dataclass(frozen=FROZEN)
class PubSubConfiguration2DataType(PubSubConfigurationDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.12/#6.2.12.4

    :ivar PublishedDataSets:
    :vartype PublishedDataSets: PublishedDataSetDataType
    :ivar Connections:
    :vartype Connections: PubSubConnectionDataType
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar SubscribedDataSets:
    :vartype SubscribedDataSets: StandaloneSubscribedDataSetDataType
    :ivar DataSetClasses:
    :vartype DataSetClasses: DataSetMetaDataType
    :ivar DefaultSecurityKeyServices:
    :vartype DefaultSecurityKeyServices: EndpointDescription
    :ivar SecurityGroups:
    :vartype SecurityGroups: SecurityGroupDataType
    :ivar PubSubKeyPushTargets:
    :vartype PubSubKeyPushTargets: PubSubKeyPushTargetDataType
    :ivar ConfigurationVersion:
    :vartype ConfigurationVersion: VersionTime
    :ivar ConfigurationProperties:
    :vartype ConfigurationProperties: KeyValuePair
    """

    data_type = NodeId(ObjectIds.PubSubConfiguration2DataType)

    PublishedDataSets: List[PublishedDataSetDataType] = field(default_factory=list)
    Connections: List[PubSubConnectionDataType] = field(default_factory=list)
    Enabled: Boolean = True
    SubscribedDataSets: List[StandaloneSubscribedDataSetDataType] = field(default_factory=list)
    DataSetClasses: List[DataSetMetaDataType] = field(default_factory=list)
    DefaultSecurityKeyServices: List[EndpointDescription] = field(default_factory=list)
    SecurityGroups: List[SecurityGroupDataType] = field(default_factory=list)
    PubSubKeyPushTargets: List[PubSubKeyPushTargetDataType] = field(default_factory=list)
    ConfigurationVersion: VersionTime = 0
    ConfigurationProperties: List[KeyValuePair] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class GetEndpointsParameters:
    """
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar LocaleIds:
    :vartype LocaleIds: LocaleId
    :ivar ProfileUris:
    :vartype ProfileUris: String
    """

    EndpointUrl: String = None
    LocaleIds: List[LocaleId] = field(default_factory=list)
    ProfileUris: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class GetEndpointsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.4/#5.4.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: GetEndpointsParameters
    """

    data_type = NodeId(ObjectIds.GetEndpointsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.GetEndpointsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: GetEndpointsParameters = field(default_factory=GetEndpointsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class GetEndpointsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.4/#5.4.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Endpoints:
    :vartype Endpoints: EndpointDescription
    """

    data_type = NodeId(ObjectIds.GetEndpointsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.GetEndpointsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Endpoints: List[EndpointDescription] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class RegisteredServer:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.32

    :ivar ServerUri:
    :vartype ServerUri: String
    :ivar ProductUri:
    :vartype ProductUri: String
    :ivar ServerNames:
    :vartype ServerNames: LocalizedText
    :ivar ServerType:
    :vartype ServerType: ApplicationType
    :ivar GatewayServerUri:
    :vartype GatewayServerUri: String
    :ivar DiscoveryUrls:
    :vartype DiscoveryUrls: String
    :ivar SemaphoreFilePath:
    :vartype SemaphoreFilePath: String
    :ivar IsOnline:
    :vartype IsOnline: Boolean
    """

    data_type = NodeId(ObjectIds.RegisteredServer)

    ServerUri: String = None
    ProductUri: String = None
    ServerNames: List[LocalizedText] = field(default_factory=list)
    ServerType: ApplicationType = ApplicationType.Server
    GatewayServerUri: String = None
    DiscoveryUrls: List[String] = field(default_factory=list)
    SemaphoreFilePath: String = None
    IsOnline: Boolean = True


@dataclass(frozen=FROZEN)
class RegisterServerRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.5/#5.4.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Server:
    :vartype Server: RegisteredServer
    """

    data_type = NodeId(ObjectIds.RegisterServerRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RegisterServerRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Server: RegisteredServer = field(default_factory=RegisteredServer)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class RegisterServerResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.5/#5.4.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = NodeId(ObjectIds.RegisterServerResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RegisterServerResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class DiscoveryConfiguration:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.13.1

    """

    data_type = NodeId(ObjectIds.DiscoveryConfiguration)


@dataclass(frozen=FROZEN)
class MdnsDiscoveryConfiguration(DiscoveryConfiguration):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.13.2

    :ivar MdnsServerName:
    :vartype MdnsServerName: String
    :ivar ServerCapabilities:
    :vartype ServerCapabilities: String
    """

    data_type = NodeId(ObjectIds.MdnsDiscoveryConfiguration)

    MdnsServerName: String = None
    ServerCapabilities: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class RegisterServer2Parameters:
    """
    :ivar Server:
    :vartype Server: RegisteredServer
    :ivar DiscoveryConfiguration:
    :vartype DiscoveryConfiguration: ExtensionObject
    """

    Server: RegisteredServer = field(default_factory=RegisteredServer)
    DiscoveryConfiguration: List[ExtensionObject] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class RegisterServer2Request:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.6/#5.4.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: RegisterServer2Parameters
    """

    data_type = NodeId(ObjectIds.RegisterServer2Request)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RegisterServer2Request_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: RegisterServer2Parameters = field(default_factory=RegisterServer2Parameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class RegisterServer2Response:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.4.6/#5.4.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar ConfigurationResults:
    :vartype ConfigurationResults: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.RegisterServer2Response)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RegisterServer2Response_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    ConfigurationResults: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class ChannelSecurityToken:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.5.2/#5.5.2.2

    :ivar ChannelId:
    :vartype ChannelId: UInt32
    :ivar TokenId:
    :vartype TokenId: UInt32
    :ivar CreatedAt:
    :vartype CreatedAt: UtcTime
    :ivar RevisedLifetime:
    :vartype RevisedLifetime: UInt32
    """

    data_type = NodeId(ObjectIds.ChannelSecurityToken)

    ChannelId: UInt32 = 0
    TokenId: UInt32 = 0
    CreatedAt: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    RevisedLifetime: UInt32 = 0


@dataclass(frozen=FROZEN)
class OpenSecureChannelParameters:
    """
    :ivar ClientProtocolVersion:
    :vartype ClientProtocolVersion: UInt32
    :ivar RequestType:
    :vartype RequestType: SecurityTokenRequestType
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar ClientNonce:
    :vartype ClientNonce: ByteString
    :ivar RequestedLifetime:
    :vartype RequestedLifetime: UInt32
    """

    ClientProtocolVersion: UInt32 = 0
    RequestType: SecurityTokenRequestType = SecurityTokenRequestType.Issue
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    ClientNonce: ByteString = None
    RequestedLifetime: UInt32 = 0


@dataclass(frozen=FROZEN)
class OpenSecureChannelRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.5.2/#5.5.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: OpenSecureChannelParameters
    """

    data_type = NodeId(ObjectIds.OpenSecureChannelRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.OpenSecureChannelRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: OpenSecureChannelParameters = field(default_factory=OpenSecureChannelParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class OpenSecureChannelResult:
    """
    :ivar ServerProtocolVersion:
    :vartype ServerProtocolVersion: UInt32
    :ivar SecurityToken:
    :vartype SecurityToken: ChannelSecurityToken
    :ivar ServerNonce:
    :vartype ServerNonce: ByteString
    """

    ServerProtocolVersion: UInt32 = 0
    SecurityToken: ChannelSecurityToken = field(default_factory=ChannelSecurityToken)
    ServerNonce: ByteString = None


@dataclass(frozen=FROZEN)
class OpenSecureChannelResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.5.2/#5.5.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: OpenSecureChannelResult
    """

    data_type = NodeId(ObjectIds.OpenSecureChannelResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.OpenSecureChannelResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: OpenSecureChannelResult = field(default_factory=OpenSecureChannelResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class CloseSecureChannelRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.5.3/#5.5.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    """

    data_type = NodeId(ObjectIds.CloseSecureChannelRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CloseSecureChannelRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CloseSecureChannelResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.5.3/#5.5.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = NodeId(ObjectIds.CloseSecureChannelResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CloseSecureChannelResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class SignedSoftwareCertificate:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.13

    :ivar CertificateData:
    :vartype CertificateData: ByteString
    :ivar Signature:
    :vartype Signature: ByteString
    """

    data_type = NodeId(ObjectIds.SignedSoftwareCertificate)

    CertificateData: ByteString = None
    Signature: ByteString = None


@dataclass(frozen=FROZEN)
class SignatureData:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.37

    :ivar Algorithm:
    :vartype Algorithm: String
    :ivar Signature:
    :vartype Signature: ByteString
    """

    data_type = NodeId(ObjectIds.SignatureData)

    Algorithm: String = None
    Signature: ByteString = None


@dataclass(frozen=FROZEN)
class CreateSessionParameters:
    """
    :ivar ClientDescription:
    :vartype ClientDescription: ApplicationDescription
    :ivar ServerUri:
    :vartype ServerUri: String
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar SessionName:
    :vartype SessionName: String
    :ivar ClientNonce:
    :vartype ClientNonce: ByteString
    :ivar ClientCertificate:
    :vartype ClientCertificate: ApplicationInstanceCertificate
    :ivar RequestedSessionTimeout:
    :vartype RequestedSessionTimeout: Duration
    :ivar MaxResponseMessageSize:
    :vartype MaxResponseMessageSize: UInt32
    """

    ClientDescription: ApplicationDescription = field(default_factory=ApplicationDescription)
    ServerUri: String = None
    EndpointUrl: String = None
    SessionName: String = None
    ClientNonce: ByteString = None
    ClientCertificate: ApplicationInstanceCertificate = None
    RequestedSessionTimeout: Duration = 0
    MaxResponseMessageSize: UInt32 = 0


@dataclass(frozen=FROZEN)
class CreateSessionRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.2/#5.6.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CreateSessionParameters
    """

    data_type = NodeId(ObjectIds.CreateSessionRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CreateSessionRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: CreateSessionParameters = field(default_factory=CreateSessionParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CreateSessionResult:
    """
    :ivar SessionId:
    :vartype SessionId: NodeId
    :ivar AuthenticationToken:
    :vartype AuthenticationToken: SessionAuthenticationToken
    :ivar RevisedSessionTimeout:
    :vartype RevisedSessionTimeout: Duration
    :ivar ServerNonce:
    :vartype ServerNonce: ByteString
    :ivar ServerCertificate:
    :vartype ServerCertificate: ApplicationInstanceCertificate
    :ivar ServerEndpoints:
    :vartype ServerEndpoints: EndpointDescription
    :ivar ServerSoftwareCertificates:
    :vartype ServerSoftwareCertificates: SignedSoftwareCertificate
    :ivar ServerSignature:
    :vartype ServerSignature: SignatureData
    :ivar MaxRequestMessageSize:
    :vartype MaxRequestMessageSize: UInt32
    """

    SessionId: NodeId = field(default_factory=NodeId)
    AuthenticationToken: SessionAuthenticationToken = field(default_factory=NodeId)
    RevisedSessionTimeout: Duration = 0
    ServerNonce: ByteString = None
    ServerCertificate: ApplicationInstanceCertificate = None
    ServerEndpoints: List[EndpointDescription] = field(default_factory=list)
    ServerSoftwareCertificates: List[SignedSoftwareCertificate] = field(default_factory=list)
    ServerSignature: SignatureData = field(default_factory=SignatureData)
    MaxRequestMessageSize: UInt32 = 0


@dataclass(frozen=FROZEN)
class CreateSessionResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.2/#5.6.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: CreateSessionResult
    """

    data_type = NodeId(ObjectIds.CreateSessionResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CreateSessionResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: CreateSessionResult = field(default_factory=CreateSessionResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class UserIdentityToken:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.15

    :ivar PolicyId:
    :vartype PolicyId: String
    """

    data_type = NodeId(ObjectIds.UserIdentityToken)

    PolicyId: String = None


@dataclass(frozen=FROZEN)
class AnonymousIdentityToken(UserIdentityToken):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.15/#12.3.15.1

    :ivar PolicyId:
    :vartype PolicyId: String
    """

    data_type = NodeId(ObjectIds.AnonymousIdentityToken)

    PolicyId: String = None


@dataclass(frozen=FROZEN)
class UserNameIdentityToken(UserIdentityToken):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.15/#12.3.15.3

    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar UserName:
    :vartype UserName: String
    :ivar Password:
    :vartype Password: ByteString
    :ivar EncryptionAlgorithm:
    :vartype EncryptionAlgorithm: String
    """

    data_type = NodeId(ObjectIds.UserNameIdentityToken)

    PolicyId: String = None
    UserName: String = None
    Password: ByteString = None
    EncryptionAlgorithm: String = None


@dataclass(frozen=FROZEN)
class X509IdentityToken(UserIdentityToken):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.15/#12.3.15.4

    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar CertificateData:
    :vartype CertificateData: ByteString
    """

    data_type = NodeId(ObjectIds.X509IdentityToken)

    PolicyId: String = None
    CertificateData: ByteString = None


@dataclass(frozen=FROZEN)
class IssuedIdentityToken(UserIdentityToken):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.15/#12.3.15.2

    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar TokenData:
    :vartype TokenData: ByteString
    :ivar EncryptionAlgorithm:
    :vartype EncryptionAlgorithm: String
    """

    data_type = NodeId(ObjectIds.IssuedIdentityToken)

    PolicyId: String = None
    TokenData: ByteString = None
    EncryptionAlgorithm: String = None


@dataclass(frozen=FROZEN)
class ActivateSessionParameters:
    """
    :ivar ClientSignature:
    :vartype ClientSignature: SignatureData
    :ivar ClientSoftwareCertificates:
    :vartype ClientSoftwareCertificates: SignedSoftwareCertificate
    :ivar LocaleIds:
    :vartype LocaleIds: LocaleId
    :ivar UserIdentityToken:
    :vartype UserIdentityToken: ExtensionObject
    :ivar UserTokenSignature:
    :vartype UserTokenSignature: SignatureData
    """

    ClientSignature: SignatureData = field(default_factory=SignatureData)
    ClientSoftwareCertificates: List[SignedSoftwareCertificate] = field(default_factory=list)
    LocaleIds: List[LocaleId] = field(default_factory=list)
    UserIdentityToken: ExtensionObject = ExtensionObject()
    UserTokenSignature: SignatureData = field(default_factory=SignatureData)


@dataclass(frozen=FROZEN)
class ActivateSessionRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.3/#5.6.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ActivateSessionParameters
    """

    data_type = NodeId(ObjectIds.ActivateSessionRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: ActivateSessionParameters = field(default_factory=ActivateSessionParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class ActivateSessionResult:
    """
    :ivar ServerNonce:
    :vartype ServerNonce: ByteString
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ServerNonce: ByteString = None
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class ActivateSessionResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.3/#5.6.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: ActivateSessionResult
    """

    data_type = NodeId(ObjectIds.ActivateSessionResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ActivateSessionResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: ActivateSessionResult = field(default_factory=ActivateSessionResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class CloseSessionRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.4/#5.6.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar DeleteSubscriptions:
    :vartype DeleteSubscriptions: Boolean
    """

    data_type = NodeId(ObjectIds.CloseSessionRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CloseSessionRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    DeleteSubscriptions: Boolean = True

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CloseSessionResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.4/#5.6.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = NodeId(ObjectIds.CloseSessionResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CloseSessionResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class CancelParameters:
    """
    :ivar RequestHandle:
    :vartype RequestHandle: IntegerId
    """

    RequestHandle: IntegerId = 0


@dataclass(frozen=FROZEN)
class CancelRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.5/#5.6.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CancelParameters
    """

    data_type = NodeId(ObjectIds.CancelRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CancelRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: CancelParameters = field(default_factory=CancelParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CancelResult:
    """
    :ivar CancelCount:
    :vartype CancelCount: UInt32
    """

    CancelCount: UInt32 = 0


@dataclass(frozen=FROZEN)
class CancelResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.6.5/#5.6.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: CancelResult
    """

    data_type = NodeId(ObjectIds.CancelResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CancelResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: CancelResult = field(default_factory=CancelResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class NodeAttributes:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.1

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    """

    data_type = NodeId(ObjectIds.NodeAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0


@dataclass(frozen=FROZEN)
class ObjectAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.2

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar EventNotifier:
    :vartype EventNotifier: Byte
    """

    data_type = NodeId(ObjectIds.ObjectAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    EventNotifier: Byte = 0


@dataclass(frozen=FROZEN)
class VariableAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.3

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar Value:
    :vartype Value: Variant
    :ivar DataType:
    :vartype DataType: NodeId
    :ivar ValueRank:
    :vartype ValueRank: Int32
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: UInt32
    :ivar AccessLevel:
    :vartype AccessLevel: Byte
    :ivar UserAccessLevel:
    :vartype UserAccessLevel: Byte
    :ivar MinimumSamplingInterval:
    :vartype MinimumSamplingInterval: Duration
    :ivar Historizing:
    :vartype Historizing: Boolean
    """

    data_type = NodeId(ObjectIds.VariableAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    Value: Variant = field(default_factory=Variant)
    DataType: NodeId = field(default_factory=NodeId)
    ValueRank: Int32 = 0
    ArrayDimensions: List[UInt32] = field(default_factory=list)
    AccessLevel: Byte = 0
    UserAccessLevel: Byte = 0
    MinimumSamplingInterval: Duration = 0
    Historizing: Boolean = True


@dataclass(frozen=FROZEN)
class MethodAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.4

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar Executable:
    :vartype Executable: Boolean
    :ivar UserExecutable:
    :vartype UserExecutable: Boolean
    """

    data_type = NodeId(ObjectIds.MethodAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    Executable: Boolean = True
    UserExecutable: Boolean = True


@dataclass(frozen=FROZEN)
class ObjectTypeAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.5

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar IsAbstract:
    :vartype IsAbstract: Boolean
    """

    data_type = NodeId(ObjectIds.ObjectTypeAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    IsAbstract: Boolean = True


@dataclass(frozen=FROZEN)
class VariableTypeAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.6

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar Value:
    :vartype Value: Variant
    :ivar DataType:
    :vartype DataType: NodeId
    :ivar ValueRank:
    :vartype ValueRank: Int32
    :ivar ArrayDimensions:
    :vartype ArrayDimensions: UInt32
    :ivar IsAbstract:
    :vartype IsAbstract: Boolean
    """

    data_type = NodeId(ObjectIds.VariableTypeAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    Value: Variant = field(default_factory=Variant)
    DataType: NodeId = field(default_factory=NodeId)
    ValueRank: Int32 = 0
    ArrayDimensions: List[UInt32] = field(default_factory=list)
    IsAbstract: Boolean = True


@dataclass(frozen=FROZEN)
class ReferenceTypeAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.7

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar IsAbstract:
    :vartype IsAbstract: Boolean
    :ivar Symmetric:
    :vartype Symmetric: Boolean
    :ivar InverseName:
    :vartype InverseName: LocalizedText
    """

    data_type = NodeId(ObjectIds.ReferenceTypeAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    IsAbstract: Boolean = True
    Symmetric: Boolean = True
    InverseName: LocalizedText = field(default_factory=LocalizedText)


@dataclass(frozen=FROZEN)
class DataTypeAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.8

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar IsAbstract:
    :vartype IsAbstract: Boolean
    """

    data_type = NodeId(ObjectIds.DataTypeAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    IsAbstract: Boolean = True


@dataclass(frozen=FROZEN)
class ViewAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.9

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar ContainsNoLoops:
    :vartype ContainsNoLoops: Boolean
    :ivar EventNotifier:
    :vartype EventNotifier: Byte
    """

    data_type = NodeId(ObjectIds.ViewAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    ContainsNoLoops: Boolean = True
    EventNotifier: Byte = 0


@dataclass(frozen=FROZEN)
class GenericAttributeValue:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.10

    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar Value:
    :vartype Value: Variant
    """

    data_type = NodeId(ObjectIds.GenericAttributeValue)

    AttributeId: IntegerId = 0
    Value: Variant = field(default_factory=Variant)


@dataclass(frozen=FROZEN)
class GenericAttributes(NodeAttributes):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.24.10

    :ivar SpecifiedAttributes:
    :vartype SpecifiedAttributes: UInt32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar WriteMask:
    :vartype WriteMask: UInt32
    :ivar UserWriteMask:
    :vartype UserWriteMask: UInt32
    :ivar AttributeValues:
    :vartype AttributeValues: GenericAttributeValue
    """

    data_type = NodeId(ObjectIds.GenericAttributes)

    SpecifiedAttributes: UInt32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)
    WriteMask: UInt32 = 0
    UserWriteMask: UInt32 = 0
    AttributeValues: List[GenericAttributeValue] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class AddNodesItem:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.1

    :ivar ParentNodeId:
    :vartype ParentNodeId: ExpandedNodeId
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar RequestedNewNodeId:
    :vartype RequestedNewNodeId: ExpandedNodeId
    :ivar BrowseName:
    :vartype BrowseName: QualifiedName
    :ivar NodeClass:
    :vartype NodeClass: NodeClass
    :ivar NodeAttributes:
    :vartype NodeAttributes: ExtensionObject
    :ivar TypeDefinition:
    :vartype TypeDefinition: ExpandedNodeId
    """

    data_type = NodeId(ObjectIds.AddNodesItem)

    ParentNodeId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    ReferenceTypeId: NodeId = field(default_factory=NodeId)
    RequestedNewNodeId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    BrowseName: QualifiedName = field(default_factory=QualifiedName)
    NodeClass_: NodeClass = NodeClass.Unspecified
    NodeAttributes: ExtensionObject = ExtensionObject()
    TypeDefinition: ExpandedNodeId = field(default_factory=ExpandedNodeId)

    @property
    def NodeClass(self):
        return self.NodeClass_

    @NodeClass.setter
    def NodeClass(self, val):
        self.NodeClass_ = val


@dataclass(frozen=FROZEN)
class AddNodesResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.2/#5.7.2.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar AddedNodeId:
    :vartype AddedNodeId: NodeId
    """

    data_type = NodeId(ObjectIds.AddNodesResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    AddedNodeId: NodeId = field(default_factory=NodeId)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class AddNodesParameters:
    """
    :ivar NodesToAdd:
    :vartype NodesToAdd: AddNodesItem
    """

    NodesToAdd: List[AddNodesItem] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class AddNodesRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.2/#5.7.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: AddNodesParameters
    """

    data_type = NodeId(ObjectIds.AddNodesRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.AddNodesRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: AddNodesParameters = field(default_factory=AddNodesParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class AddNodesResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.2/#5.7.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: AddNodesResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.AddNodesResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.AddNodesResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[AddNodesResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class AddReferencesItem:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.2

    :ivar SourceNodeId:
    :vartype SourceNodeId: NodeId
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar IsForward:
    :vartype IsForward: Boolean
    :ivar TargetServerUri:
    :vartype TargetServerUri: String
    :ivar TargetNodeId:
    :vartype TargetNodeId: ExpandedNodeId
    :ivar TargetNodeClass:
    :vartype TargetNodeClass: NodeClass
    """

    data_type = NodeId(ObjectIds.AddReferencesItem)

    SourceNodeId: NodeId = field(default_factory=NodeId)
    ReferenceTypeId: NodeId = field(default_factory=NodeId)
    IsForward: Boolean = True
    TargetServerUri: String = None
    TargetNodeId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    TargetNodeClass: NodeClass = NodeClass.Unspecified


@dataclass(frozen=FROZEN)
class AddReferencesParameters:
    """
    :ivar ReferencesToAdd:
    :vartype ReferencesToAdd: AddReferencesItem
    """

    ReferencesToAdd: List[AddReferencesItem] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class AddReferencesRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.3/#5.7.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: AddReferencesParameters
    """

    data_type = NodeId(ObjectIds.AddReferencesRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.AddReferencesRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: AddReferencesParameters = field(default_factory=AddReferencesParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class AddReferencesResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.3/#5.7.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.AddReferencesResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.AddReferencesResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteNodesItem:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.6

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar DeleteTargetReferences:
    :vartype DeleteTargetReferences: Boolean
    """

    data_type = NodeId(ObjectIds.DeleteNodesItem)

    NodeId_: NodeId = field(default_factory=NodeId)
    DeleteTargetReferences: Boolean = True

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class DeleteNodesParameters:
    """
    :ivar NodesToDelete:
    :vartype NodesToDelete: DeleteNodesItem
    """

    NodesToDelete: List[DeleteNodesItem] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DeleteNodesRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.4/#5.7.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteNodesParameters
    """

    data_type = NodeId(ObjectIds.DeleteNodesRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteNodesRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: DeleteNodesParameters = field(default_factory=DeleteNodesParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteNodesResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.4/#5.7.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.DeleteNodesResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteNodesResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteReferencesItem:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.7

    :ivar SourceNodeId:
    :vartype SourceNodeId: NodeId
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar IsForward:
    :vartype IsForward: Boolean
    :ivar TargetNodeId:
    :vartype TargetNodeId: ExpandedNodeId
    :ivar DeleteBidirectional:
    :vartype DeleteBidirectional: Boolean
    """

    data_type = NodeId(ObjectIds.DeleteReferencesItem)

    SourceNodeId: NodeId = field(default_factory=NodeId)
    ReferenceTypeId: NodeId = field(default_factory=NodeId)
    IsForward: Boolean = True
    TargetNodeId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    DeleteBidirectional: Boolean = True


@dataclass(frozen=FROZEN)
class DeleteReferencesParameters:
    """
    :ivar ReferencesToDelete:
    :vartype ReferencesToDelete: DeleteReferencesItem
    """

    ReferencesToDelete: List[DeleteReferencesItem] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DeleteReferencesRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.5/#5.7.5.1

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteReferencesParameters
    """

    data_type = NodeId(ObjectIds.DeleteReferencesRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteReferencesRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: DeleteReferencesParameters = field(default_factory=DeleteReferencesParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteReferencesResult:
    """
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DeleteReferencesResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.5/#5.7.5.1

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: DeleteReferencesResult
    """

    data_type = NodeId(ObjectIds.DeleteReferencesResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteReferencesResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: DeleteReferencesResult = field(default_factory=DeleteReferencesResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class ViewDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.45

    :ivar ViewId:
    :vartype ViewId: NodeId
    :ivar Timestamp:
    :vartype Timestamp: UtcTime
    :ivar ViewVersion:
    :vartype ViewVersion: UInt32
    """

    data_type = NodeId(ObjectIds.ViewDescription)

    ViewId: NodeId = field(default_factory=NodeId)
    Timestamp: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    ViewVersion: UInt32 = 0


@dataclass(frozen=FROZEN)
class BrowseDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.2/#5.8.2.2

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar BrowseDirection:
    :vartype BrowseDirection: BrowseDirection
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar IncludeSubtypes:
    :vartype IncludeSubtypes: Boolean
    :ivar NodeClassMask:
    :vartype NodeClassMask: UInt32
    :ivar ResultMask:
    :vartype ResultMask: UInt32
    """

    data_type = NodeId(ObjectIds.BrowseDescription)

    NodeId_: NodeId = field(default_factory=NodeId)
    BrowseDirection_: BrowseDirection = BrowseDirection.Forward
    ReferenceTypeId: NodeId = field(default_factory=NodeId)
    IncludeSubtypes: Boolean = True
    NodeClassMask: UInt32 = 0
    ResultMask: UInt32 = 0

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val
    @property
    def BrowseDirection(self):
        return self.BrowseDirection_

    @BrowseDirection.setter
    def BrowseDirection(self, val):
        self.BrowseDirection_ = val


@dataclass(frozen=FROZEN)
class ReferenceDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.30

    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar IsForward:
    :vartype IsForward: Boolean
    :ivar NodeId:
    :vartype NodeId: ExpandedNodeId
    :ivar BrowseName:
    :vartype BrowseName: QualifiedName
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar NodeClass:
    :vartype NodeClass: NodeClass
    :ivar TypeDefinition:
    :vartype TypeDefinition: ExpandedNodeId
    """

    data_type = NodeId(ObjectIds.ReferenceDescription)

    ReferenceTypeId: NodeId = field(default_factory=NodeId)
    IsForward: Boolean = True
    NodeId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    BrowseName: QualifiedName = field(default_factory=QualifiedName)
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    NodeClass_: NodeClass = NodeClass.Unspecified
    TypeDefinition: ExpandedNodeId = field(default_factory=ExpandedNodeId)

    @property
    def NodeClass(self):
        return self.NodeClass_

    @NodeClass.setter
    def NodeClass(self, val):
        self.NodeClass_ = val


@dataclass(frozen=FROZEN)
class BrowseResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.6

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ContinuationPoint
    :ivar References:
    :vartype References: ReferenceDescription
    """

    data_type = NodeId(ObjectIds.BrowseResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    ContinuationPoint_: ContinuationPoint = None
    References: List[ReferenceDescription] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val
    @property
    def ContinuationPoint(self):
        return self.ContinuationPoint_

    @ContinuationPoint.setter
    def ContinuationPoint(self, val):
        self.ContinuationPoint_ = val


@dataclass(frozen=FROZEN)
class BrowseParameters:
    """
    :ivar View:
    :vartype View: ViewDescription
    :ivar RequestedMaxReferencesPerNode:
    :vartype RequestedMaxReferencesPerNode: Counter
    :ivar NodesToBrowse:
    :vartype NodesToBrowse: BrowseDescription
    """

    View: ViewDescription = field(default_factory=ViewDescription)
    RequestedMaxReferencesPerNode: Counter = 0
    NodesToBrowse: List[BrowseDescription] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class BrowseRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.2/#5.8.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: BrowseParameters
    """

    data_type = NodeId(ObjectIds.BrowseRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.BrowseRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: BrowseParameters = field(default_factory=BrowseParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class BrowseResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.2/#5.8.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: BrowseResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.BrowseResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.BrowseResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[BrowseResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class BrowseNextParameters:
    """
    :ivar ReleaseContinuationPoints:
    :vartype ReleaseContinuationPoints: Boolean
    :ivar ContinuationPoints:
    :vartype ContinuationPoints: ContinuationPoint
    """

    ReleaseContinuationPoints: Boolean = True
    ContinuationPoints: List[ContinuationPoint] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class BrowseNextRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.3/#5.8.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: BrowseNextParameters
    """

    data_type = NodeId(ObjectIds.BrowseNextRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.BrowseNextRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: BrowseNextParameters = field(default_factory=BrowseNextParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class BrowseNextResult:
    """
    :ivar Results:
    :vartype Results: BrowseResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    Results: List[BrowseResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class BrowseNextResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.3/#5.8.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: BrowseNextResult
    """

    data_type = NodeId(ObjectIds.BrowseNextResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.BrowseNextResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: BrowseNextResult = field(default_factory=BrowseNextResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class BrowsePath:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part3/6.2.5

    :ivar StartingNode:
    :vartype StartingNode: NodeId
    :ivar RelativePath:
    :vartype RelativePath: RelativePath
    """

    data_type = NodeId(ObjectIds.BrowsePath)

    StartingNode: NodeId = field(default_factory=NodeId)
    RelativePath_: RelativePath = field(default_factory=RelativePath)

    @property
    def RelativePath(self):
        return self.RelativePath_

    @RelativePath.setter
    def RelativePath(self, val):
        self.RelativePath_ = val


@dataclass(frozen=FROZEN)
class BrowsePathTarget:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.4/#5.8.4.2

    :ivar TargetId:
    :vartype TargetId: ExpandedNodeId
    :ivar RemainingPathIndex:
    :vartype RemainingPathIndex: Index
    """

    data_type = NodeId(ObjectIds.BrowsePathTarget)

    TargetId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    RemainingPathIndex: Index = 0


@dataclass(frozen=FROZEN)
class BrowsePathResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.4/#5.8.4.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar Targets:
    :vartype Targets: BrowsePathTarget
    """

    data_type = NodeId(ObjectIds.BrowsePathResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    Targets: List[BrowsePathTarget] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class TranslateBrowsePathsToNodeIdsParameters:
    """
    :ivar BrowsePaths:
    :vartype BrowsePaths: BrowsePath
    """

    BrowsePaths: List[BrowsePath] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class TranslateBrowsePathsToNodeIdsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.4/#5.8.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: TranslateBrowsePathsToNodeIdsParameters
    """

    data_type = NodeId(ObjectIds.TranslateBrowsePathsToNodeIdsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.TranslateBrowsePathsToNodeIdsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: TranslateBrowsePathsToNodeIdsParameters = field(default_factory=TranslateBrowsePathsToNodeIdsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class TranslateBrowsePathsToNodeIdsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.4/#5.8.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: BrowsePathResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.TranslateBrowsePathsToNodeIdsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.TranslateBrowsePathsToNodeIdsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[BrowsePathResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class RegisterNodesParameters:
    """
    :ivar NodesToRegister:
    :vartype NodesToRegister: NodeId
    """

    NodesToRegister: List[NodeId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class RegisterNodesRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.5/#5.8.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: RegisterNodesParameters
    """

    data_type = NodeId(ObjectIds.RegisterNodesRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RegisterNodesRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: RegisterNodesParameters = field(default_factory=RegisterNodesParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class RegisterNodesResult:
    """
    :ivar RegisteredNodeIds:
    :vartype RegisteredNodeIds: NodeId
    """

    RegisteredNodeIds: List[NodeId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class RegisterNodesResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.5/#5.8.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: RegisterNodesResult
    """

    data_type = NodeId(ObjectIds.RegisterNodesResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RegisterNodesResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: RegisterNodesResult = field(default_factory=RegisterNodesResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class UnregisterNodesParameters:
    """
    :ivar NodesToUnregister:
    :vartype NodesToUnregister: NodeId
    """

    NodesToUnregister: List[NodeId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class UnregisterNodesRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.6/#5.8.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: UnregisterNodesParameters
    """

    data_type = NodeId(ObjectIds.UnregisterNodesRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.UnregisterNodesRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: UnregisterNodesParameters = field(default_factory=UnregisterNodesParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class UnregisterNodesResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.8.6/#5.8.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = NodeId(ObjectIds.UnregisterNodesResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.UnregisterNodesResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class EndpointConfiguration:
    """
    :ivar OperationTimeout:
    :vartype OperationTimeout: Int32
    :ivar UseBinaryEncoding:
    :vartype UseBinaryEncoding: Boolean
    :ivar MaxStringLength:
    :vartype MaxStringLength: Int32
    :ivar MaxByteStringLength:
    :vartype MaxByteStringLength: Int32
    :ivar MaxArrayLength:
    :vartype MaxArrayLength: Int32
    :ivar MaxMessageSize:
    :vartype MaxMessageSize: Int32
    :ivar MaxBufferSize:
    :vartype MaxBufferSize: Int32
    :ivar ChannelLifetime:
    :vartype ChannelLifetime: Int32
    :ivar SecurityTokenLifetime:
    :vartype SecurityTokenLifetime: Int32
    """

    data_type = NodeId(ObjectIds.EndpointConfiguration)

    OperationTimeout: Int32 = 0
    UseBinaryEncoding: Boolean = True
    MaxStringLength: Int32 = 0
    MaxByteStringLength: Int32 = 0
    MaxArrayLength: Int32 = 0
    MaxMessageSize: Int32 = 0
    MaxBufferSize: Int32 = 0
    ChannelLifetime: Int32 = 0
    SecurityTokenLifetime: Int32 = 0


@dataclass(frozen=FROZEN)
class QueryDataDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.3/#5.9.3.1

    :ivar RelativePath:
    :vartype RelativePath: RelativePath
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    """

    data_type = NodeId(ObjectIds.QueryDataDescription)

    RelativePath_: RelativePath = field(default_factory=RelativePath)
    AttributeId: IntegerId = 0
    IndexRange: NumericRange = None

    @property
    def RelativePath(self):
        return self.RelativePath_

    @RelativePath.setter
    def RelativePath(self, val):
        self.RelativePath_ = val


@dataclass(frozen=FROZEN)
class NodeTypeDescription:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.3/#5.9.3.1

    :ivar TypeDefinitionNode:
    :vartype TypeDefinitionNode: ExpandedNodeId
    :ivar IncludeSubTypes:
    :vartype IncludeSubTypes: Boolean
    :ivar DataToReturn:
    :vartype DataToReturn: QueryDataDescription
    """

    data_type = NodeId(ObjectIds.NodeTypeDescription)

    TypeDefinitionNode: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    IncludeSubTypes: Boolean = True
    DataToReturn: List[QueryDataDescription] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class QueryDataSet:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.28

    :ivar NodeId:
    :vartype NodeId: ExpandedNodeId
    :ivar TypeDefinitionNode:
    :vartype TypeDefinitionNode: ExpandedNodeId
    :ivar Values:
    :vartype Values: Variant
    """

    data_type = NodeId(ObjectIds.QueryDataSet)

    NodeId: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    TypeDefinitionNode: ExpandedNodeId = field(default_factory=ExpandedNodeId)
    Values: List[Variant] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class NodeReference:
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar IsForward:
    :vartype IsForward: Boolean
    :ivar ReferencedNodeIds:
    :vartype ReferencedNodeIds: NodeId
    """

    data_type = NodeId(ObjectIds.NodeReference)

    NodeId_: NodeId = field(default_factory=NodeId)
    ReferenceTypeId: NodeId = field(default_factory=NodeId)
    IsForward: Boolean = True
    ReferencedNodeIds: List[NodeId] = field(default_factory=list)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class ContentFilterElement:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.1

    :ivar FilterOperator:
    :vartype FilterOperator: FilterOperator
    :ivar FilterOperands:
    :vartype FilterOperands: ExtensionObject
    """

    data_type = NodeId(ObjectIds.ContentFilterElement)

    FilterOperator_: FilterOperator = FilterOperator.Equals
    FilterOperands: List[ExtensionObject] = field(default_factory=list)

    @property
    def FilterOperator(self):
        return self.FilterOperator_

    @FilterOperator.setter
    def FilterOperator(self, val):
        self.FilterOperator_ = val


@dataclass(frozen=FROZEN)
class ContentFilter:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.3.4

    :ivar Elements:
    :vartype Elements: ContentFilterElement
    """

    data_type = NodeId(ObjectIds.ContentFilter)

    Elements: List[ContentFilterElement] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class FilterOperand:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.4

    """

    data_type = NodeId(ObjectIds.FilterOperand)


@dataclass(frozen=FROZEN)
class ElementOperand(FilterOperand):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.4/#7.7.4.2

    :ivar Index:
    :vartype Index: UInt32
    """

    data_type = NodeId(ObjectIds.ElementOperand)

    Index: UInt32 = 0


@dataclass(frozen=FROZEN)
class LiteralOperand(FilterOperand):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.4/#7.7.4.3

    :ivar Value:
    :vartype Value: Variant
    """

    data_type = NodeId(ObjectIds.LiteralOperand)

    Value: Variant = field(default_factory=Variant)


@dataclass(frozen=FROZEN)
class AttributeOperand(FilterOperand):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.4/#7.7.4.4

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar Alias:
    :vartype Alias: String
    :ivar BrowsePath:
    :vartype BrowsePath: RelativePath
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    """

    data_type = NodeId(ObjectIds.AttributeOperand)

    NodeId_: NodeId = field(default_factory=NodeId)
    Alias: String = None
    BrowsePath: RelativePath = field(default_factory=RelativePath)
    AttributeId: IntegerId = 0
    IndexRange: NumericRange = None

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class SimpleAttributeOperand(FilterOperand):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.4/#7.7.4.5

    :ivar TypeDefinitionId:
    :vartype TypeDefinitionId: NodeId
    :ivar BrowsePath:
    :vartype BrowsePath: QualifiedName
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    """

    data_type = NodeId(ObjectIds.SimpleAttributeOperand)

    TypeDefinitionId: NodeId = field(default_factory=NodeId)
    BrowsePath: List[QualifiedName] = field(default_factory=list)
    AttributeId: IntegerId = 0
    IndexRange: NumericRange = None


@dataclass(frozen=FROZEN)
class PublishedEventsDataType(PublishedDataSetSourceDataType):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part14/6.2.3/#6.2.3.8.4

    :ivar EventNotifier:
    :vartype EventNotifier: NodeId
    :ivar SelectedFields:
    :vartype SelectedFields: SimpleAttributeOperand
    :ivar Filter:
    :vartype Filter: ContentFilter
    """

    data_type = NodeId(ObjectIds.PublishedEventsDataType)

    EventNotifier: NodeId = field(default_factory=NodeId)
    SelectedFields: List[SimpleAttributeOperand] = field(default_factory=list)
    Filter: ContentFilter = field(default_factory=ContentFilter)


@dataclass(frozen=FROZEN)
class ContentFilterElementResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar OperandStatusCodes:
    :vartype OperandStatusCodes: StatusCode
    :ivar OperandDiagnosticInfos:
    :vartype OperandDiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.ContentFilterElementResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    OperandStatusCodes: List[StatusCode] = field(default_factory=list)
    OperandDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class ContentFilterResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.7.2

    :ivar ElementResults:
    :vartype ElementResults: ContentFilterElementResult
    :ivar ElementDiagnosticInfos:
    :vartype ElementDiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.ContentFilterResult)

    ElementResults: List[ContentFilterElementResult] = field(default_factory=list)
    ElementDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class ParsingResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.3/#5.9.3.1

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar DataStatusCodes:
    :vartype DataStatusCodes: StatusCode
    :ivar DataDiagnosticInfos:
    :vartype DataDiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.ParsingResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    DataStatusCodes: List[StatusCode] = field(default_factory=list)
    DataDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class QueryFirstParameters:
    """
    :ivar View:
    :vartype View: ViewDescription
    :ivar NodeTypes:
    :vartype NodeTypes: NodeTypeDescription
    :ivar Filter:
    :vartype Filter: ContentFilter
    :ivar MaxDataSetsToReturn:
    :vartype MaxDataSetsToReturn: Counter
    :ivar MaxReferencesToReturn:
    :vartype MaxReferencesToReturn: Counter
    """

    View: ViewDescription = field(default_factory=ViewDescription)
    NodeTypes: List[NodeTypeDescription] = field(default_factory=list)
    Filter: ContentFilter = field(default_factory=ContentFilter)
    MaxDataSetsToReturn: Counter = 0
    MaxReferencesToReturn: Counter = 0


@dataclass(frozen=FROZEN)
class QueryFirstRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.3/#5.9.3.1

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: QueryFirstParameters
    """

    data_type = NodeId(ObjectIds.QueryFirstRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.QueryFirstRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: QueryFirstParameters = field(default_factory=QueryFirstParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class QueryFirstResult:
    """
    :ivar QueryDataSets:
    :vartype QueryDataSets: QueryDataSet
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ContinuationPoint
    :ivar ParsingResults:
    :vartype ParsingResults: ParsingResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    :ivar FilterResult:
    :vartype FilterResult: ContentFilterResult
    """

    QueryDataSets: List[QueryDataSet] = field(default_factory=list)
    ContinuationPoint_: ContinuationPoint = None
    ParsingResults: List[ParsingResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)
    FilterResult: ContentFilterResult = field(default_factory=ContentFilterResult)

    @property
    def ContinuationPoint(self):
        return self.ContinuationPoint_

    @ContinuationPoint.setter
    def ContinuationPoint(self, val):
        self.ContinuationPoint_ = val


@dataclass(frozen=FROZEN)
class QueryFirstResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.3/#5.9.3.1

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: QueryFirstResult
    """

    data_type = NodeId(ObjectIds.QueryFirstResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.QueryFirstResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: QueryFirstResult = field(default_factory=QueryFirstResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class QueryNextParameters:
    """
    :ivar ReleaseContinuationPoint:
    :vartype ReleaseContinuationPoint: Boolean
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ContinuationPoint
    """

    ReleaseContinuationPoint: Boolean = True
    ContinuationPoint_: ContinuationPoint = None

    @property
    def ContinuationPoint(self):
        return self.ContinuationPoint_

    @ContinuationPoint.setter
    def ContinuationPoint(self, val):
        self.ContinuationPoint_ = val


@dataclass(frozen=FROZEN)
class QueryNextRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.4/#5.9.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: QueryNextParameters
    """

    data_type = NodeId(ObjectIds.QueryNextRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.QueryNextRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: QueryNextParameters = field(default_factory=QueryNextParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class QueryNextResult:
    """
    :ivar QueryDataSets:
    :vartype QueryDataSets: QueryDataSet
    :ivar RevisedContinuationPoint:
    :vartype RevisedContinuationPoint: ContinuationPoint
    """

    QueryDataSets: List[QueryDataSet] = field(default_factory=list)
    RevisedContinuationPoint: ContinuationPoint = None


@dataclass(frozen=FROZEN)
class QueryNextResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.9.4/#5.9.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: QueryNextResult
    """

    data_type = NodeId(ObjectIds.QueryNextResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.QueryNextResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: QueryNextResult = field(default_factory=QueryNextResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class ReadValueId:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.29

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    :ivar DataEncoding:
    :vartype DataEncoding: QualifiedName
    """

    data_type = NodeId(ObjectIds.ReadValueId)

    NodeId_: NodeId = field(default_factory=NodeId)
    AttributeId: IntegerId = 0
    IndexRange: NumericRange = None
    DataEncoding: QualifiedName = field(default_factory=QualifiedName)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class ReadParameters:
    """
    :ivar MaxAge:
    :vartype MaxAge: Duration
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar NodesToRead:
    :vartype NodesToRead: ReadValueId
    """

    MaxAge: Duration = 0
    TimestampsToReturn_: TimestampsToReturn = TimestampsToReturn.Source
    NodesToRead: List[ReadValueId] = field(default_factory=list)

    @property
    def TimestampsToReturn(self):
        return self.TimestampsToReturn_

    @TimestampsToReturn.setter
    def TimestampsToReturn(self, val):
        self.TimestampsToReturn_ = val


@dataclass(frozen=FROZEN)
class ReadRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.2/#5.10.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ReadParameters
    """

    data_type = NodeId(ObjectIds.ReadRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ReadRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: ReadParameters = field(default_factory=ReadParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class ReadResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.2/#5.10.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: DataValue
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.ReadResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ReadResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[DataValue] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class HistoryReadValueId:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.3/#5.10.3.2

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    :ivar DataEncoding:
    :vartype DataEncoding: QualifiedName
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ContinuationPoint
    """

    data_type = NodeId(ObjectIds.HistoryReadValueId)

    NodeId_: NodeId = field(default_factory=NodeId)
    IndexRange: NumericRange = None
    DataEncoding: QualifiedName = field(default_factory=QualifiedName)
    ContinuationPoint_: ContinuationPoint = None

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val
    @property
    def ContinuationPoint(self):
        return self.ContinuationPoint_

    @ContinuationPoint.setter
    def ContinuationPoint(self, val):
        self.ContinuationPoint_ = val


@dataclass(frozen=FROZEN)
class HistoryReadResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.3/#5.10.3.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ContinuationPoint
    :ivar HistoryData:
    :vartype HistoryData: ExtensionObject
    """

    data_type = NodeId(ObjectIds.HistoryReadResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    ContinuationPoint_: ContinuationPoint = None
    HistoryData: ExtensionObject = ExtensionObject()

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val
    @property
    def ContinuationPoint(self):
        return self.ContinuationPoint_

    @ContinuationPoint.setter
    def ContinuationPoint(self, val):
        self.ContinuationPoint_ = val


@dataclass(frozen=FROZEN)
class HistoryReadDetails:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.1

    """

    data_type = NodeId(ObjectIds.HistoryReadDetails)


@dataclass(frozen=FROZEN)
class ReadRawModifiedDetails(HistoryReadDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.3/#6.5.3.1

    :ivar IsReadModified:
    :vartype IsReadModified: Boolean
    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar EndTime:
    :vartype EndTime: UtcTime
    :ivar NumValuesPerNode:
    :vartype NumValuesPerNode: Counter
    :ivar ReturnBounds:
    :vartype ReturnBounds: Boolean
    """

    data_type = NodeId(ObjectIds.ReadRawModifiedDetails)

    IsReadModified: Boolean = True
    StartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    EndTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    NumValuesPerNode: Counter = 0
    ReturnBounds: Boolean = True


@dataclass(frozen=FROZEN)
class ReadAtTimeDetails(HistoryReadDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.5/#6.5.5.1

    :ivar ReqTimes:
    :vartype ReqTimes: UtcTime
    :ivar UseSimpleBounds:
    :vartype UseSimpleBounds: Boolean
    """

    data_type = NodeId(ObjectIds.ReadAtTimeDetails)

    ReqTimes: List[UtcTime] = field(default_factory=list)
    UseSimpleBounds: Boolean = True


@dataclass(frozen=FROZEN)
class ReadAnnotationDataDetails(HistoryReadDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.6/#6.5.6.1

    :ivar ReqTimes:
    :vartype ReqTimes: UtcTime
    """

    data_type = NodeId(ObjectIds.ReadAnnotationDataDetails)

    ReqTimes: List[UtcTime] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class HistoryData:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.2

    :ivar DataValues:
    :vartype DataValues: DataValue
    """

    data_type = NodeId(ObjectIds.HistoryData)

    DataValues: List[DataValue] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class ModificationInfo:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.5

    :ivar ModificationTime:
    :vartype ModificationTime: UtcTime
    :ivar UpdateType:
    :vartype UpdateType: HistoryUpdateType
    :ivar UserName:
    :vartype UserName: String
    """

    data_type = NodeId(ObjectIds.ModificationInfo)

    ModificationTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    UpdateType: HistoryUpdateType = HistoryUpdateType.Insert
    UserName: String = None


@dataclass(frozen=FROZEN)
class HistoryModifiedData(HistoryData):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.3

    :ivar DataValues:
    :vartype DataValues: DataValue
    :ivar ModificationInfos:
    :vartype ModificationInfos: ModificationInfo
    """

    data_type = NodeId(ObjectIds.HistoryModifiedData)

    DataValues: List[DataValue] = field(default_factory=list)
    ModificationInfos: List[ModificationInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class HistoryReadParameters:
    """
    :ivar HistoryReadDetails:
    :vartype HistoryReadDetails: ExtensionObject
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar ReleaseContinuationPoints:
    :vartype ReleaseContinuationPoints: Boolean
    :ivar NodesToRead:
    :vartype NodesToRead: HistoryReadValueId
    """

    HistoryReadDetails: ExtensionObject = ExtensionObject()
    TimestampsToReturn_: TimestampsToReturn = TimestampsToReturn.Source
    ReleaseContinuationPoints: Boolean = True
    NodesToRead: List[HistoryReadValueId] = field(default_factory=list)

    @property
    def TimestampsToReturn(self):
        return self.TimestampsToReturn_

    @TimestampsToReturn.setter
    def TimestampsToReturn(self, val):
        self.TimestampsToReturn_ = val


@dataclass(frozen=FROZEN)
class HistoryReadRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.3/#5.10.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: HistoryReadParameters
    """

    data_type = NodeId(ObjectIds.HistoryReadRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.HistoryReadRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: HistoryReadParameters = field(default_factory=HistoryReadParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class HistoryReadResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.3/#5.10.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: HistoryReadResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.HistoryReadResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.HistoryReadResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[HistoryReadResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class WriteValue:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.4/#5.10.4.2

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar AttributeId:
    :vartype AttributeId: IntegerId
    :ivar IndexRange:
    :vartype IndexRange: NumericRange
    :ivar Value:
    :vartype Value: DataValue
    """

    data_type = NodeId(ObjectIds.WriteValue)

    NodeId_: NodeId = field(default_factory=NodeId)
    AttributeId: IntegerId = 0
    IndexRange: NumericRange = None
    Value: DataValue = field(default_factory=DataValue)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class WriteParameters:
    """
    :ivar NodesToWrite:
    :vartype NodesToWrite: WriteValue
    """

    NodesToWrite: List[WriteValue] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class WriteRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.4/#5.10.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: WriteParameters
    """

    data_type = NodeId(ObjectIds.WriteRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.WriteRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: WriteParameters = field(default_factory=WriteParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class WriteResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.4/#5.10.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.WriteResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.WriteResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class HistoryUpdateDetails:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.1

    """

    data_type = NodeId(ObjectIds.HistoryUpdateDetails)


@dataclass(frozen=FROZEN)
class UpdateDataDetails(HistoryUpdateDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.2/#6.9.2.1

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar PerformInsertReplace:
    :vartype PerformInsertReplace: PerformUpdateType
    :ivar UpdateValues:
    :vartype UpdateValues: DataValue
    """

    data_type = NodeId(ObjectIds.UpdateDataDetails)

    NodeId_: NodeId = field(default_factory=NodeId)
    PerformInsertReplace: PerformUpdateType = PerformUpdateType.Insert
    UpdateValues: List[DataValue] = field(default_factory=list)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class UpdateStructureDataDetails(HistoryUpdateDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.3/#6.9.3.1

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar PerformInsertReplace:
    :vartype PerformInsertReplace: PerformUpdateType
    :ivar UpdateValues:
    :vartype UpdateValues: DataValue
    """

    data_type = NodeId(ObjectIds.UpdateStructureDataDetails)

    NodeId_: NodeId = field(default_factory=NodeId)
    PerformInsertReplace: PerformUpdateType = PerformUpdateType.Insert
    UpdateValues: List[DataValue] = field(default_factory=list)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class DeleteRawModifiedDetails(HistoryUpdateDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.5/#6.9.5.1

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar IsDeleteModified:
    :vartype IsDeleteModified: Boolean
    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar EndTime:
    :vartype EndTime: UtcTime
    """

    data_type = NodeId(ObjectIds.DeleteRawModifiedDetails)

    NodeId_: NodeId = field(default_factory=NodeId)
    IsDeleteModified: Boolean = True
    StartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    EndTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class DeleteAtTimeDetails(HistoryUpdateDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.6/#6.9.6.1

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar ReqTimes:
    :vartype ReqTimes: UtcTime
    """

    data_type = NodeId(ObjectIds.DeleteAtTimeDetails)

    NodeId_: NodeId = field(default_factory=NodeId)
    ReqTimes: List[UtcTime] = field(default_factory=list)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class DeleteEventDetails(HistoryUpdateDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.7/#6.9.7.1

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar EventIds:
    :vartype EventIds: ByteString
    """

    data_type = NodeId(ObjectIds.DeleteEventDetails)

    NodeId_: NodeId = field(default_factory=NodeId)
    EventIds: List[ByteString] = field(default_factory=list)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class HistoryUpdateResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.5/#5.10.5.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar OperationResults:
    :vartype OperationResults: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.HistoryUpdateResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    OperationResults: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class HistoryUpdateParameters:
    """
    :ivar HistoryUpdateDetails:
    :vartype HistoryUpdateDetails: ExtensionObject
    """

    HistoryUpdateDetails: List[ExtensionObject] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class HistoryUpdateRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.5/#5.10.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: HistoryUpdateParameters
    """

    data_type = NodeId(ObjectIds.HistoryUpdateRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.HistoryUpdateRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: HistoryUpdateParameters = field(default_factory=HistoryUpdateParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class HistoryUpdateResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.10.5/#5.10.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: HistoryUpdateResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.HistoryUpdateResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.HistoryUpdateResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[HistoryUpdateResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class CallMethodRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.11.2/#5.11.2.2

    :ivar ObjectId:
    :vartype ObjectId: NodeId
    :ivar MethodId:
    :vartype MethodId: NodeId
    :ivar InputArguments:
    :vartype InputArguments: Variant
    """

    data_type = NodeId(ObjectIds.CallMethodRequest)

    ObjectId: NodeId = field(default_factory=NodeId)
    MethodId: NodeId = field(default_factory=NodeId)
    InputArguments: List[Variant] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class CallMethodResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.11.2/#5.11.2.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar InputArgumentResults:
    :vartype InputArgumentResults: StatusCode
    :ivar InputArgumentDiagnosticInfos:
    :vartype InputArgumentDiagnosticInfos: DiagnosticInfo
    :ivar OutputArguments:
    :vartype OutputArguments: Variant
    """

    data_type = NodeId(ObjectIds.CallMethodResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    InputArgumentResults: List[StatusCode] = field(default_factory=list)
    InputArgumentDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)
    OutputArguments: List[Variant] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class CallParameters:
    """
    :ivar MethodsToCall:
    :vartype MethodsToCall: CallMethodRequest
    """

    MethodsToCall: List[CallMethodRequest] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class CallRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.11.2/#5.11.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CallParameters
    """

    data_type = NodeId(ObjectIds.CallRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CallRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: CallParameters = field(default_factory=CallParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CallResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.11.2/#5.11.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: CallMethodResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.CallResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CallResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[CallMethodResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class MonitoringFilter:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.1

    """

    data_type = NodeId(ObjectIds.MonitoringFilter)


@dataclass(frozen=FROZEN)
class DataChangeFilter(MonitoringFilter):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.2

    :ivar Trigger:
    :vartype Trigger: DataChangeTrigger
    :ivar DeadbandType:
    :vartype DeadbandType: UInt32
    :ivar DeadbandValue:
    :vartype DeadbandValue: Double
    """

    data_type = NodeId(ObjectIds.DataChangeFilter)

    Trigger: DataChangeTrigger = DataChangeTrigger.Status
    DeadbandType: UInt32 = 0
    DeadbandValue: Double = 0


@dataclass(frozen=FROZEN)
class EventFilter(MonitoringFilter):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.3

    :ivar SelectClauses:
    :vartype SelectClauses: SimpleAttributeOperand
    :ivar WhereClause:
    :vartype WhereClause: ContentFilter
    """

    data_type = NodeId(ObjectIds.EventFilter)

    SelectClauses: List[SimpleAttributeOperand] = field(default_factory=list)
    WhereClause: ContentFilter = field(default_factory=ContentFilter)


@dataclass(frozen=FROZEN)
class ReadEventDetails(HistoryReadDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.2/#6.5.2.1

    :ivar NumValuesPerNode:
    :vartype NumValuesPerNode: Counter
    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar EndTime:
    :vartype EndTime: UtcTime
    :ivar Filter:
    :vartype Filter: EventFilter
    """

    data_type = NodeId(ObjectIds.ReadEventDetails)

    NumValuesPerNode: Counter = 0
    StartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    EndTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    Filter: EventFilter = field(default_factory=EventFilter)


@dataclass(frozen=FROZEN)
class ReadEventDetails2(ReadEventDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.2/#6.5.2.3

    :ivar NumValuesPerNode:
    :vartype NumValuesPerNode: Counter
    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar EndTime:
    :vartype EndTime: UtcTime
    :ivar Filter:
    :vartype Filter: EventFilter
    :ivar ReadModified:
    :vartype ReadModified: Boolean
    """

    data_type = NodeId(ObjectIds.ReadEventDetails2)

    NumValuesPerNode: Counter = 0
    StartTime: UtcTime = field(default_factory=datetime.utcnow)
    EndTime: UtcTime = field(default_factory=datetime.utcnow)
    Filter: EventFilter = field(default_factory=EventFilter)
    ReadModified: Boolean = True


@dataclass(frozen=FROZEN)
class AggregateConfiguration:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.4

    :ivar UseServerCapabilitiesDefaults:
    :vartype UseServerCapabilitiesDefaults: Boolean
    :ivar TreatUncertainAsBad:
    :vartype TreatUncertainAsBad: Boolean
    :ivar PercentDataBad:
    :vartype PercentDataBad: Byte
    :ivar PercentDataGood:
    :vartype PercentDataGood: Byte
    :ivar UseSlopedExtrapolation:
    :vartype UseSlopedExtrapolation: Boolean
    """

    data_type = NodeId(ObjectIds.AggregateConfiguration)

    UseServerCapabilitiesDefaults: Boolean = True
    TreatUncertainAsBad: Boolean = True
    PercentDataBad: Byte = 0
    PercentDataGood: Byte = 0
    UseSlopedExtrapolation: Boolean = True


@dataclass(frozen=FROZEN)
class ReadProcessedDetails(HistoryReadDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.5.4/#6.5.4.1

    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar EndTime:
    :vartype EndTime: UtcTime
    :ivar ProcessingInterval:
    :vartype ProcessingInterval: Duration
    :ivar AggregateType:
    :vartype AggregateType: NodeId
    :ivar AggregateConfiguration:
    :vartype AggregateConfiguration: AggregateConfiguration
    """

    data_type = NodeId(ObjectIds.ReadProcessedDetails)

    StartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    EndTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    ProcessingInterval: Duration = 0
    AggregateType: List[NodeId] = field(default_factory=list)
    AggregateConfiguration_: AggregateConfiguration = field(default_factory=AggregateConfiguration)

    @property
    def AggregateConfiguration(self):
        return self.AggregateConfiguration_

    @AggregateConfiguration.setter
    def AggregateConfiguration(self, val):
        self.AggregateConfiguration_ = val


@dataclass(frozen=FROZEN)
class AggregateFilter(MonitoringFilter):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.4

    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar AggregateType:
    :vartype AggregateType: NodeId
    :ivar ProcessingInterval:
    :vartype ProcessingInterval: Duration
    :ivar AggregateConfiguration:
    :vartype AggregateConfiguration: AggregateConfiguration
    """

    data_type = NodeId(ObjectIds.AggregateFilter)

    StartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    AggregateType: NodeId = field(default_factory=NodeId)
    ProcessingInterval: Duration = 0
    AggregateConfiguration_: AggregateConfiguration = field(default_factory=AggregateConfiguration)

    @property
    def AggregateConfiguration(self):
        return self.AggregateConfiguration_

    @AggregateConfiguration.setter
    def AggregateConfiguration(self, val):
        self.AggregateConfiguration_ = val


@dataclass(frozen=FROZEN)
class MonitoringFilterResult:
    """
    """

    data_type = NodeId(ObjectIds.MonitoringFilterResult)


@dataclass(frozen=FROZEN)
class EventFilterResult(MonitoringFilterResult):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.3

    :ivar SelectClauseResults:
    :vartype SelectClauseResults: StatusCode
    :ivar SelectClauseDiagnosticInfos:
    :vartype SelectClauseDiagnosticInfos: DiagnosticInfo
    :ivar WhereClauseResult:
    :vartype WhereClauseResult: ContentFilterResult
    """

    data_type = NodeId(ObjectIds.EventFilterResult)

    SelectClauseResults: List[StatusCode] = field(default_factory=list)
    SelectClauseDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)
    WhereClauseResult: ContentFilterResult = field(default_factory=ContentFilterResult)


@dataclass(frozen=FROZEN)
class AggregateFilterResult(MonitoringFilterResult):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.22.4

    :ivar RevisedStartTime:
    :vartype RevisedStartTime: UtcTime
    :ivar RevisedProcessingInterval:
    :vartype RevisedProcessingInterval: Duration
    :ivar RevisedAggregateConfiguration:
    :vartype RevisedAggregateConfiguration: AggregateConfiguration
    """

    data_type = NodeId(ObjectIds.AggregateFilterResult)

    RevisedStartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    RevisedProcessingInterval: Duration = 0
    RevisedAggregateConfiguration: AggregateConfiguration = field(default_factory=AggregateConfiguration)


@dataclass(frozen=FROZEN)
class MonitoringParameters:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.21

    :ivar ClientHandle:
    :vartype ClientHandle: IntegerId
    :ivar SamplingInterval:
    :vartype SamplingInterval: Duration
    :ivar Filter:
    :vartype Filter: ExtensionObject
    :ivar QueueSize:
    :vartype QueueSize: Counter
    :ivar DiscardOldest:
    :vartype DiscardOldest: Boolean
    """

    data_type = NodeId(ObjectIds.MonitoringParameters)

    ClientHandle: IntegerId = 0
    SamplingInterval: Duration = 0
    Filter: ExtensionObject = ExtensionObject()
    QueueSize: Counter = 0
    DiscardOldest: Boolean = True


@dataclass(frozen=FROZEN)
class MonitoredItemCreateRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.2/#5.12.2.2

    :ivar ItemToMonitor:
    :vartype ItemToMonitor: ReadValueId
    :ivar MonitoringMode:
    :vartype MonitoringMode: MonitoringMode
    :ivar RequestedParameters:
    :vartype RequestedParameters: MonitoringParameters
    """

    data_type = NodeId(ObjectIds.MonitoredItemCreateRequest)

    ItemToMonitor: ReadValueId = field(default_factory=ReadValueId)
    MonitoringMode_: MonitoringMode = MonitoringMode.Disabled
    RequestedParameters: MonitoringParameters = field(default_factory=MonitoringParameters)

    @property
    def MonitoringMode(self):
        return self.MonitoringMode_

    @MonitoringMode.setter
    def MonitoringMode(self, val):
        self.MonitoringMode_ = val


@dataclass(frozen=FROZEN)
class MonitoredItemCreateResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.2/#5.12.2.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar MonitoredItemId:
    :vartype MonitoredItemId: IntegerId
    :ivar RevisedSamplingInterval:
    :vartype RevisedSamplingInterval: Duration
    :ivar RevisedQueueSize:
    :vartype RevisedQueueSize: Counter
    :ivar FilterResult:
    :vartype FilterResult: ExtensionObject
    """

    data_type = NodeId(ObjectIds.MonitoredItemCreateResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    MonitoredItemId: IntegerId = 0
    RevisedSamplingInterval: Duration = 0
    RevisedQueueSize: Counter = 0
    FilterResult: ExtensionObject = ExtensionObject()

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class CreateMonitoredItemsParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar ItemsToCreate:
    :vartype ItemsToCreate: MonitoredItemCreateRequest
    """

    SubscriptionId: IntegerId = 0
    TimestampsToReturn_: TimestampsToReturn = TimestampsToReturn.Source
    ItemsToCreate: List[MonitoredItemCreateRequest] = field(default_factory=list)

    @property
    def TimestampsToReturn(self):
        return self.TimestampsToReturn_

    @TimestampsToReturn.setter
    def TimestampsToReturn(self, val):
        self.TimestampsToReturn_ = val


@dataclass(frozen=FROZEN)
class CreateMonitoredItemsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.2/#5.12.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CreateMonitoredItemsParameters
    """

    data_type = NodeId(ObjectIds.CreateMonitoredItemsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CreateMonitoredItemsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: CreateMonitoredItemsParameters = field(default_factory=CreateMonitoredItemsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CreateMonitoredItemsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.2/#5.12.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: MonitoredItemCreateResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.CreateMonitoredItemsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CreateMonitoredItemsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[MonitoredItemCreateResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class MonitoredItemModifyRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.3/#5.12.3.2

    :ivar MonitoredItemId:
    :vartype MonitoredItemId: IntegerId
    :ivar RequestedParameters:
    :vartype RequestedParameters: MonitoringParameters
    """

    data_type = NodeId(ObjectIds.MonitoredItemModifyRequest)

    MonitoredItemId: IntegerId = 0
    RequestedParameters: MonitoringParameters = field(default_factory=MonitoringParameters)


@dataclass(frozen=FROZEN)
class MonitoredItemModifyResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.3/#5.12.3.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar RevisedSamplingInterval:
    :vartype RevisedSamplingInterval: Duration
    :ivar RevisedQueueSize:
    :vartype RevisedQueueSize: Counter
    :ivar FilterResult:
    :vartype FilterResult: ExtensionObject
    """

    data_type = NodeId(ObjectIds.MonitoredItemModifyResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    RevisedSamplingInterval: Duration = 0
    RevisedQueueSize: Counter = 0
    FilterResult: ExtensionObject = ExtensionObject()

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class ModifyMonitoredItemsParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar ItemsToModify:
    :vartype ItemsToModify: MonitoredItemModifyRequest
    """

    SubscriptionId: IntegerId = 0
    TimestampsToReturn_: TimestampsToReturn = TimestampsToReturn.Source
    ItemsToModify: List[MonitoredItemModifyRequest] = field(default_factory=list)

    @property
    def TimestampsToReturn(self):
        return self.TimestampsToReturn_

    @TimestampsToReturn.setter
    def TimestampsToReturn(self, val):
        self.TimestampsToReturn_ = val


@dataclass(frozen=FROZEN)
class ModifyMonitoredItemsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.3/#5.12.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ModifyMonitoredItemsParameters
    """

    data_type = NodeId(ObjectIds.ModifyMonitoredItemsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ModifyMonitoredItemsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: ModifyMonitoredItemsParameters = field(default_factory=ModifyMonitoredItemsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class ModifyMonitoredItemsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.3/#5.12.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: MonitoredItemModifyResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.ModifyMonitoredItemsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ModifyMonitoredItemsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[MonitoredItemModifyResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class SetMonitoringModeParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar MonitoringMode:
    :vartype MonitoringMode: MonitoringMode
    :ivar MonitoredItemIds:
    :vartype MonitoredItemIds: IntegerId
    """

    SubscriptionId: IntegerId = 0
    MonitoringMode_: MonitoringMode = MonitoringMode.Disabled
    MonitoredItemIds: List[IntegerId] = field(default_factory=list)

    @property
    def MonitoringMode(self):
        return self.MonitoringMode_

    @MonitoringMode.setter
    def MonitoringMode(self, val):
        self.MonitoringMode_ = val


@dataclass(frozen=FROZEN)
class SetMonitoringModeRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.4/#5.12.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: SetMonitoringModeParameters
    """

    data_type = NodeId(ObjectIds.SetMonitoringModeRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.SetMonitoringModeRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: SetMonitoringModeParameters = field(default_factory=SetMonitoringModeParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class SetMonitoringModeResult:
    """
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SetMonitoringModeResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.4/#5.12.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: SetMonitoringModeResult
    """

    data_type = NodeId(ObjectIds.SetMonitoringModeResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.SetMonitoringModeResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: SetMonitoringModeResult = field(default_factory=SetMonitoringModeResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class SetTriggeringParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar TriggeringItemId:
    :vartype TriggeringItemId: IntegerId
    :ivar LinksToAdd:
    :vartype LinksToAdd: IntegerId
    :ivar LinksToRemove:
    :vartype LinksToRemove: IntegerId
    """

    SubscriptionId: IntegerId = 0
    TriggeringItemId: IntegerId = 0
    LinksToAdd: List[IntegerId] = field(default_factory=list)
    LinksToRemove: List[IntegerId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SetTriggeringRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.5/#5.12.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: SetTriggeringParameters
    """

    data_type = NodeId(ObjectIds.SetTriggeringRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.SetTriggeringRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: SetTriggeringParameters = field(default_factory=SetTriggeringParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class SetTriggeringResult:
    """
    :ivar AddResults:
    :vartype AddResults: StatusCode
    :ivar AddDiagnosticInfos:
    :vartype AddDiagnosticInfos: DiagnosticInfo
    :ivar RemoveResults:
    :vartype RemoveResults: StatusCode
    :ivar RemoveDiagnosticInfos:
    :vartype RemoveDiagnosticInfos: DiagnosticInfo
    """

    AddResults: List[StatusCode] = field(default_factory=list)
    AddDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)
    RemoveResults: List[StatusCode] = field(default_factory=list)
    RemoveDiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SetTriggeringResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.5/#5.12.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: SetTriggeringResult
    """

    data_type = NodeId(ObjectIds.SetTriggeringResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.SetTriggeringResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: SetTriggeringResult = field(default_factory=SetTriggeringResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteMonitoredItemsParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar MonitoredItemIds:
    :vartype MonitoredItemIds: IntegerId
    """

    SubscriptionId: IntegerId = 0
    MonitoredItemIds: List[IntegerId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DeleteMonitoredItemsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.6/#5.12.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteMonitoredItemsParameters
    """

    data_type = NodeId(ObjectIds.DeleteMonitoredItemsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteMonitoredItemsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: DeleteMonitoredItemsParameters = field(default_factory=DeleteMonitoredItemsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteMonitoredItemsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.12.6/#5.12.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.DeleteMonitoredItemsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteMonitoredItemsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class CreateSubscriptionParameters:
    """
    :ivar RequestedPublishingInterval:
    :vartype RequestedPublishingInterval: Duration
    :ivar RequestedLifetimeCount:
    :vartype RequestedLifetimeCount: Counter
    :ivar RequestedMaxKeepAliveCount:
    :vartype RequestedMaxKeepAliveCount: Counter
    :ivar MaxNotificationsPerPublish:
    :vartype MaxNotificationsPerPublish: Counter
    :ivar PublishingEnabled:
    :vartype PublishingEnabled: Boolean
    :ivar Priority:
    :vartype Priority: Byte
    """

    RequestedPublishingInterval: Duration = 0
    RequestedLifetimeCount: Counter = 0
    RequestedMaxKeepAliveCount: Counter = 0
    MaxNotificationsPerPublish: Counter = 0
    PublishingEnabled: Boolean = True
    Priority: Byte = 0


@dataclass(frozen=FROZEN)
class CreateSubscriptionRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.2/#5.13.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CreateSubscriptionParameters
    """

    data_type = NodeId(ObjectIds.CreateSubscriptionRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CreateSubscriptionRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: CreateSubscriptionParameters = field(default_factory=CreateSubscriptionParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class CreateSubscriptionResult:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar RevisedPublishingInterval:
    :vartype RevisedPublishingInterval: Duration
    :ivar RevisedLifetimeCount:
    :vartype RevisedLifetimeCount: Counter
    :ivar RevisedMaxKeepAliveCount:
    :vartype RevisedMaxKeepAliveCount: Counter
    """

    SubscriptionId: IntegerId = 0
    RevisedPublishingInterval: Duration = 0
    RevisedLifetimeCount: Counter = 0
    RevisedMaxKeepAliveCount: Counter = 0


@dataclass(frozen=FROZEN)
class CreateSubscriptionResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.2/#5.13.2.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: CreateSubscriptionResult
    """

    data_type = NodeId(ObjectIds.CreateSubscriptionResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.CreateSubscriptionResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: CreateSubscriptionResult = field(default_factory=CreateSubscriptionResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class ModifySubscriptionParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar RequestedPublishingInterval:
    :vartype RequestedPublishingInterval: Duration
    :ivar RequestedLifetimeCount:
    :vartype RequestedLifetimeCount: Counter
    :ivar RequestedMaxKeepAliveCount:
    :vartype RequestedMaxKeepAliveCount: Counter
    :ivar MaxNotificationsPerPublish:
    :vartype MaxNotificationsPerPublish: Counter
    :ivar Priority:
    :vartype Priority: Byte
    """

    SubscriptionId: IntegerId = 0
    RequestedPublishingInterval: Duration = 0
    RequestedLifetimeCount: Counter = 0
    RequestedMaxKeepAliveCount: Counter = 0
    MaxNotificationsPerPublish: Counter = 0
    Priority: Byte = 0


@dataclass(frozen=FROZEN)
class ModifySubscriptionRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.3/#5.13.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ModifySubscriptionParameters
    """

    data_type = NodeId(ObjectIds.ModifySubscriptionRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ModifySubscriptionRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: ModifySubscriptionParameters = field(default_factory=ModifySubscriptionParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class ModifySubscriptionResult:
    """
    :ivar RevisedPublishingInterval:
    :vartype RevisedPublishingInterval: Duration
    :ivar RevisedLifetimeCount:
    :vartype RevisedLifetimeCount: Counter
    :ivar RevisedMaxKeepAliveCount:
    :vartype RevisedMaxKeepAliveCount: Counter
    """

    RevisedPublishingInterval: Duration = 0
    RevisedLifetimeCount: Counter = 0
    RevisedMaxKeepAliveCount: Counter = 0


@dataclass(frozen=FROZEN)
class ModifySubscriptionResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.3/#5.13.3.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: ModifySubscriptionResult
    """

    data_type = NodeId(ObjectIds.ModifySubscriptionResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.ModifySubscriptionResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: ModifySubscriptionResult = field(default_factory=ModifySubscriptionResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class SetPublishingModeParameters:
    """
    :ivar PublishingEnabled:
    :vartype PublishingEnabled: Boolean
    :ivar SubscriptionIds:
    :vartype SubscriptionIds: IntegerId
    """

    PublishingEnabled: Boolean = True
    SubscriptionIds: List[IntegerId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SetPublishingModeRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.4/#5.13.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: SetPublishingModeParameters
    """

    data_type = NodeId(ObjectIds.SetPublishingModeRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.SetPublishingModeRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: SetPublishingModeParameters = field(default_factory=SetPublishingModeParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class SetPublishingModeResult:
    """
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SetPublishingModeResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.4/#5.13.4.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: SetPublishingModeResult
    """

    data_type = NodeId(ObjectIds.SetPublishingModeResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.SetPublishingModeResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: SetPublishingModeResult = field(default_factory=SetPublishingModeResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class NotificationMessage:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.26

    :ivar SequenceNumber:
    :vartype SequenceNumber: Counter
    :ivar PublishTime:
    :vartype PublishTime: UtcTime
    :ivar NotificationData:
    :vartype NotificationData: ExtensionObject
    """

    data_type = NodeId(ObjectIds.NotificationMessage)

    SequenceNumber: Counter = 0
    PublishTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    NotificationData: List[ExtensionObject] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class NotificationData:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.25.1

    """

    data_type = NodeId(ObjectIds.NotificationData)


@dataclass(frozen=FROZEN)
class MonitoredItemNotification:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.25.2

    :ivar ClientHandle:
    :vartype ClientHandle: IntegerId
    :ivar Value:
    :vartype Value: DataValue
    """

    data_type = NodeId(ObjectIds.MonitoredItemNotification)

    ClientHandle: IntegerId = 0
    Value: DataValue = field(default_factory=DataValue)


@dataclass(frozen=FROZEN)
class DataChangeNotification(NotificationData):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.25.2

    :ivar MonitoredItems:
    :vartype MonitoredItems: MonitoredItemNotification
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.DataChangeNotification)

    MonitoredItems: List[MonitoredItemNotification] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class EventFieldList:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.25.3

    :ivar ClientHandle:
    :vartype ClientHandle: IntegerId
    :ivar EventFields:
    :vartype EventFields: Variant
    """

    data_type = NodeId(ObjectIds.EventFieldList)

    ClientHandle: IntegerId = 0
    EventFields: List[Variant] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class EventNotificationList(NotificationData):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.25.3

    :ivar Events:
    :vartype Events: EventFieldList
    """

    data_type = NodeId(ObjectIds.EventNotificationList)

    Events: List[EventFieldList] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class HistoryEventFieldList:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.4

    :ivar EventFields:
    :vartype EventFields: Variant
    """

    data_type = NodeId(ObjectIds.HistoryEventFieldList)

    EventFields: List[Variant] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class HistoryEvent:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.4

    :ivar Events:
    :vartype Events: HistoryEventFieldList
    """

    data_type = NodeId(ObjectIds.HistoryEvent)

    Events: List[HistoryEventFieldList] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class HistoryModifiedEvent(HistoryEvent):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.5

    :ivar Events:
    :vartype Events: HistoryEventFieldList
    :ivar ModificationInfos:
    :vartype ModificationInfos: ModificationInfo
    """

    data_type = NodeId(ObjectIds.HistoryModifiedEvent)

    Events: List[HistoryEventFieldList] = field(default_factory=list)
    ModificationInfos: List[ModificationInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class UpdateEventDetails(HistoryUpdateDetails):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.9.4/#6.9.4.1

    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar PerformInsertReplace:
    :vartype PerformInsertReplace: PerformUpdateType
    :ivar Filter:
    :vartype Filter: EventFilter
    :ivar EventData:
    :vartype EventData: HistoryEventFieldList
    """

    data_type = NodeId(ObjectIds.UpdateEventDetails)

    NodeId_: NodeId = field(default_factory=NodeId)
    PerformInsertReplace: PerformUpdateType = PerformUpdateType.Insert
    Filter: EventFilter = field(default_factory=EventFilter)
    EventData: List[HistoryEventFieldList] = field(default_factory=list)

    @property
    def NodeId(self):
        return self.NodeId_

    @NodeId.setter
    def NodeId(self, val):
        self.NodeId_ = val


@dataclass(frozen=FROZEN)
class StatusChangeNotification(NotificationData):
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/7.25.4

    :ivar Status:
    :vartype Status: StatusCode
    :ivar DiagnosticInfo:
    :vartype DiagnosticInfo: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.StatusChangeNotification)

    Status: StatusCode = field(default_factory=StatusCode)
    DiagnosticInfo_: DiagnosticInfo = field(default_factory=DiagnosticInfo)

    @property
    def DiagnosticInfo(self):
        return self.DiagnosticInfo_

    @DiagnosticInfo.setter
    def DiagnosticInfo(self, val):
        self.DiagnosticInfo_ = val


@dataclass(frozen=FROZEN)
class SubscriptionAcknowledgement:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.5/#5.13.5.2

    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar SequenceNumber:
    :vartype SequenceNumber: Counter
    """

    data_type = NodeId(ObjectIds.SubscriptionAcknowledgement)

    SubscriptionId: IntegerId = 0
    SequenceNumber: Counter = 0


@dataclass(frozen=FROZEN)
class PublishParameters:
    """
    :ivar SubscriptionAcknowledgements:
    :vartype SubscriptionAcknowledgements: SubscriptionAcknowledgement
    """

    SubscriptionAcknowledgements: List[SubscriptionAcknowledgement] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class PublishRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.5/#5.13.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: PublishParameters
    """

    data_type = NodeId(ObjectIds.PublishRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.PublishRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: PublishParameters = field(default_factory=PublishParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class PublishResult:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar AvailableSequenceNumbers:
    :vartype AvailableSequenceNumbers: Counter
    :ivar MoreNotifications:
    :vartype MoreNotifications: Boolean
    :ivar NotificationMessage:
    :vartype NotificationMessage: NotificationMessage
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    SubscriptionId: IntegerId = 0
    AvailableSequenceNumbers: List[Counter] = field(default_factory=list)
    MoreNotifications: Boolean = True
    NotificationMessage_: NotificationMessage = field(default_factory=NotificationMessage)
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def NotificationMessage(self):
        return self.NotificationMessage_

    @NotificationMessage.setter
    def NotificationMessage(self, val):
        self.NotificationMessage_ = val


@dataclass(frozen=FROZEN)
class PublishResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.5/#5.13.5.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: PublishResult
    """

    data_type = NodeId(ObjectIds.PublishResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.PublishResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: PublishResult = field(default_factory=PublishResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class RepublishParameters:
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: IntegerId
    :ivar RetransmitSequenceNumber:
    :vartype RetransmitSequenceNumber: Counter
    """

    SubscriptionId: IntegerId = 0
    RetransmitSequenceNumber: Counter = 0


@dataclass(frozen=FROZEN)
class RepublishRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.6/#5.13.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: RepublishParameters
    """

    data_type = NodeId(ObjectIds.RepublishRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RepublishRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: RepublishParameters = field(default_factory=RepublishParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class RepublishResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.6/#5.13.6.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar NotificationMessage:
    :vartype NotificationMessage: NotificationMessage
    """

    data_type = NodeId(ObjectIds.RepublishResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.RepublishResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    NotificationMessage_: NotificationMessage = field(default_factory=NotificationMessage)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val
    @property
    def NotificationMessage(self):
        return self.NotificationMessage_

    @NotificationMessage.setter
    def NotificationMessage(self, val):
        self.NotificationMessage_ = val


@dataclass(frozen=FROZEN)
class TransferResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.7/#5.13.7.2

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar AvailableSequenceNumbers:
    :vartype AvailableSequenceNumbers: Counter
    """

    data_type = NodeId(ObjectIds.TransferResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    AvailableSequenceNumbers: List[Counter] = field(default_factory=list)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val


@dataclass(frozen=FROZEN)
class TransferSubscriptionsParameters:
    """
    :ivar SubscriptionIds:
    :vartype SubscriptionIds: IntegerId
    :ivar SendInitialValues:
    :vartype SendInitialValues: Boolean
    """

    SubscriptionIds: List[IntegerId] = field(default_factory=list)
    SendInitialValues: Boolean = True


@dataclass(frozen=FROZEN)
class TransferSubscriptionsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.7/#5.13.7.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: TransferSubscriptionsParameters
    """

    data_type = NodeId(ObjectIds.TransferSubscriptionsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.TransferSubscriptionsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: TransferSubscriptionsParameters = field(default_factory=TransferSubscriptionsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class TransferSubscriptionsResult:
    """
    :ivar Results:
    :vartype Results: TransferResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    Results: List[TransferResult] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class TransferSubscriptionsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.7/#5.13.7.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: TransferSubscriptionsResult
    """

    data_type = NodeId(ObjectIds.TransferSubscriptionsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.TransferSubscriptionsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Parameters: TransferSubscriptionsResult = field(default_factory=TransferSubscriptionsResult)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteSubscriptionsParameters:
    """
    :ivar SubscriptionIds:
    :vartype SubscriptionIds: IntegerId
    """

    SubscriptionIds: List[IntegerId] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class DeleteSubscriptionsRequest:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.8/#5.13.8.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteSubscriptionsParameters
    """

    data_type = NodeId(ObjectIds.DeleteSubscriptionsRequest)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteSubscriptionsRequest_Encoding_DefaultBinary)
    RequestHeader_: RequestHeader = field(default_factory=RequestHeader)
    Parameters: DeleteSubscriptionsParameters = field(default_factory=DeleteSubscriptionsParameters)

    @property
    def RequestHeader(self):
        return self.RequestHeader_

    @RequestHeader.setter
    def RequestHeader(self, val):
        self.RequestHeader_ = val


@dataclass(frozen=FROZEN)
class DeleteSubscriptionsResponse:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.13.8/#5.13.8.2

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.DeleteSubscriptionsResponse)

    TypeId: NodeId = FourByteNodeId(ObjectIds.DeleteSubscriptionsResponse_Encoding_DefaultBinary)
    ResponseHeader_: ResponseHeader = field(default_factory=ResponseHeader)
    Results: List[StatusCode] = field(default_factory=list)
    DiagnosticInfos: List[DiagnosticInfo] = field(default_factory=list)

    @property
    def ResponseHeader(self):
        return self.ResponseHeader_

    @ResponseHeader.setter
    def ResponseHeader(self, val):
        self.ResponseHeader_ = val


@dataclass(frozen=FROZEN)
class BuildInfo:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.4

    :ivar ProductUri:
    :vartype ProductUri: String
    :ivar ManufacturerName:
    :vartype ManufacturerName: String
    :ivar ProductName:
    :vartype ProductName: String
    :ivar SoftwareVersion:
    :vartype SoftwareVersion: String
    :ivar BuildNumber:
    :vartype BuildNumber: String
    :ivar BuildDate:
    :vartype BuildDate: UtcTime
    """

    data_type = NodeId(ObjectIds.BuildInfo)

    ProductUri: String = None
    ManufacturerName: String = None
    ProductName: String = None
    SoftwareVersion: String = None
    BuildNumber: String = None
    BuildDate: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=FROZEN)
class RedundantServerDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.7

    :ivar ServerId:
    :vartype ServerId: String
    :ivar ServiceLevel:
    :vartype ServiceLevel: Byte
    :ivar ServerState:
    :vartype ServerState: ServerState
    """

    data_type = NodeId(ObjectIds.RedundantServerDataType)

    ServerId: String = None
    ServiceLevel: Byte = 0
    ServerState_: ServerState = ServerState.Running

    @property
    def ServerState(self):
        return self.ServerState_

    @ServerState.setter
    def ServerState(self, val):
        self.ServerState_ = val


@dataclass(frozen=FROZEN)
class EndpointUrlListDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.20

    :ivar EndpointUrlList:
    :vartype EndpointUrlList: String
    """

    data_type = NodeId(ObjectIds.EndpointUrlListDataType)

    EndpointUrlList: List[String] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class NetworkGroupDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.19

    :ivar ServerUri:
    :vartype ServerUri: String
    :ivar NetworkPaths:
    :vartype NetworkPaths: EndpointUrlListDataType
    """

    data_type = NodeId(ObjectIds.NetworkGroupDataType)

    ServerUri: String = None
    NetworkPaths: List[EndpointUrlListDataType] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class SamplingIntervalDiagnosticsDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.8

    :ivar SamplingInterval:
    :vartype SamplingInterval: Duration
    :ivar MonitoredItemCount:
    :vartype MonitoredItemCount: UInt32
    :ivar MaxMonitoredItemCount:
    :vartype MaxMonitoredItemCount: UInt32
    :ivar DisabledMonitoredItemCount:
    :vartype DisabledMonitoredItemCount: UInt32
    """

    data_type = NodeId(ObjectIds.SamplingIntervalDiagnosticsDataType)

    SamplingInterval: Duration = 0
    MonitoredItemCount: UInt32 = 0
    MaxMonitoredItemCount: UInt32 = 0
    DisabledMonitoredItemCount: UInt32 = 0


@dataclass(frozen=FROZEN)
class ServerDiagnosticsSummaryDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.9

    :ivar ServerViewCount:
    :vartype ServerViewCount: UInt32
    :ivar CurrentSessionCount:
    :vartype CurrentSessionCount: UInt32
    :ivar CumulatedSessionCount:
    :vartype CumulatedSessionCount: UInt32
    :ivar SecurityRejectedSessionCount:
    :vartype SecurityRejectedSessionCount: UInt32
    :ivar RejectedSessionCount:
    :vartype RejectedSessionCount: UInt32
    :ivar SessionTimeoutCount:
    :vartype SessionTimeoutCount: UInt32
    :ivar SessionAbortCount:
    :vartype SessionAbortCount: UInt32
    :ivar CurrentSubscriptionCount:
    :vartype CurrentSubscriptionCount: UInt32
    :ivar CumulatedSubscriptionCount:
    :vartype CumulatedSubscriptionCount: UInt32
    :ivar PublishingIntervalCount:
    :vartype PublishingIntervalCount: UInt32
    :ivar SecurityRejectedRequestsCount:
    :vartype SecurityRejectedRequestsCount: UInt32
    :ivar RejectedRequestsCount:
    :vartype RejectedRequestsCount: UInt32
    """

    data_type = NodeId(ObjectIds.ServerDiagnosticsSummaryDataType)

    ServerViewCount: UInt32 = 0
    CurrentSessionCount: UInt32 = 0
    CumulatedSessionCount: UInt32 = 0
    SecurityRejectedSessionCount: UInt32 = 0
    RejectedSessionCount: UInt32 = 0
    SessionTimeoutCount: UInt32 = 0
    SessionAbortCount: UInt32 = 0
    CurrentSubscriptionCount: UInt32 = 0
    CumulatedSubscriptionCount: UInt32 = 0
    PublishingIntervalCount: UInt32 = 0
    SecurityRejectedRequestsCount: UInt32 = 0
    RejectedRequestsCount: UInt32 = 0


@dataclass(frozen=FROZEN)
class ServerStatusDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.10

    :ivar StartTime:
    :vartype StartTime: UtcTime
    :ivar CurrentTime:
    :vartype CurrentTime: UtcTime
    :ivar State:
    :vartype State: ServerState
    :ivar BuildInfo:
    :vartype BuildInfo: BuildInfo
    :ivar SecondsTillShutdown:
    :vartype SecondsTillShutdown: UInt32
    :ivar ShutdownReason:
    :vartype ShutdownReason: LocalizedText
    """

    data_type = NodeId(ObjectIds.ServerStatusDataType)

    StartTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    CurrentTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    State: ServerState = ServerState.Running
    BuildInfo_: BuildInfo = field(default_factory=BuildInfo)
    SecondsTillShutdown: UInt32 = 0
    ShutdownReason: LocalizedText = field(default_factory=LocalizedText)

    @property
    def BuildInfo(self):
        return self.BuildInfo_

    @BuildInfo.setter
    def BuildInfo(self, val):
        self.BuildInfo_ = val


@dataclass(frozen=FROZEN)
class SessionSecurityDiagnosticsDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.12

    :ivar SessionId:
    :vartype SessionId: NodeId
    :ivar ClientUserIdOfSession:
    :vartype ClientUserIdOfSession: String
    :ivar ClientUserIdHistory:
    :vartype ClientUserIdHistory: String
    :ivar AuthenticationMechanism:
    :vartype AuthenticationMechanism: String
    :ivar Encoding:
    :vartype Encoding: String
    :ivar TransportProtocol:
    :vartype TransportProtocol: String
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    :ivar ClientCertificate:
    :vartype ClientCertificate: ByteString
    """

    data_type = NodeId(ObjectIds.SessionSecurityDiagnosticsDataType)

    SessionId: NodeId = field(default_factory=NodeId)
    ClientUserIdOfSession: String = None
    ClientUserIdHistory: List[String] = field(default_factory=list)
    AuthenticationMechanism: String = None
    Encoding: Byte = field(default=0, repr=False, init=False, compare=False)
    TransportProtocol: String = None
    SecurityMode: MessageSecurityMode = MessageSecurityMode.Invalid
    SecurityPolicyUri: String = None
    ClientCertificate: ByteString = None


@dataclass(frozen=FROZEN)
class ServiceCounterDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.13

    :ivar TotalCount:
    :vartype TotalCount: UInt32
    :ivar ErrorCount:
    :vartype ErrorCount: UInt32
    """

    data_type = NodeId(ObjectIds.ServiceCounterDataType)

    TotalCount: UInt32 = 0
    ErrorCount: UInt32 = 0


@dataclass(frozen=FROZEN)
class SessionDiagnosticsDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.11

    :ivar SessionId:
    :vartype SessionId: NodeId
    :ivar SessionName:
    :vartype SessionName: String
    :ivar ClientDescription:
    :vartype ClientDescription: ApplicationDescription
    :ivar ServerUri:
    :vartype ServerUri: String
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar LocaleIds:
    :vartype LocaleIds: LocaleId
    :ivar ActualSessionTimeout:
    :vartype ActualSessionTimeout: Duration
    :ivar MaxResponseMessageSize:
    :vartype MaxResponseMessageSize: UInt32
    :ivar ClientConnectionTime:
    :vartype ClientConnectionTime: UtcTime
    :ivar ClientLastContactTime:
    :vartype ClientLastContactTime: UtcTime
    :ivar CurrentSubscriptionsCount:
    :vartype CurrentSubscriptionsCount: UInt32
    :ivar CurrentMonitoredItemsCount:
    :vartype CurrentMonitoredItemsCount: UInt32
    :ivar CurrentPublishRequestsInQueue:
    :vartype CurrentPublishRequestsInQueue: UInt32
    :ivar TotalRequestCount:
    :vartype TotalRequestCount: ServiceCounterDataType
    :ivar UnauthorizedRequestCount:
    :vartype UnauthorizedRequestCount: UInt32
    :ivar ReadCount:
    :vartype ReadCount: ServiceCounterDataType
    :ivar HistoryReadCount:
    :vartype HistoryReadCount: ServiceCounterDataType
    :ivar WriteCount:
    :vartype WriteCount: ServiceCounterDataType
    :ivar HistoryUpdateCount:
    :vartype HistoryUpdateCount: ServiceCounterDataType
    :ivar CallCount:
    :vartype CallCount: ServiceCounterDataType
    :ivar CreateMonitoredItemsCount:
    :vartype CreateMonitoredItemsCount: ServiceCounterDataType
    :ivar ModifyMonitoredItemsCount:
    :vartype ModifyMonitoredItemsCount: ServiceCounterDataType
    :ivar SetMonitoringModeCount:
    :vartype SetMonitoringModeCount: ServiceCounterDataType
    :ivar SetTriggeringCount:
    :vartype SetTriggeringCount: ServiceCounterDataType
    :ivar DeleteMonitoredItemsCount:
    :vartype DeleteMonitoredItemsCount: ServiceCounterDataType
    :ivar CreateSubscriptionCount:
    :vartype CreateSubscriptionCount: ServiceCounterDataType
    :ivar ModifySubscriptionCount:
    :vartype ModifySubscriptionCount: ServiceCounterDataType
    :ivar SetPublishingModeCount:
    :vartype SetPublishingModeCount: ServiceCounterDataType
    :ivar PublishCount:
    :vartype PublishCount: ServiceCounterDataType
    :ivar RepublishCount:
    :vartype RepublishCount: ServiceCounterDataType
    :ivar TransferSubscriptionsCount:
    :vartype TransferSubscriptionsCount: ServiceCounterDataType
    :ivar DeleteSubscriptionsCount:
    :vartype DeleteSubscriptionsCount: ServiceCounterDataType
    :ivar AddNodesCount:
    :vartype AddNodesCount: ServiceCounterDataType
    :ivar AddReferencesCount:
    :vartype AddReferencesCount: ServiceCounterDataType
    :ivar DeleteNodesCount:
    :vartype DeleteNodesCount: ServiceCounterDataType
    :ivar DeleteReferencesCount:
    :vartype DeleteReferencesCount: ServiceCounterDataType
    :ivar BrowseCount:
    :vartype BrowseCount: ServiceCounterDataType
    :ivar BrowseNextCount:
    :vartype BrowseNextCount: ServiceCounterDataType
    :ivar TranslateBrowsePathsToNodeIdsCount:
    :vartype TranslateBrowsePathsToNodeIdsCount: ServiceCounterDataType
    :ivar QueryFirstCount:
    :vartype QueryFirstCount: ServiceCounterDataType
    :ivar QueryNextCount:
    :vartype QueryNextCount: ServiceCounterDataType
    :ivar RegisterNodesCount:
    :vartype RegisterNodesCount: ServiceCounterDataType
    :ivar UnregisterNodesCount:
    :vartype UnregisterNodesCount: ServiceCounterDataType
    """

    data_type = NodeId(ObjectIds.SessionDiagnosticsDataType)

    SessionId: NodeId = field(default_factory=NodeId)
    SessionName: String = None
    ClientDescription: ApplicationDescription = field(default_factory=ApplicationDescription)
    ServerUri: String = None
    EndpointUrl: String = None
    LocaleIds: List[LocaleId] = field(default_factory=list)
    ActualSessionTimeout: Duration = 0
    MaxResponseMessageSize: UInt32 = 0
    ClientConnectionTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    ClientLastContactTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    CurrentSubscriptionsCount: UInt32 = 0
    CurrentMonitoredItemsCount: UInt32 = 0
    CurrentPublishRequestsInQueue: UInt32 = 0
    TotalRequestCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    UnauthorizedRequestCount: UInt32 = 0
    ReadCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    HistoryReadCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    WriteCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    HistoryUpdateCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    CallCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    CreateMonitoredItemsCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    ModifyMonitoredItemsCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    SetMonitoringModeCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    SetTriggeringCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    DeleteMonitoredItemsCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    CreateSubscriptionCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    ModifySubscriptionCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    SetPublishingModeCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    PublishCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    RepublishCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    TransferSubscriptionsCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    DeleteSubscriptionsCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    AddNodesCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    AddReferencesCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    DeleteNodesCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    DeleteReferencesCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    BrowseCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    BrowseNextCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    TranslateBrowsePathsToNodeIdsCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    QueryFirstCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    QueryNextCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    RegisterNodesCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)
    UnregisterNodesCount: ServiceCounterDataType = field(default_factory=ServiceCounterDataType)


@dataclass(frozen=FROZEN)
class StatusResult:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.14

    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar DiagnosticInfo:
    :vartype DiagnosticInfo: DiagnosticInfo
    """

    data_type = NodeId(ObjectIds.StatusResult)

    StatusCode_: StatusCode = field(default_factory=StatusCode)
    DiagnosticInfo_: DiagnosticInfo = field(default_factory=DiagnosticInfo)

    @property
    def StatusCode(self):
        return self.StatusCode_

    @StatusCode.setter
    def StatusCode(self, val):
        self.StatusCode_ = val
    @property
    def DiagnosticInfo(self):
        return self.DiagnosticInfo_

    @DiagnosticInfo.setter
    def DiagnosticInfo(self, val):
        self.DiagnosticInfo_ = val


@dataclass(frozen=FROZEN)
class SubscriptionDiagnosticsDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.15

    :ivar SessionId:
    :vartype SessionId: NodeId
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar Priority:
    :vartype Priority: Byte
    :ivar PublishingInterval:
    :vartype PublishingInterval: Duration
    :ivar MaxKeepAliveCount:
    :vartype MaxKeepAliveCount: UInt32
    :ivar MaxLifetimeCount:
    :vartype MaxLifetimeCount: UInt32
    :ivar MaxNotificationsPerPublish:
    :vartype MaxNotificationsPerPublish: UInt32
    :ivar PublishingEnabled:
    :vartype PublishingEnabled: Boolean
    :ivar ModifyCount:
    :vartype ModifyCount: UInt32
    :ivar EnableCount:
    :vartype EnableCount: UInt32
    :ivar DisableCount:
    :vartype DisableCount: UInt32
    :ivar RepublishRequestCount:
    :vartype RepublishRequestCount: UInt32
    :ivar RepublishMessageRequestCount:
    :vartype RepublishMessageRequestCount: UInt32
    :ivar RepublishMessageCount:
    :vartype RepublishMessageCount: UInt32
    :ivar TransferRequestCount:
    :vartype TransferRequestCount: UInt32
    :ivar TransferredToAltClientCount:
    :vartype TransferredToAltClientCount: UInt32
    :ivar TransferredToSameClientCount:
    :vartype TransferredToSameClientCount: UInt32
    :ivar PublishRequestCount:
    :vartype PublishRequestCount: UInt32
    :ivar DataChangeNotificationsCount:
    :vartype DataChangeNotificationsCount: UInt32
    :ivar EventNotificationsCount:
    :vartype EventNotificationsCount: UInt32
    :ivar NotificationsCount:
    :vartype NotificationsCount: UInt32
    :ivar LatePublishRequestCount:
    :vartype LatePublishRequestCount: UInt32
    :ivar CurrentKeepAliveCount:
    :vartype CurrentKeepAliveCount: UInt32
    :ivar CurrentLifetimeCount:
    :vartype CurrentLifetimeCount: UInt32
    :ivar UnacknowledgedMessageCount:
    :vartype UnacknowledgedMessageCount: UInt32
    :ivar DiscardedMessageCount:
    :vartype DiscardedMessageCount: UInt32
    :ivar MonitoredItemCount:
    :vartype MonitoredItemCount: UInt32
    :ivar DisabledMonitoredItemCount:
    :vartype DisabledMonitoredItemCount: UInt32
    :ivar MonitoringQueueOverflowCount:
    :vartype MonitoringQueueOverflowCount: UInt32
    :ivar NextSequenceNumber:
    :vartype NextSequenceNumber: UInt32
    :ivar EventQueueOverFlowCount:
    :vartype EventQueueOverFlowCount: UInt32
    """

    data_type = NodeId(ObjectIds.SubscriptionDiagnosticsDataType)

    SessionId: NodeId = field(default_factory=NodeId)
    SubscriptionId: UInt32 = 0
    Priority: Byte = 0
    PublishingInterval: Duration = 0
    MaxKeepAliveCount: UInt32 = 0
    MaxLifetimeCount: UInt32 = 0
    MaxNotificationsPerPublish: UInt32 = 0
    PublishingEnabled: Boolean = True
    ModifyCount: UInt32 = 0
    EnableCount: UInt32 = 0
    DisableCount: UInt32 = 0
    RepublishRequestCount: UInt32 = 0
    RepublishMessageRequestCount: UInt32 = 0
    RepublishMessageCount: UInt32 = 0
    TransferRequestCount: UInt32 = 0
    TransferredToAltClientCount: UInt32 = 0
    TransferredToSameClientCount: UInt32 = 0
    PublishRequestCount: UInt32 = 0
    DataChangeNotificationsCount: UInt32 = 0
    EventNotificationsCount: UInt32 = 0
    NotificationsCount: UInt32 = 0
    LatePublishRequestCount: UInt32 = 0
    CurrentKeepAliveCount: UInt32 = 0
    CurrentLifetimeCount: UInt32 = 0
    UnacknowledgedMessageCount: UInt32 = 0
    DiscardedMessageCount: UInt32 = 0
    MonitoredItemCount: UInt32 = 0
    DisabledMonitoredItemCount: UInt32 = 0
    MonitoringQueueOverflowCount: UInt32 = 0
    NextSequenceNumber: UInt32 = 0
    EventQueueOverFlowCount: UInt32 = 0


@dataclass(frozen=FROZEN)
class ModelChangeStructureDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.16

    :ivar Affected:
    :vartype Affected: NodeId
    :ivar AffectedType:
    :vartype AffectedType: NodeId
    :ivar Verb:
    :vartype Verb: Byte
    """

    data_type = NodeId(ObjectIds.ModelChangeStructureDataType)

    Affected: NodeId = field(default_factory=NodeId)
    AffectedType: NodeId = field(default_factory=NodeId)
    Verb: Byte = 0


@dataclass(frozen=FROZEN)
class SemanticChangeStructureDataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part5/12.17

    :ivar Affected:
    :vartype Affected: NodeId
    :ivar AffectedType:
    :vartype AffectedType: NodeId
    """

    data_type = NodeId(ObjectIds.SemanticChangeStructureDataType)

    Affected: NodeId = field(default_factory=NodeId)
    AffectedType: NodeId = field(default_factory=NodeId)


@dataclass(frozen=FROZEN)
class Range:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.2

    :ivar Low:
    :vartype Low: Double
    :ivar High:
    :vartype High: Double
    """

    data_type = NodeId(ObjectIds.Range)

    Low: Double = 0
    High: Double = 0


@dataclass(frozen=FROZEN)
class EUInformation:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.3/#5.6.3.3

    :ivar NamespaceUri:
    :vartype NamespaceUri: String
    :ivar UnitId:
    :vartype UnitId: Int32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    """

    data_type = NodeId(ObjectIds.EUInformation)

    NamespaceUri: String = None
    UnitId: Int32 = 0
    DisplayName: LocalizedText = field(default_factory=LocalizedText)
    Description: LocalizedText = field(default_factory=LocalizedText)


@dataclass(frozen=FROZEN)
class ComplexNumberType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.4

    :ivar Real:
    :vartype Real: Float
    :ivar Imaginary:
    :vartype Imaginary: Float
    """

    data_type = NodeId(ObjectIds.ComplexNumberType)

    Real: Float = 0
    Imaginary: Float = 0


@dataclass(frozen=FROZEN)
class DoubleComplexNumberType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.5

    :ivar Real:
    :vartype Real: Double
    :ivar Imaginary:
    :vartype Imaginary: Double
    """

    data_type = NodeId(ObjectIds.DoubleComplexNumberType)

    Real: Double = 0
    Imaginary: Double = 0


@dataclass(frozen=FROZEN)
class AxisInformation:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.6

    :ivar EngineeringUnits:
    :vartype EngineeringUnits: EUInformation
    :ivar EURange:
    :vartype EURange: Range
    :ivar Title:
    :vartype Title: LocalizedText
    :ivar AxisScaleType:
    :vartype AxisScaleType: AxisScaleEnumeration
    :ivar AxisSteps:
    :vartype AxisSteps: Double
    """

    data_type = NodeId(ObjectIds.AxisInformation)

    EngineeringUnits: EUInformation = field(default_factory=EUInformation)
    EURange: Range = field(default_factory=Range)
    Title: LocalizedText = field(default_factory=LocalizedText)
    AxisScaleType: AxisScaleEnumeration = AxisScaleEnumeration.Linear
    AxisSteps: List[Double] = field(default_factory=list)


@dataclass(frozen=FROZEN)
class XVType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part8/5.6.8

    :ivar X:
    :vartype X: Double
    :ivar Value:
    :vartype Value: Float
    """

    data_type = NodeId(ObjectIds.XVType)

    X: Double = 0
    Value: Float = 0


@dataclass(frozen=FROZEN)
class ProgramDiagnosticDataType:
    """
    :ivar CreateSessionId:
    :vartype CreateSessionId: NodeId
    :ivar CreateClientName:
    :vartype CreateClientName: String
    :ivar InvocationCreationTime:
    :vartype InvocationCreationTime: UtcTime
    :ivar LastTransitionTime:
    :vartype LastTransitionTime: UtcTime
    :ivar LastMethodCall:
    :vartype LastMethodCall: String
    :ivar LastMethodSessionId:
    :vartype LastMethodSessionId: NodeId
    :ivar LastMethodInputArguments:
    :vartype LastMethodInputArguments: Argument
    :ivar LastMethodOutputArguments:
    :vartype LastMethodOutputArguments: Argument
    :ivar LastMethodCallTime:
    :vartype LastMethodCallTime: UtcTime
    :ivar LastMethodReturnStatus:
    :vartype LastMethodReturnStatus: StatusResult
    """

    data_type = NodeId(ObjectIds.ProgramDiagnosticDataType)

    CreateSessionId: NodeId = field(default_factory=NodeId)
    CreateClientName: String = None
    InvocationCreationTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    LastTransitionTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    LastMethodCall: String = None
    LastMethodSessionId: NodeId = field(default_factory=NodeId)
    LastMethodInputArguments: List[Argument] = field(default_factory=list)
    LastMethodOutputArguments: List[Argument] = field(default_factory=list)
    LastMethodCallTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    LastMethodReturnStatus: StatusResult = field(default_factory=StatusResult)


@dataclass(frozen=FROZEN)
class ProgramDiagnostic2DataType:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part10/5.2.8

    :ivar CreateSessionId:
    :vartype CreateSessionId: NodeId
    :ivar CreateClientName:
    :vartype CreateClientName: String
    :ivar InvocationCreationTime:
    :vartype InvocationCreationTime: UtcTime
    :ivar LastTransitionTime:
    :vartype LastTransitionTime: UtcTime
    :ivar LastMethodCall:
    :vartype LastMethodCall: String
    :ivar LastMethodSessionId:
    :vartype LastMethodSessionId: NodeId
    :ivar LastMethodInputArguments:
    :vartype LastMethodInputArguments: Argument
    :ivar LastMethodOutputArguments:
    :vartype LastMethodOutputArguments: Argument
    :ivar LastMethodInputValues:
    :vartype LastMethodInputValues: Variant
    :ivar LastMethodOutputValues:
    :vartype LastMethodOutputValues: Variant
    :ivar LastMethodCallTime:
    :vartype LastMethodCallTime: UtcTime
    :ivar LastMethodReturnStatus:
    :vartype LastMethodReturnStatus: StatusCode
    """

    data_type = NodeId(ObjectIds.ProgramDiagnostic2DataType)

    CreateSessionId: NodeId = field(default_factory=NodeId)
    CreateClientName: String = None
    InvocationCreationTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    LastTransitionTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    LastMethodCall: String = None
    LastMethodSessionId: NodeId = field(default_factory=NodeId)
    LastMethodInputArguments: List[Argument] = field(default_factory=list)
    LastMethodOutputArguments: List[Argument] = field(default_factory=list)
    LastMethodInputValues: List[Variant] = field(default_factory=list)
    LastMethodOutputValues: List[Variant] = field(default_factory=list)
    LastMethodCallTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))
    LastMethodReturnStatus: StatusCode = field(default_factory=StatusCode)


@dataclass(frozen=FROZEN)
class Annotation:
    """
    https://reference.opcfoundation.org/v105/Core/docs/Part11/6.6.6

    :ivar Message:
    :vartype Message: String
    :ivar UserName:
    :vartype UserName: String
    :ivar AnnotationTime:
    :vartype AnnotationTime: UtcTime
    """

    data_type = NodeId(ObjectIds.Annotation)

    Message: String = None
    UserName: String = None
    AnnotationTime: UtcTime = field(default_factory=lambda: datetime.now(timezone.utc))


nid = FourByteNodeId(ObjectIds.Union_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Union
extension_object_typeids['Union'] = nid
nid = FourByteNodeId(ObjectIds.KeyValuePair_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = KeyValuePair
extension_object_typeids['KeyValuePair'] = nid
nid = FourByteNodeId(ObjectIds.AdditionalParametersType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AdditionalParametersType
extension_object_typeids['AdditionalParametersType'] = nid
nid = FourByteNodeId(ObjectIds.EphemeralKeyType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EphemeralKeyType
extension_object_typeids['EphemeralKeyType'] = nid
nid = FourByteNodeId(ObjectIds.EndpointType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EndpointType
extension_object_typeids['EndpointType'] = nid
nid = FourByteNodeId(ObjectIds.BitFieldDefinition_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BitFieldDefinition
extension_object_typeids['BitFieldDefinition'] = nid
nid = FourByteNodeId(ObjectIds.RationalNumber_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RationalNumber
extension_object_typeids['RationalNumber'] = nid
nid = FourByteNodeId(ObjectIds.Vector_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Vector
extension_object_typeids['Vector'] = nid
nid = FourByteNodeId(ObjectIds.ThreeDVector_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ThreeDVector
extension_object_typeids['ThreeDVector'] = nid
nid = FourByteNodeId(ObjectIds.CartesianCoordinates_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CartesianCoordinates
extension_object_typeids['CartesianCoordinates'] = nid
nid = FourByteNodeId(ObjectIds.ThreeDCartesianCoordinates_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ThreeDCartesianCoordinates
extension_object_typeids['ThreeDCartesianCoordinates'] = nid
nid = FourByteNodeId(ObjectIds.Orientation_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Orientation
extension_object_typeids['Orientation'] = nid
nid = FourByteNodeId(ObjectIds.ThreeDOrientation_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ThreeDOrientation
extension_object_typeids['ThreeDOrientation'] = nid
nid = FourByteNodeId(ObjectIds.Frame_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Frame
extension_object_typeids['Frame'] = nid
nid = FourByteNodeId(ObjectIds.ThreeDFrame_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ThreeDFrame
extension_object_typeids['ThreeDFrame'] = nid
nid = FourByteNodeId(ObjectIds.IdentityMappingRuleType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = IdentityMappingRuleType
extension_object_typeids['IdentityMappingRuleType'] = nid
nid = FourByteNodeId(ObjectIds.CurrencyUnitType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CurrencyUnitType
extension_object_typeids['CurrencyUnitType'] = nid
nid = FourByteNodeId(ObjectIds.AnnotationDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AnnotationDataType
extension_object_typeids['AnnotationDataType'] = nid
nid = FourByteNodeId(ObjectIds.LinearConversionDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = LinearConversionDataType
extension_object_typeids['LinearConversionDataType'] = nid
nid = FourByteNodeId(ObjectIds.QuantityDimension_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QuantityDimension
extension_object_typeids['QuantityDimension'] = nid
nid = FourByteNodeId(ObjectIds.TrustListDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TrustListDataType
extension_object_typeids['TrustListDataType'] = nid
nid = FourByteNodeId(ObjectIds.TransactionErrorType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TransactionErrorType
extension_object_typeids['TransactionErrorType'] = nid
nid = FourByteNodeId(ObjectIds.DecimalDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DecimalDataType
extension_object_typeids['DecimalDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataTypeDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataTypeDescription
extension_object_typeids['DataTypeDescription'] = nid
nid = FourByteNodeId(ObjectIds.SimpleTypeDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SimpleTypeDescription
extension_object_typeids['SimpleTypeDescription'] = nid
nid = FourByteNodeId(ObjectIds.PortableQualifiedName_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PortableQualifiedName
extension_object_typeids['PortableQualifiedName'] = nid
nid = FourByteNodeId(ObjectIds.UnsignedRationalNumber_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UnsignedRationalNumber
extension_object_typeids['UnsignedRationalNumber'] = nid
nid = FourByteNodeId(ObjectIds.FieldMetaData_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FieldMetaData
extension_object_typeids['FieldMetaData'] = nid
nid = FourByteNodeId(ObjectIds.ConfigurationVersionDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ConfigurationVersionDataType
extension_object_typeids['ConfigurationVersionDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataSetSourceDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataSetSourceDataType
extension_object_typeids['PublishedDataSetSourceDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedVariableDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedVariableDataType
extension_object_typeids['PublishedVariableDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataItemsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataItemsDataType
extension_object_typeids['PublishedDataItemsDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataSetCustomSourceDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataSetCustomSourceDataType
extension_object_typeids['PublishedDataSetCustomSourceDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetWriterTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetWriterTransportDataType
extension_object_typeids['DataSetWriterTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetWriterMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetWriterMessageDataType
extension_object_typeids['DataSetWriterMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetWriterDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetWriterDataType
extension_object_typeids['DataSetWriterDataType'] = nid
nid = FourByteNodeId(ObjectIds.WriterGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriterGroupTransportDataType
extension_object_typeids['WriterGroupTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.WriterGroupMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriterGroupMessageDataType
extension_object_typeids['WriterGroupMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.ConnectionTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ConnectionTransportDataType
extension_object_typeids['ConnectionTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.NetworkAddressDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NetworkAddressDataType
extension_object_typeids['NetworkAddressDataType'] = nid
nid = FourByteNodeId(ObjectIds.NetworkAddressUrlDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NetworkAddressUrlDataType
extension_object_typeids['NetworkAddressUrlDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReaderGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReaderGroupTransportDataType
extension_object_typeids['ReaderGroupTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReaderGroupMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReaderGroupMessageDataType
extension_object_typeids['ReaderGroupMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetReaderTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetReaderTransportDataType
extension_object_typeids['DataSetReaderTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetReaderMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetReaderMessageDataType
extension_object_typeids['DataSetReaderMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.SubscribedDataSetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SubscribedDataSetDataType
extension_object_typeids['SubscribedDataSetDataType'] = nid
nid = FourByteNodeId(ObjectIds.FieldTargetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FieldTargetDataType
extension_object_typeids['FieldTargetDataType'] = nid
nid = FourByteNodeId(ObjectIds.TargetVariablesDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TargetVariablesDataType
extension_object_typeids['TargetVariablesDataType'] = nid
nid = FourByteNodeId(ObjectIds.StandaloneSubscribedDataSetRefDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StandaloneSubscribedDataSetRefDataType
extension_object_typeids['StandaloneSubscribedDataSetRefDataType'] = nid
nid = FourByteNodeId(ObjectIds.UadpWriterGroupMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UadpWriterGroupMessageDataType
extension_object_typeids['UadpWriterGroupMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.UadpDataSetWriterMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UadpDataSetWriterMessageDataType
extension_object_typeids['UadpDataSetWriterMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.UadpDataSetReaderMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UadpDataSetReaderMessageDataType
extension_object_typeids['UadpDataSetReaderMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.JsonWriterGroupMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = JsonWriterGroupMessageDataType
extension_object_typeids['JsonWriterGroupMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.JsonDataSetWriterMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = JsonDataSetWriterMessageDataType
extension_object_typeids['JsonDataSetWriterMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.JsonDataSetReaderMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = JsonDataSetReaderMessageDataType
extension_object_typeids['JsonDataSetReaderMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.QosDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QosDataType
extension_object_typeids['QosDataType'] = nid
nid = FourByteNodeId(ObjectIds.TransmitQosDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TransmitQosDataType
extension_object_typeids['TransmitQosDataType'] = nid
nid = FourByteNodeId(ObjectIds.TransmitQosPriorityDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TransmitQosPriorityDataType
extension_object_typeids['TransmitQosPriorityDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReceiveQosDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReceiveQosDataType
extension_object_typeids['ReceiveQosDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReceiveQosPriorityDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReceiveQosPriorityDataType
extension_object_typeids['ReceiveQosPriorityDataType'] = nid
nid = FourByteNodeId(ObjectIds.DatagramConnectionTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramConnectionTransportDataType
extension_object_typeids['DatagramConnectionTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DatagramConnectionTransport2DataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramConnectionTransport2DataType
extension_object_typeids['DatagramConnectionTransport2DataType'] = nid
nid = FourByteNodeId(ObjectIds.DatagramWriterGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramWriterGroupTransportDataType
extension_object_typeids['DatagramWriterGroupTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DatagramWriterGroupTransport2DataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramWriterGroupTransport2DataType
extension_object_typeids['DatagramWriterGroupTransport2DataType'] = nid
nid = FourByteNodeId(ObjectIds.DatagramDataSetReaderTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramDataSetReaderTransportDataType
extension_object_typeids['DatagramDataSetReaderTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.BrokerConnectionTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrokerConnectionTransportDataType
extension_object_typeids['BrokerConnectionTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.BrokerWriterGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrokerWriterGroupTransportDataType
extension_object_typeids['BrokerWriterGroupTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.BrokerDataSetWriterTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrokerDataSetWriterTransportDataType
extension_object_typeids['BrokerDataSetWriterTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.BrokerDataSetReaderTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrokerDataSetReaderTransportDataType
extension_object_typeids['BrokerDataSetReaderTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConfigurationRefDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConfigurationRefDataType
extension_object_typeids['PubSubConfigurationRefDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConfigurationValueDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConfigurationValueDataType
extension_object_typeids['PubSubConfigurationValueDataType'] = nid
nid = FourByteNodeId(ObjectIds.AliasNameDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AliasNameDataType
extension_object_typeids['AliasNameDataType'] = nid
nid = FourByteNodeId(ObjectIds.UserManagementDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UserManagementDataType
extension_object_typeids['UserManagementDataType'] = nid
nid = FourByteNodeId(ObjectIds.PriorityMappingEntryType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PriorityMappingEntryType
extension_object_typeids['PriorityMappingEntryType'] = nid
nid = FourByteNodeId(ObjectIds.ReferenceDescriptionDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReferenceDescriptionDataType
extension_object_typeids['ReferenceDescriptionDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReferenceListEntryDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReferenceListEntryDataType
extension_object_typeids['ReferenceListEntryDataType'] = nid
nid = FourByteNodeId(ObjectIds.RolePermissionType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RolePermissionType
extension_object_typeids['RolePermissionType'] = nid
nid = FourByteNodeId(ObjectIds.SubscribedDataSetMirrorDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SubscribedDataSetMirrorDataType
extension_object_typeids['SubscribedDataSetMirrorDataType'] = nid
nid = FourByteNodeId(ObjectIds.SecurityGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SecurityGroupDataType
extension_object_typeids['SecurityGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataTypeDefinition_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataTypeDefinition
extension_object_typeids['DataTypeDefinition'] = nid
nid = FourByteNodeId(ObjectIds.StructureField_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StructureField
extension_object_typeids['StructureField'] = nid
nid = FourByteNodeId(ObjectIds.StructureDefinition_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StructureDefinition
extension_object_typeids['StructureDefinition'] = nid
nid = FourByteNodeId(ObjectIds.StructureDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StructureDescription
extension_object_typeids['StructureDescription'] = nid
nid = FourByteNodeId(ObjectIds.Argument_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Argument
extension_object_typeids['Argument'] = nid
nid = FourByteNodeId(ObjectIds.EnumValueType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumValueType
extension_object_typeids['EnumValueType'] = nid
nid = FourByteNodeId(ObjectIds.EnumField_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumField
extension_object_typeids['EnumField'] = nid
nid = FourByteNodeId(ObjectIds.EnumDefinition_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumDefinition
extension_object_typeids['EnumDefinition'] = nid
nid = FourByteNodeId(ObjectIds.EnumDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumDescription
extension_object_typeids['EnumDescription'] = nid
nid = FourByteNodeId(ObjectIds.DataTypeSchemaHeader_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataTypeSchemaHeader
extension_object_typeids['DataTypeSchemaHeader'] = nid
nid = FourByteNodeId(ObjectIds.UABinaryFileDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UABinaryFileDataType
extension_object_typeids['UABinaryFileDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetMetaDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetMetaDataType
extension_object_typeids['DataSetMetaDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataSetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataSetDataType
extension_object_typeids['PublishedDataSetDataType'] = nid
nid = FourByteNodeId(ObjectIds.StandaloneSubscribedDataSetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StandaloneSubscribedDataSetDataType
extension_object_typeids['StandaloneSubscribedDataSetDataType'] = nid
nid = FourByteNodeId(ObjectIds.OptionSet_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = OptionSet
extension_object_typeids['OptionSet'] = nid
nid = FourByteNodeId(ObjectIds.TimeZoneDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TimeZoneDataType
extension_object_typeids['TimeZoneDataType'] = nid
nid = FourByteNodeId(ObjectIds.ApplicationDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ApplicationDescription
extension_object_typeids['ApplicationDescription'] = nid
nid = FourByteNodeId(ObjectIds.RequestHeader_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RequestHeader
extension_object_typeids['RequestHeader'] = nid
nid = FourByteNodeId(ObjectIds.ResponseHeader_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ResponseHeader
extension_object_typeids['ResponseHeader'] = nid
nid = FourByteNodeId(ObjectIds.ServiceFault_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ServiceFault
extension_object_typeids['ServiceFault'] = nid
nid = FourByteNodeId(ObjectIds.SessionlessInvokeRequestType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SessionlessInvokeRequestType
extension_object_typeids['SessionlessInvokeRequestType'] = nid
nid = FourByteNodeId(ObjectIds.SessionlessInvokeResponseType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SessionlessInvokeResponseType
extension_object_typeids['SessionlessInvokeResponseType'] = nid
nid = FourByteNodeId(ObjectIds.FindServersRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FindServersRequest
extension_object_typeids['FindServersRequest'] = nid
nid = FourByteNodeId(ObjectIds.FindServersResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FindServersResponse
extension_object_typeids['FindServersResponse'] = nid
nid = FourByteNodeId(ObjectIds.ServerOnNetwork_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ServerOnNetwork
extension_object_typeids['ServerOnNetwork'] = nid
nid = FourByteNodeId(ObjectIds.FindServersOnNetworkRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FindServersOnNetworkRequest
extension_object_typeids['FindServersOnNetworkRequest'] = nid
nid = FourByteNodeId(ObjectIds.FindServersOnNetworkResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FindServersOnNetworkResponse
extension_object_typeids['FindServersOnNetworkResponse'] = nid
nid = FourByteNodeId(ObjectIds.UserTokenPolicy_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UserTokenPolicy
extension_object_typeids['UserTokenPolicy'] = nid
nid = FourByteNodeId(ObjectIds.PubSubKeyPushTargetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubKeyPushTargetDataType
extension_object_typeids['PubSubKeyPushTargetDataType'] = nid
nid = FourByteNodeId(ObjectIds.EndpointDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EndpointDescription
extension_object_typeids['EndpointDescription'] = nid
nid = FourByteNodeId(ObjectIds.PubSubGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubGroupDataType
extension_object_typeids['PubSubGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.WriterGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriterGroupDataType
extension_object_typeids['WriterGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetReaderDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetReaderDataType
extension_object_typeids['DataSetReaderDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReaderGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReaderGroupDataType
extension_object_typeids['ReaderGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConnectionDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConnectionDataType
extension_object_typeids['PubSubConnectionDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConfigurationDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConfigurationDataType
extension_object_typeids['PubSubConfigurationDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConfiguration2DataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConfiguration2DataType
extension_object_typeids['PubSubConfiguration2DataType'] = nid
nid = FourByteNodeId(ObjectIds.GetEndpointsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = GetEndpointsRequest
extension_object_typeids['GetEndpointsRequest'] = nid
nid = FourByteNodeId(ObjectIds.GetEndpointsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = GetEndpointsResponse
extension_object_typeids['GetEndpointsResponse'] = nid
nid = FourByteNodeId(ObjectIds.RegisteredServer_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisteredServer
extension_object_typeids['RegisteredServer'] = nid
nid = FourByteNodeId(ObjectIds.RegisterServerRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisterServerRequest
extension_object_typeids['RegisterServerRequest'] = nid
nid = FourByteNodeId(ObjectIds.RegisterServerResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisterServerResponse
extension_object_typeids['RegisterServerResponse'] = nid
nid = FourByteNodeId(ObjectIds.DiscoveryConfiguration_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DiscoveryConfiguration
extension_object_typeids['DiscoveryConfiguration'] = nid
nid = FourByteNodeId(ObjectIds.MdnsDiscoveryConfiguration_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MdnsDiscoveryConfiguration
extension_object_typeids['MdnsDiscoveryConfiguration'] = nid
nid = FourByteNodeId(ObjectIds.RegisterServer2Request_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisterServer2Request
extension_object_typeids['RegisterServer2Request'] = nid
nid = FourByteNodeId(ObjectIds.RegisterServer2Response_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisterServer2Response
extension_object_typeids['RegisterServer2Response'] = nid
nid = FourByteNodeId(ObjectIds.ChannelSecurityToken_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ChannelSecurityToken
extension_object_typeids['ChannelSecurityToken'] = nid
nid = FourByteNodeId(ObjectIds.OpenSecureChannelRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = OpenSecureChannelRequest
extension_object_typeids['OpenSecureChannelRequest'] = nid
nid = FourByteNodeId(ObjectIds.OpenSecureChannelResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = OpenSecureChannelResponse
extension_object_typeids['OpenSecureChannelResponse'] = nid
nid = FourByteNodeId(ObjectIds.CloseSecureChannelRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CloseSecureChannelRequest
extension_object_typeids['CloseSecureChannelRequest'] = nid
nid = FourByteNodeId(ObjectIds.CloseSecureChannelResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CloseSecureChannelResponse
extension_object_typeids['CloseSecureChannelResponse'] = nid
nid = FourByteNodeId(ObjectIds.SignedSoftwareCertificate_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SignedSoftwareCertificate
extension_object_typeids['SignedSoftwareCertificate'] = nid
nid = FourByteNodeId(ObjectIds.SignatureData_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SignatureData
extension_object_typeids['SignatureData'] = nid
nid = FourByteNodeId(ObjectIds.CreateSessionRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CreateSessionRequest
extension_object_typeids['CreateSessionRequest'] = nid
nid = FourByteNodeId(ObjectIds.CreateSessionResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CreateSessionResponse
extension_object_typeids['CreateSessionResponse'] = nid
nid = FourByteNodeId(ObjectIds.UserIdentityToken_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UserIdentityToken
extension_object_typeids['UserIdentityToken'] = nid
nid = FourByteNodeId(ObjectIds.AnonymousIdentityToken_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AnonymousIdentityToken
extension_object_typeids['AnonymousIdentityToken'] = nid
nid = FourByteNodeId(ObjectIds.UserNameIdentityToken_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UserNameIdentityToken
extension_object_typeids['UserNameIdentityToken'] = nid
nid = FourByteNodeId(ObjectIds.X509IdentityToken_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = X509IdentityToken
extension_object_typeids['X509IdentityToken'] = nid
nid = FourByteNodeId(ObjectIds.IssuedIdentityToken_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = IssuedIdentityToken
extension_object_typeids['IssuedIdentityToken'] = nid
nid = FourByteNodeId(ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ActivateSessionRequest
extension_object_typeids['ActivateSessionRequest'] = nid
nid = FourByteNodeId(ObjectIds.ActivateSessionResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ActivateSessionResponse
extension_object_typeids['ActivateSessionResponse'] = nid
nid = FourByteNodeId(ObjectIds.CloseSessionRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CloseSessionRequest
extension_object_typeids['CloseSessionRequest'] = nid
nid = FourByteNodeId(ObjectIds.CloseSessionResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CloseSessionResponse
extension_object_typeids['CloseSessionResponse'] = nid
nid = FourByteNodeId(ObjectIds.CancelRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CancelRequest
extension_object_typeids['CancelRequest'] = nid
nid = FourByteNodeId(ObjectIds.CancelResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CancelResponse
extension_object_typeids['CancelResponse'] = nid
nid = FourByteNodeId(ObjectIds.NodeAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NodeAttributes
extension_object_typeids['NodeAttributes'] = nid
nid = FourByteNodeId(ObjectIds.ObjectAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ObjectAttributes
extension_object_typeids['ObjectAttributes'] = nid
nid = FourByteNodeId(ObjectIds.VariableAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = VariableAttributes
extension_object_typeids['VariableAttributes'] = nid
nid = FourByteNodeId(ObjectIds.MethodAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MethodAttributes
extension_object_typeids['MethodAttributes'] = nid
nid = FourByteNodeId(ObjectIds.ObjectTypeAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ObjectTypeAttributes
extension_object_typeids['ObjectTypeAttributes'] = nid
nid = FourByteNodeId(ObjectIds.VariableTypeAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = VariableTypeAttributes
extension_object_typeids['VariableTypeAttributes'] = nid
nid = FourByteNodeId(ObjectIds.ReferenceTypeAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReferenceTypeAttributes
extension_object_typeids['ReferenceTypeAttributes'] = nid
nid = FourByteNodeId(ObjectIds.DataTypeAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataTypeAttributes
extension_object_typeids['DataTypeAttributes'] = nid
nid = FourByteNodeId(ObjectIds.ViewAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ViewAttributes
extension_object_typeids['ViewAttributes'] = nid
nid = FourByteNodeId(ObjectIds.GenericAttributeValue_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = GenericAttributeValue
extension_object_typeids['GenericAttributeValue'] = nid
nid = FourByteNodeId(ObjectIds.GenericAttributes_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = GenericAttributes
extension_object_typeids['GenericAttributes'] = nid
nid = FourByteNodeId(ObjectIds.AddNodesItem_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddNodesItem
extension_object_typeids['AddNodesItem'] = nid
nid = FourByteNodeId(ObjectIds.AddNodesResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddNodesResult
extension_object_typeids['AddNodesResult'] = nid
nid = FourByteNodeId(ObjectIds.AddNodesRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddNodesRequest
extension_object_typeids['AddNodesRequest'] = nid
nid = FourByteNodeId(ObjectIds.AddNodesResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddNodesResponse
extension_object_typeids['AddNodesResponse'] = nid
nid = FourByteNodeId(ObjectIds.AddReferencesItem_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddReferencesItem
extension_object_typeids['AddReferencesItem'] = nid
nid = FourByteNodeId(ObjectIds.AddReferencesRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddReferencesRequest
extension_object_typeids['AddReferencesRequest'] = nid
nid = FourByteNodeId(ObjectIds.AddReferencesResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AddReferencesResponse
extension_object_typeids['AddReferencesResponse'] = nid
nid = FourByteNodeId(ObjectIds.DeleteNodesItem_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteNodesItem
extension_object_typeids['DeleteNodesItem'] = nid
nid = FourByteNodeId(ObjectIds.DeleteNodesRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteNodesRequest
extension_object_typeids['DeleteNodesRequest'] = nid
nid = FourByteNodeId(ObjectIds.DeleteNodesResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteNodesResponse
extension_object_typeids['DeleteNodesResponse'] = nid
nid = FourByteNodeId(ObjectIds.DeleteReferencesItem_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteReferencesItem
extension_object_typeids['DeleteReferencesItem'] = nid
nid = FourByteNodeId(ObjectIds.DeleteReferencesRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteReferencesRequest
extension_object_typeids['DeleteReferencesRequest'] = nid
nid = FourByteNodeId(ObjectIds.DeleteReferencesResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteReferencesResponse
extension_object_typeids['DeleteReferencesResponse'] = nid
nid = FourByteNodeId(ObjectIds.ViewDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ViewDescription
extension_object_typeids['ViewDescription'] = nid
nid = FourByteNodeId(ObjectIds.BrowseDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowseDescription
extension_object_typeids['BrowseDescription'] = nid
nid = FourByteNodeId(ObjectIds.ReferenceDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReferenceDescription
extension_object_typeids['ReferenceDescription'] = nid
nid = FourByteNodeId(ObjectIds.BrowseResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowseResult
extension_object_typeids['BrowseResult'] = nid
nid = FourByteNodeId(ObjectIds.BrowseRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowseRequest
extension_object_typeids['BrowseRequest'] = nid
nid = FourByteNodeId(ObjectIds.BrowseResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowseResponse
extension_object_typeids['BrowseResponse'] = nid
nid = FourByteNodeId(ObjectIds.BrowseNextRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowseNextRequest
extension_object_typeids['BrowseNextRequest'] = nid
nid = FourByteNodeId(ObjectIds.BrowseNextResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowseNextResponse
extension_object_typeids['BrowseNextResponse'] = nid
nid = FourByteNodeId(ObjectIds.BrowsePath_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowsePath
extension_object_typeids['BrowsePath'] = nid
nid = FourByteNodeId(ObjectIds.BrowsePathTarget_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowsePathTarget
extension_object_typeids['BrowsePathTarget'] = nid
nid = FourByteNodeId(ObjectIds.BrowsePathResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BrowsePathResult
extension_object_typeids['BrowsePathResult'] = nid
nid = FourByteNodeId(ObjectIds.TranslateBrowsePathsToNodeIdsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TranslateBrowsePathsToNodeIdsRequest
extension_object_typeids['TranslateBrowsePathsToNodeIdsRequest'] = nid
nid = FourByteNodeId(ObjectIds.TranslateBrowsePathsToNodeIdsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TranslateBrowsePathsToNodeIdsResponse
extension_object_typeids['TranslateBrowsePathsToNodeIdsResponse'] = nid
nid = FourByteNodeId(ObjectIds.RegisterNodesRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisterNodesRequest
extension_object_typeids['RegisterNodesRequest'] = nid
nid = FourByteNodeId(ObjectIds.RegisterNodesResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RegisterNodesResponse
extension_object_typeids['RegisterNodesResponse'] = nid
nid = FourByteNodeId(ObjectIds.UnregisterNodesRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UnregisterNodesRequest
extension_object_typeids['UnregisterNodesRequest'] = nid
nid = FourByteNodeId(ObjectIds.UnregisterNodesResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UnregisterNodesResponse
extension_object_typeids['UnregisterNodesResponse'] = nid
nid = FourByteNodeId(ObjectIds.EndpointConfiguration_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EndpointConfiguration
extension_object_typeids['EndpointConfiguration'] = nid
nid = FourByteNodeId(ObjectIds.QueryDataDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QueryDataDescription
extension_object_typeids['QueryDataDescription'] = nid
nid = FourByteNodeId(ObjectIds.NodeTypeDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NodeTypeDescription
extension_object_typeids['NodeTypeDescription'] = nid
nid = FourByteNodeId(ObjectIds.QueryDataSet_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QueryDataSet
extension_object_typeids['QueryDataSet'] = nid
nid = FourByteNodeId(ObjectIds.NodeReference_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NodeReference
extension_object_typeids['NodeReference'] = nid
nid = FourByteNodeId(ObjectIds.ContentFilterElement_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ContentFilterElement
extension_object_typeids['ContentFilterElement'] = nid
nid = FourByteNodeId(ObjectIds.ContentFilter_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ContentFilter
extension_object_typeids['ContentFilter'] = nid
nid = FourByteNodeId(ObjectIds.FilterOperand_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FilterOperand
extension_object_typeids['FilterOperand'] = nid
nid = FourByteNodeId(ObjectIds.ElementOperand_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ElementOperand
extension_object_typeids['ElementOperand'] = nid
nid = FourByteNodeId(ObjectIds.LiteralOperand_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = LiteralOperand
extension_object_typeids['LiteralOperand'] = nid
nid = FourByteNodeId(ObjectIds.AttributeOperand_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AttributeOperand
extension_object_typeids['AttributeOperand'] = nid
nid = FourByteNodeId(ObjectIds.SimpleAttributeOperand_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SimpleAttributeOperand
extension_object_typeids['SimpleAttributeOperand'] = nid
nid = FourByteNodeId(ObjectIds.PublishedEventsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedEventsDataType
extension_object_typeids['PublishedEventsDataType'] = nid
nid = FourByteNodeId(ObjectIds.ContentFilterElementResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ContentFilterElementResult
extension_object_typeids['ContentFilterElementResult'] = nid
nid = FourByteNodeId(ObjectIds.ContentFilterResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ContentFilterResult
extension_object_typeids['ContentFilterResult'] = nid
nid = FourByteNodeId(ObjectIds.ParsingResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ParsingResult
extension_object_typeids['ParsingResult'] = nid
nid = FourByteNodeId(ObjectIds.QueryFirstRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QueryFirstRequest
extension_object_typeids['QueryFirstRequest'] = nid
nid = FourByteNodeId(ObjectIds.QueryFirstResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QueryFirstResponse
extension_object_typeids['QueryFirstResponse'] = nid
nid = FourByteNodeId(ObjectIds.QueryNextRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QueryNextRequest
extension_object_typeids['QueryNextRequest'] = nid
nid = FourByteNodeId(ObjectIds.QueryNextResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = QueryNextResponse
extension_object_typeids['QueryNextResponse'] = nid
nid = FourByteNodeId(ObjectIds.ReadValueId_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadValueId
extension_object_typeids['ReadValueId'] = nid
nid = FourByteNodeId(ObjectIds.ReadRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadRequest
extension_object_typeids['ReadRequest'] = nid
nid = FourByteNodeId(ObjectIds.ReadResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadResponse
extension_object_typeids['ReadResponse'] = nid
nid = FourByteNodeId(ObjectIds.HistoryReadValueId_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryReadValueId
extension_object_typeids['HistoryReadValueId'] = nid
nid = FourByteNodeId(ObjectIds.HistoryReadResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryReadResult
extension_object_typeids['HistoryReadResult'] = nid
nid = FourByteNodeId(ObjectIds.HistoryReadDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryReadDetails
extension_object_typeids['HistoryReadDetails'] = nid
nid = FourByteNodeId(ObjectIds.ReadRawModifiedDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadRawModifiedDetails
extension_object_typeids['ReadRawModifiedDetails'] = nid
nid = FourByteNodeId(ObjectIds.ReadAtTimeDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadAtTimeDetails
extension_object_typeids['ReadAtTimeDetails'] = nid
nid = FourByteNodeId(ObjectIds.ReadAnnotationDataDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadAnnotationDataDetails
extension_object_typeids['ReadAnnotationDataDetails'] = nid
nid = FourByteNodeId(ObjectIds.HistoryData_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryData
extension_object_typeids['HistoryData'] = nid
nid = FourByteNodeId(ObjectIds.ModificationInfo_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ModificationInfo
extension_object_typeids['ModificationInfo'] = nid
nid = FourByteNodeId(ObjectIds.HistoryModifiedData_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryModifiedData
extension_object_typeids['HistoryModifiedData'] = nid
nid = FourByteNodeId(ObjectIds.HistoryReadRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryReadRequest
extension_object_typeids['HistoryReadRequest'] = nid
nid = FourByteNodeId(ObjectIds.HistoryReadResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryReadResponse
extension_object_typeids['HistoryReadResponse'] = nid
nid = FourByteNodeId(ObjectIds.WriteValue_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriteValue
extension_object_typeids['WriteValue'] = nid
nid = FourByteNodeId(ObjectIds.WriteRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriteRequest
extension_object_typeids['WriteRequest'] = nid
nid = FourByteNodeId(ObjectIds.WriteResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriteResponse
extension_object_typeids['WriteResponse'] = nid
nid = FourByteNodeId(ObjectIds.HistoryUpdateDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryUpdateDetails
extension_object_typeids['HistoryUpdateDetails'] = nid
nid = FourByteNodeId(ObjectIds.UpdateDataDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UpdateDataDetails
extension_object_typeids['UpdateDataDetails'] = nid
nid = FourByteNodeId(ObjectIds.UpdateStructureDataDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UpdateStructureDataDetails
extension_object_typeids['UpdateStructureDataDetails'] = nid
nid = FourByteNodeId(ObjectIds.DeleteRawModifiedDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteRawModifiedDetails
extension_object_typeids['DeleteRawModifiedDetails'] = nid
nid = FourByteNodeId(ObjectIds.DeleteAtTimeDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteAtTimeDetails
extension_object_typeids['DeleteAtTimeDetails'] = nid
nid = FourByteNodeId(ObjectIds.DeleteEventDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteEventDetails
extension_object_typeids['DeleteEventDetails'] = nid
nid = FourByteNodeId(ObjectIds.HistoryUpdateResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryUpdateResult
extension_object_typeids['HistoryUpdateResult'] = nid
nid = FourByteNodeId(ObjectIds.HistoryUpdateRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryUpdateRequest
extension_object_typeids['HistoryUpdateRequest'] = nid
nid = FourByteNodeId(ObjectIds.HistoryUpdateResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryUpdateResponse
extension_object_typeids['HistoryUpdateResponse'] = nid
nid = FourByteNodeId(ObjectIds.CallMethodRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CallMethodRequest
extension_object_typeids['CallMethodRequest'] = nid
nid = FourByteNodeId(ObjectIds.CallMethodResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CallMethodResult
extension_object_typeids['CallMethodResult'] = nid
nid = FourByteNodeId(ObjectIds.CallRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CallRequest
extension_object_typeids['CallRequest'] = nid
nid = FourByteNodeId(ObjectIds.CallResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CallResponse
extension_object_typeids['CallResponse'] = nid
nid = FourByteNodeId(ObjectIds.MonitoringFilter_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoringFilter
extension_object_typeids['MonitoringFilter'] = nid
nid = FourByteNodeId(ObjectIds.DataChangeFilter_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataChangeFilter
extension_object_typeids['DataChangeFilter'] = nid
nid = FourByteNodeId(ObjectIds.EventFilter_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EventFilter
extension_object_typeids['EventFilter'] = nid
nid = FourByteNodeId(ObjectIds.ReadEventDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadEventDetails
extension_object_typeids['ReadEventDetails'] = nid
nid = FourByteNodeId(ObjectIds.ReadEventDetails2_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadEventDetails2
extension_object_typeids['ReadEventDetails2'] = nid
nid = FourByteNodeId(ObjectIds.AggregateConfiguration_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AggregateConfiguration
extension_object_typeids['AggregateConfiguration'] = nid
nid = FourByteNodeId(ObjectIds.ReadProcessedDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadProcessedDetails
extension_object_typeids['ReadProcessedDetails'] = nid
nid = FourByteNodeId(ObjectIds.AggregateFilter_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AggregateFilter
extension_object_typeids['AggregateFilter'] = nid
nid = FourByteNodeId(ObjectIds.MonitoringFilterResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoringFilterResult
extension_object_typeids['MonitoringFilterResult'] = nid
nid = FourByteNodeId(ObjectIds.EventFilterResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EventFilterResult
extension_object_typeids['EventFilterResult'] = nid
nid = FourByteNodeId(ObjectIds.AggregateFilterResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AggregateFilterResult
extension_object_typeids['AggregateFilterResult'] = nid
nid = FourByteNodeId(ObjectIds.MonitoringParameters_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoringParameters
extension_object_typeids['MonitoringParameters'] = nid
nid = FourByteNodeId(ObjectIds.MonitoredItemCreateRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoredItemCreateRequest
extension_object_typeids['MonitoredItemCreateRequest'] = nid
nid = FourByteNodeId(ObjectIds.MonitoredItemCreateResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoredItemCreateResult
extension_object_typeids['MonitoredItemCreateResult'] = nid
nid = FourByteNodeId(ObjectIds.CreateMonitoredItemsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CreateMonitoredItemsRequest
extension_object_typeids['CreateMonitoredItemsRequest'] = nid
nid = FourByteNodeId(ObjectIds.CreateMonitoredItemsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CreateMonitoredItemsResponse
extension_object_typeids['CreateMonitoredItemsResponse'] = nid
nid = FourByteNodeId(ObjectIds.MonitoredItemModifyRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoredItemModifyRequest
extension_object_typeids['MonitoredItemModifyRequest'] = nid
nid = FourByteNodeId(ObjectIds.MonitoredItemModifyResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoredItemModifyResult
extension_object_typeids['MonitoredItemModifyResult'] = nid
nid = FourByteNodeId(ObjectIds.ModifyMonitoredItemsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ModifyMonitoredItemsRequest
extension_object_typeids['ModifyMonitoredItemsRequest'] = nid
nid = FourByteNodeId(ObjectIds.ModifyMonitoredItemsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ModifyMonitoredItemsResponse
extension_object_typeids['ModifyMonitoredItemsResponse'] = nid
nid = FourByteNodeId(ObjectIds.SetMonitoringModeRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SetMonitoringModeRequest
extension_object_typeids['SetMonitoringModeRequest'] = nid
nid = FourByteNodeId(ObjectIds.SetMonitoringModeResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SetMonitoringModeResponse
extension_object_typeids['SetMonitoringModeResponse'] = nid
nid = FourByteNodeId(ObjectIds.SetTriggeringRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SetTriggeringRequest
extension_object_typeids['SetTriggeringRequest'] = nid
nid = FourByteNodeId(ObjectIds.SetTriggeringResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SetTriggeringResponse
extension_object_typeids['SetTriggeringResponse'] = nid
nid = FourByteNodeId(ObjectIds.DeleteMonitoredItemsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteMonitoredItemsRequest
extension_object_typeids['DeleteMonitoredItemsRequest'] = nid
nid = FourByteNodeId(ObjectIds.DeleteMonitoredItemsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteMonitoredItemsResponse
extension_object_typeids['DeleteMonitoredItemsResponse'] = nid
nid = FourByteNodeId(ObjectIds.CreateSubscriptionRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CreateSubscriptionRequest
extension_object_typeids['CreateSubscriptionRequest'] = nid
nid = FourByteNodeId(ObjectIds.CreateSubscriptionResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = CreateSubscriptionResponse
extension_object_typeids['CreateSubscriptionResponse'] = nid
nid = FourByteNodeId(ObjectIds.ModifySubscriptionRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ModifySubscriptionRequest
extension_object_typeids['ModifySubscriptionRequest'] = nid
nid = FourByteNodeId(ObjectIds.ModifySubscriptionResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ModifySubscriptionResponse
extension_object_typeids['ModifySubscriptionResponse'] = nid
nid = FourByteNodeId(ObjectIds.SetPublishingModeRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SetPublishingModeRequest
extension_object_typeids['SetPublishingModeRequest'] = nid
nid = FourByteNodeId(ObjectIds.SetPublishingModeResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SetPublishingModeResponse
extension_object_typeids['SetPublishingModeResponse'] = nid
nid = FourByteNodeId(ObjectIds.NotificationMessage_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NotificationMessage
extension_object_typeids['NotificationMessage'] = nid
nid = FourByteNodeId(ObjectIds.NotificationData_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NotificationData
extension_object_typeids['NotificationData'] = nid
nid = FourByteNodeId(ObjectIds.MonitoredItemNotification_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoredItemNotification
extension_object_typeids['MonitoredItemNotification'] = nid
nid = FourByteNodeId(ObjectIds.DataChangeNotification_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataChangeNotification
extension_object_typeids['DataChangeNotification'] = nid
nid = FourByteNodeId(ObjectIds.EventFieldList_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EventFieldList
extension_object_typeids['EventFieldList'] = nid
nid = FourByteNodeId(ObjectIds.EventNotificationList_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EventNotificationList
extension_object_typeids['EventNotificationList'] = nid
nid = FourByteNodeId(ObjectIds.HistoryEventFieldList_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryEventFieldList
extension_object_typeids['HistoryEventFieldList'] = nid
nid = FourByteNodeId(ObjectIds.HistoryEvent_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryEvent
extension_object_typeids['HistoryEvent'] = nid
nid = FourByteNodeId(ObjectIds.HistoryModifiedEvent_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryModifiedEvent
extension_object_typeids['HistoryModifiedEvent'] = nid
nid = FourByteNodeId(ObjectIds.UpdateEventDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UpdateEventDetails
extension_object_typeids['UpdateEventDetails'] = nid
nid = FourByteNodeId(ObjectIds.StatusChangeNotification_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StatusChangeNotification
extension_object_typeids['StatusChangeNotification'] = nid
nid = FourByteNodeId(ObjectIds.SubscriptionAcknowledgement_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SubscriptionAcknowledgement
extension_object_typeids['SubscriptionAcknowledgement'] = nid
nid = FourByteNodeId(ObjectIds.PublishRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishRequest
extension_object_typeids['PublishRequest'] = nid
nid = FourByteNodeId(ObjectIds.PublishResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishResponse
extension_object_typeids['PublishResponse'] = nid
nid = FourByteNodeId(ObjectIds.RepublishRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RepublishRequest
extension_object_typeids['RepublishRequest'] = nid
nid = FourByteNodeId(ObjectIds.RepublishResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RepublishResponse
extension_object_typeids['RepublishResponse'] = nid
nid = FourByteNodeId(ObjectIds.TransferResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TransferResult
extension_object_typeids['TransferResult'] = nid
nid = FourByteNodeId(ObjectIds.TransferSubscriptionsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TransferSubscriptionsRequest
extension_object_typeids['TransferSubscriptionsRequest'] = nid
nid = FourByteNodeId(ObjectIds.TransferSubscriptionsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TransferSubscriptionsResponse
extension_object_typeids['TransferSubscriptionsResponse'] = nid
nid = FourByteNodeId(ObjectIds.DeleteSubscriptionsRequest_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteSubscriptionsRequest
extension_object_typeids['DeleteSubscriptionsRequest'] = nid
nid = FourByteNodeId(ObjectIds.DeleteSubscriptionsResponse_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DeleteSubscriptionsResponse
extension_object_typeids['DeleteSubscriptionsResponse'] = nid
nid = FourByteNodeId(ObjectIds.BuildInfo_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = BuildInfo
extension_object_typeids['BuildInfo'] = nid
nid = FourByteNodeId(ObjectIds.RedundantServerDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RedundantServerDataType
extension_object_typeids['RedundantServerDataType'] = nid
nid = FourByteNodeId(ObjectIds.EndpointUrlListDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EndpointUrlListDataType
extension_object_typeids['EndpointUrlListDataType'] = nid
nid = FourByteNodeId(ObjectIds.NetworkGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NetworkGroupDataType
extension_object_typeids['NetworkGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.SamplingIntervalDiagnosticsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SamplingIntervalDiagnosticsDataType
extension_object_typeids['SamplingIntervalDiagnosticsDataType'] = nid
nid = FourByteNodeId(ObjectIds.ServerDiagnosticsSummaryDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ServerDiagnosticsSummaryDataType
extension_object_typeids['ServerDiagnosticsSummaryDataType'] = nid
nid = FourByteNodeId(ObjectIds.ServerStatusDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ServerStatusDataType
extension_object_typeids['ServerStatusDataType'] = nid
nid = FourByteNodeId(ObjectIds.SessionSecurityDiagnosticsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SessionSecurityDiagnosticsDataType
extension_object_typeids['SessionSecurityDiagnosticsDataType'] = nid
nid = FourByteNodeId(ObjectIds.ServiceCounterDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ServiceCounterDataType
extension_object_typeids['ServiceCounterDataType'] = nid
nid = FourByteNodeId(ObjectIds.SessionDiagnosticsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SessionDiagnosticsDataType
extension_object_typeids['SessionDiagnosticsDataType'] = nid
nid = FourByteNodeId(ObjectIds.StatusResult_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StatusResult
extension_object_typeids['StatusResult'] = nid
nid = FourByteNodeId(ObjectIds.SubscriptionDiagnosticsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SubscriptionDiagnosticsDataType
extension_object_typeids['SubscriptionDiagnosticsDataType'] = nid
nid = FourByteNodeId(ObjectIds.ModelChangeStructureDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ModelChangeStructureDataType
extension_object_typeids['ModelChangeStructureDataType'] = nid
nid = FourByteNodeId(ObjectIds.SemanticChangeStructureDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SemanticChangeStructureDataType
extension_object_typeids['SemanticChangeStructureDataType'] = nid
nid = FourByteNodeId(ObjectIds.Range_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Range
extension_object_typeids['Range'] = nid
nid = FourByteNodeId(ObjectIds.EUInformation_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EUInformation
extension_object_typeids['EUInformation'] = nid
nid = FourByteNodeId(ObjectIds.ComplexNumberType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ComplexNumberType
extension_object_typeids['ComplexNumberType'] = nid
nid = FourByteNodeId(ObjectIds.DoubleComplexNumberType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DoubleComplexNumberType
extension_object_typeids['DoubleComplexNumberType'] = nid
nid = FourByteNodeId(ObjectIds.AxisInformation_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AxisInformation
extension_object_typeids['AxisInformation'] = nid
nid = FourByteNodeId(ObjectIds.XVType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = XVType
extension_object_typeids['XVType'] = nid
nid = FourByteNodeId(ObjectIds.ProgramDiagnosticDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ProgramDiagnosticDataType
extension_object_typeids['ProgramDiagnosticDataType'] = nid
nid = FourByteNodeId(ObjectIds.ProgramDiagnostic2DataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ProgramDiagnostic2DataType
extension_object_typeids['ProgramDiagnostic2DataType'] = nid
nid = FourByteNodeId(ObjectIds.Annotation_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Annotation
extension_object_typeids['Annotation'] = nid
