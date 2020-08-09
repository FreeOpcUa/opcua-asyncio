"""
Autogenerate code from xml spec
Date:2020-08-09 20:11:42.865863
"""

from datetime import datetime
from enum import IntEnum

from asyncua.ua.uatypes import *
from asyncua.ua.object_ids import ObjectIds


class NamingRuleType(IntEnum):
    """
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
    """
    UserName = 1
    Thumbprint = 2
    Role = 3
    GroupId = 4
    Anonymous = 5
    AuthenticatedUser = 6


class TrustListMasks(IntEnum):
    """
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
    :ivar Disabled:
    :vartype Disabled: 0
    :ivar Paused:
    :vartype Paused: 1
    :ivar Operational:
    :vartype Operational: 2
    :ivar Error:
    :vartype Error: 3
    """
    Disabled = 0
    Paused = 1
    Operational = 2
    Error = 3


class DataSetFieldFlags(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar PromotedField:
    :vartype PromotedField: 1
    """
    None_ = 0
    PromotedField = 1


class DataSetFieldContentMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar StatusCode:
    :vartype StatusCode: 1
    :ivar SourceTimestamp:
    :vartype SourceTimestamp: 2
    :ivar ServerTimestamp:
    :vartype ServerTimestamp: 4
    :ivar SourcePicoSeconds:
    :vartype SourcePicoSeconds: 8
    :ivar ServerPicoSeconds:
    :vartype ServerPicoSeconds: 16
    :ivar RawData:
    :vartype RawData: 32
    """
    None_ = 0
    StatusCode = 1
    SourceTimestamp = 2
    ServerTimestamp = 4
    SourcePicoSeconds = 8
    ServerPicoSeconds = 16
    RawData = 32


class OverrideValueHandling(IntEnum):
    """
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


class UadpNetworkMessageContentMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar PublisherId:
    :vartype PublisherId: 1
    :ivar GroupHeader:
    :vartype GroupHeader: 2
    :ivar WriterGroupId:
    :vartype WriterGroupId: 4
    :ivar GroupVersion:
    :vartype GroupVersion: 8
    :ivar NetworkMessageNumber:
    :vartype NetworkMessageNumber: 16
    :ivar SequenceNumber:
    :vartype SequenceNumber: 32
    :ivar PayloadHeader:
    :vartype PayloadHeader: 64
    :ivar Timestamp:
    :vartype Timestamp: 128
    :ivar PicoSeconds:
    :vartype PicoSeconds: 256
    :ivar DataSetClassId:
    :vartype DataSetClassId: 512
    :ivar PromotedFields:
    :vartype PromotedFields: 1024
    """
    None_ = 0
    PublisherId = 1
    GroupHeader = 2
    WriterGroupId = 4
    GroupVersion = 8
    NetworkMessageNumber = 16
    SequenceNumber = 32
    PayloadHeader = 64
    Timestamp = 128
    PicoSeconds = 256
    DataSetClassId = 512
    PromotedFields = 1024


class UadpDataSetMessageContentMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar Timestamp:
    :vartype Timestamp: 1
    :ivar PicoSeconds:
    :vartype PicoSeconds: 2
    :ivar Status:
    :vartype Status: 4
    :ivar MajorVersion:
    :vartype MajorVersion: 8
    :ivar MinorVersion:
    :vartype MinorVersion: 16
    :ivar SequenceNumber:
    :vartype SequenceNumber: 32
    """
    None_ = 0
    Timestamp = 1
    PicoSeconds = 2
    Status = 4
    MajorVersion = 8
    MinorVersion = 16
    SequenceNumber = 32


class JsonNetworkMessageContentMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar NetworkMessageHeader:
    :vartype NetworkMessageHeader: 1
    :ivar DataSetMessageHeader:
    :vartype DataSetMessageHeader: 2
    :ivar SingleDataSetMessage:
    :vartype SingleDataSetMessage: 4
    :ivar PublisherId:
    :vartype PublisherId: 8
    :ivar DataSetClassId:
    :vartype DataSetClassId: 16
    :ivar ReplyTo:
    :vartype ReplyTo: 32
    """
    None_ = 0
    NetworkMessageHeader = 1
    DataSetMessageHeader = 2
    SingleDataSetMessage = 4
    PublisherId = 8
    DataSetClassId = 16
    ReplyTo = 32


class JsonDataSetMessageContentMask(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar DataSetWriterId:
    :vartype DataSetWriterId: 1
    :ivar MetaDataVersion:
    :vartype MetaDataVersion: 2
    :ivar SequenceNumber:
    :vartype SequenceNumber: 4
    :ivar Timestamp:
    :vartype Timestamp: 8
    :ivar Status:
    :vartype Status: 16
    """
    None_ = 0
    DataSetWriterId = 1
    MetaDataVersion = 2
    SequenceNumber = 4
    Timestamp = 8
    Status = 16


class BrokerTransportQualityOfService(IntEnum):
    """
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


class DiagnosticsLevel(IntEnum):
    """
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
    :ivar Information:
    :vartype Information: 0
    :ivar Error:
    :vartype Error: 1
    """
    Information = 0
    Error = 1


class IdType(IntEnum):
    """
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


class PermissionType(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar Browse:
    :vartype Browse: 1
    :ivar ReadRolePermissions:
    :vartype ReadRolePermissions: 2
    :ivar WriteAttribute:
    :vartype WriteAttribute: 4
    :ivar WriteRolePermissions:
    :vartype WriteRolePermissions: 8
    :ivar WriteHistorizing:
    :vartype WriteHistorizing: 16
    :ivar Read:
    :vartype Read: 32
    :ivar Write:
    :vartype Write: 64
    :ivar ReadHistory:
    :vartype ReadHistory: 128
    :ivar InsertHistory:
    :vartype InsertHistory: 256
    :ivar ModifyHistory:
    :vartype ModifyHistory: 512
    :ivar DeleteHistory:
    :vartype DeleteHistory: 1024
    :ivar ReceiveEvents:
    :vartype ReceiveEvents: 2048
    :ivar Call:
    :vartype Call: 4096
    :ivar AddReference:
    :vartype AddReference: 8192
    :ivar RemoveReference:
    :vartype RemoveReference: 16384
    :ivar DeleteNode:
    :vartype DeleteNode: 32768
    :ivar AddNode:
    :vartype AddNode: 65536
    """
    None_ = 0
    Browse = 1
    ReadRolePermissions = 2
    WriteAttribute = 4
    WriteRolePermissions = 8
    WriteHistorizing = 16
    Read = 32
    Write = 64
    ReadHistory = 128
    InsertHistory = 256
    ModifyHistory = 512
    DeleteHistory = 1024
    ReceiveEvents = 2048
    Call = 4096
    AddReference = 8192
    RemoveReference = 16384
    DeleteNode = 32768
    AddNode = 65536


class AccessLevelType(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar CurrentRead:
    :vartype CurrentRead: 1
    :ivar CurrentWrite:
    :vartype CurrentWrite: 2
    :ivar HistoryRead:
    :vartype HistoryRead: 4
    :ivar HistoryWrite:
    :vartype HistoryWrite: 8
    :ivar SemanticChange:
    :vartype SemanticChange: 16
    :ivar StatusWrite:
    :vartype StatusWrite: 32
    :ivar TimestampWrite:
    :vartype TimestampWrite: 64
    """
    None_ = 0
    CurrentRead = 1
    CurrentWrite = 2
    HistoryRead = 4
    HistoryWrite = 8
    SemanticChange = 16
    StatusWrite = 32
    TimestampWrite = 64


class AccessLevelExType(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar CurrentRead:
    :vartype CurrentRead: 1
    :ivar CurrentWrite:
    :vartype CurrentWrite: 2
    :ivar HistoryRead:
    :vartype HistoryRead: 4
    :ivar HistoryWrite:
    :vartype HistoryWrite: 8
    :ivar SemanticChange:
    :vartype SemanticChange: 16
    :ivar StatusWrite:
    :vartype StatusWrite: 32
    :ivar TimestampWrite:
    :vartype TimestampWrite: 64
    :ivar NonatomicRead:
    :vartype NonatomicRead: 256
    :ivar NonatomicWrite:
    :vartype NonatomicWrite: 512
    :ivar WriteFullArrayOnly:
    :vartype WriteFullArrayOnly: 1024
    """
    None_ = 0
    CurrentRead = 1
    CurrentWrite = 2
    HistoryRead = 4
    HistoryWrite = 8
    SemanticChange = 16
    StatusWrite = 32
    TimestampWrite = 64
    NonatomicRead = 256
    NonatomicWrite = 512
    WriteFullArrayOnly = 1024


class EventNotifierType(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar SubscribeToEvents:
    :vartype SubscribeToEvents: 1
    :ivar HistoryRead:
    :vartype HistoryRead: 4
    :ivar HistoryWrite:
    :vartype HistoryWrite: 8
    """
    None_ = 0
    SubscribeToEvents = 1
    HistoryRead = 4
    HistoryWrite = 8


class AccessRestrictionType(IntEnum):
    """
    :ivar None_:
    :vartype None_: 0
    :ivar SigningRequired:
    :vartype SigningRequired: 1
    :ivar EncryptionRequired:
    :vartype EncryptionRequired: 2
    :ivar SessionRequired:
    :vartype SessionRequired: 4
    """
    None_ = 0
    SigningRequired = 1
    EncryptionRequired = 2
    SessionRequired = 4


class StructureType(IntEnum):
    """
    :ivar Structure:
    :vartype Structure: 0
    :ivar StructureWithOptionalFields:
    :vartype StructureWithOptionalFields: 1
    :ivar Union:
    :vartype Union: 2
    """
    Structure = 0
    StructureWithOptionalFields = 1
    Union = 2


class ApplicationType(IntEnum):
    """
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


class AttributeWriteMask(IntEnum):
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
    :ivar ValueForVariableType:
    :vartype ValueForVariableType: 2097152
    :ivar DataTypeDefinition:
    :vartype DataTypeDefinition: 4194304
    :ivar RolePermissions:
    :vartype RolePermissions: 8388608
    :ivar AccessRestrictions:
    :vartype AccessRestrictions: 16777216
    :ivar AccessLevelEx:
    :vartype AccessLevelEx: 33554432
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
    ValueForVariableType = 2097152
    DataTypeDefinition = 4194304
    RolePermissions = 8388608
    AccessRestrictions = 16777216
    AccessLevelEx = 33554432


class BrowseDirection(IntEnum):
    """
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


class DataTypeDefinition(FrozenClass):
    """
    """

    data_type = ObjectIds.DataTypeDefinition

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'DataTypeDefinition()'

    __repr__ = __str__


class DiagnosticInfo(FrozenClass):
    """
    A recursive structure containing diagnostic information associated with a status code.

    :ivar Encoding:
    :vartype Encoding: Byte
    :ivar SymbolicId:
    :vartype SymbolicId: Int32
    :ivar NamespaceURI:
    :vartype NamespaceURI: Int32
    :ivar Locale:
    :vartype Locale: Int32
    :ivar LocalizedText:
    :vartype LocalizedText: Int32
    :ivar AdditionalInfo:
    :vartype AdditionalInfo: String
    :ivar InnerStatusCode:
    :vartype InnerStatusCode: StatusCode
    :ivar InnerDiagnosticInfo:
    :vartype InnerDiagnosticInfo: DiagnosticInfo
    """

    data_type = ObjectIds.DiagnosticInfo

    ua_switches = {
        'SymbolicId': ('Encoding', 0),
        'NamespaceURI': ('Encoding', 1),
        'Locale': ('Encoding', 3),
        'LocalizedText': ('Encoding', 2),
        'AdditionalInfo': ('Encoding', 4),
        'InnerStatusCode': ('Encoding', 5),
        'InnerDiagnosticInfo': ('Encoding', 6),
               }
    ua_types = [
        ('Encoding', 'Byte'),
        ('SymbolicId', 'Int32'),
        ('NamespaceURI', 'Int32'),
        ('Locale', 'Int32'),
        ('LocalizedText', 'Int32'),
        ('AdditionalInfo', 'String'),
        ('InnerStatusCode', 'StatusCode'),
        ('InnerDiagnosticInfo', 'DiagnosticInfo'),
               ]

    def __init__(self):
        self.Encoding = 0
        self.SymbolicId = None
        self.NamespaceURI = None
        self.Locale = None
        self.LocalizedText = None
        self.AdditionalInfo = None
        self.InnerStatusCode = None
        self.InnerDiagnosticInfo = None
        self._freeze = True

    def __str__(self):
        return f'DiagnosticInfo(Encoding:{self.Encoding}, SymbolicId:{self.SymbolicId}, NamespaceURI:{self.NamespaceURI}, Locale:{self.Locale}, LocalizedText:{self.LocalizedText}, AdditionalInfo:{self.AdditionalInfo}, InnerStatusCode:{self.InnerStatusCode}, InnerDiagnosticInfo:{self.InnerDiagnosticInfo})'

    __repr__ = __str__


class KeyValuePair(FrozenClass):
    """
    :ivar Key:
    :vartype Key: QualifiedName
    :ivar Value:
    :vartype Value: Variant
    """

    data_type = ObjectIds.KeyValuePair

    ua_types = [
        ('Key', 'QualifiedName'),
        ('Value', 'Variant'),
               ]

    def __init__(self):
        self.Key = QualifiedName()
        self.Value = Variant()
        self._freeze = True

    def __str__(self):
        return f'KeyValuePair(Key:{self.Key}, Value:{self.Value})'

    __repr__ = __str__


class EndpointType(FrozenClass):
    """
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar SecurityMode:
    :vartype SecurityMode: MessageSecurityMode
    :ivar SecurityPolicyUri:
    :vartype SecurityPolicyUri: String
    :ivar TransportProfileUri:
    :vartype TransportProfileUri: String
    """

    data_type = ObjectIds.EndpointType

    ua_types = [
        ('EndpointUrl', 'String'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityPolicyUri', 'String'),
        ('TransportProfileUri', 'String'),
               ]

    def __init__(self):
        self.EndpointUrl = None
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityPolicyUri = None
        self.TransportProfileUri = None
        self._freeze = True

    def __str__(self):
        return f'EndpointType(EndpointUrl:{self.EndpointUrl}, SecurityMode:{self.SecurityMode}, SecurityPolicyUri:{self.SecurityPolicyUri}, TransportProfileUri:{self.TransportProfileUri})'

    __repr__ = __str__


class RationalNumber(FrozenClass):
    """
    :ivar Numerator:
    :vartype Numerator: Int32
    :ivar Denominator:
    :vartype Denominator: UInt32
    """

    data_type = ObjectIds.RationalNumber

    ua_types = [
        ('Numerator', 'Int32'),
        ('Denominator', 'UInt32'),
               ]

    def __init__(self):
        self.Numerator = 0
        self.Denominator = 0
        self._freeze = True

    def __str__(self):
        return f'RationalNumber(Numerator:{self.Numerator}, Denominator:{self.Denominator})'

    __repr__ = __str__


class Vector(FrozenClass):
    """
    """

    data_type = ObjectIds.Vector

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'Vector()'

    __repr__ = __str__


class ThreeDVector(FrozenClass):
    """
    :ivar X:
    :vartype X: Double
    :ivar Y:
    :vartype Y: Double
    :ivar Z:
    :vartype Z: Double
    """

    data_type = ObjectIds.ThreeDVector

    ua_types = [
        ('X', 'Double'),
        ('Y', 'Double'),
        ('Z', 'Double'),
               ]

    def __init__(self):
        self.X = 0
        self.Y = 0
        self.Z = 0
        self._freeze = True

    def __str__(self):
        return f'ThreeDVector(X:{self.X}, Y:{self.Y}, Z:{self.Z})'

    __repr__ = __str__


class CartesianCoordinates(FrozenClass):
    """
    """

    data_type = ObjectIds.CartesianCoordinates

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'CartesianCoordinates()'

    __repr__ = __str__


class ThreeDCartesianCoordinates(FrozenClass):
    """
    :ivar X:
    :vartype X: Double
    :ivar Y:
    :vartype Y: Double
    :ivar Z:
    :vartype Z: Double
    """

    data_type = ObjectIds.ThreeDCartesianCoordinates

    ua_types = [
        ('X', 'Double'),
        ('Y', 'Double'),
        ('Z', 'Double'),
               ]

    def __init__(self):
        self.X = 0
        self.Y = 0
        self.Z = 0
        self._freeze = True

    def __str__(self):
        return f'ThreeDCartesianCoordinates(X:{self.X}, Y:{self.Y}, Z:{self.Z})'

    __repr__ = __str__


class Orientation(FrozenClass):
    """
    """

    data_type = ObjectIds.Orientation

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'Orientation()'

    __repr__ = __str__


class ThreeDOrientation(FrozenClass):
    """
    :ivar A:
    :vartype A: Double
    :ivar B:
    :vartype B: Double
    :ivar C:
    :vartype C: Double
    """

    data_type = ObjectIds.ThreeDOrientation

    ua_types = [
        ('A', 'Double'),
        ('B', 'Double'),
        ('C', 'Double'),
               ]

    def __init__(self):
        self.A = 0
        self.B = 0
        self.C = 0
        self._freeze = True

    def __str__(self):
        return f'ThreeDOrientation(A:{self.A}, B:{self.B}, C:{self.C})'

    __repr__ = __str__


class Frame(FrozenClass):
    """
    """

    data_type = ObjectIds.Frame

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'Frame()'

    __repr__ = __str__


class ThreeDFrame(FrozenClass):
    """
    :ivar CartesianCoordinates:
    :vartype CartesianCoordinates: ThreeDCartesianCoordinates
    :ivar Orientation:
    :vartype Orientation: ThreeDOrientation
    """

    data_type = ObjectIds.ThreeDFrame

    ua_types = [
        ('CartesianCoordinates', 'ThreeDCartesianCoordinates'),
        ('Orientation', 'ThreeDOrientation'),
               ]

    def __init__(self):
        self.CartesianCoordinates = ThreeDCartesianCoordinates()
        self.Orientation = ThreeDOrientation()
        self._freeze = True

    def __str__(self):
        return f'ThreeDFrame(CartesianCoordinates:{self.CartesianCoordinates}, Orientation:{self.Orientation})'

    __repr__ = __str__


class IdentityMappingRuleType(FrozenClass):
    """
    :ivar CriteriaType:
    :vartype CriteriaType: IdentityCriteriaType
    :ivar Criteria:
    :vartype Criteria: String
    """

    data_type = ObjectIds.IdentityMappingRuleType

    ua_types = [
        ('CriteriaType', 'IdentityCriteriaType'),
        ('Criteria', 'String'),
               ]

    def __init__(self):
        self.CriteriaType = IdentityCriteriaType(0)
        self.Criteria = None
        self._freeze = True

    def __str__(self):
        return f'IdentityMappingRuleType(CriteriaType:{self.CriteriaType}, Criteria:{self.Criteria})'

    __repr__ = __str__


class CurrencyUnitType(FrozenClass):
    """
    :ivar NumericCode:
    :vartype NumericCode: Int16
    :ivar Exponent:
    :vartype Exponent: SByte
    :ivar AlphabeticCode:
    :vartype AlphabeticCode: String
    :ivar Currency:
    :vartype Currency: LocalizedText
    """

    data_type = ObjectIds.CurrencyUnitType

    ua_types = [
        ('NumericCode', 'Int16'),
        ('Exponent', 'SByte'),
        ('AlphabeticCode', 'String'),
        ('Currency', 'LocalizedText'),
               ]

    def __init__(self):
        self.NumericCode = 0
        self.Exponent = SByte()
        self.AlphabeticCode = None
        self.Currency = LocalizedText()
        self._freeze = True

    def __str__(self):
        return f'CurrencyUnitType(NumericCode:{self.NumericCode}, Exponent:{self.Exponent}, AlphabeticCode:{self.AlphabeticCode}, Currency:{self.Currency})'

    __repr__ = __str__


class TrustListDataType(FrozenClass):
    """
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

    data_type = ObjectIds.TrustListDataType

    ua_types = [
        ('SpecifiedLists', 'UInt32'),
        ('TrustedCertificates', 'ListOfByteString'),
        ('TrustedCrls', 'ListOfByteString'),
        ('IssuerCertificates', 'ListOfByteString'),
        ('IssuerCrls', 'ListOfByteString'),
               ]

    def __init__(self):
        self.SpecifiedLists = 0
        self.TrustedCertificates = []
        self.TrustedCrls = []
        self.IssuerCertificates = []
        self.IssuerCrls = []
        self._freeze = True

    def __str__(self):
        return f'TrustListDataType(SpecifiedLists:{self.SpecifiedLists}, TrustedCertificates:{self.TrustedCertificates}, TrustedCrls:{self.TrustedCrls}, IssuerCertificates:{self.IssuerCertificates}, IssuerCrls:{self.IssuerCrls})'

    __repr__ = __str__


class DecimalDataType(FrozenClass):
    """
    :ivar Scale:
    :vartype Scale: Int16
    :ivar Value:
    :vartype Value: ByteString
    """

    data_type = ObjectIds.DecimalDataType

    ua_types = [
        ('Scale', 'Int16'),
        ('Value', 'ByteString'),
               ]

    def __init__(self):
        self.Scale = 0
        self.Value = None
        self._freeze = True

    def __str__(self):
        return f'DecimalDataType(Scale:{self.Scale}, Value:{self.Value})'

    __repr__ = __str__


class DataTypeSchemaHeader(FrozenClass):
    """
    :ivar Namespaces:
    :vartype Namespaces: String
    :ivar StructureDataTypes:
    :vartype StructureDataTypes: StructureDescription
    :ivar EnumDataTypes:
    :vartype EnumDataTypes: EnumDescription
    :ivar SimpleDataTypes:
    :vartype SimpleDataTypes: SimpleTypeDescription
    """

    data_type = ObjectIds.DataTypeSchemaHeader

    ua_types = [
        ('Namespaces', 'ListOfString'),
        ('StructureDataTypes', 'ListOfStructureDescription'),
        ('EnumDataTypes', 'ListOfEnumDescription'),
        ('SimpleDataTypes', 'ListOfSimpleTypeDescription'),
               ]

    def __init__(self):
        self.Namespaces = []
        self.StructureDataTypes = []
        self.EnumDataTypes = []
        self.SimpleDataTypes = []
        self._freeze = True

    def __str__(self):
        return f'DataTypeSchemaHeader(Namespaces:{self.Namespaces}, StructureDataTypes:{self.StructureDataTypes}, EnumDataTypes:{self.EnumDataTypes}, SimpleDataTypes:{self.SimpleDataTypes})'

    __repr__ = __str__


class DataTypeDescription(FrozenClass):
    """
    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    """

    data_type = ObjectIds.DataTypeDescription

    ua_types = [
        ('DataTypeId', 'NodeId'),
        ('Name', 'QualifiedName'),
               ]

    def __init__(self):
        self.DataTypeId = NodeId()
        self.Name = QualifiedName()
        self._freeze = True

    def __str__(self):
        return f'DataTypeDescription(DataTypeId:{self.DataTypeId}, Name:{self.Name})'

    __repr__ = __str__


class StructureDescription(FrozenClass):
    """
    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    :ivar StructureDefinition:
    :vartype StructureDefinition: StructureDefinition
    """

    data_type = ObjectIds.StructureDescription

    ua_types = [
        ('DataTypeId', 'NodeId'),
        ('Name', 'QualifiedName'),
        ('StructureDefinition', 'StructureDefinition'),
               ]

    def __init__(self):
        self.DataTypeId = NodeId()
        self.Name = QualifiedName()
        self.StructureDefinition = StructureDefinition()
        self._freeze = True

    def __str__(self):
        return f'StructureDescription(DataTypeId:{self.DataTypeId}, Name:{self.Name}, StructureDefinition:{self.StructureDefinition})'

    __repr__ = __str__


class EnumDescription(FrozenClass):
    """
    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    :ivar EnumDefinition:
    :vartype EnumDefinition: EnumDefinition
    :ivar BuiltInType:
    :vartype BuiltInType: Byte
    """

    data_type = ObjectIds.EnumDescription

    ua_types = [
        ('DataTypeId', 'NodeId'),
        ('Name', 'QualifiedName'),
        ('EnumDefinition', 'EnumDefinition'),
        ('BuiltInType', 'Byte'),
               ]

    def __init__(self):
        self.DataTypeId = NodeId()
        self.Name = QualifiedName()
        self.EnumDefinition = EnumDefinition()
        self.BuiltInType = 0
        self._freeze = True

    def __str__(self):
        return f'EnumDescription(DataTypeId:{self.DataTypeId}, Name:{self.Name}, EnumDefinition:{self.EnumDefinition}, BuiltInType:{self.BuiltInType})'

    __repr__ = __str__


class SimpleTypeDescription(FrozenClass):
    """
    :ivar DataTypeId:
    :vartype DataTypeId: NodeId
    :ivar Name:
    :vartype Name: QualifiedName
    :ivar BaseDataType:
    :vartype BaseDataType: NodeId
    :ivar BuiltInType:
    :vartype BuiltInType: Byte
    """

    data_type = ObjectIds.SimpleTypeDescription

    ua_types = [
        ('DataTypeId', 'NodeId'),
        ('Name', 'QualifiedName'),
        ('BaseDataType', 'NodeId'),
        ('BuiltInType', 'Byte'),
               ]

    def __init__(self):
        self.DataTypeId = NodeId()
        self.Name = QualifiedName()
        self.BaseDataType = NodeId()
        self.BuiltInType = 0
        self._freeze = True

    def __str__(self):
        return f'SimpleTypeDescription(DataTypeId:{self.DataTypeId}, Name:{self.Name}, BaseDataType:{self.BaseDataType}, BuiltInType:{self.BuiltInType})'

    __repr__ = __str__


class UABinaryFileDataType(FrozenClass):
    """
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

    data_type = ObjectIds.UABinaryFileDataType

    ua_types = [
        ('Namespaces', 'ListOfString'),
        ('StructureDataTypes', 'ListOfStructureDescription'),
        ('EnumDataTypes', 'ListOfEnumDescription'),
        ('SimpleDataTypes', 'ListOfSimpleTypeDescription'),
        ('SchemaLocation', 'String'),
        ('FileHeader', 'ListOfKeyValuePair'),
        ('Body', 'Variant'),
               ]

    def __init__(self):
        self.Namespaces = []
        self.StructureDataTypes = []
        self.EnumDataTypes = []
        self.SimpleDataTypes = []
        self.SchemaLocation = None
        self.FileHeader = []
        self.Body = Variant()
        self._freeze = True

    def __str__(self):
        return f'UABinaryFileDataType(Namespaces:{self.Namespaces}, StructureDataTypes:{self.StructureDataTypes}, EnumDataTypes:{self.EnumDataTypes}, SimpleDataTypes:{self.SimpleDataTypes}, SchemaLocation:{self.SchemaLocation}, FileHeader:{self.FileHeader}, Body:{self.Body})'

    __repr__ = __str__


class DataSetMetaDataType(FrozenClass):
    """
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

    data_type = ObjectIds.DataSetMetaDataType

    ua_types = [
        ('Namespaces', 'ListOfString'),
        ('StructureDataTypes', 'ListOfStructureDescription'),
        ('EnumDataTypes', 'ListOfEnumDescription'),
        ('SimpleDataTypes', 'ListOfSimpleTypeDescription'),
        ('Name', 'String'),
        ('Description', 'LocalizedText'),
        ('Fields', 'ListOfFieldMetaData'),
        ('DataSetClassId', 'Guid'),
        ('ConfigurationVersion', 'ConfigurationVersionDataType'),
               ]

    def __init__(self):
        self.Namespaces = []
        self.StructureDataTypes = []
        self.EnumDataTypes = []
        self.SimpleDataTypes = []
        self.Name = None
        self.Description = LocalizedText()
        self.Fields = []
        self.DataSetClassId = Guid()
        self.ConfigurationVersion = ConfigurationVersionDataType()
        self._freeze = True

    def __str__(self):
        return f'DataSetMetaDataType(Namespaces:{self.Namespaces}, StructureDataTypes:{self.StructureDataTypes}, EnumDataTypes:{self.EnumDataTypes}, SimpleDataTypes:{self.SimpleDataTypes}, Name:{self.Name}, Description:{self.Description}, Fields:{self.Fields}, DataSetClassId:{self.DataSetClassId}, ConfigurationVersion:{self.ConfigurationVersion})'

    __repr__ = __str__


class FieldMetaData(FrozenClass):
    """
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

    data_type = ObjectIds.FieldMetaData

    ua_types = [
        ('Name', 'String'),
        ('Description', 'LocalizedText'),
        ('FieldFlags', 'DataSetFieldFlags'),
        ('BuiltInType', 'Byte'),
        ('DataType', 'NodeId'),
        ('ValueRank', 'Int32'),
        ('ArrayDimensions', 'ListOfUInt32'),
        ('MaxStringLength', 'UInt32'),
        ('DataSetFieldId', 'Guid'),
        ('Properties', 'ListOfKeyValuePair'),
               ]

    def __init__(self):
        self.Name = None
        self.Description = LocalizedText()
        self.FieldFlags = DataSetFieldFlags(0)
        self.BuiltInType = 0
        self.DataType = NodeId()
        self.ValueRank = 0
        self.ArrayDimensions = []
        self.MaxStringLength = 0
        self.DataSetFieldId = Guid()
        self.Properties = []
        self._freeze = True

    def __str__(self):
        return f'FieldMetaData(Name:{self.Name}, Description:{self.Description}, FieldFlags:{self.FieldFlags}, BuiltInType:{self.BuiltInType}, DataType:{self.DataType}, ValueRank:{self.ValueRank}, ArrayDimensions:{self.ArrayDimensions}, MaxStringLength:{self.MaxStringLength}, DataSetFieldId:{self.DataSetFieldId}, Properties:{self.Properties})'

    __repr__ = __str__


class ConfigurationVersionDataType(FrozenClass):
    """
    :ivar MajorVersion:
    :vartype MajorVersion: UInt32
    :ivar MinorVersion:
    :vartype MinorVersion: UInt32
    """

    data_type = ObjectIds.ConfigurationVersionDataType

    ua_types = [
        ('MajorVersion', 'UInt32'),
        ('MinorVersion', 'UInt32'),
               ]

    def __init__(self):
        self.MajorVersion = 0
        self.MinorVersion = 0
        self._freeze = True

    def __str__(self):
        return f'ConfigurationVersionDataType(MajorVersion:{self.MajorVersion}, MinorVersion:{self.MinorVersion})'

    __repr__ = __str__


class PublishedDataSetDataType(FrozenClass):
    """
    :ivar Name:
    :vartype Name: String
    :ivar DataSetFolder:
    :vartype DataSetFolder: String
    :ivar DataSetMetaData:
    :vartype DataSetMetaData: DataSetMetaDataType
    :ivar ExtensionFields:
    :vartype ExtensionFields: KeyValuePair
    :ivar DataSetSource:
    :vartype DataSetSource: ExtensionObject
    """

    data_type = ObjectIds.PublishedDataSetDataType

    ua_types = [
        ('Name', 'String'),
        ('DataSetFolder', 'ListOfString'),
        ('DataSetMetaData', 'DataSetMetaDataType'),
        ('ExtensionFields', 'ListOfKeyValuePair'),
        ('DataSetSource', 'ExtensionObject'),
               ]

    def __init__(self):
        self.Name = None
        self.DataSetFolder = []
        self.DataSetMetaData = DataSetMetaDataType()
        self.ExtensionFields = []
        self.DataSetSource = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'PublishedDataSetDataType(Name:{self.Name}, DataSetFolder:{self.DataSetFolder}, DataSetMetaData:{self.DataSetMetaData}, ExtensionFields:{self.ExtensionFields}, DataSetSource:{self.DataSetSource})'

    __repr__ = __str__


class PublishedDataSetSourceDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.PublishedDataSetSourceDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'PublishedDataSetSourceDataType()'

    __repr__ = __str__


class PublishedVariableDataType(FrozenClass):
    """
    :ivar PublishedVariable:
    :vartype PublishedVariable: NodeId
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar SamplingIntervalHint:
    :vartype SamplingIntervalHint: Double
    :ivar DeadbandType:
    :vartype DeadbandType: UInt32
    :ivar DeadbandValue:
    :vartype DeadbandValue: Double
    :ivar IndexRange:
    :vartype IndexRange: String
    :ivar SubstituteValue:
    :vartype SubstituteValue: Variant
    :ivar MetaDataProperties:
    :vartype MetaDataProperties: QualifiedName
    """

    data_type = ObjectIds.PublishedVariableDataType

    ua_types = [
        ('PublishedVariable', 'NodeId'),
        ('AttributeId', 'UInt32'),
        ('SamplingIntervalHint', 'Double'),
        ('DeadbandType', 'UInt32'),
        ('DeadbandValue', 'Double'),
        ('IndexRange', 'String'),
        ('SubstituteValue', 'Variant'),
        ('MetaDataProperties', 'ListOfQualifiedName'),
               ]

    def __init__(self):
        self.PublishedVariable = NodeId()
        self.AttributeId = 0
        self.SamplingIntervalHint = 0
        self.DeadbandType = 0
        self.DeadbandValue = 0
        self.IndexRange = None
        self.SubstituteValue = Variant()
        self.MetaDataProperties = []
        self._freeze = True

    def __str__(self):
        return f'PublishedVariableDataType(PublishedVariable:{self.PublishedVariable}, AttributeId:{self.AttributeId}, SamplingIntervalHint:{self.SamplingIntervalHint}, DeadbandType:{self.DeadbandType}, DeadbandValue:{self.DeadbandValue}, IndexRange:{self.IndexRange}, SubstituteValue:{self.SubstituteValue}, MetaDataProperties:{self.MetaDataProperties})'

    __repr__ = __str__


class PublishedDataItemsDataType(FrozenClass):
    """
    :ivar PublishedData:
    :vartype PublishedData: PublishedVariableDataType
    """

    data_type = ObjectIds.PublishedDataItemsDataType

    ua_types = [
        ('PublishedData', 'ListOfPublishedVariableDataType'),
               ]

    def __init__(self):
        self.PublishedData = []
        self._freeze = True

    def __str__(self):
        return f'PublishedDataItemsDataType(PublishedData:{self.PublishedData})'

    __repr__ = __str__


class PublishedEventsDataType(FrozenClass):
    """
    :ivar EventNotifier:
    :vartype EventNotifier: NodeId
    :ivar SelectedFields:
    :vartype SelectedFields: SimpleAttributeOperand
    :ivar Filter:
    :vartype Filter: ContentFilter
    """

    data_type = ObjectIds.PublishedEventsDataType

    ua_types = [
        ('EventNotifier', 'NodeId'),
        ('SelectedFields', 'ListOfSimpleAttributeOperand'),
        ('Filter', 'ContentFilter'),
               ]

    def __init__(self):
        self.EventNotifier = NodeId()
        self.SelectedFields = []
        self.Filter = ContentFilter()
        self._freeze = True

    def __str__(self):
        return f'PublishedEventsDataType(EventNotifier:{self.EventNotifier}, SelectedFields:{self.SelectedFields}, Filter:{self.Filter})'

    __repr__ = __str__


class DataSetWriterDataType(FrozenClass):
    """
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
    :vartype TransportSettings: ExtensionObject
    :ivar MessageSettings:
    :vartype MessageSettings: ExtensionObject
    """

    data_type = ObjectIds.DataSetWriterDataType

    ua_types = [
        ('Name', 'String'),
        ('Enabled', 'Boolean'),
        ('DataSetWriterId', 'UInt16'),
        ('DataSetFieldContentMask', 'DataSetFieldContentMask'),
        ('KeyFrameCount', 'UInt32'),
        ('DataSetName', 'String'),
        ('DataSetWriterProperties', 'ListOfKeyValuePair'),
        ('TransportSettings', 'ExtensionObject'),
        ('MessageSettings', 'ExtensionObject'),
               ]

    def __init__(self):
        self.Name = None
        self.Enabled = True
        self.DataSetWriterId = 0
        self.DataSetFieldContentMask = DataSetFieldContentMask(0)
        self.KeyFrameCount = 0
        self.DataSetName = None
        self.DataSetWriterProperties = []
        self.TransportSettings = ExtensionObject()
        self.MessageSettings = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'DataSetWriterDataType(Name:{self.Name}, Enabled:{self.Enabled}, DataSetWriterId:{self.DataSetWriterId}, DataSetFieldContentMask:{self.DataSetFieldContentMask}, KeyFrameCount:{self.KeyFrameCount}, DataSetName:{self.DataSetName}, DataSetWriterProperties:{self.DataSetWriterProperties}, TransportSettings:{self.TransportSettings}, MessageSettings:{self.MessageSettings})'

    __repr__ = __str__


class DataSetWriterTransportDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.DataSetWriterTransportDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'DataSetWriterTransportDataType()'

    __repr__ = __str__


class DataSetWriterMessageDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.DataSetWriterMessageDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'DataSetWriterMessageDataType()'

    __repr__ = __str__


class PubSubGroupDataType(FrozenClass):
    """
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

    data_type = ObjectIds.PubSubGroupDataType

    ua_types = [
        ('Name', 'String'),
        ('Enabled', 'Boolean'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityGroupId', 'String'),
        ('SecurityKeyServices', 'ListOfEndpointDescription'),
        ('MaxNetworkMessageSize', 'UInt32'),
        ('GroupProperties', 'ListOfKeyValuePair'),
               ]

    def __init__(self):
        self.Name = None
        self.Enabled = True
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityGroupId = None
        self.SecurityKeyServices = []
        self.MaxNetworkMessageSize = 0
        self.GroupProperties = []
        self._freeze = True

    def __str__(self):
        return f'PubSubGroupDataType(Name:{self.Name}, Enabled:{self.Enabled}, SecurityMode:{self.SecurityMode}, SecurityGroupId:{self.SecurityGroupId}, SecurityKeyServices:{self.SecurityKeyServices}, MaxNetworkMessageSize:{self.MaxNetworkMessageSize}, GroupProperties:{self.GroupProperties})'

    __repr__ = __str__


class WriterGroupDataType(FrozenClass):
    """
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
    :vartype PublishingInterval: Double
    :ivar KeepAliveTime:
    :vartype KeepAliveTime: Double
    :ivar Priority:
    :vartype Priority: Byte
    :ivar LocaleIds:
    :vartype LocaleIds: String
    :ivar HeaderLayoutUri:
    :vartype HeaderLayoutUri: String
    :ivar TransportSettings:
    :vartype TransportSettings: ExtensionObject
    :ivar MessageSettings:
    :vartype MessageSettings: ExtensionObject
    :ivar DataSetWriters:
    :vartype DataSetWriters: DataSetWriterDataType
    """

    data_type = ObjectIds.WriterGroupDataType

    ua_types = [
        ('Name', 'String'),
        ('Enabled', 'Boolean'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityGroupId', 'String'),
        ('SecurityKeyServices', 'ListOfEndpointDescription'),
        ('MaxNetworkMessageSize', 'UInt32'),
        ('GroupProperties', 'ListOfKeyValuePair'),
        ('WriterGroupId', 'UInt16'),
        ('PublishingInterval', 'Double'),
        ('KeepAliveTime', 'Double'),
        ('Priority', 'Byte'),
        ('LocaleIds', 'ListOfString'),
        ('HeaderLayoutUri', 'String'),
        ('TransportSettings', 'ExtensionObject'),
        ('MessageSettings', 'ExtensionObject'),
        ('DataSetWriters', 'ListOfDataSetWriterDataType'),
               ]

    def __init__(self):
        self.Name = None
        self.Enabled = True
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityGroupId = None
        self.SecurityKeyServices = []
        self.MaxNetworkMessageSize = 0
        self.GroupProperties = []
        self.WriterGroupId = 0
        self.PublishingInterval = 0
        self.KeepAliveTime = 0
        self.Priority = 0
        self.LocaleIds = []
        self.HeaderLayoutUri = None
        self.TransportSettings = ExtensionObject()
        self.MessageSettings = ExtensionObject()
        self.DataSetWriters = []
        self._freeze = True

    def __str__(self):
        return f'WriterGroupDataType(Name:{self.Name}, Enabled:{self.Enabled}, SecurityMode:{self.SecurityMode}, SecurityGroupId:{self.SecurityGroupId}, SecurityKeyServices:{self.SecurityKeyServices}, MaxNetworkMessageSize:{self.MaxNetworkMessageSize}, GroupProperties:{self.GroupProperties}, WriterGroupId:{self.WriterGroupId}, PublishingInterval:{self.PublishingInterval}, KeepAliveTime:{self.KeepAliveTime}, Priority:{self.Priority}, LocaleIds:{self.LocaleIds}, HeaderLayoutUri:{self.HeaderLayoutUri}, TransportSettings:{self.TransportSettings}, MessageSettings:{self.MessageSettings}, DataSetWriters:{self.DataSetWriters})'

    __repr__ = __str__


class WriterGroupTransportDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.WriterGroupTransportDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'WriterGroupTransportDataType()'

    __repr__ = __str__


class WriterGroupMessageDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.WriterGroupMessageDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'WriterGroupMessageDataType()'

    __repr__ = __str__


class PubSubConnectionDataType(FrozenClass):
    """
    :ivar Name:
    :vartype Name: String
    :ivar Enabled:
    :vartype Enabled: Boolean
    :ivar PublisherId:
    :vartype PublisherId: Variant
    :ivar TransportProfileUri:
    :vartype TransportProfileUri: String
    :ivar Address:
    :vartype Address: ExtensionObject
    :ivar ConnectionProperties:
    :vartype ConnectionProperties: KeyValuePair
    :ivar TransportSettings:
    :vartype TransportSettings: ExtensionObject
    :ivar WriterGroups:
    :vartype WriterGroups: WriterGroupDataType
    :ivar ReaderGroups:
    :vartype ReaderGroups: ReaderGroupDataType
    """

    data_type = ObjectIds.PubSubConnectionDataType

    ua_types = [
        ('Name', 'String'),
        ('Enabled', 'Boolean'),
        ('PublisherId', 'Variant'),
        ('TransportProfileUri', 'String'),
        ('Address', 'ExtensionObject'),
        ('ConnectionProperties', 'ListOfKeyValuePair'),
        ('TransportSettings', 'ExtensionObject'),
        ('WriterGroups', 'ListOfWriterGroupDataType'),
        ('ReaderGroups', 'ListOfReaderGroupDataType'),
               ]

    def __init__(self):
        self.Name = None
        self.Enabled = True
        self.PublisherId = Variant()
        self.TransportProfileUri = None
        self.Address = ExtensionObject()
        self.ConnectionProperties = []
        self.TransportSettings = ExtensionObject()
        self.WriterGroups = []
        self.ReaderGroups = []
        self._freeze = True

    def __str__(self):
        return f'PubSubConnectionDataType(Name:{self.Name}, Enabled:{self.Enabled}, PublisherId:{self.PublisherId}, TransportProfileUri:{self.TransportProfileUri}, Address:{self.Address}, ConnectionProperties:{self.ConnectionProperties}, TransportSettings:{self.TransportSettings}, WriterGroups:{self.WriterGroups}, ReaderGroups:{self.ReaderGroups})'

    __repr__ = __str__


class ConnectionTransportDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.ConnectionTransportDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'ConnectionTransportDataType()'

    __repr__ = __str__


class NetworkAddressDataType(FrozenClass):
    """
    :ivar NetworkInterface:
    :vartype NetworkInterface: String
    """

    data_type = ObjectIds.NetworkAddressDataType

    ua_types = [
        ('NetworkInterface', 'String'),
               ]

    def __init__(self):
        self.NetworkInterface = None
        self._freeze = True

    def __str__(self):
        return f'NetworkAddressDataType(NetworkInterface:{self.NetworkInterface})'

    __repr__ = __str__


class NetworkAddressUrlDataType(FrozenClass):
    """
    :ivar NetworkInterface:
    :vartype NetworkInterface: String
    :ivar Url:
    :vartype Url: String
    """

    data_type = ObjectIds.NetworkAddressUrlDataType

    ua_types = [
        ('NetworkInterface', 'String'),
        ('Url', 'String'),
               ]

    def __init__(self):
        self.NetworkInterface = None
        self.Url = None
        self._freeze = True

    def __str__(self):
        return f'NetworkAddressUrlDataType(NetworkInterface:{self.NetworkInterface}, Url:{self.Url})'

    __repr__ = __str__


class ReaderGroupDataType(FrozenClass):
    """
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
    :vartype TransportSettings: ExtensionObject
    :ivar MessageSettings:
    :vartype MessageSettings: ExtensionObject
    :ivar DataSetReaders:
    :vartype DataSetReaders: DataSetReaderDataType
    """

    data_type = ObjectIds.ReaderGroupDataType

    ua_types = [
        ('Name', 'String'),
        ('Enabled', 'Boolean'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityGroupId', 'String'),
        ('SecurityKeyServices', 'ListOfEndpointDescription'),
        ('MaxNetworkMessageSize', 'UInt32'),
        ('GroupProperties', 'ListOfKeyValuePair'),
        ('TransportSettings', 'ExtensionObject'),
        ('MessageSettings', 'ExtensionObject'),
        ('DataSetReaders', 'ListOfDataSetReaderDataType'),
               ]

    def __init__(self):
        self.Name = None
        self.Enabled = True
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityGroupId = None
        self.SecurityKeyServices = []
        self.MaxNetworkMessageSize = 0
        self.GroupProperties = []
        self.TransportSettings = ExtensionObject()
        self.MessageSettings = ExtensionObject()
        self.DataSetReaders = []
        self._freeze = True

    def __str__(self):
        return f'ReaderGroupDataType(Name:{self.Name}, Enabled:{self.Enabled}, SecurityMode:{self.SecurityMode}, SecurityGroupId:{self.SecurityGroupId}, SecurityKeyServices:{self.SecurityKeyServices}, MaxNetworkMessageSize:{self.MaxNetworkMessageSize}, GroupProperties:{self.GroupProperties}, TransportSettings:{self.TransportSettings}, MessageSettings:{self.MessageSettings}, DataSetReaders:{self.DataSetReaders})'

    __repr__ = __str__


class ReaderGroupTransportDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.ReaderGroupTransportDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'ReaderGroupTransportDataType()'

    __repr__ = __str__


class ReaderGroupMessageDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.ReaderGroupMessageDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'ReaderGroupMessageDataType()'

    __repr__ = __str__


class DataSetReaderDataType(FrozenClass):
    """
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
    :vartype MessageReceiveTimeout: Double
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
    :vartype TransportSettings: ExtensionObject
    :ivar MessageSettings:
    :vartype MessageSettings: ExtensionObject
    :ivar SubscribedDataSet:
    :vartype SubscribedDataSet: ExtensionObject
    """

    data_type = ObjectIds.DataSetReaderDataType

    ua_types = [
        ('Name', 'String'),
        ('Enabled', 'Boolean'),
        ('PublisherId', 'Variant'),
        ('WriterGroupId', 'UInt16'),
        ('DataSetWriterId', 'UInt16'),
        ('DataSetMetaData', 'DataSetMetaDataType'),
        ('DataSetFieldContentMask', 'DataSetFieldContentMask'),
        ('MessageReceiveTimeout', 'Double'),
        ('KeyFrameCount', 'UInt32'),
        ('HeaderLayoutUri', 'String'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityGroupId', 'String'),
        ('SecurityKeyServices', 'ListOfEndpointDescription'),
        ('DataSetReaderProperties', 'ListOfKeyValuePair'),
        ('TransportSettings', 'ExtensionObject'),
        ('MessageSettings', 'ExtensionObject'),
        ('SubscribedDataSet', 'ExtensionObject'),
               ]

    def __init__(self):
        self.Name = None
        self.Enabled = True
        self.PublisherId = Variant()
        self.WriterGroupId = 0
        self.DataSetWriterId = 0
        self.DataSetMetaData = DataSetMetaDataType()
        self.DataSetFieldContentMask = DataSetFieldContentMask(0)
        self.MessageReceiveTimeout = 0
        self.KeyFrameCount = 0
        self.HeaderLayoutUri = None
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityGroupId = None
        self.SecurityKeyServices = []
        self.DataSetReaderProperties = []
        self.TransportSettings = ExtensionObject()
        self.MessageSettings = ExtensionObject()
        self.SubscribedDataSet = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'DataSetReaderDataType(Name:{self.Name}, Enabled:{self.Enabled}, PublisherId:{self.PublisherId}, WriterGroupId:{self.WriterGroupId}, DataSetWriterId:{self.DataSetWriterId}, DataSetMetaData:{self.DataSetMetaData}, DataSetFieldContentMask:{self.DataSetFieldContentMask}, MessageReceiveTimeout:{self.MessageReceiveTimeout}, KeyFrameCount:{self.KeyFrameCount}, HeaderLayoutUri:{self.HeaderLayoutUri}, SecurityMode:{self.SecurityMode}, SecurityGroupId:{self.SecurityGroupId}, SecurityKeyServices:{self.SecurityKeyServices}, DataSetReaderProperties:{self.DataSetReaderProperties}, TransportSettings:{self.TransportSettings}, MessageSettings:{self.MessageSettings}, SubscribedDataSet:{self.SubscribedDataSet})'

    __repr__ = __str__


class DataSetReaderTransportDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.DataSetReaderTransportDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'DataSetReaderTransportDataType()'

    __repr__ = __str__


class DataSetReaderMessageDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.DataSetReaderMessageDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'DataSetReaderMessageDataType()'

    __repr__ = __str__


class SubscribedDataSetDataType(FrozenClass):
    """
    """

    data_type = ObjectIds.SubscribedDataSetDataType

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'SubscribedDataSetDataType()'

    __repr__ = __str__


class TargetVariablesDataType(FrozenClass):
    """
    :ivar TargetVariables:
    :vartype TargetVariables: FieldTargetDataType
    """

    data_type = ObjectIds.TargetVariablesDataType

    ua_types = [
        ('TargetVariables', 'ListOfFieldTargetDataType'),
               ]

    def __init__(self):
        self.TargetVariables = []
        self._freeze = True

    def __str__(self):
        return f'TargetVariablesDataType(TargetVariables:{self.TargetVariables})'

    __repr__ = __str__


class FieldTargetDataType(FrozenClass):
    """
    :ivar DataSetFieldId:
    :vartype DataSetFieldId: Guid
    :ivar ReceiverIndexRange:
    :vartype ReceiverIndexRange: String
    :ivar TargetNodeId:
    :vartype TargetNodeId: NodeId
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar WriteIndexRange:
    :vartype WriteIndexRange: String
    :ivar OverrideValueHandling:
    :vartype OverrideValueHandling: OverrideValueHandling
    :ivar OverrideValue:
    :vartype OverrideValue: Variant
    """

    data_type = ObjectIds.FieldTargetDataType

    ua_types = [
        ('DataSetFieldId', 'Guid'),
        ('ReceiverIndexRange', 'String'),
        ('TargetNodeId', 'NodeId'),
        ('AttributeId', 'UInt32'),
        ('WriteIndexRange', 'String'),
        ('OverrideValueHandling', 'OverrideValueHandling'),
        ('OverrideValue', 'Variant'),
               ]

    def __init__(self):
        self.DataSetFieldId = Guid()
        self.ReceiverIndexRange = None
        self.TargetNodeId = NodeId()
        self.AttributeId = 0
        self.WriteIndexRange = None
        self.OverrideValueHandling = OverrideValueHandling(0)
        self.OverrideValue = Variant()
        self._freeze = True

    def __str__(self):
        return f'FieldTargetDataType(DataSetFieldId:{self.DataSetFieldId}, ReceiverIndexRange:{self.ReceiverIndexRange}, TargetNodeId:{self.TargetNodeId}, AttributeId:{self.AttributeId}, WriteIndexRange:{self.WriteIndexRange}, OverrideValueHandling:{self.OverrideValueHandling}, OverrideValue:{self.OverrideValue})'

    __repr__ = __str__


class SubscribedDataSetMirrorDataType(FrozenClass):
    """
    :ivar ParentNodeName:
    :vartype ParentNodeName: String
    :ivar RolePermissions:
    :vartype RolePermissions: RolePermissionType
    """

    data_type = ObjectIds.SubscribedDataSetMirrorDataType

    ua_types = [
        ('ParentNodeName', 'String'),
        ('RolePermissions', 'ListOfRolePermissionType'),
               ]

    def __init__(self):
        self.ParentNodeName = None
        self.RolePermissions = []
        self._freeze = True

    def __str__(self):
        return f'SubscribedDataSetMirrorDataType(ParentNodeName:{self.ParentNodeName}, RolePermissions:{self.RolePermissions})'

    __repr__ = __str__


class PubSubConfigurationDataType(FrozenClass):
    """
    :ivar PublishedDataSets:
    :vartype PublishedDataSets: PublishedDataSetDataType
    :ivar Connections:
    :vartype Connections: PubSubConnectionDataType
    :ivar Enabled:
    :vartype Enabled: Boolean
    """

    data_type = ObjectIds.PubSubConfigurationDataType

    ua_types = [
        ('PublishedDataSets', 'ListOfPublishedDataSetDataType'),
        ('Connections', 'ListOfPubSubConnectionDataType'),
        ('Enabled', 'Boolean'),
               ]

    def __init__(self):
        self.PublishedDataSets = []
        self.Connections = []
        self.Enabled = True
        self._freeze = True

    def __str__(self):
        return f'PubSubConfigurationDataType(PublishedDataSets:{self.PublishedDataSets}, Connections:{self.Connections}, Enabled:{self.Enabled})'

    __repr__ = __str__


class UadpWriterGroupMessageDataType(FrozenClass):
    """
    :ivar GroupVersion:
    :vartype GroupVersion: UInt32
    :ivar DataSetOrdering:
    :vartype DataSetOrdering: DataSetOrderingType
    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: UadpNetworkMessageContentMask
    :ivar SamplingOffset:
    :vartype SamplingOffset: Double
    :ivar PublishingOffset:
    :vartype PublishingOffset: Double
    """

    data_type = ObjectIds.UadpWriterGroupMessageDataType

    ua_types = [
        ('GroupVersion', 'UInt32'),
        ('DataSetOrdering', 'DataSetOrderingType'),
        ('NetworkMessageContentMask', 'UadpNetworkMessageContentMask'),
        ('SamplingOffset', 'Double'),
        ('PublishingOffset', 'ListOfDouble'),
               ]

    def __init__(self):
        self.GroupVersion = 0
        self.DataSetOrdering = DataSetOrderingType(0)
        self.NetworkMessageContentMask = UadpNetworkMessageContentMask(0)
        self.SamplingOffset = 0
        self.PublishingOffset = []
        self._freeze = True

    def __str__(self):
        return f'UadpWriterGroupMessageDataType(GroupVersion:{self.GroupVersion}, DataSetOrdering:{self.DataSetOrdering}, NetworkMessageContentMask:{self.NetworkMessageContentMask}, SamplingOffset:{self.SamplingOffset}, PublishingOffset:{self.PublishingOffset})'

    __repr__ = __str__


class UadpDataSetWriterMessageDataType(FrozenClass):
    """
    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: UadpDataSetMessageContentMask
    :ivar ConfiguredSize:
    :vartype ConfiguredSize: UInt16
    :ivar NetworkMessageNumber:
    :vartype NetworkMessageNumber: UInt16
    :ivar DataSetOffset:
    :vartype DataSetOffset: UInt16
    """

    data_type = ObjectIds.UadpDataSetWriterMessageDataType

    ua_types = [
        ('DataSetMessageContentMask', 'UadpDataSetMessageContentMask'),
        ('ConfiguredSize', 'UInt16'),
        ('NetworkMessageNumber', 'UInt16'),
        ('DataSetOffset', 'UInt16'),
               ]

    def __init__(self):
        self.DataSetMessageContentMask = UadpDataSetMessageContentMask(0)
        self.ConfiguredSize = 0
        self.NetworkMessageNumber = 0
        self.DataSetOffset = 0
        self._freeze = True

    def __str__(self):
        return f'UadpDataSetWriterMessageDataType(DataSetMessageContentMask:{self.DataSetMessageContentMask}, ConfiguredSize:{self.ConfiguredSize}, NetworkMessageNumber:{self.NetworkMessageNumber}, DataSetOffset:{self.DataSetOffset})'

    __repr__ = __str__


class UadpDataSetReaderMessageDataType(FrozenClass):
    """
    :ivar GroupVersion:
    :vartype GroupVersion: UInt32
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
    :vartype PublishingInterval: Double
    :ivar ReceiveOffset:
    :vartype ReceiveOffset: Double
    :ivar ProcessingOffset:
    :vartype ProcessingOffset: Double
    """

    data_type = ObjectIds.UadpDataSetReaderMessageDataType

    ua_types = [
        ('GroupVersion', 'UInt32'),
        ('NetworkMessageNumber', 'UInt16'),
        ('DataSetOffset', 'UInt16'),
        ('DataSetClassId', 'Guid'),
        ('NetworkMessageContentMask', 'UadpNetworkMessageContentMask'),
        ('DataSetMessageContentMask', 'UadpDataSetMessageContentMask'),
        ('PublishingInterval', 'Double'),
        ('ReceiveOffset', 'Double'),
        ('ProcessingOffset', 'Double'),
               ]

    def __init__(self):
        self.GroupVersion = 0
        self.NetworkMessageNumber = 0
        self.DataSetOffset = 0
        self.DataSetClassId = Guid()
        self.NetworkMessageContentMask = UadpNetworkMessageContentMask(0)
        self.DataSetMessageContentMask = UadpDataSetMessageContentMask(0)
        self.PublishingInterval = 0
        self.ReceiveOffset = 0
        self.ProcessingOffset = 0
        self._freeze = True

    def __str__(self):
        return f'UadpDataSetReaderMessageDataType(GroupVersion:{self.GroupVersion}, NetworkMessageNumber:{self.NetworkMessageNumber}, DataSetOffset:{self.DataSetOffset}, DataSetClassId:{self.DataSetClassId}, NetworkMessageContentMask:{self.NetworkMessageContentMask}, DataSetMessageContentMask:{self.DataSetMessageContentMask}, PublishingInterval:{self.PublishingInterval}, ReceiveOffset:{self.ReceiveOffset}, ProcessingOffset:{self.ProcessingOffset})'

    __repr__ = __str__


class JsonWriterGroupMessageDataType(FrozenClass):
    """
    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: JsonNetworkMessageContentMask
    """

    data_type = ObjectIds.JsonWriterGroupMessageDataType

    ua_types = [
        ('NetworkMessageContentMask', 'JsonNetworkMessageContentMask'),
               ]

    def __init__(self):
        self.NetworkMessageContentMask = JsonNetworkMessageContentMask(0)
        self._freeze = True

    def __str__(self):
        return f'JsonWriterGroupMessageDataType(NetworkMessageContentMask:{self.NetworkMessageContentMask})'

    __repr__ = __str__


class JsonDataSetWriterMessageDataType(FrozenClass):
    """
    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: JsonDataSetMessageContentMask
    """

    data_type = ObjectIds.JsonDataSetWriterMessageDataType

    ua_types = [
        ('DataSetMessageContentMask', 'JsonDataSetMessageContentMask'),
               ]

    def __init__(self):
        self.DataSetMessageContentMask = JsonDataSetMessageContentMask(0)
        self._freeze = True

    def __str__(self):
        return f'JsonDataSetWriterMessageDataType(DataSetMessageContentMask:{self.DataSetMessageContentMask})'

    __repr__ = __str__


class JsonDataSetReaderMessageDataType(FrozenClass):
    """
    :ivar NetworkMessageContentMask:
    :vartype NetworkMessageContentMask: JsonNetworkMessageContentMask
    :ivar DataSetMessageContentMask:
    :vartype DataSetMessageContentMask: JsonDataSetMessageContentMask
    """

    data_type = ObjectIds.JsonDataSetReaderMessageDataType

    ua_types = [
        ('NetworkMessageContentMask', 'JsonNetworkMessageContentMask'),
        ('DataSetMessageContentMask', 'JsonDataSetMessageContentMask'),
               ]

    def __init__(self):
        self.NetworkMessageContentMask = JsonNetworkMessageContentMask(0)
        self.DataSetMessageContentMask = JsonDataSetMessageContentMask(0)
        self._freeze = True

    def __str__(self):
        return f'JsonDataSetReaderMessageDataType(NetworkMessageContentMask:{self.NetworkMessageContentMask}, DataSetMessageContentMask:{self.DataSetMessageContentMask})'

    __repr__ = __str__


class DatagramConnectionTransportDataType(FrozenClass):
    """
    :ivar DiscoveryAddress:
    :vartype DiscoveryAddress: ExtensionObject
    """

    data_type = ObjectIds.DatagramConnectionTransportDataType

    ua_types = [
        ('DiscoveryAddress', 'ExtensionObject'),
               ]

    def __init__(self):
        self.DiscoveryAddress = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'DatagramConnectionTransportDataType(DiscoveryAddress:{self.DiscoveryAddress})'

    __repr__ = __str__


class DatagramWriterGroupTransportDataType(FrozenClass):
    """
    :ivar MessageRepeatCount:
    :vartype MessageRepeatCount: Byte
    :ivar MessageRepeatDelay:
    :vartype MessageRepeatDelay: Double
    """

    data_type = ObjectIds.DatagramWriterGroupTransportDataType

    ua_types = [
        ('MessageRepeatCount', 'Byte'),
        ('MessageRepeatDelay', 'Double'),
               ]

    def __init__(self):
        self.MessageRepeatCount = 0
        self.MessageRepeatDelay = 0
        self._freeze = True

    def __str__(self):
        return f'DatagramWriterGroupTransportDataType(MessageRepeatCount:{self.MessageRepeatCount}, MessageRepeatDelay:{self.MessageRepeatDelay})'

    __repr__ = __str__


class BrokerConnectionTransportDataType(FrozenClass):
    """
    :ivar ResourceUri:
    :vartype ResourceUri: String
    :ivar AuthenticationProfileUri:
    :vartype AuthenticationProfileUri: String
    """

    data_type = ObjectIds.BrokerConnectionTransportDataType

    ua_types = [
        ('ResourceUri', 'String'),
        ('AuthenticationProfileUri', 'String'),
               ]

    def __init__(self):
        self.ResourceUri = None
        self.AuthenticationProfileUri = None
        self._freeze = True

    def __str__(self):
        return f'BrokerConnectionTransportDataType(ResourceUri:{self.ResourceUri}, AuthenticationProfileUri:{self.AuthenticationProfileUri})'

    __repr__ = __str__


class BrokerWriterGroupTransportDataType(FrozenClass):
    """
    :ivar QueueName:
    :vartype QueueName: String
    :ivar ResourceUri:
    :vartype ResourceUri: String
    :ivar AuthenticationProfileUri:
    :vartype AuthenticationProfileUri: String
    :ivar RequestedDeliveryGuarantee:
    :vartype RequestedDeliveryGuarantee: BrokerTransportQualityOfService
    """

    data_type = ObjectIds.BrokerWriterGroupTransportDataType

    ua_types = [
        ('QueueName', 'String'),
        ('ResourceUri', 'String'),
        ('AuthenticationProfileUri', 'String'),
        ('RequestedDeliveryGuarantee', 'BrokerTransportQualityOfService'),
               ]

    def __init__(self):
        self.QueueName = None
        self.ResourceUri = None
        self.AuthenticationProfileUri = None
        self.RequestedDeliveryGuarantee = BrokerTransportQualityOfService(0)
        self._freeze = True

    def __str__(self):
        return f'BrokerWriterGroupTransportDataType(QueueName:{self.QueueName}, ResourceUri:{self.ResourceUri}, AuthenticationProfileUri:{self.AuthenticationProfileUri}, RequestedDeliveryGuarantee:{self.RequestedDeliveryGuarantee})'

    __repr__ = __str__


class BrokerDataSetWriterTransportDataType(FrozenClass):
    """
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
    :vartype MetaDataUpdateTime: Double
    """

    data_type = ObjectIds.BrokerDataSetWriterTransportDataType

    ua_types = [
        ('QueueName', 'String'),
        ('ResourceUri', 'String'),
        ('AuthenticationProfileUri', 'String'),
        ('RequestedDeliveryGuarantee', 'BrokerTransportQualityOfService'),
        ('MetaDataQueueName', 'String'),
        ('MetaDataUpdateTime', 'Double'),
               ]

    def __init__(self):
        self.QueueName = None
        self.ResourceUri = None
        self.AuthenticationProfileUri = None
        self.RequestedDeliveryGuarantee = BrokerTransportQualityOfService(0)
        self.MetaDataQueueName = None
        self.MetaDataUpdateTime = 0
        self._freeze = True

    def __str__(self):
        return f'BrokerDataSetWriterTransportDataType(QueueName:{self.QueueName}, ResourceUri:{self.ResourceUri}, AuthenticationProfileUri:{self.AuthenticationProfileUri}, RequestedDeliveryGuarantee:{self.RequestedDeliveryGuarantee}, MetaDataQueueName:{self.MetaDataQueueName}, MetaDataUpdateTime:{self.MetaDataUpdateTime})'

    __repr__ = __str__


class BrokerDataSetReaderTransportDataType(FrozenClass):
    """
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

    data_type = ObjectIds.BrokerDataSetReaderTransportDataType

    ua_types = [
        ('QueueName', 'String'),
        ('ResourceUri', 'String'),
        ('AuthenticationProfileUri', 'String'),
        ('RequestedDeliveryGuarantee', 'BrokerTransportQualityOfService'),
        ('MetaDataQueueName', 'String'),
               ]

    def __init__(self):
        self.QueueName = None
        self.ResourceUri = None
        self.AuthenticationProfileUri = None
        self.RequestedDeliveryGuarantee = BrokerTransportQualityOfService(0)
        self.MetaDataQueueName = None
        self._freeze = True

    def __str__(self):
        return f'BrokerDataSetReaderTransportDataType(QueueName:{self.QueueName}, ResourceUri:{self.ResourceUri}, AuthenticationProfileUri:{self.AuthenticationProfileUri}, RequestedDeliveryGuarantee:{self.RequestedDeliveryGuarantee}, MetaDataQueueName:{self.MetaDataQueueName})'

    __repr__ = __str__


class AliasNameDataType(FrozenClass):
    """
    :ivar AliasName:
    :vartype AliasName: QualifiedName
    :ivar ReferencedNodes:
    :vartype ReferencedNodes: ExpandedNodeId
    """

    data_type = ObjectIds.AliasNameDataType

    ua_types = [
        ('AliasName', 'QualifiedName'),
        ('ReferencedNodes', 'ListOfExpandedNodeId'),
               ]

    def __init__(self):
        self.AliasName = QualifiedName()
        self.ReferencedNodes = []
        self._freeze = True

    def __str__(self):
        return f'AliasNameDataType(AliasName:{self.AliasName}, ReferencedNodes:{self.ReferencedNodes})'

    __repr__ = __str__


class RolePermissionType(FrozenClass):
    """
    :ivar RoleId:
    :vartype RoleId: NodeId
    :ivar Permissions:
    :vartype Permissions: PermissionType
    """

    data_type = ObjectIds.RolePermissionType

    ua_types = [
        ('RoleId', 'NodeId'),
        ('Permissions', 'PermissionType'),
               ]

    def __init__(self):
        self.RoleId = NodeId()
        self.Permissions = PermissionType(0)
        self._freeze = True

    def __str__(self):
        return f'RolePermissionType(RoleId:{self.RoleId}, Permissions:{self.Permissions})'

    __repr__ = __str__


class StructureField(FrozenClass):
    """
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

    data_type = ObjectIds.StructureField

    ua_types = [
        ('Name', 'String'),
        ('Description', 'LocalizedText'),
        ('DataType', 'NodeId'),
        ('ValueRank', 'Int32'),
        ('ArrayDimensions', 'ListOfUInt32'),
        ('MaxStringLength', 'UInt32'),
        ('IsOptional', 'Boolean'),
               ]

    def __init__(self):
        self.Name = None
        self.Description = LocalizedText()
        self.DataType = NodeId()
        self.ValueRank = 0
        self.ArrayDimensions = []
        self.MaxStringLength = 0
        self.IsOptional = True
        self._freeze = True

    def __str__(self):
        return f'StructureField(Name:{self.Name}, Description:{self.Description}, DataType:{self.DataType}, ValueRank:{self.ValueRank}, ArrayDimensions:{self.ArrayDimensions}, MaxStringLength:{self.MaxStringLength}, IsOptional:{self.IsOptional})'

    __repr__ = __str__


class StructureDefinition(FrozenClass):
    """
    :ivar DefaultEncodingId:
    :vartype DefaultEncodingId: NodeId
    :ivar BaseDataType:
    :vartype BaseDataType: NodeId
    :ivar StructureType:
    :vartype StructureType: StructureType
    :ivar Fields:
    :vartype Fields: StructureField
    """

    data_type = ObjectIds.StructureDefinition

    ua_types = [
        ('DefaultEncodingId', 'NodeId'),
        ('BaseDataType', 'NodeId'),
        ('StructureType', 'StructureType'),
        ('Fields', 'ListOfStructureField'),
               ]

    def __init__(self):
        self.DefaultEncodingId = NodeId()
        self.BaseDataType = NodeId()
        self.StructureType = StructureType(0)
        self.Fields = []
        self._freeze = True

    def __str__(self):
        return f'StructureDefinition(DefaultEncodingId:{self.DefaultEncodingId}, BaseDataType:{self.BaseDataType}, StructureType:{self.StructureType}, Fields:{self.Fields})'

    __repr__ = __str__


class EnumDefinition(FrozenClass):
    """
    :ivar Fields:
    :vartype Fields: EnumField
    """

    data_type = ObjectIds.EnumDefinition

    ua_types = [
        ('Fields', 'ListOfEnumField'),
               ]

    def __init__(self):
        self.Fields = []
        self._freeze = True

    def __str__(self):
        return f'EnumDefinition(Fields:{self.Fields})'

    __repr__ = __str__


class Argument(FrozenClass):
    """
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

    data_type = ObjectIds.Argument

    ua_types = [
        ('Name', 'String'),
        ('DataType', 'NodeId'),
        ('ValueRank', 'Int32'),
        ('ArrayDimensions', 'ListOfUInt32'),
        ('Description', 'LocalizedText'),
               ]

    def __init__(self):
        self.Name = None
        self.DataType = NodeId()
        self.ValueRank = 0
        self.ArrayDimensions = []
        self.Description = LocalizedText()
        self._freeze = True

    def __str__(self):
        return f'Argument(Name:{self.Name}, DataType:{self.DataType}, ValueRank:{self.ValueRank}, ArrayDimensions:{self.ArrayDimensions}, Description:{self.Description})'

    __repr__ = __str__


class EnumValueType(FrozenClass):
    """
    :ivar Value:
    :vartype Value: Int64
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    """

    data_type = ObjectIds.EnumValueType

    ua_types = [
        ('Value', 'Int64'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
               ]

    def __init__(self):
        self.Value = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self._freeze = True

    def __str__(self):
        return f'EnumValueType(Value:{self.Value}, DisplayName:{self.DisplayName}, Description:{self.Description})'

    __repr__ = __str__


class EnumField(FrozenClass):
    """
    :ivar Value:
    :vartype Value: Int64
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    :ivar Name:
    :vartype Name: String
    """

    data_type = ObjectIds.EnumField

    ua_types = [
        ('Value', 'Int64'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('Name', 'String'),
               ]

    def __init__(self):
        self.Value = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.Name = None
        self._freeze = True

    def __str__(self):
        return f'EnumField(Value:{self.Value}, DisplayName:{self.DisplayName}, Description:{self.Description}, Name:{self.Name})'

    __repr__ = __str__


class OptionSet(FrozenClass):
    """
    :ivar Value:
    :vartype Value: ByteString
    :ivar ValidBits:
    :vartype ValidBits: ByteString
    """

    data_type = ObjectIds.OptionSet

    ua_types = [
        ('Value', 'ByteString'),
        ('ValidBits', 'ByteString'),
               ]

    def __init__(self):
        self.Value = None
        self.ValidBits = None
        self._freeze = True

    def __str__(self):
        return f'OptionSet(Value:{self.Value}, ValidBits:{self.ValidBits})'

    __repr__ = __str__


class Union(FrozenClass):
    """
    """

    data_type = ObjectIds.Union

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'Union()'

    __repr__ = __str__


class TimeZoneDataType(FrozenClass):
    """
    :ivar Offset:
    :vartype Offset: Int16
    :ivar DaylightSavingInOffset:
    :vartype DaylightSavingInOffset: Boolean
    """

    data_type = ObjectIds.TimeZoneDataType

    ua_types = [
        ('Offset', 'Int16'),
        ('DaylightSavingInOffset', 'Boolean'),
               ]

    def __init__(self):
        self.Offset = 0
        self.DaylightSavingInOffset = True
        self._freeze = True

    def __str__(self):
        return f'TimeZoneDataType(Offset:{self.Offset}, DaylightSavingInOffset:{self.DaylightSavingInOffset})'

    __repr__ = __str__


class ApplicationDescription(FrozenClass):
    """
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

    data_type = ObjectIds.ApplicationDescription

    ua_types = [
        ('ApplicationUri', 'String'),
        ('ProductUri', 'String'),
        ('ApplicationName', 'LocalizedText'),
        ('ApplicationType', 'ApplicationType'),
        ('GatewayServerUri', 'String'),
        ('DiscoveryProfileUri', 'String'),
        ('DiscoveryUrls', 'ListOfString'),
               ]

    def __init__(self):
        self.ApplicationUri = None
        self.ProductUri = None
        self.ApplicationName = LocalizedText()
        self.ApplicationType = ApplicationType(0)
        self.GatewayServerUri = None
        self.DiscoveryProfileUri = None
        self.DiscoveryUrls = []
        self._freeze = True

    def __str__(self):
        return f'ApplicationDescription(ApplicationUri:{self.ApplicationUri}, ProductUri:{self.ProductUri}, ApplicationName:{self.ApplicationName}, ApplicationType:{self.ApplicationType}, GatewayServerUri:{self.GatewayServerUri}, DiscoveryProfileUri:{self.DiscoveryProfileUri}, DiscoveryUrls:{self.DiscoveryUrls})'

    __repr__ = __str__


class RequestHeader(FrozenClass):
    """
    :ivar AuthenticationToken:
    :vartype AuthenticationToken: NodeId
    :ivar Timestamp:
    :vartype Timestamp: DateTime
    :ivar RequestHandle:
    :vartype RequestHandle: UInt32
    :ivar ReturnDiagnostics:
    :vartype ReturnDiagnostics: UInt32
    :ivar AuditEntryId:
    :vartype AuditEntryId: String
    :ivar TimeoutHint:
    :vartype TimeoutHint: UInt32
    :ivar AdditionalHeader:
    :vartype AdditionalHeader: ExtensionObject
    """

    data_type = ObjectIds.RequestHeader

    ua_types = [
        ('AuthenticationToken', 'NodeId'),
        ('Timestamp', 'DateTime'),
        ('RequestHandle', 'UInt32'),
        ('ReturnDiagnostics', 'UInt32'),
        ('AuditEntryId', 'String'),
        ('TimeoutHint', 'UInt32'),
        ('AdditionalHeader', 'ExtensionObject'),
               ]

    def __init__(self):
        self.AuthenticationToken = NodeId()
        self.Timestamp = datetime.utcnow()
        self.RequestHandle = 0
        self.ReturnDiagnostics = 0
        self.AuditEntryId = None
        self.TimeoutHint = 0
        self.AdditionalHeader = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'RequestHeader(AuthenticationToken:{self.AuthenticationToken}, Timestamp:{self.Timestamp}, RequestHandle:{self.RequestHandle}, ReturnDiagnostics:{self.ReturnDiagnostics}, AuditEntryId:{self.AuditEntryId}, TimeoutHint:{self.TimeoutHint}, AdditionalHeader:{self.AdditionalHeader})'

    __repr__ = __str__


class ResponseHeader(FrozenClass):
    """
    :ivar Timestamp:
    :vartype Timestamp: DateTime
    :ivar RequestHandle:
    :vartype RequestHandle: UInt32
    :ivar ServiceResult:
    :vartype ServiceResult: StatusCode
    :ivar ServiceDiagnostics:
    :vartype ServiceDiagnostics: DiagnosticInfo
    :ivar StringTable:
    :vartype StringTable: String
    :ivar AdditionalHeader:
    :vartype AdditionalHeader: ExtensionObject
    """

    data_type = ObjectIds.ResponseHeader

    ua_types = [
        ('Timestamp', 'DateTime'),
        ('RequestHandle', 'UInt32'),
        ('ServiceResult', 'StatusCode'),
        ('ServiceDiagnostics', 'DiagnosticInfo'),
        ('StringTable', 'ListOfString'),
        ('AdditionalHeader', 'ExtensionObject'),
               ]

    def __init__(self):
        self.Timestamp = datetime.utcnow()
        self.RequestHandle = 0
        self.ServiceResult = StatusCode()
        self.ServiceDiagnostics = DiagnosticInfo()
        self.StringTable = []
        self.AdditionalHeader = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'ResponseHeader(Timestamp:{self.Timestamp}, RequestHandle:{self.RequestHandle}, ServiceResult:{self.ServiceResult}, ServiceDiagnostics:{self.ServiceDiagnostics}, StringTable:{self.StringTable}, AdditionalHeader:{self.AdditionalHeader})'

    __repr__ = __str__


class ServiceFault(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = ObjectIds.ServiceFault

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ServiceFault_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self._freeze = True

    def __str__(self):
        return f'ServiceFault(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader})'

    __repr__ = __str__


class SessionlessInvokeRequestType(FrozenClass):
    """
    :ivar UrisVersion:
    :vartype UrisVersion: UInt32
    :ivar NamespaceUris:
    :vartype NamespaceUris: String
    :ivar ServerUris:
    :vartype ServerUris: String
    :ivar LocaleIds:
    :vartype LocaleIds: String
    :ivar ServiceId:
    :vartype ServiceId: UInt32
    """

    data_type = ObjectIds.SessionlessInvokeRequestType

    ua_types = [
        ('UrisVersion', 'ListOfUInt32'),
        ('NamespaceUris', 'ListOfString'),
        ('ServerUris', 'ListOfString'),
        ('LocaleIds', 'ListOfString'),
        ('ServiceId', 'UInt32'),
               ]

    def __init__(self):
        self.UrisVersion = []
        self.NamespaceUris = []
        self.ServerUris = []
        self.LocaleIds = []
        self.ServiceId = 0
        self._freeze = True

    def __str__(self):
        return f'SessionlessInvokeRequestType(UrisVersion:{self.UrisVersion}, NamespaceUris:{self.NamespaceUris}, ServerUris:{self.ServerUris}, LocaleIds:{self.LocaleIds}, ServiceId:{self.ServiceId})'

    __repr__ = __str__


class SessionlessInvokeResponseType(FrozenClass):
    """
    :ivar NamespaceUris:
    :vartype NamespaceUris: String
    :ivar ServerUris:
    :vartype ServerUris: String
    :ivar ServiceId:
    :vartype ServiceId: UInt32
    """

    data_type = ObjectIds.SessionlessInvokeResponseType

    ua_types = [
        ('NamespaceUris', 'ListOfString'),
        ('ServerUris', 'ListOfString'),
        ('ServiceId', 'UInt32'),
               ]

    def __init__(self):
        self.NamespaceUris = []
        self.ServerUris = []
        self.ServiceId = 0
        self._freeze = True

    def __str__(self):
        return f'SessionlessInvokeResponseType(NamespaceUris:{self.NamespaceUris}, ServerUris:{self.ServerUris}, ServiceId:{self.ServiceId})'

    __repr__ = __str__


class FindServersParameters(FrozenClass):
    """
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar LocaleIds:
    :vartype LocaleIds: String
    :ivar ServerUris:
    :vartype ServerUris: String
    """

    ua_types = [
        ('EndpointUrl', 'String'),
        ('LocaleIds', 'ListOfString'),
        ('ServerUris', 'ListOfString'),
               ]

    def __init__(self):
        self.EndpointUrl = None
        self.LocaleIds = []
        self.ServerUris = []
        self._freeze = True

    def __str__(self):
        return f'FindServersParameters(EndpointUrl:{self.EndpointUrl}, LocaleIds:{self.LocaleIds}, ServerUris:{self.ServerUris})'

    __repr__ = __str__


class FindServersRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: FindServersParameters
    """

    data_type = ObjectIds.FindServersRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'FindServersParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.FindServersRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = FindServersParameters()
        self._freeze = True

    def __str__(self):
        return f'FindServersRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class FindServersResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Servers:
    :vartype Servers: ApplicationDescription
    """

    data_type = ObjectIds.FindServersResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Servers', 'ListOfApplicationDescription'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.FindServersResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Servers = []
        self._freeze = True

    def __str__(self):
        return f'FindServersResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Servers:{self.Servers})'

    __repr__ = __str__


class ServerOnNetwork(FrozenClass):
    """
    :ivar RecordId:
    :vartype RecordId: UInt32
    :ivar ServerName:
    :vartype ServerName: String
    :ivar DiscoveryUrl:
    :vartype DiscoveryUrl: String
    :ivar ServerCapabilities:
    :vartype ServerCapabilities: String
    """

    data_type = ObjectIds.ServerOnNetwork

    ua_types = [
        ('RecordId', 'UInt32'),
        ('ServerName', 'String'),
        ('DiscoveryUrl', 'String'),
        ('ServerCapabilities', 'ListOfString'),
               ]

    def __init__(self):
        self.RecordId = 0
        self.ServerName = None
        self.DiscoveryUrl = None
        self.ServerCapabilities = []
        self._freeze = True

    def __str__(self):
        return f'ServerOnNetwork(RecordId:{self.RecordId}, ServerName:{self.ServerName}, DiscoveryUrl:{self.DiscoveryUrl}, ServerCapabilities:{self.ServerCapabilities})'

    __repr__ = __str__


class FindServersOnNetworkParameters(FrozenClass):
    """
    :ivar StartingRecordId:
    :vartype StartingRecordId: UInt32
    :ivar MaxRecordsToReturn:
    :vartype MaxRecordsToReturn: UInt32
    :ivar ServerCapabilityFilter:
    :vartype ServerCapabilityFilter: String
    """

    ua_types = [
        ('StartingRecordId', 'UInt32'),
        ('MaxRecordsToReturn', 'UInt32'),
        ('ServerCapabilityFilter', 'ListOfString'),
               ]

    def __init__(self):
        self.StartingRecordId = 0
        self.MaxRecordsToReturn = 0
        self.ServerCapabilityFilter = []
        self._freeze = True

    def __str__(self):
        return f'FindServersOnNetworkParameters(StartingRecordId:{self.StartingRecordId}, MaxRecordsToReturn:{self.MaxRecordsToReturn}, ServerCapabilityFilter:{self.ServerCapabilityFilter})'

    __repr__ = __str__


class FindServersOnNetworkRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: FindServersOnNetworkParameters
    """

    data_type = ObjectIds.FindServersOnNetworkRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'FindServersOnNetworkParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.FindServersOnNetworkRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = FindServersOnNetworkParameters()
        self._freeze = True

    def __str__(self):
        return f'FindServersOnNetworkRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class FindServersOnNetworkResult(FrozenClass):
    """
    :ivar LastCounterResetTime:
    :vartype LastCounterResetTime: DateTime
    :ivar Servers:
    :vartype Servers: ServerOnNetwork
    """

    ua_types = [
        ('LastCounterResetTime', 'DateTime'),
        ('Servers', 'ListOfServerOnNetwork'),
               ]

    def __init__(self):
        self.LastCounterResetTime = datetime.utcnow()
        self.Servers = []
        self._freeze = True

    def __str__(self):
        return f'FindServersOnNetworkResult(LastCounterResetTime:{self.LastCounterResetTime}, Servers:{self.Servers})'

    __repr__ = __str__


class FindServersOnNetworkResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: FindServersOnNetworkResult
    """

    data_type = ObjectIds.FindServersOnNetworkResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'FindServersOnNetworkResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.FindServersOnNetworkResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = FindServersOnNetworkResult()
        self._freeze = True

    def __str__(self):
        return f'FindServersOnNetworkResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class UserTokenPolicy(FrozenClass):
    """
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

    data_type = ObjectIds.UserTokenPolicy

    ua_types = [
        ('PolicyId', 'String'),
        ('TokenType', 'UserTokenType'),
        ('IssuedTokenType', 'String'),
        ('IssuerEndpointUrl', 'String'),
        ('SecurityPolicyUri', 'String'),
               ]

    def __init__(self):
        self.PolicyId = None
        self.TokenType = UserTokenType(0)
        self.IssuedTokenType = None
        self.IssuerEndpointUrl = None
        self.SecurityPolicyUri = None
        self._freeze = True

    def __str__(self):
        return f'UserTokenPolicy(PolicyId:{self.PolicyId}, TokenType:{self.TokenType}, IssuedTokenType:{self.IssuedTokenType}, IssuerEndpointUrl:{self.IssuerEndpointUrl}, SecurityPolicyUri:{self.SecurityPolicyUri})'

    __repr__ = __str__


class EndpointDescription(FrozenClass):
    """
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar Server:
    :vartype Server: ApplicationDescription
    :ivar ServerCertificate:
    :vartype ServerCertificate: ByteString
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

    data_type = ObjectIds.EndpointDescription

    ua_types = [
        ('EndpointUrl', 'String'),
        ('Server', 'ApplicationDescription'),
        ('ServerCertificate', 'ByteString'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityPolicyUri', 'String'),
        ('UserIdentityTokens', 'ListOfUserTokenPolicy'),
        ('TransportProfileUri', 'String'),
        ('SecurityLevel', 'Byte'),
               ]

    def __init__(self):
        self.EndpointUrl = None
        self.Server = ApplicationDescription()
        self.ServerCertificate = None
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityPolicyUri = None
        self.UserIdentityTokens = []
        self.TransportProfileUri = None
        self.SecurityLevel = 0
        self._freeze = True

    def __str__(self):
        return f'EndpointDescription(EndpointUrl:{self.EndpointUrl}, Server:{self.Server}, ServerCertificate:{self.ServerCertificate}, SecurityMode:{self.SecurityMode}, SecurityPolicyUri:{self.SecurityPolicyUri}, UserIdentityTokens:{self.UserIdentityTokens}, TransportProfileUri:{self.TransportProfileUri}, SecurityLevel:{self.SecurityLevel})'

    __repr__ = __str__


class GetEndpointsParameters(FrozenClass):
    """
    :ivar EndpointUrl:
    :vartype EndpointUrl: String
    :ivar LocaleIds:
    :vartype LocaleIds: String
    :ivar ProfileUris:
    :vartype ProfileUris: String
    """

    ua_types = [
        ('EndpointUrl', 'String'),
        ('LocaleIds', 'ListOfString'),
        ('ProfileUris', 'ListOfString'),
               ]

    def __init__(self):
        self.EndpointUrl = None
        self.LocaleIds = []
        self.ProfileUris = []
        self._freeze = True

    def __str__(self):
        return f'GetEndpointsParameters(EndpointUrl:{self.EndpointUrl}, LocaleIds:{self.LocaleIds}, ProfileUris:{self.ProfileUris})'

    __repr__ = __str__


class GetEndpointsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: GetEndpointsParameters
    """

    data_type = ObjectIds.GetEndpointsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'GetEndpointsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.GetEndpointsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = GetEndpointsParameters()
        self._freeze = True

    def __str__(self):
        return f'GetEndpointsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class GetEndpointsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Endpoints:
    :vartype Endpoints: EndpointDescription
    """

    data_type = ObjectIds.GetEndpointsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Endpoints', 'ListOfEndpointDescription'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.GetEndpointsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Endpoints = []
        self._freeze = True

    def __str__(self):
        return f'GetEndpointsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Endpoints:{self.Endpoints})'

    __repr__ = __str__


class RegisteredServer(FrozenClass):
    """
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

    data_type = ObjectIds.RegisteredServer

    ua_types = [
        ('ServerUri', 'String'),
        ('ProductUri', 'String'),
        ('ServerNames', 'ListOfLocalizedText'),
        ('ServerType', 'ApplicationType'),
        ('GatewayServerUri', 'String'),
        ('DiscoveryUrls', 'ListOfString'),
        ('SemaphoreFilePath', 'String'),
        ('IsOnline', 'Boolean'),
               ]

    def __init__(self):
        self.ServerUri = None
        self.ProductUri = None
        self.ServerNames = []
        self.ServerType = ApplicationType(0)
        self.GatewayServerUri = None
        self.DiscoveryUrls = []
        self.SemaphoreFilePath = None
        self.IsOnline = True
        self._freeze = True

    def __str__(self):
        return f'RegisteredServer(ServerUri:{self.ServerUri}, ProductUri:{self.ProductUri}, ServerNames:{self.ServerNames}, ServerType:{self.ServerType}, GatewayServerUri:{self.GatewayServerUri}, DiscoveryUrls:{self.DiscoveryUrls}, SemaphoreFilePath:{self.SemaphoreFilePath}, IsOnline:{self.IsOnline})'

    __repr__ = __str__


class RegisterServerRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Server:
    :vartype Server: RegisteredServer
    """

    data_type = ObjectIds.RegisterServerRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Server', 'RegisteredServer'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RegisterServerRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Server = RegisteredServer()
        self._freeze = True

    def __str__(self):
        return f'RegisterServerRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Server:{self.Server})'

    __repr__ = __str__


class RegisterServerResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = ObjectIds.RegisterServerResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RegisterServerResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self._freeze = True

    def __str__(self):
        return f'RegisterServerResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader})'

    __repr__ = __str__


class DiscoveryConfiguration(FrozenClass):
    """
    """

    data_type = ObjectIds.DiscoveryConfiguration

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'DiscoveryConfiguration()'

    __repr__ = __str__


class MdnsDiscoveryConfiguration(FrozenClass):
    """
    :ivar MdnsServerName:
    :vartype MdnsServerName: String
    :ivar ServerCapabilities:
    :vartype ServerCapabilities: String
    """

    data_type = ObjectIds.MdnsDiscoveryConfiguration

    ua_types = [
        ('MdnsServerName', 'String'),
        ('ServerCapabilities', 'ListOfString'),
               ]

    def __init__(self):
        self.MdnsServerName = None
        self.ServerCapabilities = []
        self._freeze = True

    def __str__(self):
        return f'MdnsDiscoveryConfiguration(MdnsServerName:{self.MdnsServerName}, ServerCapabilities:{self.ServerCapabilities})'

    __repr__ = __str__


class RegisterServer2Parameters(FrozenClass):
    """
    :ivar Server:
    :vartype Server: RegisteredServer
    :ivar DiscoveryConfiguration:
    :vartype DiscoveryConfiguration: ExtensionObject
    """

    ua_types = [
        ('Server', 'RegisteredServer'),
        ('DiscoveryConfiguration', 'ListOfExtensionObject'),
               ]

    def __init__(self):
        self.Server = RegisteredServer()
        self.DiscoveryConfiguration = []
        self._freeze = True

    def __str__(self):
        return f'RegisterServer2Parameters(Server:{self.Server}, DiscoveryConfiguration:{self.DiscoveryConfiguration})'

    __repr__ = __str__


class RegisterServer2Request(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: RegisterServer2Parameters
    """

    data_type = ObjectIds.RegisterServer2Request

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'RegisterServer2Parameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RegisterServer2Request_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = RegisterServer2Parameters()
        self._freeze = True

    def __str__(self):
        return f'RegisterServer2Request(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class RegisterServer2Response(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar ConfigurationResults:
    :vartype ConfigurationResults: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.RegisterServer2Response

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('ConfigurationResults', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RegisterServer2Response_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.ConfigurationResults = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'RegisterServer2Response(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, ConfigurationResults:{self.ConfigurationResults}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class ChannelSecurityToken(FrozenClass):
    """
    :ivar ChannelId:
    :vartype ChannelId: UInt32
    :ivar TokenId:
    :vartype TokenId: UInt32
    :ivar CreatedAt:
    :vartype CreatedAt: DateTime
    :ivar RevisedLifetime:
    :vartype RevisedLifetime: UInt32
    """

    data_type = ObjectIds.ChannelSecurityToken

    ua_types = [
        ('ChannelId', 'UInt32'),
        ('TokenId', 'UInt32'),
        ('CreatedAt', 'DateTime'),
        ('RevisedLifetime', 'UInt32'),
               ]

    def __init__(self):
        self.ChannelId = 0
        self.TokenId = 0
        self.CreatedAt = datetime.utcnow()
        self.RevisedLifetime = 0
        self._freeze = True

    def __str__(self):
        return f'ChannelSecurityToken(ChannelId:{self.ChannelId}, TokenId:{self.TokenId}, CreatedAt:{self.CreatedAt}, RevisedLifetime:{self.RevisedLifetime})'

    __repr__ = __str__


class OpenSecureChannelParameters(FrozenClass):
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

    ua_types = [
        ('ClientProtocolVersion', 'UInt32'),
        ('RequestType', 'SecurityTokenRequestType'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('ClientNonce', 'ByteString'),
        ('RequestedLifetime', 'UInt32'),
               ]

    def __init__(self):
        self.ClientProtocolVersion = 0
        self.RequestType = SecurityTokenRequestType(0)
        self.SecurityMode = MessageSecurityMode(0)
        self.ClientNonce = None
        self.RequestedLifetime = 0
        self._freeze = True

    def __str__(self):
        return f'OpenSecureChannelParameters(ClientProtocolVersion:{self.ClientProtocolVersion}, RequestType:{self.RequestType}, SecurityMode:{self.SecurityMode}, ClientNonce:{self.ClientNonce}, RequestedLifetime:{self.RequestedLifetime})'

    __repr__ = __str__


class OpenSecureChannelRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: OpenSecureChannelParameters
    """

    data_type = ObjectIds.OpenSecureChannelRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'OpenSecureChannelParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.OpenSecureChannelRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = OpenSecureChannelParameters()
        self._freeze = True

    def __str__(self):
        return f'OpenSecureChannelRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class OpenSecureChannelResult(FrozenClass):
    """
    :ivar ServerProtocolVersion:
    :vartype ServerProtocolVersion: UInt32
    :ivar SecurityToken:
    :vartype SecurityToken: ChannelSecurityToken
    :ivar ServerNonce:
    :vartype ServerNonce: ByteString
    """

    ua_types = [
        ('ServerProtocolVersion', 'UInt32'),
        ('SecurityToken', 'ChannelSecurityToken'),
        ('ServerNonce', 'ByteString'),
               ]

    def __init__(self):
        self.ServerProtocolVersion = 0
        self.SecurityToken = ChannelSecurityToken()
        self.ServerNonce = None
        self._freeze = True

    def __str__(self):
        return f'OpenSecureChannelResult(ServerProtocolVersion:{self.ServerProtocolVersion}, SecurityToken:{self.SecurityToken}, ServerNonce:{self.ServerNonce})'

    __repr__ = __str__


class OpenSecureChannelResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: OpenSecureChannelResult
    """

    data_type = ObjectIds.OpenSecureChannelResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'OpenSecureChannelResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.OpenSecureChannelResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = OpenSecureChannelResult()
        self._freeze = True

    def __str__(self):
        return f'OpenSecureChannelResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CloseSecureChannelRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    """

    data_type = ObjectIds.CloseSecureChannelRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CloseSecureChannelRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self._freeze = True

    def __str__(self):
        return f'CloseSecureChannelRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader})'

    __repr__ = __str__


class CloseSecureChannelResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = ObjectIds.CloseSecureChannelResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CloseSecureChannelResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self._freeze = True

    def __str__(self):
        return f'CloseSecureChannelResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader})'

    __repr__ = __str__


class SignedSoftwareCertificate(FrozenClass):
    """
    :ivar CertificateData:
    :vartype CertificateData: ByteString
    :ivar Signature:
    :vartype Signature: ByteString
    """

    data_type = ObjectIds.SignedSoftwareCertificate

    ua_types = [
        ('CertificateData', 'ByteString'),
        ('Signature', 'ByteString'),
               ]

    def __init__(self):
        self.CertificateData = None
        self.Signature = None
        self._freeze = True

    def __str__(self):
        return f'SignedSoftwareCertificate(CertificateData:{self.CertificateData}, Signature:{self.Signature})'

    __repr__ = __str__


class SignatureData(FrozenClass):
    """
    :ivar Algorithm:
    :vartype Algorithm: String
    :ivar Signature:
    :vartype Signature: ByteString
    """

    data_type = ObjectIds.SignatureData

    ua_types = [
        ('Algorithm', 'String'),
        ('Signature', 'ByteString'),
               ]

    def __init__(self):
        self.Algorithm = None
        self.Signature = None
        self._freeze = True

    def __str__(self):
        return f'SignatureData(Algorithm:{self.Algorithm}, Signature:{self.Signature})'

    __repr__ = __str__


class CreateSessionParameters(FrozenClass):
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
    :vartype ClientCertificate: ByteString
    :ivar RequestedSessionTimeout:
    :vartype RequestedSessionTimeout: Double
    :ivar MaxResponseMessageSize:
    :vartype MaxResponseMessageSize: UInt32
    """

    ua_types = [
        ('ClientDescription', 'ApplicationDescription'),
        ('ServerUri', 'String'),
        ('EndpointUrl', 'String'),
        ('SessionName', 'String'),
        ('ClientNonce', 'ByteString'),
        ('ClientCertificate', 'ByteString'),
        ('RequestedSessionTimeout', 'Double'),
        ('MaxResponseMessageSize', 'UInt32'),
               ]

    def __init__(self):
        self.ClientDescription = ApplicationDescription()
        self.ServerUri = None
        self.EndpointUrl = None
        self.SessionName = None
        self.ClientNonce = None
        self.ClientCertificate = None
        self.RequestedSessionTimeout = 0
        self.MaxResponseMessageSize = 0
        self._freeze = True

    def __str__(self):
        return f'CreateSessionParameters(ClientDescription:{self.ClientDescription}, ServerUri:{self.ServerUri}, EndpointUrl:{self.EndpointUrl}, SessionName:{self.SessionName}, ClientNonce:{self.ClientNonce}, ClientCertificate:{self.ClientCertificate}, RequestedSessionTimeout:{self.RequestedSessionTimeout}, MaxResponseMessageSize:{self.MaxResponseMessageSize})'

    __repr__ = __str__


class CreateSessionRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CreateSessionParameters
    """

    data_type = ObjectIds.CreateSessionRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'CreateSessionParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CreateSessionRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = CreateSessionParameters()
        self._freeze = True

    def __str__(self):
        return f'CreateSessionRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CreateSessionResult(FrozenClass):
    """
    :ivar SessionId:
    :vartype SessionId: NodeId
    :ivar AuthenticationToken:
    :vartype AuthenticationToken: NodeId
    :ivar RevisedSessionTimeout:
    :vartype RevisedSessionTimeout: Double
    :ivar ServerNonce:
    :vartype ServerNonce: ByteString
    :ivar ServerCertificate:
    :vartype ServerCertificate: ByteString
    :ivar ServerEndpoints:
    :vartype ServerEndpoints: EndpointDescription
    :ivar ServerSoftwareCertificates:
    :vartype ServerSoftwareCertificates: SignedSoftwareCertificate
    :ivar ServerSignature:
    :vartype ServerSignature: SignatureData
    :ivar MaxRequestMessageSize:
    :vartype MaxRequestMessageSize: UInt32
    """

    ua_types = [
        ('SessionId', 'NodeId'),
        ('AuthenticationToken', 'NodeId'),
        ('RevisedSessionTimeout', 'Double'),
        ('ServerNonce', 'ByteString'),
        ('ServerCertificate', 'ByteString'),
        ('ServerEndpoints', 'ListOfEndpointDescription'),
        ('ServerSoftwareCertificates', 'ListOfSignedSoftwareCertificate'),
        ('ServerSignature', 'SignatureData'),
        ('MaxRequestMessageSize', 'UInt32'),
               ]

    def __init__(self):
        self.SessionId = NodeId()
        self.AuthenticationToken = NodeId()
        self.RevisedSessionTimeout = 0
        self.ServerNonce = None
        self.ServerCertificate = None
        self.ServerEndpoints = []
        self.ServerSoftwareCertificates = []
        self.ServerSignature = SignatureData()
        self.MaxRequestMessageSize = 0
        self._freeze = True

    def __str__(self):
        return f'CreateSessionResult(SessionId:{self.SessionId}, AuthenticationToken:{self.AuthenticationToken}, RevisedSessionTimeout:{self.RevisedSessionTimeout}, ServerNonce:{self.ServerNonce}, ServerCertificate:{self.ServerCertificate}, ServerEndpoints:{self.ServerEndpoints}, ServerSoftwareCertificates:{self.ServerSoftwareCertificates}, ServerSignature:{self.ServerSignature}, MaxRequestMessageSize:{self.MaxRequestMessageSize})'

    __repr__ = __str__


class CreateSessionResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: CreateSessionResult
    """

    data_type = ObjectIds.CreateSessionResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'CreateSessionResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CreateSessionResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = CreateSessionResult()
        self._freeze = True

    def __str__(self):
        return f'CreateSessionResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class UserIdentityToken(FrozenClass):
    """
    :ivar PolicyId:
    :vartype PolicyId: String
    """

    data_type = ObjectIds.UserIdentityToken

    ua_types = [
        ('PolicyId', 'String'),
               ]

    def __init__(self):
        self.PolicyId = None
        self._freeze = True

    def __str__(self):
        return f'UserIdentityToken(PolicyId:{self.PolicyId})'

    __repr__ = __str__


class AnonymousIdentityToken(FrozenClass):
    """
    :ivar PolicyId:
    :vartype PolicyId: String
    """

    data_type = ObjectIds.AnonymousIdentityToken

    ua_types = [
        ('PolicyId', 'String'),
               ]

    def __init__(self):
        self.PolicyId = None
        self._freeze = True

    def __str__(self):
        return f'AnonymousIdentityToken(PolicyId:{self.PolicyId})'

    __repr__ = __str__


class UserNameIdentityToken(FrozenClass):
    """
    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar UserName:
    :vartype UserName: String
    :ivar Password:
    :vartype Password: ByteString
    :ivar EncryptionAlgorithm:
    :vartype EncryptionAlgorithm: String
    """

    data_type = ObjectIds.UserNameIdentityToken

    ua_types = [
        ('PolicyId', 'String'),
        ('UserName', 'String'),
        ('Password', 'ByteString'),
        ('EncryptionAlgorithm', 'String'),
               ]

    def __init__(self):
        self.PolicyId = None
        self.UserName = None
        self.Password = None
        self.EncryptionAlgorithm = None
        self._freeze = True

    def __str__(self):
        return f'UserNameIdentityToken(PolicyId:{self.PolicyId}, UserName:{self.UserName}, Password:{self.Password}, EncryptionAlgorithm:{self.EncryptionAlgorithm})'

    __repr__ = __str__


class X509IdentityToken(FrozenClass):
    """
    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar CertificateData:
    :vartype CertificateData: ByteString
    """

    data_type = ObjectIds.X509IdentityToken

    ua_types = [
        ('PolicyId', 'String'),
        ('CertificateData', 'ByteString'),
               ]

    def __init__(self):
        self.PolicyId = None
        self.CertificateData = None
        self._freeze = True

    def __str__(self):
        return f'X509IdentityToken(PolicyId:{self.PolicyId}, CertificateData:{self.CertificateData})'

    __repr__ = __str__


class IssuedIdentityToken(FrozenClass):
    """
    :ivar PolicyId:
    :vartype PolicyId: String
    :ivar TokenData:
    :vartype TokenData: ByteString
    :ivar EncryptionAlgorithm:
    :vartype EncryptionAlgorithm: String
    """

    data_type = ObjectIds.IssuedIdentityToken

    ua_types = [
        ('PolicyId', 'String'),
        ('TokenData', 'ByteString'),
        ('EncryptionAlgorithm', 'String'),
               ]

    def __init__(self):
        self.PolicyId = None
        self.TokenData = None
        self.EncryptionAlgorithm = None
        self._freeze = True

    def __str__(self):
        return f'IssuedIdentityToken(PolicyId:{self.PolicyId}, TokenData:{self.TokenData}, EncryptionAlgorithm:{self.EncryptionAlgorithm})'

    __repr__ = __str__


class ActivateSessionParameters(FrozenClass):
    """
    :ivar ClientSignature:
    :vartype ClientSignature: SignatureData
    :ivar ClientSoftwareCertificates:
    :vartype ClientSoftwareCertificates: SignedSoftwareCertificate
    :ivar LocaleIds:
    :vartype LocaleIds: String
    :ivar UserIdentityToken:
    :vartype UserIdentityToken: ExtensionObject
    :ivar UserTokenSignature:
    :vartype UserTokenSignature: SignatureData
    """

    ua_types = [
        ('ClientSignature', 'SignatureData'),
        ('ClientSoftwareCertificates', 'ListOfSignedSoftwareCertificate'),
        ('LocaleIds', 'ListOfString'),
        ('UserIdentityToken', 'ExtensionObject'),
        ('UserTokenSignature', 'SignatureData'),
               ]

    def __init__(self):
        self.ClientSignature = SignatureData()
        self.ClientSoftwareCertificates = []
        self.LocaleIds = []
        self.UserIdentityToken = ExtensionObject()
        self.UserTokenSignature = SignatureData()
        self._freeze = True

    def __str__(self):
        return f'ActivateSessionParameters(ClientSignature:{self.ClientSignature}, ClientSoftwareCertificates:{self.ClientSoftwareCertificates}, LocaleIds:{self.LocaleIds}, UserIdentityToken:{self.UserIdentityToken}, UserTokenSignature:{self.UserTokenSignature})'

    __repr__ = __str__


class ActivateSessionRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ActivateSessionParameters
    """

    data_type = ObjectIds.ActivateSessionRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'ActivateSessionParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = ActivateSessionParameters()
        self._freeze = True

    def __str__(self):
        return f'ActivateSessionRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ActivateSessionResult(FrozenClass):
    """
    :ivar ServerNonce:
    :vartype ServerNonce: ByteString
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('ServerNonce', 'ByteString'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.ServerNonce = None
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'ActivateSessionResult(ServerNonce:{self.ServerNonce}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class ActivateSessionResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: ActivateSessionResult
    """

    data_type = ObjectIds.ActivateSessionResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'ActivateSessionResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ActivateSessionResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = ActivateSessionResult()
        self._freeze = True

    def __str__(self):
        return f'ActivateSessionResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CloseSessionRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar DeleteSubscriptions:
    :vartype DeleteSubscriptions: Boolean
    """

    data_type = ObjectIds.CloseSessionRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('DeleteSubscriptions', 'Boolean'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CloseSessionRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.DeleteSubscriptions = True
        self._freeze = True

    def __str__(self):
        return f'CloseSessionRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, DeleteSubscriptions:{self.DeleteSubscriptions})'

    __repr__ = __str__


class CloseSessionResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = ObjectIds.CloseSessionResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CloseSessionResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self._freeze = True

    def __str__(self):
        return f'CloseSessionResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader})'

    __repr__ = __str__


class CancelParameters(FrozenClass):
    """
    :ivar RequestHandle:
    :vartype RequestHandle: UInt32
    """

    ua_types = [
        ('RequestHandle', 'UInt32'),
               ]

    def __init__(self):
        self.RequestHandle = 0
        self._freeze = True

    def __str__(self):
        return f'CancelParameters(RequestHandle:{self.RequestHandle})'

    __repr__ = __str__


class CancelRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CancelParameters
    """

    data_type = ObjectIds.CancelRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'CancelParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CancelRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = CancelParameters()
        self._freeze = True

    def __str__(self):
        return f'CancelRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CancelResult(FrozenClass):
    """
    :ivar CancelCount:
    :vartype CancelCount: UInt32
    """

    ua_types = [
        ('CancelCount', 'UInt32'),
               ]

    def __init__(self):
        self.CancelCount = 0
        self._freeze = True

    def __str__(self):
        return f'CancelResult(CancelCount:{self.CancelCount})'

    __repr__ = __str__


class CancelResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: CancelResult
    """

    data_type = ObjectIds.CancelResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'CancelResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CancelResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = CancelResult()
        self._freeze = True

    def __str__(self):
        return f'CancelResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class NodeAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.NodeAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self._freeze = True

    def __str__(self):
        return f'NodeAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask})'

    __repr__ = __str__


class ObjectAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.ObjectAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('EventNotifier', 'Byte'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.EventNotifier = 0
        self._freeze = True

    def __str__(self):
        return f'ObjectAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, EventNotifier:{self.EventNotifier})'

    __repr__ = __str__


class VariableAttributes(FrozenClass):
    """
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
    :vartype MinimumSamplingInterval: Double
    :ivar Historizing:
    :vartype Historizing: Boolean
    """

    data_type = ObjectIds.VariableAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('Value', 'Variant'),
        ('DataType', 'NodeId'),
        ('ValueRank', 'Int32'),
        ('ArrayDimensions', 'ListOfUInt32'),
        ('AccessLevel', 'Byte'),
        ('UserAccessLevel', 'Byte'),
        ('MinimumSamplingInterval', 'Double'),
        ('Historizing', 'Boolean'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.Value = Variant()
        self.DataType = NodeId()
        self.ValueRank = 0
        self.ArrayDimensions = []
        self.AccessLevel = 0
        self.UserAccessLevel = 0
        self.MinimumSamplingInterval = 0
        self.Historizing = True
        self._freeze = True

    def __str__(self):
        return f'VariableAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, Value:{self.Value}, DataType:{self.DataType}, ValueRank:{self.ValueRank}, ArrayDimensions:{self.ArrayDimensions}, AccessLevel:{self.AccessLevel}, UserAccessLevel:{self.UserAccessLevel}, MinimumSamplingInterval:{self.MinimumSamplingInterval}, Historizing:{self.Historizing})'

    __repr__ = __str__


class MethodAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.MethodAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('Executable', 'Boolean'),
        ('UserExecutable', 'Boolean'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.Executable = True
        self.UserExecutable = True
        self._freeze = True

    def __str__(self):
        return f'MethodAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, Executable:{self.Executable}, UserExecutable:{self.UserExecutable})'

    __repr__ = __str__


class ObjectTypeAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.ObjectTypeAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('IsAbstract', 'Boolean'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.IsAbstract = True
        self._freeze = True

    def __str__(self):
        return f'ObjectTypeAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, IsAbstract:{self.IsAbstract})'

    __repr__ = __str__


class VariableTypeAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.VariableTypeAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('Value', 'Variant'),
        ('DataType', 'NodeId'),
        ('ValueRank', 'Int32'),
        ('ArrayDimensions', 'ListOfUInt32'),
        ('IsAbstract', 'Boolean'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.Value = Variant()
        self.DataType = NodeId()
        self.ValueRank = 0
        self.ArrayDimensions = []
        self.IsAbstract = True
        self._freeze = True

    def __str__(self):
        return f'VariableTypeAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, Value:{self.Value}, DataType:{self.DataType}, ValueRank:{self.ValueRank}, ArrayDimensions:{self.ArrayDimensions}, IsAbstract:{self.IsAbstract})'

    __repr__ = __str__


class ReferenceTypeAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.ReferenceTypeAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('IsAbstract', 'Boolean'),
        ('Symmetric', 'Boolean'),
        ('InverseName', 'LocalizedText'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.IsAbstract = True
        self.Symmetric = True
        self.InverseName = LocalizedText()
        self._freeze = True

    def __str__(self):
        return f'ReferenceTypeAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, IsAbstract:{self.IsAbstract}, Symmetric:{self.Symmetric}, InverseName:{self.InverseName})'

    __repr__ = __str__


class DataTypeAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.DataTypeAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('IsAbstract', 'Boolean'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.IsAbstract = True
        self._freeze = True

    def __str__(self):
        return f'DataTypeAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, IsAbstract:{self.IsAbstract})'

    __repr__ = __str__


class ViewAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.ViewAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('ContainsNoLoops', 'Boolean'),
        ('EventNotifier', 'Byte'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.ContainsNoLoops = True
        self.EventNotifier = 0
        self._freeze = True

    def __str__(self):
        return f'ViewAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, ContainsNoLoops:{self.ContainsNoLoops}, EventNotifier:{self.EventNotifier})'

    __repr__ = __str__


class GenericAttributeValue(FrozenClass):
    """
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar Value:
    :vartype Value: Variant
    """

    data_type = ObjectIds.GenericAttributeValue

    ua_types = [
        ('AttributeId', 'UInt32'),
        ('Value', 'Variant'),
               ]

    def __init__(self):
        self.AttributeId = 0
        self.Value = Variant()
        self._freeze = True

    def __str__(self):
        return f'GenericAttributeValue(AttributeId:{self.AttributeId}, Value:{self.Value})'

    __repr__ = __str__


class GenericAttributes(FrozenClass):
    """
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

    data_type = ObjectIds.GenericAttributes

    ua_types = [
        ('SpecifiedAttributes', 'UInt32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
        ('WriteMask', 'UInt32'),
        ('UserWriteMask', 'UInt32'),
        ('AttributeValues', 'ListOfGenericAttributeValue'),
               ]

    def __init__(self):
        self.SpecifiedAttributes = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self.WriteMask = 0
        self.UserWriteMask = 0
        self.AttributeValues = []
        self._freeze = True

    def __str__(self):
        return f'GenericAttributes(SpecifiedAttributes:{self.SpecifiedAttributes}, DisplayName:{self.DisplayName}, Description:{self.Description}, WriteMask:{self.WriteMask}, UserWriteMask:{self.UserWriteMask}, AttributeValues:{self.AttributeValues})'

    __repr__ = __str__


class AddNodesItem(FrozenClass):
    """
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

    data_type = ObjectIds.AddNodesItem

    ua_types = [
        ('ParentNodeId', 'ExpandedNodeId'),
        ('ReferenceTypeId', 'NodeId'),
        ('RequestedNewNodeId', 'ExpandedNodeId'),
        ('BrowseName', 'QualifiedName'),
        ('NodeClass', 'NodeClass'),
        ('NodeAttributes', 'ExtensionObject'),
        ('TypeDefinition', 'ExpandedNodeId'),
               ]

    def __init__(self):
        self.ParentNodeId = ExpandedNodeId()
        self.ReferenceTypeId = NodeId()
        self.RequestedNewNodeId = ExpandedNodeId()
        self.BrowseName = QualifiedName()
        self.NodeClass = NodeClass(0)
        self.NodeAttributes = ExtensionObject()
        self.TypeDefinition = ExpandedNodeId()
        self._freeze = True

    def __str__(self):
        return f'AddNodesItem(ParentNodeId:{self.ParentNodeId}, ReferenceTypeId:{self.ReferenceTypeId}, RequestedNewNodeId:{self.RequestedNewNodeId}, BrowseName:{self.BrowseName}, NodeClass:{self.NodeClass}, NodeAttributes:{self.NodeAttributes}, TypeDefinition:{self.TypeDefinition})'

    __repr__ = __str__


class AddNodesResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar AddedNodeId:
    :vartype AddedNodeId: NodeId
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('AddedNodeId', 'NodeId'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.AddedNodeId = NodeId()
        self._freeze = True

    def __str__(self):
        return f'AddNodesResult(StatusCode:{self.StatusCode}, AddedNodeId:{self.AddedNodeId})'

    __repr__ = __str__


class AddNodesParameters(FrozenClass):
    """
    :ivar NodesToAdd:
    :vartype NodesToAdd: AddNodesItem
    """

    ua_types = [
        ('NodesToAdd', 'ListOfAddNodesItem'),
               ]

    def __init__(self):
        self.NodesToAdd = []
        self._freeze = True

    def __str__(self):
        return f'AddNodesParameters(NodesToAdd:{self.NodesToAdd})'

    __repr__ = __str__


class AddNodesRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: AddNodesParameters
    """

    data_type = ObjectIds.AddNodesRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'AddNodesParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.AddNodesRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = AddNodesParameters()
        self._freeze = True

    def __str__(self):
        return f'AddNodesRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class AddNodesResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: AddNodesResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.AddNodesResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfAddNodesResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.AddNodesResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'AddNodesResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class AddReferencesItem(FrozenClass):
    """
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

    data_type = ObjectIds.AddReferencesItem

    ua_types = [
        ('SourceNodeId', 'NodeId'),
        ('ReferenceTypeId', 'NodeId'),
        ('IsForward', 'Boolean'),
        ('TargetServerUri', 'String'),
        ('TargetNodeId', 'ExpandedNodeId'),
        ('TargetNodeClass', 'NodeClass'),
               ]

    def __init__(self):
        self.SourceNodeId = NodeId()
        self.ReferenceTypeId = NodeId()
        self.IsForward = True
        self.TargetServerUri = None
        self.TargetNodeId = ExpandedNodeId()
        self.TargetNodeClass = NodeClass(0)
        self._freeze = True

    def __str__(self):
        return f'AddReferencesItem(SourceNodeId:{self.SourceNodeId}, ReferenceTypeId:{self.ReferenceTypeId}, IsForward:{self.IsForward}, TargetServerUri:{self.TargetServerUri}, TargetNodeId:{self.TargetNodeId}, TargetNodeClass:{self.TargetNodeClass})'

    __repr__ = __str__


class AddReferencesParameters(FrozenClass):
    """
    :ivar ReferencesToAdd:
    :vartype ReferencesToAdd: AddReferencesItem
    """

    ua_types = [
        ('ReferencesToAdd', 'ListOfAddReferencesItem'),
               ]

    def __init__(self):
        self.ReferencesToAdd = []
        self._freeze = True

    def __str__(self):
        return f'AddReferencesParameters(ReferencesToAdd:{self.ReferencesToAdd})'

    __repr__ = __str__


class AddReferencesRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: AddReferencesParameters
    """

    data_type = ObjectIds.AddReferencesRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'AddReferencesParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.AddReferencesRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = AddReferencesParameters()
        self._freeze = True

    def __str__(self):
        return f'AddReferencesRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class AddReferencesResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.AddReferencesResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.AddReferencesResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'AddReferencesResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class DeleteNodesItem(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar DeleteTargetReferences:
    :vartype DeleteTargetReferences: Boolean
    """

    data_type = ObjectIds.DeleteNodesItem

    ua_types = [
        ('NodeId', 'NodeId'),
        ('DeleteTargetReferences', 'Boolean'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.DeleteTargetReferences = True
        self._freeze = True

    def __str__(self):
        return f'DeleteNodesItem(NodeId:{self.NodeId}, DeleteTargetReferences:{self.DeleteTargetReferences})'

    __repr__ = __str__


class DeleteNodesParameters(FrozenClass):
    """
    :ivar NodesToDelete:
    :vartype NodesToDelete: DeleteNodesItem
    """

    ua_types = [
        ('NodesToDelete', 'ListOfDeleteNodesItem'),
               ]

    def __init__(self):
        self.NodesToDelete = []
        self._freeze = True

    def __str__(self):
        return f'DeleteNodesParameters(NodesToDelete:{self.NodesToDelete})'

    __repr__ = __str__


class DeleteNodesRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteNodesParameters
    """

    data_type = ObjectIds.DeleteNodesRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'DeleteNodesParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteNodesRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = DeleteNodesParameters()
        self._freeze = True

    def __str__(self):
        return f'DeleteNodesRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class DeleteNodesResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.DeleteNodesResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteNodesResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'DeleteNodesResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class DeleteReferencesItem(FrozenClass):
    """
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

    data_type = ObjectIds.DeleteReferencesItem

    ua_types = [
        ('SourceNodeId', 'NodeId'),
        ('ReferenceTypeId', 'NodeId'),
        ('IsForward', 'Boolean'),
        ('TargetNodeId', 'ExpandedNodeId'),
        ('DeleteBidirectional', 'Boolean'),
               ]

    def __init__(self):
        self.SourceNodeId = NodeId()
        self.ReferenceTypeId = NodeId()
        self.IsForward = True
        self.TargetNodeId = ExpandedNodeId()
        self.DeleteBidirectional = True
        self._freeze = True

    def __str__(self):
        return f'DeleteReferencesItem(SourceNodeId:{self.SourceNodeId}, ReferenceTypeId:{self.ReferenceTypeId}, IsForward:{self.IsForward}, TargetNodeId:{self.TargetNodeId}, DeleteBidirectional:{self.DeleteBidirectional})'

    __repr__ = __str__


class DeleteReferencesParameters(FrozenClass):
    """
    :ivar ReferencesToDelete:
    :vartype ReferencesToDelete: DeleteReferencesItem
    """

    ua_types = [
        ('ReferencesToDelete', 'ListOfDeleteReferencesItem'),
               ]

    def __init__(self):
        self.ReferencesToDelete = []
        self._freeze = True

    def __str__(self):
        return f'DeleteReferencesParameters(ReferencesToDelete:{self.ReferencesToDelete})'

    __repr__ = __str__


class DeleteReferencesRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteReferencesParameters
    """

    data_type = ObjectIds.DeleteReferencesRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'DeleteReferencesParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteReferencesRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = DeleteReferencesParameters()
        self._freeze = True

    def __str__(self):
        return f'DeleteReferencesRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class DeleteReferencesResult(FrozenClass):
    """
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'DeleteReferencesResult(Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class DeleteReferencesResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: DeleteReferencesResult
    """

    data_type = ObjectIds.DeleteReferencesResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'DeleteReferencesResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteReferencesResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = DeleteReferencesResult()
        self._freeze = True

    def __str__(self):
        return f'DeleteReferencesResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ViewDescription(FrozenClass):
    """
    :ivar ViewId:
    :vartype ViewId: NodeId
    :ivar Timestamp:
    :vartype Timestamp: DateTime
    :ivar ViewVersion:
    :vartype ViewVersion: UInt32
    """

    data_type = ObjectIds.ViewDescription

    ua_types = [
        ('ViewId', 'NodeId'),
        ('Timestamp', 'DateTime'),
        ('ViewVersion', 'UInt32'),
               ]

    def __init__(self):
        self.ViewId = NodeId()
        self.Timestamp = datetime.utcnow()
        self.ViewVersion = 0
        self._freeze = True

    def __str__(self):
        return f'ViewDescription(ViewId:{self.ViewId}, Timestamp:{self.Timestamp}, ViewVersion:{self.ViewVersion})'

    __repr__ = __str__


class BrowseDescription(FrozenClass):
    """
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

    data_type = ObjectIds.BrowseDescription

    ua_types = [
        ('NodeId', 'NodeId'),
        ('BrowseDirection', 'BrowseDirection'),
        ('ReferenceTypeId', 'NodeId'),
        ('IncludeSubtypes', 'Boolean'),
        ('NodeClassMask', 'UInt32'),
        ('ResultMask', 'UInt32'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.BrowseDirection = BrowseDirection(0)
        self.ReferenceTypeId = NodeId()
        self.IncludeSubtypes = True
        self.NodeClassMask = 0
        self.ResultMask = 0
        self._freeze = True

    def __str__(self):
        return f'BrowseDescription(NodeId:{self.NodeId}, BrowseDirection:{self.BrowseDirection}, ReferenceTypeId:{self.ReferenceTypeId}, IncludeSubtypes:{self.IncludeSubtypes}, NodeClassMask:{self.NodeClassMask}, ResultMask:{self.ResultMask})'

    __repr__ = __str__


class ReferenceDescription(FrozenClass):
    """
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

    data_type = ObjectIds.ReferenceDescription

    ua_types = [
        ('ReferenceTypeId', 'NodeId'),
        ('IsForward', 'Boolean'),
        ('NodeId', 'ExpandedNodeId'),
        ('BrowseName', 'QualifiedName'),
        ('DisplayName', 'LocalizedText'),
        ('NodeClass', 'NodeClass'),
        ('TypeDefinition', 'ExpandedNodeId'),
               ]

    def __init__(self):
        self.ReferenceTypeId = NodeId()
        self.IsForward = True
        self.NodeId = ExpandedNodeId()
        self.BrowseName = QualifiedName()
        self.DisplayName = LocalizedText()
        self.NodeClass = NodeClass(0)
        self.TypeDefinition = ExpandedNodeId()
        self._freeze = True

    def __str__(self):
        return f'ReferenceDescription(ReferenceTypeId:{self.ReferenceTypeId}, IsForward:{self.IsForward}, NodeId:{self.NodeId}, BrowseName:{self.BrowseName}, DisplayName:{self.DisplayName}, NodeClass:{self.NodeClass}, TypeDefinition:{self.TypeDefinition})'

    __repr__ = __str__


class BrowseResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ByteString
    :ivar References:
    :vartype References: ReferenceDescription
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('ContinuationPoint', 'ByteString'),
        ('References', 'ListOfReferenceDescription'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.ContinuationPoint = None
        self.References = []
        self._freeze = True

    def __str__(self):
        return f'BrowseResult(StatusCode:{self.StatusCode}, ContinuationPoint:{self.ContinuationPoint}, References:{self.References})'

    __repr__ = __str__


class BrowseParameters(FrozenClass):
    """
    :ivar View:
    :vartype View: ViewDescription
    :ivar RequestedMaxReferencesPerNode:
    :vartype RequestedMaxReferencesPerNode: UInt32
    :ivar NodesToBrowse:
    :vartype NodesToBrowse: BrowseDescription
    """

    ua_types = [
        ('View', 'ViewDescription'),
        ('RequestedMaxReferencesPerNode', 'UInt32'),
        ('NodesToBrowse', 'ListOfBrowseDescription'),
               ]

    def __init__(self):
        self.View = ViewDescription()
        self.RequestedMaxReferencesPerNode = 0
        self.NodesToBrowse = []
        self._freeze = True

    def __str__(self):
        return f'BrowseParameters(View:{self.View}, RequestedMaxReferencesPerNode:{self.RequestedMaxReferencesPerNode}, NodesToBrowse:{self.NodesToBrowse})'

    __repr__ = __str__


class BrowseRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: BrowseParameters
    """

    data_type = ObjectIds.BrowseRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'BrowseParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.BrowseRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = BrowseParameters()
        self._freeze = True

    def __str__(self):
        return f'BrowseRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class BrowseResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: BrowseResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.BrowseResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfBrowseResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.BrowseResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'BrowseResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class BrowseNextParameters(FrozenClass):
    """
    :ivar ReleaseContinuationPoints:
    :vartype ReleaseContinuationPoints: Boolean
    :ivar ContinuationPoints:
    :vartype ContinuationPoints: ByteString
    """

    ua_types = [
        ('ReleaseContinuationPoints', 'Boolean'),
        ('ContinuationPoints', 'ListOfByteString'),
               ]

    def __init__(self):
        self.ReleaseContinuationPoints = True
        self.ContinuationPoints = []
        self._freeze = True

    def __str__(self):
        return f'BrowseNextParameters(ReleaseContinuationPoints:{self.ReleaseContinuationPoints}, ContinuationPoints:{self.ContinuationPoints})'

    __repr__ = __str__


class BrowseNextRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: BrowseNextParameters
    """

    data_type = ObjectIds.BrowseNextRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'BrowseNextParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.BrowseNextRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = BrowseNextParameters()
        self._freeze = True

    def __str__(self):
        return f'BrowseNextRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class BrowseNextResult(FrozenClass):
    """
    :ivar Results:
    :vartype Results: BrowseResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('Results', 'ListOfBrowseResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'BrowseNextResult(Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class BrowseNextResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: BrowseNextResult
    """

    data_type = ObjectIds.BrowseNextResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'BrowseNextResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.BrowseNextResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = BrowseNextResult()
        self._freeze = True

    def __str__(self):
        return f'BrowseNextResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class RelativePathElement(FrozenClass):
    """
    :ivar ReferenceTypeId:
    :vartype ReferenceTypeId: NodeId
    :ivar IsInverse:
    :vartype IsInverse: Boolean
    :ivar IncludeSubtypes:
    :vartype IncludeSubtypes: Boolean
    :ivar TargetName:
    :vartype TargetName: QualifiedName
    """

    data_type = ObjectIds.RelativePathElement

    ua_types = [
        ('ReferenceTypeId', 'NodeId'),
        ('IsInverse', 'Boolean'),
        ('IncludeSubtypes', 'Boolean'),
        ('TargetName', 'QualifiedName'),
               ]

    def __init__(self):
        self.ReferenceTypeId = NodeId()
        self.IsInverse = True
        self.IncludeSubtypes = True
        self.TargetName = QualifiedName()
        self._freeze = True

    def __str__(self):
        return f'RelativePathElement(ReferenceTypeId:{self.ReferenceTypeId}, IsInverse:{self.IsInverse}, IncludeSubtypes:{self.IncludeSubtypes}, TargetName:{self.TargetName})'

    __repr__ = __str__


class RelativePath(FrozenClass):
    """
    :ivar Elements:
    :vartype Elements: RelativePathElement
    """

    data_type = ObjectIds.RelativePath

    ua_types = [
        ('Elements', 'ListOfRelativePathElement'),
               ]

    def __init__(self):
        self.Elements = []
        self._freeze = True

    def __str__(self):
        return f'RelativePath(Elements:{self.Elements})'

    __repr__ = __str__


class BrowsePath(FrozenClass):
    """
    :ivar StartingNode:
    :vartype StartingNode: NodeId
    :ivar RelativePath:
    :vartype RelativePath: RelativePath
    """

    data_type = ObjectIds.BrowsePath

    ua_types = [
        ('StartingNode', 'NodeId'),
        ('RelativePath', 'RelativePath'),
               ]

    def __init__(self):
        self.StartingNode = NodeId()
        self.RelativePath = RelativePath()
        self._freeze = True

    def __str__(self):
        return f'BrowsePath(StartingNode:{self.StartingNode}, RelativePath:{self.RelativePath})'

    __repr__ = __str__


class BrowsePathTarget(FrozenClass):
    """
    :ivar TargetId:
    :vartype TargetId: ExpandedNodeId
    :ivar RemainingPathIndex:
    :vartype RemainingPathIndex: UInt32
    """

    data_type = ObjectIds.BrowsePathTarget

    ua_types = [
        ('TargetId', 'ExpandedNodeId'),
        ('RemainingPathIndex', 'UInt32'),
               ]

    def __init__(self):
        self.TargetId = ExpandedNodeId()
        self.RemainingPathIndex = 0
        self._freeze = True

    def __str__(self):
        return f'BrowsePathTarget(TargetId:{self.TargetId}, RemainingPathIndex:{self.RemainingPathIndex})'

    __repr__ = __str__


class BrowsePathResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar Targets:
    :vartype Targets: BrowsePathTarget
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('Targets', 'ListOfBrowsePathTarget'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.Targets = []
        self._freeze = True

    def __str__(self):
        return f'BrowsePathResult(StatusCode:{self.StatusCode}, Targets:{self.Targets})'

    __repr__ = __str__


class TranslateBrowsePathsToNodeIdsParameters(FrozenClass):
    """
    :ivar BrowsePaths:
    :vartype BrowsePaths: BrowsePath
    """

    ua_types = [
        ('BrowsePaths', 'ListOfBrowsePath'),
               ]

    def __init__(self):
        self.BrowsePaths = []
        self._freeze = True

    def __str__(self):
        return f'TranslateBrowsePathsToNodeIdsParameters(BrowsePaths:{self.BrowsePaths})'

    __repr__ = __str__


class TranslateBrowsePathsToNodeIdsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: TranslateBrowsePathsToNodeIdsParameters
    """

    data_type = ObjectIds.TranslateBrowsePathsToNodeIdsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'TranslateBrowsePathsToNodeIdsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.TranslateBrowsePathsToNodeIdsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = TranslateBrowsePathsToNodeIdsParameters()
        self._freeze = True

    def __str__(self):
        return f'TranslateBrowsePathsToNodeIdsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class TranslateBrowsePathsToNodeIdsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: BrowsePathResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.TranslateBrowsePathsToNodeIdsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfBrowsePathResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.TranslateBrowsePathsToNodeIdsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'TranslateBrowsePathsToNodeIdsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class RegisterNodesParameters(FrozenClass):
    """
    :ivar NodesToRegister:
    :vartype NodesToRegister: NodeId
    """

    ua_types = [
        ('NodesToRegister', 'ListOfNodeId'),
               ]

    def __init__(self):
        self.NodesToRegister = []
        self._freeze = True

    def __str__(self):
        return f'RegisterNodesParameters(NodesToRegister:{self.NodesToRegister})'

    __repr__ = __str__


class RegisterNodesRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: RegisterNodesParameters
    """

    data_type = ObjectIds.RegisterNodesRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'RegisterNodesParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RegisterNodesRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = RegisterNodesParameters()
        self._freeze = True

    def __str__(self):
        return f'RegisterNodesRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class RegisterNodesResult(FrozenClass):
    """
    :ivar RegisteredNodeIds:
    :vartype RegisteredNodeIds: NodeId
    """

    ua_types = [
        ('RegisteredNodeIds', 'ListOfNodeId'),
               ]

    def __init__(self):
        self.RegisteredNodeIds = []
        self._freeze = True

    def __str__(self):
        return f'RegisterNodesResult(RegisteredNodeIds:{self.RegisteredNodeIds})'

    __repr__ = __str__


class RegisterNodesResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: RegisterNodesResult
    """

    data_type = ObjectIds.RegisterNodesResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'RegisterNodesResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RegisterNodesResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = RegisterNodesResult()
        self._freeze = True

    def __str__(self):
        return f'RegisterNodesResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class UnregisterNodesParameters(FrozenClass):
    """
    :ivar NodesToUnregister:
    :vartype NodesToUnregister: NodeId
    """

    ua_types = [
        ('NodesToUnregister', 'ListOfNodeId'),
               ]

    def __init__(self):
        self.NodesToUnregister = []
        self._freeze = True

    def __str__(self):
        return f'UnregisterNodesParameters(NodesToUnregister:{self.NodesToUnregister})'

    __repr__ = __str__


class UnregisterNodesRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: UnregisterNodesParameters
    """

    data_type = ObjectIds.UnregisterNodesRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'UnregisterNodesParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.UnregisterNodesRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = UnregisterNodesParameters()
        self._freeze = True

    def __str__(self):
        return f'UnregisterNodesRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class UnregisterNodesResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    """

    data_type = ObjectIds.UnregisterNodesResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.UnregisterNodesResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self._freeze = True

    def __str__(self):
        return f'UnregisterNodesResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader})'

    __repr__ = __str__


class EndpointConfiguration(FrozenClass):
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

    data_type = ObjectIds.EndpointConfiguration

    ua_types = [
        ('OperationTimeout', 'Int32'),
        ('UseBinaryEncoding', 'Boolean'),
        ('MaxStringLength', 'Int32'),
        ('MaxByteStringLength', 'Int32'),
        ('MaxArrayLength', 'Int32'),
        ('MaxMessageSize', 'Int32'),
        ('MaxBufferSize', 'Int32'),
        ('ChannelLifetime', 'Int32'),
        ('SecurityTokenLifetime', 'Int32'),
               ]

    def __init__(self):
        self.OperationTimeout = 0
        self.UseBinaryEncoding = True
        self.MaxStringLength = 0
        self.MaxByteStringLength = 0
        self.MaxArrayLength = 0
        self.MaxMessageSize = 0
        self.MaxBufferSize = 0
        self.ChannelLifetime = 0
        self.SecurityTokenLifetime = 0
        self._freeze = True

    def __str__(self):
        return f'EndpointConfiguration(OperationTimeout:{self.OperationTimeout}, UseBinaryEncoding:{self.UseBinaryEncoding}, MaxStringLength:{self.MaxStringLength}, MaxByteStringLength:{self.MaxByteStringLength}, MaxArrayLength:{self.MaxArrayLength}, MaxMessageSize:{self.MaxMessageSize}, MaxBufferSize:{self.MaxBufferSize}, ChannelLifetime:{self.ChannelLifetime}, SecurityTokenLifetime:{self.SecurityTokenLifetime})'

    __repr__ = __str__


class QueryDataDescription(FrozenClass):
    """
    :ivar RelativePath:
    :vartype RelativePath: RelativePath
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar IndexRange:
    :vartype IndexRange: String
    """

    data_type = ObjectIds.QueryDataDescription

    ua_types = [
        ('RelativePath', 'RelativePath'),
        ('AttributeId', 'UInt32'),
        ('IndexRange', 'String'),
               ]

    def __init__(self):
        self.RelativePath = RelativePath()
        self.AttributeId = 0
        self.IndexRange = None
        self._freeze = True

    def __str__(self):
        return f'QueryDataDescription(RelativePath:{self.RelativePath}, AttributeId:{self.AttributeId}, IndexRange:{self.IndexRange})'

    __repr__ = __str__


class NodeTypeDescription(FrozenClass):
    """
    :ivar TypeDefinitionNode:
    :vartype TypeDefinitionNode: ExpandedNodeId
    :ivar IncludeSubTypes:
    :vartype IncludeSubTypes: Boolean
    :ivar DataToReturn:
    :vartype DataToReturn: QueryDataDescription
    """

    data_type = ObjectIds.NodeTypeDescription

    ua_types = [
        ('TypeDefinitionNode', 'ExpandedNodeId'),
        ('IncludeSubTypes', 'Boolean'),
        ('DataToReturn', 'ListOfQueryDataDescription'),
               ]

    def __init__(self):
        self.TypeDefinitionNode = ExpandedNodeId()
        self.IncludeSubTypes = True
        self.DataToReturn = []
        self._freeze = True

    def __str__(self):
        return f'NodeTypeDescription(TypeDefinitionNode:{self.TypeDefinitionNode}, IncludeSubTypes:{self.IncludeSubTypes}, DataToReturn:{self.DataToReturn})'

    __repr__ = __str__


class QueryDataSet(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: ExpandedNodeId
    :ivar TypeDefinitionNode:
    :vartype TypeDefinitionNode: ExpandedNodeId
    :ivar Values:
    :vartype Values: Variant
    """

    data_type = ObjectIds.QueryDataSet

    ua_types = [
        ('NodeId', 'ExpandedNodeId'),
        ('TypeDefinitionNode', 'ExpandedNodeId'),
        ('Values', 'ListOfVariant'),
               ]

    def __init__(self):
        self.NodeId = ExpandedNodeId()
        self.TypeDefinitionNode = ExpandedNodeId()
        self.Values = []
        self._freeze = True

    def __str__(self):
        return f'QueryDataSet(NodeId:{self.NodeId}, TypeDefinitionNode:{self.TypeDefinitionNode}, Values:{self.Values})'

    __repr__ = __str__


class NodeReference(FrozenClass):
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

    data_type = ObjectIds.NodeReference

    ua_types = [
        ('NodeId', 'NodeId'),
        ('ReferenceTypeId', 'NodeId'),
        ('IsForward', 'Boolean'),
        ('ReferencedNodeIds', 'ListOfNodeId'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.ReferenceTypeId = NodeId()
        self.IsForward = True
        self.ReferencedNodeIds = []
        self._freeze = True

    def __str__(self):
        return f'NodeReference(NodeId:{self.NodeId}, ReferenceTypeId:{self.ReferenceTypeId}, IsForward:{self.IsForward}, ReferencedNodeIds:{self.ReferencedNodeIds})'

    __repr__ = __str__


class ContentFilterElement(FrozenClass):
    """
    :ivar FilterOperator:
    :vartype FilterOperator: FilterOperator
    :ivar FilterOperands:
    :vartype FilterOperands: ExtensionObject
    """

    data_type = ObjectIds.ContentFilterElement

    ua_types = [
        ('FilterOperator', 'FilterOperator'),
        ('FilterOperands', 'ListOfExtensionObject'),
               ]

    def __init__(self):
        self.FilterOperator = FilterOperator(0)
        self.FilterOperands = []
        self._freeze = True

    def __str__(self):
        return f'ContentFilterElement(FilterOperator:{self.FilterOperator}, FilterOperands:{self.FilterOperands})'

    __repr__ = __str__


class ContentFilter(FrozenClass):
    """
    :ivar Elements:
    :vartype Elements: ContentFilterElement
    """

    data_type = ObjectIds.ContentFilter

    ua_types = [
        ('Elements', 'ListOfContentFilterElement'),
               ]

    def __init__(self):
        self.Elements = []
        self._freeze = True

    def __str__(self):
        return f'ContentFilter(Elements:{self.Elements})'

    __repr__ = __str__


class ElementOperand(FrozenClass):
    """
    :ivar Index:
    :vartype Index: UInt32
    """

    data_type = ObjectIds.ElementOperand

    ua_types = [
        ('Index', 'UInt32'),
               ]

    def __init__(self):
        self.Index = 0
        self._freeze = True

    def __str__(self):
        return f'ElementOperand(Index:{self.Index})'

    __repr__ = __str__


class LiteralOperand(FrozenClass):
    """
    :ivar Value:
    :vartype Value: Variant
    """

    data_type = ObjectIds.LiteralOperand

    ua_types = [
        ('Value', 'Variant'),
               ]

    def __init__(self):
        self.Value = Variant()
        self._freeze = True

    def __str__(self):
        return f'LiteralOperand(Value:{self.Value})'

    __repr__ = __str__


class AttributeOperand(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar Alias:
    :vartype Alias: String
    :ivar BrowsePath:
    :vartype BrowsePath: RelativePath
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar IndexRange:
    :vartype IndexRange: String
    """

    data_type = ObjectIds.AttributeOperand

    ua_types = [
        ('NodeId', 'NodeId'),
        ('Alias', 'String'),
        ('BrowsePath', 'RelativePath'),
        ('AttributeId', 'UInt32'),
        ('IndexRange', 'String'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.Alias = None
        self.BrowsePath = RelativePath()
        self.AttributeId = 0
        self.IndexRange = None
        self._freeze = True

    def __str__(self):
        return f'AttributeOperand(NodeId:{self.NodeId}, Alias:{self.Alias}, BrowsePath:{self.BrowsePath}, AttributeId:{self.AttributeId}, IndexRange:{self.IndexRange})'

    __repr__ = __str__


class SimpleAttributeOperand(FrozenClass):
    """
    :ivar TypeDefinitionId:
    :vartype TypeDefinitionId: NodeId
    :ivar BrowsePath:
    :vartype BrowsePath: QualifiedName
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar IndexRange:
    :vartype IndexRange: String
    """

    data_type = ObjectIds.SimpleAttributeOperand

    ua_types = [
        ('TypeDefinitionId', 'NodeId'),
        ('BrowsePath', 'ListOfQualifiedName'),
        ('AttributeId', 'UInt32'),
        ('IndexRange', 'String'),
               ]

    def __init__(self):
        self.TypeDefinitionId = NodeId()
        self.BrowsePath = []
        self.AttributeId = 0
        self.IndexRange = None
        self._freeze = True

    def __str__(self):
        return f'SimpleAttributeOperand(TypeDefinitionId:{self.TypeDefinitionId}, BrowsePath:{self.BrowsePath}, AttributeId:{self.AttributeId}, IndexRange:{self.IndexRange})'

    __repr__ = __str__


class ContentFilterElementResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar OperandStatusCodes:
    :vartype OperandStatusCodes: StatusCode
    :ivar OperandDiagnosticInfos:
    :vartype OperandDiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('OperandStatusCodes', 'ListOfStatusCode'),
        ('OperandDiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.OperandStatusCodes = []
        self.OperandDiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'ContentFilterElementResult(StatusCode:{self.StatusCode}, OperandStatusCodes:{self.OperandStatusCodes}, OperandDiagnosticInfos:{self.OperandDiagnosticInfos})'

    __repr__ = __str__


class ContentFilterResult(FrozenClass):
    """
    :ivar ElementResults:
    :vartype ElementResults: ContentFilterElementResult
    :ivar ElementDiagnosticInfos:
    :vartype ElementDiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('ElementResults', 'ListOfContentFilterElementResult'),
        ('ElementDiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.ElementResults = []
        self.ElementDiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'ContentFilterResult(ElementResults:{self.ElementResults}, ElementDiagnosticInfos:{self.ElementDiagnosticInfos})'

    __repr__ = __str__


class ParsingResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar DataStatusCodes:
    :vartype DataStatusCodes: StatusCode
    :ivar DataDiagnosticInfos:
    :vartype DataDiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('DataStatusCodes', 'ListOfStatusCode'),
        ('DataDiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.DataStatusCodes = []
        self.DataDiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'ParsingResult(StatusCode:{self.StatusCode}, DataStatusCodes:{self.DataStatusCodes}, DataDiagnosticInfos:{self.DataDiagnosticInfos})'

    __repr__ = __str__


class QueryFirstParameters(FrozenClass):
    """
    :ivar View:
    :vartype View: ViewDescription
    :ivar NodeTypes:
    :vartype NodeTypes: NodeTypeDescription
    :ivar Filter:
    :vartype Filter: ContentFilter
    :ivar MaxDataSetsToReturn:
    :vartype MaxDataSetsToReturn: UInt32
    :ivar MaxReferencesToReturn:
    :vartype MaxReferencesToReturn: UInt32
    """

    ua_types = [
        ('View', 'ViewDescription'),
        ('NodeTypes', 'ListOfNodeTypeDescription'),
        ('Filter', 'ContentFilter'),
        ('MaxDataSetsToReturn', 'UInt32'),
        ('MaxReferencesToReturn', 'UInt32'),
               ]

    def __init__(self):
        self.View = ViewDescription()
        self.NodeTypes = []
        self.Filter = ContentFilter()
        self.MaxDataSetsToReturn = 0
        self.MaxReferencesToReturn = 0
        self._freeze = True

    def __str__(self):
        return f'QueryFirstParameters(View:{self.View}, NodeTypes:{self.NodeTypes}, Filter:{self.Filter}, MaxDataSetsToReturn:{self.MaxDataSetsToReturn}, MaxReferencesToReturn:{self.MaxReferencesToReturn})'

    __repr__ = __str__


class QueryFirstRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: QueryFirstParameters
    """

    data_type = ObjectIds.QueryFirstRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'QueryFirstParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.QueryFirstRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = QueryFirstParameters()
        self._freeze = True

    def __str__(self):
        return f'QueryFirstRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class QueryFirstResult(FrozenClass):
    """
    :ivar QueryDataSets:
    :vartype QueryDataSets: QueryDataSet
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ByteString
    :ivar ParsingResults:
    :vartype ParsingResults: ParsingResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    :ivar FilterResult:
    :vartype FilterResult: ContentFilterResult
    """

    ua_types = [
        ('QueryDataSets', 'ListOfQueryDataSet'),
        ('ContinuationPoint', 'ByteString'),
        ('ParsingResults', 'ListOfParsingResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
        ('FilterResult', 'ContentFilterResult'),
               ]

    def __init__(self):
        self.QueryDataSets = []
        self.ContinuationPoint = None
        self.ParsingResults = []
        self.DiagnosticInfos = []
        self.FilterResult = ContentFilterResult()
        self._freeze = True

    def __str__(self):
        return f'QueryFirstResult(QueryDataSets:{self.QueryDataSets}, ContinuationPoint:{self.ContinuationPoint}, ParsingResults:{self.ParsingResults}, DiagnosticInfos:{self.DiagnosticInfos}, FilterResult:{self.FilterResult})'

    __repr__ = __str__


class QueryFirstResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: QueryFirstResult
    """

    data_type = ObjectIds.QueryFirstResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'QueryFirstResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.QueryFirstResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = QueryFirstResult()
        self._freeze = True

    def __str__(self):
        return f'QueryFirstResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class QueryNextParameters(FrozenClass):
    """
    :ivar ReleaseContinuationPoint:
    :vartype ReleaseContinuationPoint: Boolean
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ByteString
    """

    ua_types = [
        ('ReleaseContinuationPoint', 'Boolean'),
        ('ContinuationPoint', 'ByteString'),
               ]

    def __init__(self):
        self.ReleaseContinuationPoint = True
        self.ContinuationPoint = None
        self._freeze = True

    def __str__(self):
        return f'QueryNextParameters(ReleaseContinuationPoint:{self.ReleaseContinuationPoint}, ContinuationPoint:{self.ContinuationPoint})'

    __repr__ = __str__


class QueryNextRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: QueryNextParameters
    """

    data_type = ObjectIds.QueryNextRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'QueryNextParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.QueryNextRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = QueryNextParameters()
        self._freeze = True

    def __str__(self):
        return f'QueryNextRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class QueryNextResult(FrozenClass):
    """
    :ivar QueryDataSets:
    :vartype QueryDataSets: QueryDataSet
    :ivar RevisedContinuationPoint:
    :vartype RevisedContinuationPoint: ByteString
    """

    ua_types = [
        ('QueryDataSets', 'ListOfQueryDataSet'),
        ('RevisedContinuationPoint', 'ByteString'),
               ]

    def __init__(self):
        self.QueryDataSets = []
        self.RevisedContinuationPoint = None
        self._freeze = True

    def __str__(self):
        return f'QueryNextResult(QueryDataSets:{self.QueryDataSets}, RevisedContinuationPoint:{self.RevisedContinuationPoint})'

    __repr__ = __str__


class QueryNextResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: QueryNextResult
    """

    data_type = ObjectIds.QueryNextResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'QueryNextResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.QueryNextResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = QueryNextResult()
        self._freeze = True

    def __str__(self):
        return f'QueryNextResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ReadValueId(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar IndexRange:
    :vartype IndexRange: String
    :ivar DataEncoding:
    :vartype DataEncoding: QualifiedName
    """

    data_type = ObjectIds.ReadValueId

    ua_types = [
        ('NodeId', 'NodeId'),
        ('AttributeId', 'UInt32'),
        ('IndexRange', 'String'),
        ('DataEncoding', 'QualifiedName'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.AttributeId = 0
        self.IndexRange = None
        self.DataEncoding = QualifiedName()
        self._freeze = True

    def __str__(self):
        return f'ReadValueId(NodeId:{self.NodeId}, AttributeId:{self.AttributeId}, IndexRange:{self.IndexRange}, DataEncoding:{self.DataEncoding})'

    __repr__ = __str__


class ReadParameters(FrozenClass):
    """
    :ivar MaxAge:
    :vartype MaxAge: Double
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar NodesToRead:
    :vartype NodesToRead: ReadValueId
    """

    ua_types = [
        ('MaxAge', 'Double'),
        ('TimestampsToReturn', 'TimestampsToReturn'),
        ('NodesToRead', 'ListOfReadValueId'),
               ]

    def __init__(self):
        self.MaxAge = 0
        self.TimestampsToReturn = TimestampsToReturn(0)
        self.NodesToRead = []
        self._freeze = True

    def __str__(self):
        return f'ReadParameters(MaxAge:{self.MaxAge}, TimestampsToReturn:{self.TimestampsToReturn}, NodesToRead:{self.NodesToRead})'

    __repr__ = __str__


class ReadRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ReadParameters
    """

    data_type = ObjectIds.ReadRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'ReadParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ReadRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = ReadParameters()
        self._freeze = True

    def __str__(self):
        return f'ReadRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ReadResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: DataValue
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.ReadResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfDataValue'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ReadResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'ReadResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class HistoryReadValueId(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar IndexRange:
    :vartype IndexRange: String
    :ivar DataEncoding:
    :vartype DataEncoding: QualifiedName
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ByteString
    """

    data_type = ObjectIds.HistoryReadValueId

    ua_types = [
        ('NodeId', 'NodeId'),
        ('IndexRange', 'String'),
        ('DataEncoding', 'QualifiedName'),
        ('ContinuationPoint', 'ByteString'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.IndexRange = None
        self.DataEncoding = QualifiedName()
        self.ContinuationPoint = None
        self._freeze = True

    def __str__(self):
        return f'HistoryReadValueId(NodeId:{self.NodeId}, IndexRange:{self.IndexRange}, DataEncoding:{self.DataEncoding}, ContinuationPoint:{self.ContinuationPoint})'

    __repr__ = __str__


class HistoryReadResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar ContinuationPoint:
    :vartype ContinuationPoint: ByteString
    :ivar HistoryData:
    :vartype HistoryData: ExtensionObject
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('ContinuationPoint', 'ByteString'),
        ('HistoryData', 'ExtensionObject'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.ContinuationPoint = None
        self.HistoryData = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'HistoryReadResult(StatusCode:{self.StatusCode}, ContinuationPoint:{self.ContinuationPoint}, HistoryData:{self.HistoryData})'

    __repr__ = __str__


class HistoryReadDetails(FrozenClass):
    """
    """

    data_type = ObjectIds.HistoryReadDetails

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'HistoryReadDetails()'

    __repr__ = __str__


class ReadEventDetails(FrozenClass):
    """
    :ivar NumValuesPerNode:
    :vartype NumValuesPerNode: UInt32
    :ivar StartTime:
    :vartype StartTime: DateTime
    :ivar EndTime:
    :vartype EndTime: DateTime
    :ivar Filter:
    :vartype Filter: EventFilter
    """

    data_type = ObjectIds.ReadEventDetails

    ua_types = [
        ('NumValuesPerNode', 'UInt32'),
        ('StartTime', 'DateTime'),
        ('EndTime', 'DateTime'),
        ('Filter', 'EventFilter'),
               ]

    def __init__(self):
        self.NumValuesPerNode = 0
        self.StartTime = datetime.utcnow()
        self.EndTime = datetime.utcnow()
        self.Filter = EventFilter()
        self._freeze = True

    def __str__(self):
        return f'ReadEventDetails(NumValuesPerNode:{self.NumValuesPerNode}, StartTime:{self.StartTime}, EndTime:{self.EndTime}, Filter:{self.Filter})'

    __repr__ = __str__


class ReadRawModifiedDetails(FrozenClass):
    """
    :ivar IsReadModified:
    :vartype IsReadModified: Boolean
    :ivar StartTime:
    :vartype StartTime: DateTime
    :ivar EndTime:
    :vartype EndTime: DateTime
    :ivar NumValuesPerNode:
    :vartype NumValuesPerNode: UInt32
    :ivar ReturnBounds:
    :vartype ReturnBounds: Boolean
    """

    data_type = ObjectIds.ReadRawModifiedDetails

    ua_types = [
        ('IsReadModified', 'Boolean'),
        ('StartTime', 'DateTime'),
        ('EndTime', 'DateTime'),
        ('NumValuesPerNode', 'UInt32'),
        ('ReturnBounds', 'Boolean'),
               ]

    def __init__(self):
        self.IsReadModified = True
        self.StartTime = datetime.utcnow()
        self.EndTime = datetime.utcnow()
        self.NumValuesPerNode = 0
        self.ReturnBounds = True
        self._freeze = True

    def __str__(self):
        return f'ReadRawModifiedDetails(IsReadModified:{self.IsReadModified}, StartTime:{self.StartTime}, EndTime:{self.EndTime}, NumValuesPerNode:{self.NumValuesPerNode}, ReturnBounds:{self.ReturnBounds})'

    __repr__ = __str__


class ReadProcessedDetails(FrozenClass):
    """
    :ivar StartTime:
    :vartype StartTime: DateTime
    :ivar EndTime:
    :vartype EndTime: DateTime
    :ivar ProcessingInterval:
    :vartype ProcessingInterval: Double
    :ivar AggregateType:
    :vartype AggregateType: NodeId
    :ivar AggregateConfiguration:
    :vartype AggregateConfiguration: AggregateConfiguration
    """

    data_type = ObjectIds.ReadProcessedDetails

    ua_types = [
        ('StartTime', 'DateTime'),
        ('EndTime', 'DateTime'),
        ('ProcessingInterval', 'Double'),
        ('AggregateType', 'ListOfNodeId'),
        ('AggregateConfiguration', 'AggregateConfiguration'),
               ]

    def __init__(self):
        self.StartTime = datetime.utcnow()
        self.EndTime = datetime.utcnow()
        self.ProcessingInterval = 0
        self.AggregateType = []
        self.AggregateConfiguration = AggregateConfiguration()
        self._freeze = True

    def __str__(self):
        return f'ReadProcessedDetails(StartTime:{self.StartTime}, EndTime:{self.EndTime}, ProcessingInterval:{self.ProcessingInterval}, AggregateType:{self.AggregateType}, AggregateConfiguration:{self.AggregateConfiguration})'

    __repr__ = __str__


class ReadAtTimeDetails(FrozenClass):
    """
    :ivar ReqTimes:
    :vartype ReqTimes: DateTime
    :ivar UseSimpleBounds:
    :vartype UseSimpleBounds: Boolean
    """

    data_type = ObjectIds.ReadAtTimeDetails

    ua_types = [
        ('ReqTimes', 'ListOfDateTime'),
        ('UseSimpleBounds', 'Boolean'),
               ]

    def __init__(self):
        self.ReqTimes = []
        self.UseSimpleBounds = True
        self._freeze = True

    def __str__(self):
        return f'ReadAtTimeDetails(ReqTimes:{self.ReqTimes}, UseSimpleBounds:{self.UseSimpleBounds})'

    __repr__ = __str__


class ReadAnnotationDataDetails(FrozenClass):
    """
    :ivar ReqTimes:
    :vartype ReqTimes: DateTime
    """

    data_type = ObjectIds.ReadAnnotationDataDetails

    ua_types = [
        ('ReqTimes', 'ListOfDateTime'),
               ]

    def __init__(self):
        self.ReqTimes = []
        self._freeze = True

    def __str__(self):
        return f'ReadAnnotationDataDetails(ReqTimes:{self.ReqTimes})'

    __repr__ = __str__


class HistoryData(FrozenClass):
    """
    :ivar DataValues:
    :vartype DataValues: DataValue
    """

    data_type = ObjectIds.HistoryData

    ua_types = [
        ('DataValues', 'ListOfDataValue'),
               ]

    def __init__(self):
        self.DataValues = []
        self._freeze = True

    def __str__(self):
        return f'HistoryData(DataValues:{self.DataValues})'

    __repr__ = __str__


class ModificationInfo(FrozenClass):
    """
    :ivar ModificationTime:
    :vartype ModificationTime: DateTime
    :ivar UpdateType:
    :vartype UpdateType: HistoryUpdateType
    :ivar UserName:
    :vartype UserName: String
    """

    data_type = ObjectIds.ModificationInfo

    ua_types = [
        ('ModificationTime', 'DateTime'),
        ('UpdateType', 'HistoryUpdateType'),
        ('UserName', 'String'),
               ]

    def __init__(self):
        self.ModificationTime = datetime.utcnow()
        self.UpdateType = HistoryUpdateType(0)
        self.UserName = None
        self._freeze = True

    def __str__(self):
        return f'ModificationInfo(ModificationTime:{self.ModificationTime}, UpdateType:{self.UpdateType}, UserName:{self.UserName})'

    __repr__ = __str__


class HistoryModifiedData(FrozenClass):
    """
    :ivar DataValues:
    :vartype DataValues: DataValue
    :ivar ModificationInfos:
    :vartype ModificationInfos: ModificationInfo
    """

    data_type = ObjectIds.HistoryModifiedData

    ua_types = [
        ('DataValues', 'ListOfDataValue'),
        ('ModificationInfos', 'ListOfModificationInfo'),
               ]

    def __init__(self):
        self.DataValues = []
        self.ModificationInfos = []
        self._freeze = True

    def __str__(self):
        return f'HistoryModifiedData(DataValues:{self.DataValues}, ModificationInfos:{self.ModificationInfos})'

    __repr__ = __str__


class HistoryEvent(FrozenClass):
    """
    :ivar Events:
    :vartype Events: HistoryEventFieldList
    """

    data_type = ObjectIds.HistoryEvent

    ua_types = [
        ('Events', 'ListOfHistoryEventFieldList'),
               ]

    def __init__(self):
        self.Events = []
        self._freeze = True

    def __str__(self):
        return f'HistoryEvent(Events:{self.Events})'

    __repr__ = __str__


class HistoryReadParameters(FrozenClass):
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

    ua_types = [
        ('HistoryReadDetails', 'ExtensionObject'),
        ('TimestampsToReturn', 'TimestampsToReturn'),
        ('ReleaseContinuationPoints', 'Boolean'),
        ('NodesToRead', 'ListOfHistoryReadValueId'),
               ]

    def __init__(self):
        self.HistoryReadDetails = ExtensionObject()
        self.TimestampsToReturn = TimestampsToReturn(0)
        self.ReleaseContinuationPoints = True
        self.NodesToRead = []
        self._freeze = True

    def __str__(self):
        return f'HistoryReadParameters(HistoryReadDetails:{self.HistoryReadDetails}, TimestampsToReturn:{self.TimestampsToReturn}, ReleaseContinuationPoints:{self.ReleaseContinuationPoints}, NodesToRead:{self.NodesToRead})'

    __repr__ = __str__


class HistoryReadRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: HistoryReadParameters
    """

    data_type = ObjectIds.HistoryReadRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'HistoryReadParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.HistoryReadRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = HistoryReadParameters()
        self._freeze = True

    def __str__(self):
        return f'HistoryReadRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class HistoryReadResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: HistoryReadResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.HistoryReadResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfHistoryReadResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.HistoryReadResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'HistoryReadResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class WriteValue(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar AttributeId:
    :vartype AttributeId: UInt32
    :ivar IndexRange:
    :vartype IndexRange: String
    :ivar Value:
    :vartype Value: DataValue
    """

    data_type = ObjectIds.WriteValue

    ua_types = [
        ('NodeId', 'NodeId'),
        ('AttributeId', 'UInt32'),
        ('IndexRange', 'String'),
        ('Value', 'DataValue'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.AttributeId = 0
        self.IndexRange = None
        self.Value = DataValue()
        self._freeze = True

    def __str__(self):
        return f'WriteValue(NodeId:{self.NodeId}, AttributeId:{self.AttributeId}, IndexRange:{self.IndexRange}, Value:{self.Value})'

    __repr__ = __str__


class WriteParameters(FrozenClass):
    """
    :ivar NodesToWrite:
    :vartype NodesToWrite: WriteValue
    """

    ua_types = [
        ('NodesToWrite', 'ListOfWriteValue'),
               ]

    def __init__(self):
        self.NodesToWrite = []
        self._freeze = True

    def __str__(self):
        return f'WriteParameters(NodesToWrite:{self.NodesToWrite})'

    __repr__ = __str__


class WriteRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: WriteParameters
    """

    data_type = ObjectIds.WriteRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'WriteParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.WriteRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = WriteParameters()
        self._freeze = True

    def __str__(self):
        return f'WriteRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class WriteResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.WriteResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.WriteResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'WriteResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class HistoryUpdateDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    """

    data_type = ObjectIds.HistoryUpdateDetails

    ua_types = [
        ('NodeId', 'NodeId'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self._freeze = True

    def __str__(self):
        return f'HistoryUpdateDetails(NodeId:{self.NodeId})'

    __repr__ = __str__


class UpdateDataDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar PerformInsertReplace:
    :vartype PerformInsertReplace: PerformUpdateType
    :ivar UpdateValues:
    :vartype UpdateValues: DataValue
    """

    data_type = ObjectIds.UpdateDataDetails

    ua_types = [
        ('NodeId', 'NodeId'),
        ('PerformInsertReplace', 'PerformUpdateType'),
        ('UpdateValues', 'ListOfDataValue'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.PerformInsertReplace = PerformUpdateType(0)
        self.UpdateValues = []
        self._freeze = True

    def __str__(self):
        return f'UpdateDataDetails(NodeId:{self.NodeId}, PerformInsertReplace:{self.PerformInsertReplace}, UpdateValues:{self.UpdateValues})'

    __repr__ = __str__


class UpdateStructureDataDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar PerformInsertReplace:
    :vartype PerformInsertReplace: PerformUpdateType
    :ivar UpdateValues:
    :vartype UpdateValues: DataValue
    """

    data_type = ObjectIds.UpdateStructureDataDetails

    ua_types = [
        ('NodeId', 'NodeId'),
        ('PerformInsertReplace', 'PerformUpdateType'),
        ('UpdateValues', 'ListOfDataValue'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.PerformInsertReplace = PerformUpdateType(0)
        self.UpdateValues = []
        self._freeze = True

    def __str__(self):
        return f'UpdateStructureDataDetails(NodeId:{self.NodeId}, PerformInsertReplace:{self.PerformInsertReplace}, UpdateValues:{self.UpdateValues})'

    __repr__ = __str__


class UpdateEventDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar PerformInsertReplace:
    :vartype PerformInsertReplace: PerformUpdateType
    :ivar Filter:
    :vartype Filter: EventFilter
    :ivar EventData:
    :vartype EventData: HistoryEventFieldList
    """

    data_type = ObjectIds.UpdateEventDetails

    ua_types = [
        ('NodeId', 'NodeId'),
        ('PerformInsertReplace', 'PerformUpdateType'),
        ('Filter', 'EventFilter'),
        ('EventData', 'ListOfHistoryEventFieldList'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.PerformInsertReplace = PerformUpdateType(0)
        self.Filter = EventFilter()
        self.EventData = []
        self._freeze = True

    def __str__(self):
        return f'UpdateEventDetails(NodeId:{self.NodeId}, PerformInsertReplace:{self.PerformInsertReplace}, Filter:{self.Filter}, EventData:{self.EventData})'

    __repr__ = __str__


class DeleteRawModifiedDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar IsDeleteModified:
    :vartype IsDeleteModified: Boolean
    :ivar StartTime:
    :vartype StartTime: DateTime
    :ivar EndTime:
    :vartype EndTime: DateTime
    """

    data_type = ObjectIds.DeleteRawModifiedDetails

    ua_types = [
        ('NodeId', 'NodeId'),
        ('IsDeleteModified', 'Boolean'),
        ('StartTime', 'DateTime'),
        ('EndTime', 'DateTime'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.IsDeleteModified = True
        self.StartTime = datetime.utcnow()
        self.EndTime = datetime.utcnow()
        self._freeze = True

    def __str__(self):
        return f'DeleteRawModifiedDetails(NodeId:{self.NodeId}, IsDeleteModified:{self.IsDeleteModified}, StartTime:{self.StartTime}, EndTime:{self.EndTime})'

    __repr__ = __str__


class DeleteAtTimeDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar ReqTimes:
    :vartype ReqTimes: DateTime
    """

    data_type = ObjectIds.DeleteAtTimeDetails

    ua_types = [
        ('NodeId', 'NodeId'),
        ('ReqTimes', 'ListOfDateTime'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.ReqTimes = []
        self._freeze = True

    def __str__(self):
        return f'DeleteAtTimeDetails(NodeId:{self.NodeId}, ReqTimes:{self.ReqTimes})'

    __repr__ = __str__


class DeleteEventDetails(FrozenClass):
    """
    :ivar NodeId:
    :vartype NodeId: NodeId
    :ivar EventIds:
    :vartype EventIds: ByteString
    """

    data_type = ObjectIds.DeleteEventDetails

    ua_types = [
        ('NodeId', 'NodeId'),
        ('EventIds', 'ListOfByteString'),
               ]

    def __init__(self):
        self.NodeId = NodeId()
        self.EventIds = []
        self._freeze = True

    def __str__(self):
        return f'DeleteEventDetails(NodeId:{self.NodeId}, EventIds:{self.EventIds})'

    __repr__ = __str__


class HistoryUpdateResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar OperationResults:
    :vartype OperationResults: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('OperationResults', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.OperationResults = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'HistoryUpdateResult(StatusCode:{self.StatusCode}, OperationResults:{self.OperationResults}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class HistoryUpdateParameters(FrozenClass):
    """
    :ivar HistoryUpdateDetails:
    :vartype HistoryUpdateDetails: ExtensionObject
    """

    ua_types = [
        ('HistoryUpdateDetails', 'ListOfExtensionObject'),
               ]

    def __init__(self):
        self.HistoryUpdateDetails = []
        self._freeze = True

    def __str__(self):
        return f'HistoryUpdateParameters(HistoryUpdateDetails:{self.HistoryUpdateDetails})'

    __repr__ = __str__


class HistoryUpdateRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: HistoryUpdateParameters
    """

    data_type = ObjectIds.HistoryUpdateRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'HistoryUpdateParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.HistoryUpdateRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = HistoryUpdateParameters()
        self._freeze = True

    def __str__(self):
        return f'HistoryUpdateRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class HistoryUpdateResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: HistoryUpdateResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.HistoryUpdateResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfHistoryUpdateResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.HistoryUpdateResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'HistoryUpdateResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class CallMethodRequest(FrozenClass):
    """
    :ivar ObjectId:
    :vartype ObjectId: NodeId
    :ivar MethodId:
    :vartype MethodId: NodeId
    :ivar InputArguments:
    :vartype InputArguments: Variant
    """

    data_type = ObjectIds.CallMethodRequest

    ua_types = [
        ('ObjectId', 'NodeId'),
        ('MethodId', 'NodeId'),
        ('InputArguments', 'ListOfVariant'),
               ]

    def __init__(self):
        self.ObjectId = NodeId()
        self.MethodId = NodeId()
        self.InputArguments = []
        self._freeze = True

    def __str__(self):
        return f'CallMethodRequest(ObjectId:{self.ObjectId}, MethodId:{self.MethodId}, InputArguments:{self.InputArguments})'

    __repr__ = __str__


class CallMethodResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar InputArgumentResults:
    :vartype InputArgumentResults: StatusCode
    :ivar InputArgumentDiagnosticInfos:
    :vartype InputArgumentDiagnosticInfos: DiagnosticInfo
    :ivar OutputArguments:
    :vartype OutputArguments: Variant
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('InputArgumentResults', 'ListOfStatusCode'),
        ('InputArgumentDiagnosticInfos', 'ListOfDiagnosticInfo'),
        ('OutputArguments', 'ListOfVariant'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.InputArgumentResults = []
        self.InputArgumentDiagnosticInfos = []
        self.OutputArguments = []
        self._freeze = True

    def __str__(self):
        return f'CallMethodResult(StatusCode:{self.StatusCode}, InputArgumentResults:{self.InputArgumentResults}, InputArgumentDiagnosticInfos:{self.InputArgumentDiagnosticInfos}, OutputArguments:{self.OutputArguments})'

    __repr__ = __str__


class CallParameters(FrozenClass):
    """
    :ivar MethodsToCall:
    :vartype MethodsToCall: CallMethodRequest
    """

    ua_types = [
        ('MethodsToCall', 'ListOfCallMethodRequest'),
               ]

    def __init__(self):
        self.MethodsToCall = []
        self._freeze = True

    def __str__(self):
        return f'CallParameters(MethodsToCall:{self.MethodsToCall})'

    __repr__ = __str__


class CallRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CallParameters
    """

    data_type = ObjectIds.CallRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'CallParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CallRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = CallParameters()
        self._freeze = True

    def __str__(self):
        return f'CallRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CallResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: CallMethodResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.CallResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfCallMethodResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CallResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'CallResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class MonitoringFilter(FrozenClass):
    """
    """

    data_type = ObjectIds.MonitoringFilter

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'MonitoringFilter()'

    __repr__ = __str__


class DataChangeFilter(FrozenClass):
    """
    :ivar Trigger:
    :vartype Trigger: DataChangeTrigger
    :ivar DeadbandType:
    :vartype DeadbandType: UInt32
    :ivar DeadbandValue:
    :vartype DeadbandValue: Double
    """

    data_type = ObjectIds.DataChangeFilter

    ua_types = [
        ('Trigger', 'DataChangeTrigger'),
        ('DeadbandType', 'UInt32'),
        ('DeadbandValue', 'Double'),
               ]

    def __init__(self):
        self.Trigger = DataChangeTrigger(0)
        self.DeadbandType = 0
        self.DeadbandValue = 0
        self._freeze = True

    def __str__(self):
        return f'DataChangeFilter(Trigger:{self.Trigger}, DeadbandType:{self.DeadbandType}, DeadbandValue:{self.DeadbandValue})'

    __repr__ = __str__


class EventFilter(FrozenClass):
    """
    :ivar SelectClauses:
    :vartype SelectClauses: SimpleAttributeOperand
    :ivar WhereClause:
    :vartype WhereClause: ContentFilter
    """

    data_type = ObjectIds.EventFilter

    ua_types = [
        ('SelectClauses', 'ListOfSimpleAttributeOperand'),
        ('WhereClause', 'ContentFilter'),
               ]

    def __init__(self):
        self.SelectClauses = []
        self.WhereClause = ContentFilter()
        self._freeze = True

    def __str__(self):
        return f'EventFilter(SelectClauses:{self.SelectClauses}, WhereClause:{self.WhereClause})'

    __repr__ = __str__


class AggregateConfiguration(FrozenClass):
    """
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

    data_type = ObjectIds.AggregateConfiguration

    ua_types = [
        ('UseServerCapabilitiesDefaults', 'Boolean'),
        ('TreatUncertainAsBad', 'Boolean'),
        ('PercentDataBad', 'Byte'),
        ('PercentDataGood', 'Byte'),
        ('UseSlopedExtrapolation', 'Boolean'),
               ]

    def __init__(self):
        self.UseServerCapabilitiesDefaults = True
        self.TreatUncertainAsBad = True
        self.PercentDataBad = 0
        self.PercentDataGood = 0
        self.UseSlopedExtrapolation = True
        self._freeze = True

    def __str__(self):
        return f'AggregateConfiguration(UseServerCapabilitiesDefaults:{self.UseServerCapabilitiesDefaults}, TreatUncertainAsBad:{self.TreatUncertainAsBad}, PercentDataBad:{self.PercentDataBad}, PercentDataGood:{self.PercentDataGood}, UseSlopedExtrapolation:{self.UseSlopedExtrapolation})'

    __repr__ = __str__


class AggregateFilter(FrozenClass):
    """
    :ivar StartTime:
    :vartype StartTime: DateTime
    :ivar AggregateType:
    :vartype AggregateType: NodeId
    :ivar ProcessingInterval:
    :vartype ProcessingInterval: Double
    :ivar AggregateConfiguration:
    :vartype AggregateConfiguration: AggregateConfiguration
    """

    data_type = ObjectIds.AggregateFilter

    ua_types = [
        ('StartTime', 'DateTime'),
        ('AggregateType', 'NodeId'),
        ('ProcessingInterval', 'Double'),
        ('AggregateConfiguration', 'AggregateConfiguration'),
               ]

    def __init__(self):
        self.StartTime = datetime.utcnow()
        self.AggregateType = NodeId()
        self.ProcessingInterval = 0
        self.AggregateConfiguration = AggregateConfiguration()
        self._freeze = True

    def __str__(self):
        return f'AggregateFilter(StartTime:{self.StartTime}, AggregateType:{self.AggregateType}, ProcessingInterval:{self.ProcessingInterval}, AggregateConfiguration:{self.AggregateConfiguration})'

    __repr__ = __str__


class MonitoringFilterResult(FrozenClass):
    """
    """

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'MonitoringFilterResult()'

    __repr__ = __str__


class EventFilterResult(FrozenClass):
    """
    :ivar SelectClauseResults:
    :vartype SelectClauseResults: StatusCode
    :ivar SelectClauseDiagnosticInfos:
    :vartype SelectClauseDiagnosticInfos: DiagnosticInfo
    :ivar WhereClauseResult:
    :vartype WhereClauseResult: ContentFilterResult
    """

    ua_types = [
        ('SelectClauseResults', 'ListOfStatusCode'),
        ('SelectClauseDiagnosticInfos', 'ListOfDiagnosticInfo'),
        ('WhereClauseResult', 'ContentFilterResult'),
               ]

    def __init__(self):
        self.SelectClauseResults = []
        self.SelectClauseDiagnosticInfos = []
        self.WhereClauseResult = ContentFilterResult()
        self._freeze = True

    def __str__(self):
        return f'EventFilterResult(SelectClauseResults:{self.SelectClauseResults}, SelectClauseDiagnosticInfos:{self.SelectClauseDiagnosticInfos}, WhereClauseResult:{self.WhereClauseResult})'

    __repr__ = __str__


class AggregateFilterResult(FrozenClass):
    """
    :ivar RevisedStartTime:
    :vartype RevisedStartTime: DateTime
    :ivar RevisedProcessingInterval:
    :vartype RevisedProcessingInterval: Double
    :ivar RevisedAggregateConfiguration:
    :vartype RevisedAggregateConfiguration: AggregateConfiguration
    """

    ua_types = [
        ('RevisedStartTime', 'DateTime'),
        ('RevisedProcessingInterval', 'Double'),
        ('RevisedAggregateConfiguration', 'AggregateConfiguration'),
               ]

    def __init__(self):
        self.RevisedStartTime = datetime.utcnow()
        self.RevisedProcessingInterval = 0
        self.RevisedAggregateConfiguration = AggregateConfiguration()
        self._freeze = True

    def __str__(self):
        return f'AggregateFilterResult(RevisedStartTime:{self.RevisedStartTime}, RevisedProcessingInterval:{self.RevisedProcessingInterval}, RevisedAggregateConfiguration:{self.RevisedAggregateConfiguration})'

    __repr__ = __str__


class MonitoringParameters(FrozenClass):
    """
    :ivar ClientHandle:
    :vartype ClientHandle: UInt32
    :ivar SamplingInterval:
    :vartype SamplingInterval: Double
    :ivar Filter:
    :vartype Filter: ExtensionObject
    :ivar QueueSize:
    :vartype QueueSize: UInt32
    :ivar DiscardOldest:
    :vartype DiscardOldest: Boolean
    """

    ua_types = [
        ('ClientHandle', 'UInt32'),
        ('SamplingInterval', 'Double'),
        ('Filter', 'ExtensionObject'),
        ('QueueSize', 'UInt32'),
        ('DiscardOldest', 'Boolean'),
               ]

    def __init__(self):
        self.ClientHandle = 0
        self.SamplingInterval = 0
        self.Filter = ExtensionObject()
        self.QueueSize = 0
        self.DiscardOldest = True
        self._freeze = True

    def __str__(self):
        return f'MonitoringParameters(ClientHandle:{self.ClientHandle}, SamplingInterval:{self.SamplingInterval}, Filter:{self.Filter}, QueueSize:{self.QueueSize}, DiscardOldest:{self.DiscardOldest})'

    __repr__ = __str__


class MonitoredItemCreateRequest(FrozenClass):
    """
    :ivar ItemToMonitor:
    :vartype ItemToMonitor: ReadValueId
    :ivar MonitoringMode:
    :vartype MonitoringMode: MonitoringMode
    :ivar RequestedParameters:
    :vartype RequestedParameters: MonitoringParameters
    """

    data_type = ObjectIds.MonitoredItemCreateRequest

    ua_types = [
        ('ItemToMonitor', 'ReadValueId'),
        ('MonitoringMode', 'MonitoringMode'),
        ('RequestedParameters', 'MonitoringParameters'),
               ]

    def __init__(self):
        self.ItemToMonitor = ReadValueId()
        self.MonitoringMode = MonitoringMode(0)
        self.RequestedParameters = MonitoringParameters()
        self._freeze = True

    def __str__(self):
        return f'MonitoredItemCreateRequest(ItemToMonitor:{self.ItemToMonitor}, MonitoringMode:{self.MonitoringMode}, RequestedParameters:{self.RequestedParameters})'

    __repr__ = __str__


class MonitoredItemCreateResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar MonitoredItemId:
    :vartype MonitoredItemId: UInt32
    :ivar RevisedSamplingInterval:
    :vartype RevisedSamplingInterval: Double
    :ivar RevisedQueueSize:
    :vartype RevisedQueueSize: UInt32
    :ivar FilterResult:
    :vartype FilterResult: ExtensionObject
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('MonitoredItemId', 'UInt32'),
        ('RevisedSamplingInterval', 'Double'),
        ('RevisedQueueSize', 'UInt32'),
        ('FilterResult', 'ExtensionObject'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.MonitoredItemId = 0
        self.RevisedSamplingInterval = 0
        self.RevisedQueueSize = 0
        self.FilterResult = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'MonitoredItemCreateResult(StatusCode:{self.StatusCode}, MonitoredItemId:{self.MonitoredItemId}, RevisedSamplingInterval:{self.RevisedSamplingInterval}, RevisedQueueSize:{self.RevisedQueueSize}, FilterResult:{self.FilterResult})'

    __repr__ = __str__


class CreateMonitoredItemsParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar ItemsToCreate:
    :vartype ItemsToCreate: MonitoredItemCreateRequest
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('TimestampsToReturn', 'TimestampsToReturn'),
        ('ItemsToCreate', 'ListOfMonitoredItemCreateRequest'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.TimestampsToReturn = TimestampsToReturn(0)
        self.ItemsToCreate = []
        self._freeze = True

    def __str__(self):
        return f'CreateMonitoredItemsParameters(SubscriptionId:{self.SubscriptionId}, TimestampsToReturn:{self.TimestampsToReturn}, ItemsToCreate:{self.ItemsToCreate})'

    __repr__ = __str__


class CreateMonitoredItemsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CreateMonitoredItemsParameters
    """

    data_type = ObjectIds.CreateMonitoredItemsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'CreateMonitoredItemsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CreateMonitoredItemsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = CreateMonitoredItemsParameters()
        self._freeze = True

    def __str__(self):
        return f'CreateMonitoredItemsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CreateMonitoredItemsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: MonitoredItemCreateResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.CreateMonitoredItemsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfMonitoredItemCreateResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CreateMonitoredItemsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'CreateMonitoredItemsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class MonitoredItemModifyRequest(FrozenClass):
    """
    :ivar MonitoredItemId:
    :vartype MonitoredItemId: UInt32
    :ivar RequestedParameters:
    :vartype RequestedParameters: MonitoringParameters
    """

    data_type = ObjectIds.MonitoredItemModifyRequest

    ua_types = [
        ('MonitoredItemId', 'UInt32'),
        ('RequestedParameters', 'MonitoringParameters'),
               ]

    def __init__(self):
        self.MonitoredItemId = 0
        self.RequestedParameters = MonitoringParameters()
        self._freeze = True

    def __str__(self):
        return f'MonitoredItemModifyRequest(MonitoredItemId:{self.MonitoredItemId}, RequestedParameters:{self.RequestedParameters})'

    __repr__ = __str__


class MonitoredItemModifyResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar RevisedSamplingInterval:
    :vartype RevisedSamplingInterval: Double
    :ivar RevisedQueueSize:
    :vartype RevisedQueueSize: UInt32
    :ivar FilterResult:
    :vartype FilterResult: ExtensionObject
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('RevisedSamplingInterval', 'Double'),
        ('RevisedQueueSize', 'UInt32'),
        ('FilterResult', 'ExtensionObject'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.RevisedSamplingInterval = 0
        self.RevisedQueueSize = 0
        self.FilterResult = ExtensionObject()
        self._freeze = True

    def __str__(self):
        return f'MonitoredItemModifyResult(StatusCode:{self.StatusCode}, RevisedSamplingInterval:{self.RevisedSamplingInterval}, RevisedQueueSize:{self.RevisedQueueSize}, FilterResult:{self.FilterResult})'

    __repr__ = __str__


class ModifyMonitoredItemsParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar TimestampsToReturn:
    :vartype TimestampsToReturn: TimestampsToReturn
    :ivar ItemsToModify:
    :vartype ItemsToModify: MonitoredItemModifyRequest
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('TimestampsToReturn', 'TimestampsToReturn'),
        ('ItemsToModify', 'ListOfMonitoredItemModifyRequest'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.TimestampsToReturn = TimestampsToReturn(0)
        self.ItemsToModify = []
        self._freeze = True

    def __str__(self):
        return f'ModifyMonitoredItemsParameters(SubscriptionId:{self.SubscriptionId}, TimestampsToReturn:{self.TimestampsToReturn}, ItemsToModify:{self.ItemsToModify})'

    __repr__ = __str__


class ModifyMonitoredItemsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ModifyMonitoredItemsParameters
    """

    data_type = ObjectIds.ModifyMonitoredItemsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'ModifyMonitoredItemsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ModifyMonitoredItemsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = ModifyMonitoredItemsParameters()
        self._freeze = True

    def __str__(self):
        return f'ModifyMonitoredItemsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ModifyMonitoredItemsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: MonitoredItemModifyResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.ModifyMonitoredItemsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfMonitoredItemModifyResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ModifyMonitoredItemsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'ModifyMonitoredItemsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class SetMonitoringModeParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar MonitoringMode:
    :vartype MonitoringMode: MonitoringMode
    :ivar MonitoredItemIds:
    :vartype MonitoredItemIds: UInt32
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('MonitoringMode', 'MonitoringMode'),
        ('MonitoredItemIds', 'ListOfUInt32'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.MonitoringMode = MonitoringMode(0)
        self.MonitoredItemIds = []
        self._freeze = True

    def __str__(self):
        return f'SetMonitoringModeParameters(SubscriptionId:{self.SubscriptionId}, MonitoringMode:{self.MonitoringMode}, MonitoredItemIds:{self.MonitoredItemIds})'

    __repr__ = __str__


class SetMonitoringModeRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: SetMonitoringModeParameters
    """

    data_type = ObjectIds.SetMonitoringModeRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'SetMonitoringModeParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.SetMonitoringModeRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = SetMonitoringModeParameters()
        self._freeze = True

    def __str__(self):
        return f'SetMonitoringModeRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class SetMonitoringModeResult(FrozenClass):
    """
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'SetMonitoringModeResult(Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class SetMonitoringModeResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: SetMonitoringModeResult
    """

    data_type = ObjectIds.SetMonitoringModeResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'SetMonitoringModeResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.SetMonitoringModeResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = SetMonitoringModeResult()
        self._freeze = True

    def __str__(self):
        return f'SetMonitoringModeResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class SetTriggeringParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar TriggeringItemId:
    :vartype TriggeringItemId: UInt32
    :ivar LinksToAdd:
    :vartype LinksToAdd: UInt32
    :ivar LinksToRemove:
    :vartype LinksToRemove: UInt32
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('TriggeringItemId', 'UInt32'),
        ('LinksToAdd', 'ListOfUInt32'),
        ('LinksToRemove', 'ListOfUInt32'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.TriggeringItemId = 0
        self.LinksToAdd = []
        self.LinksToRemove = []
        self._freeze = True

    def __str__(self):
        return f'SetTriggeringParameters(SubscriptionId:{self.SubscriptionId}, TriggeringItemId:{self.TriggeringItemId}, LinksToAdd:{self.LinksToAdd}, LinksToRemove:{self.LinksToRemove})'

    __repr__ = __str__


class SetTriggeringRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: SetTriggeringParameters
    """

    data_type = ObjectIds.SetTriggeringRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'SetTriggeringParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.SetTriggeringRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = SetTriggeringParameters()
        self._freeze = True

    def __str__(self):
        return f'SetTriggeringRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class SetTriggeringResult(FrozenClass):
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

    ua_types = [
        ('AddResults', 'ListOfStatusCode'),
        ('AddDiagnosticInfos', 'ListOfDiagnosticInfo'),
        ('RemoveResults', 'ListOfStatusCode'),
        ('RemoveDiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.AddResults = []
        self.AddDiagnosticInfos = []
        self.RemoveResults = []
        self.RemoveDiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'SetTriggeringResult(AddResults:{self.AddResults}, AddDiagnosticInfos:{self.AddDiagnosticInfos}, RemoveResults:{self.RemoveResults}, RemoveDiagnosticInfos:{self.RemoveDiagnosticInfos})'

    __repr__ = __str__


class SetTriggeringResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: SetTriggeringResult
    """

    data_type = ObjectIds.SetTriggeringResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'SetTriggeringResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.SetTriggeringResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = SetTriggeringResult()
        self._freeze = True

    def __str__(self):
        return f'SetTriggeringResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class DeleteMonitoredItemsParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar MonitoredItemIds:
    :vartype MonitoredItemIds: UInt32
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('MonitoredItemIds', 'ListOfUInt32'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.MonitoredItemIds = []
        self._freeze = True

    def __str__(self):
        return f'DeleteMonitoredItemsParameters(SubscriptionId:{self.SubscriptionId}, MonitoredItemIds:{self.MonitoredItemIds})'

    __repr__ = __str__


class DeleteMonitoredItemsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteMonitoredItemsParameters
    """

    data_type = ObjectIds.DeleteMonitoredItemsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'DeleteMonitoredItemsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteMonitoredItemsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = DeleteMonitoredItemsParameters()
        self._freeze = True

    def __str__(self):
        return f'DeleteMonitoredItemsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class DeleteMonitoredItemsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.DeleteMonitoredItemsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteMonitoredItemsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'DeleteMonitoredItemsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class CreateSubscriptionParameters(FrozenClass):
    """
    :ivar RequestedPublishingInterval:
    :vartype RequestedPublishingInterval: Double
    :ivar RequestedLifetimeCount:
    :vartype RequestedLifetimeCount: UInt32
    :ivar RequestedMaxKeepAliveCount:
    :vartype RequestedMaxKeepAliveCount: UInt32
    :ivar MaxNotificationsPerPublish:
    :vartype MaxNotificationsPerPublish: UInt32
    :ivar PublishingEnabled:
    :vartype PublishingEnabled: Boolean
    :ivar Priority:
    :vartype Priority: Byte
    """

    ua_types = [
        ('RequestedPublishingInterval', 'Double'),
        ('RequestedLifetimeCount', 'UInt32'),
        ('RequestedMaxKeepAliveCount', 'UInt32'),
        ('MaxNotificationsPerPublish', 'UInt32'),
        ('PublishingEnabled', 'Boolean'),
        ('Priority', 'Byte'),
               ]

    def __init__(self):
        self.RequestedPublishingInterval = 0
        self.RequestedLifetimeCount = 0
        self.RequestedMaxKeepAliveCount = 0
        self.MaxNotificationsPerPublish = 0
        self.PublishingEnabled = True
        self.Priority = 0
        self._freeze = True

    def __str__(self):
        return f'CreateSubscriptionParameters(RequestedPublishingInterval:{self.RequestedPublishingInterval}, RequestedLifetimeCount:{self.RequestedLifetimeCount}, RequestedMaxKeepAliveCount:{self.RequestedMaxKeepAliveCount}, MaxNotificationsPerPublish:{self.MaxNotificationsPerPublish}, PublishingEnabled:{self.PublishingEnabled}, Priority:{self.Priority})'

    __repr__ = __str__


class CreateSubscriptionRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: CreateSubscriptionParameters
    """

    data_type = ObjectIds.CreateSubscriptionRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'CreateSubscriptionParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CreateSubscriptionRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = CreateSubscriptionParameters()
        self._freeze = True

    def __str__(self):
        return f'CreateSubscriptionRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class CreateSubscriptionResult(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar RevisedPublishingInterval:
    :vartype RevisedPublishingInterval: Double
    :ivar RevisedLifetimeCount:
    :vartype RevisedLifetimeCount: UInt32
    :ivar RevisedMaxKeepAliveCount:
    :vartype RevisedMaxKeepAliveCount: UInt32
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('RevisedPublishingInterval', 'Double'),
        ('RevisedLifetimeCount', 'UInt32'),
        ('RevisedMaxKeepAliveCount', 'UInt32'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.RevisedPublishingInterval = 0
        self.RevisedLifetimeCount = 0
        self.RevisedMaxKeepAliveCount = 0
        self._freeze = True

    def __str__(self):
        return f'CreateSubscriptionResult(SubscriptionId:{self.SubscriptionId}, RevisedPublishingInterval:{self.RevisedPublishingInterval}, RevisedLifetimeCount:{self.RevisedLifetimeCount}, RevisedMaxKeepAliveCount:{self.RevisedMaxKeepAliveCount})'

    __repr__ = __str__


class CreateSubscriptionResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: CreateSubscriptionResult
    """

    data_type = ObjectIds.CreateSubscriptionResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'CreateSubscriptionResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.CreateSubscriptionResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = CreateSubscriptionResult()
        self._freeze = True

    def __str__(self):
        return f'CreateSubscriptionResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ModifySubscriptionParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar RequestedPublishingInterval:
    :vartype RequestedPublishingInterval: Double
    :ivar RequestedLifetimeCount:
    :vartype RequestedLifetimeCount: UInt32
    :ivar RequestedMaxKeepAliveCount:
    :vartype RequestedMaxKeepAliveCount: UInt32
    :ivar MaxNotificationsPerPublish:
    :vartype MaxNotificationsPerPublish: UInt32
    :ivar Priority:
    :vartype Priority: Byte
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('RequestedPublishingInterval', 'Double'),
        ('RequestedLifetimeCount', 'UInt32'),
        ('RequestedMaxKeepAliveCount', 'UInt32'),
        ('MaxNotificationsPerPublish', 'UInt32'),
        ('Priority', 'Byte'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.RequestedPublishingInterval = 0
        self.RequestedLifetimeCount = 0
        self.RequestedMaxKeepAliveCount = 0
        self.MaxNotificationsPerPublish = 0
        self.Priority = 0
        self._freeze = True

    def __str__(self):
        return f'ModifySubscriptionParameters(SubscriptionId:{self.SubscriptionId}, RequestedPublishingInterval:{self.RequestedPublishingInterval}, RequestedLifetimeCount:{self.RequestedLifetimeCount}, RequestedMaxKeepAliveCount:{self.RequestedMaxKeepAliveCount}, MaxNotificationsPerPublish:{self.MaxNotificationsPerPublish}, Priority:{self.Priority})'

    __repr__ = __str__


class ModifySubscriptionRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: ModifySubscriptionParameters
    """

    data_type = ObjectIds.ModifySubscriptionRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'ModifySubscriptionParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ModifySubscriptionRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = ModifySubscriptionParameters()
        self._freeze = True

    def __str__(self):
        return f'ModifySubscriptionRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class ModifySubscriptionResult(FrozenClass):
    """
    :ivar RevisedPublishingInterval:
    :vartype RevisedPublishingInterval: Double
    :ivar RevisedLifetimeCount:
    :vartype RevisedLifetimeCount: UInt32
    :ivar RevisedMaxKeepAliveCount:
    :vartype RevisedMaxKeepAliveCount: UInt32
    """

    ua_types = [
        ('RevisedPublishingInterval', 'Double'),
        ('RevisedLifetimeCount', 'UInt32'),
        ('RevisedMaxKeepAliveCount', 'UInt32'),
               ]

    def __init__(self):
        self.RevisedPublishingInterval = 0
        self.RevisedLifetimeCount = 0
        self.RevisedMaxKeepAliveCount = 0
        self._freeze = True

    def __str__(self):
        return f'ModifySubscriptionResult(RevisedPublishingInterval:{self.RevisedPublishingInterval}, RevisedLifetimeCount:{self.RevisedLifetimeCount}, RevisedMaxKeepAliveCount:{self.RevisedMaxKeepAliveCount})'

    __repr__ = __str__


class ModifySubscriptionResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: ModifySubscriptionResult
    """

    data_type = ObjectIds.ModifySubscriptionResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'ModifySubscriptionResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.ModifySubscriptionResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = ModifySubscriptionResult()
        self._freeze = True

    def __str__(self):
        return f'ModifySubscriptionResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class SetPublishingModeParameters(FrozenClass):
    """
    :ivar PublishingEnabled:
    :vartype PublishingEnabled: Boolean
    :ivar SubscriptionIds:
    :vartype SubscriptionIds: UInt32
    """

    ua_types = [
        ('PublishingEnabled', 'Boolean'),
        ('SubscriptionIds', 'ListOfUInt32'),
               ]

    def __init__(self):
        self.PublishingEnabled = True
        self.SubscriptionIds = []
        self._freeze = True

    def __str__(self):
        return f'SetPublishingModeParameters(PublishingEnabled:{self.PublishingEnabled}, SubscriptionIds:{self.SubscriptionIds})'

    __repr__ = __str__


class SetPublishingModeRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: SetPublishingModeParameters
    """

    data_type = ObjectIds.SetPublishingModeRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'SetPublishingModeParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.SetPublishingModeRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = SetPublishingModeParameters()
        self._freeze = True

    def __str__(self):
        return f'SetPublishingModeRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class SetPublishingModeResult(FrozenClass):
    """
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'SetPublishingModeResult(Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class SetPublishingModeResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: SetPublishingModeResult
    """

    data_type = ObjectIds.SetPublishingModeResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'SetPublishingModeResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.SetPublishingModeResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = SetPublishingModeResult()
        self._freeze = True

    def __str__(self):
        return f'SetPublishingModeResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class NotificationMessage(FrozenClass):
    """
    :ivar SequenceNumber:
    :vartype SequenceNumber: UInt32
    :ivar PublishTime:
    :vartype PublishTime: DateTime
    :ivar NotificationData:
    :vartype NotificationData: ExtensionObject
    """

    data_type = ObjectIds.NotificationMessage

    ua_types = [
        ('SequenceNumber', 'UInt32'),
        ('PublishTime', 'DateTime'),
        ('NotificationData', 'ListOfExtensionObject'),
               ]

    def __init__(self):
        self.SequenceNumber = 0
        self.PublishTime = datetime.utcnow()
        self.NotificationData = []
        self._freeze = True

    def __str__(self):
        return f'NotificationMessage(SequenceNumber:{self.SequenceNumber}, PublishTime:{self.PublishTime}, NotificationData:{self.NotificationData})'

    __repr__ = __str__


class NotificationData(FrozenClass):
    """
    """

    data_type = ObjectIds.NotificationData

    ua_types = [
               ]

    def __init__(self):
        self._freeze = True

    def __str__(self):
        return 'NotificationData()'

    __repr__ = __str__


class DataChangeNotification(FrozenClass):
    """
    :ivar MonitoredItems:
    :vartype MonitoredItems: MonitoredItemNotification
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.DataChangeNotification

    ua_types = [
        ('MonitoredItems', 'ListOfMonitoredItemNotification'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.MonitoredItems = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'DataChangeNotification(MonitoredItems:{self.MonitoredItems}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class MonitoredItemNotification(FrozenClass):
    """
    :ivar ClientHandle:
    :vartype ClientHandle: UInt32
    :ivar Value:
    :vartype Value: DataValue
    """

    data_type = ObjectIds.MonitoredItemNotification

    ua_types = [
        ('ClientHandle', 'UInt32'),
        ('Value', 'DataValue'),
               ]

    def __init__(self):
        self.ClientHandle = 0
        self.Value = DataValue()
        self._freeze = True

    def __str__(self):
        return f'MonitoredItemNotification(ClientHandle:{self.ClientHandle}, Value:{self.Value})'

    __repr__ = __str__


class EventNotificationList(FrozenClass):
    """
    :ivar Events:
    :vartype Events: EventFieldList
    """

    data_type = ObjectIds.EventNotificationList

    ua_types = [
        ('Events', 'ListOfEventFieldList'),
               ]

    def __init__(self):
        self.Events = []
        self._freeze = True

    def __str__(self):
        return f'EventNotificationList(Events:{self.Events})'

    __repr__ = __str__


class EventFieldList(FrozenClass):
    """
    :ivar ClientHandle:
    :vartype ClientHandle: UInt32
    :ivar EventFields:
    :vartype EventFields: Variant
    """

    data_type = ObjectIds.EventFieldList

    ua_types = [
        ('ClientHandle', 'UInt32'),
        ('EventFields', 'ListOfVariant'),
               ]

    def __init__(self):
        self.ClientHandle = 0
        self.EventFields = []
        self._freeze = True

    def __str__(self):
        return f'EventFieldList(ClientHandle:{self.ClientHandle}, EventFields:{self.EventFields})'

    __repr__ = __str__


class HistoryEventFieldList(FrozenClass):
    """
    :ivar EventFields:
    :vartype EventFields: Variant
    """

    data_type = ObjectIds.HistoryEventFieldList

    ua_types = [
        ('EventFields', 'ListOfVariant'),
               ]

    def __init__(self):
        self.EventFields = []
        self._freeze = True

    def __str__(self):
        return f'HistoryEventFieldList(EventFields:{self.EventFields})'

    __repr__ = __str__


class StatusChangeNotification(FrozenClass):
    """
    :ivar Status:
    :vartype Status: StatusCode
    :ivar DiagnosticInfo:
    :vartype DiagnosticInfo: DiagnosticInfo
    """

    data_type = ObjectIds.StatusChangeNotification

    ua_types = [
        ('Status', 'StatusCode'),
        ('DiagnosticInfo', 'DiagnosticInfo'),
               ]

    def __init__(self):
        self.Status = StatusCode()
        self.DiagnosticInfo = DiagnosticInfo()
        self._freeze = True

    def __str__(self):
        return f'StatusChangeNotification(Status:{self.Status}, DiagnosticInfo:{self.DiagnosticInfo})'

    __repr__ = __str__


class SubscriptionAcknowledgement(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar SequenceNumber:
    :vartype SequenceNumber: UInt32
    """

    data_type = ObjectIds.SubscriptionAcknowledgement

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('SequenceNumber', 'UInt32'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.SequenceNumber = 0
        self._freeze = True

    def __str__(self):
        return f'SubscriptionAcknowledgement(SubscriptionId:{self.SubscriptionId}, SequenceNumber:{self.SequenceNumber})'

    __repr__ = __str__


class PublishParameters(FrozenClass):
    """
    :ivar SubscriptionAcknowledgements:
    :vartype SubscriptionAcknowledgements: SubscriptionAcknowledgement
    """

    ua_types = [
        ('SubscriptionAcknowledgements', 'ListOfSubscriptionAcknowledgement'),
               ]

    def __init__(self):
        self.SubscriptionAcknowledgements = []
        self._freeze = True

    def __str__(self):
        return f'PublishParameters(SubscriptionAcknowledgements:{self.SubscriptionAcknowledgements})'

    __repr__ = __str__


class PublishRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: PublishParameters
    """

    data_type = ObjectIds.PublishRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'PublishParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.PublishRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = PublishParameters()
        self._freeze = True

    def __str__(self):
        return f'PublishRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class PublishResult(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar AvailableSequenceNumbers:
    :vartype AvailableSequenceNumbers: UInt32
    :ivar MoreNotifications:
    :vartype MoreNotifications: Boolean
    :ivar NotificationMessage:
    :vartype NotificationMessage: NotificationMessage
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('AvailableSequenceNumbers', 'ListOfUInt32'),
        ('MoreNotifications', 'Boolean'),
        ('NotificationMessage', 'NotificationMessage'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.AvailableSequenceNumbers = []
        self.MoreNotifications = True
        self.NotificationMessage = NotificationMessage()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'PublishResult(SubscriptionId:{self.SubscriptionId}, AvailableSequenceNumbers:{self.AvailableSequenceNumbers}, MoreNotifications:{self.MoreNotifications}, NotificationMessage:{self.NotificationMessage}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class PublishResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: PublishResult
    """

    data_type = ObjectIds.PublishResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'PublishResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.PublishResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = PublishResult()
        self._freeze = True

    def __str__(self):
        return f'PublishResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class RepublishParameters(FrozenClass):
    """
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar RetransmitSequenceNumber:
    :vartype RetransmitSequenceNumber: UInt32
    """

    ua_types = [
        ('SubscriptionId', 'UInt32'),
        ('RetransmitSequenceNumber', 'UInt32'),
               ]

    def __init__(self):
        self.SubscriptionId = 0
        self.RetransmitSequenceNumber = 0
        self._freeze = True

    def __str__(self):
        return f'RepublishParameters(SubscriptionId:{self.SubscriptionId}, RetransmitSequenceNumber:{self.RetransmitSequenceNumber})'

    __repr__ = __str__


class RepublishRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: RepublishParameters
    """

    data_type = ObjectIds.RepublishRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'RepublishParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RepublishRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = RepublishParameters()
        self._freeze = True

    def __str__(self):
        return f'RepublishRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class RepublishResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar NotificationMessage:
    :vartype NotificationMessage: NotificationMessage
    """

    data_type = ObjectIds.RepublishResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('NotificationMessage', 'NotificationMessage'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.RepublishResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.NotificationMessage = NotificationMessage()
        self._freeze = True

    def __str__(self):
        return f'RepublishResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, NotificationMessage:{self.NotificationMessage})'

    __repr__ = __str__


class TransferResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar AvailableSequenceNumbers:
    :vartype AvailableSequenceNumbers: UInt32
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('AvailableSequenceNumbers', 'ListOfUInt32'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.AvailableSequenceNumbers = []
        self._freeze = True

    def __str__(self):
        return f'TransferResult(StatusCode:{self.StatusCode}, AvailableSequenceNumbers:{self.AvailableSequenceNumbers})'

    __repr__ = __str__


class TransferSubscriptionsParameters(FrozenClass):
    """
    :ivar SubscriptionIds:
    :vartype SubscriptionIds: UInt32
    :ivar SendInitialValues:
    :vartype SendInitialValues: Boolean
    """

    ua_types = [
        ('SubscriptionIds', 'ListOfUInt32'),
        ('SendInitialValues', 'Boolean'),
               ]

    def __init__(self):
        self.SubscriptionIds = []
        self.SendInitialValues = True
        self._freeze = True

    def __str__(self):
        return f'TransferSubscriptionsParameters(SubscriptionIds:{self.SubscriptionIds}, SendInitialValues:{self.SendInitialValues})'

    __repr__ = __str__


class TransferSubscriptionsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: TransferSubscriptionsParameters
    """

    data_type = ObjectIds.TransferSubscriptionsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'TransferSubscriptionsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.TransferSubscriptionsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = TransferSubscriptionsParameters()
        self._freeze = True

    def __str__(self):
        return f'TransferSubscriptionsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class TransferSubscriptionsResult(FrozenClass):
    """
    :ivar Results:
    :vartype Results: TransferResult
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    ua_types = [
        ('Results', 'ListOfTransferResult'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'TransferSubscriptionsResult(Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class TransferSubscriptionsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Parameters:
    :vartype Parameters: TransferSubscriptionsResult
    """

    data_type = ObjectIds.TransferSubscriptionsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Parameters', 'TransferSubscriptionsResult'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.TransferSubscriptionsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Parameters = TransferSubscriptionsResult()
        self._freeze = True

    def __str__(self):
        return f'TransferSubscriptionsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class DeleteSubscriptionsParameters(FrozenClass):
    """
    :ivar SubscriptionIds:
    :vartype SubscriptionIds: UInt32
    """

    ua_types = [
        ('SubscriptionIds', 'ListOfUInt32'),
               ]

    def __init__(self):
        self.SubscriptionIds = []
        self._freeze = True

    def __str__(self):
        return f'DeleteSubscriptionsParameters(SubscriptionIds:{self.SubscriptionIds})'

    __repr__ = __str__


class DeleteSubscriptionsRequest(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar RequestHeader:
    :vartype RequestHeader: RequestHeader
    :ivar Parameters:
    :vartype Parameters: DeleteSubscriptionsParameters
    """

    data_type = ObjectIds.DeleteSubscriptionsRequest

    ua_types = [
        ('TypeId', 'NodeId'),
        ('RequestHeader', 'RequestHeader'),
        ('Parameters', 'DeleteSubscriptionsParameters'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteSubscriptionsRequest_Encoding_DefaultBinary)
        self.RequestHeader = RequestHeader()
        self.Parameters = DeleteSubscriptionsParameters()
        self._freeze = True

    def __str__(self):
        return f'DeleteSubscriptionsRequest(TypeId:{self.TypeId}, RequestHeader:{self.RequestHeader}, Parameters:{self.Parameters})'

    __repr__ = __str__


class DeleteSubscriptionsResponse(FrozenClass):
    """
    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar ResponseHeader:
    :vartype ResponseHeader: ResponseHeader
    :ivar Results:
    :vartype Results: StatusCode
    :ivar DiagnosticInfos:
    :vartype DiagnosticInfos: DiagnosticInfo
    """

    data_type = ObjectIds.DeleteSubscriptionsResponse

    ua_types = [
        ('TypeId', 'NodeId'),
        ('ResponseHeader', 'ResponseHeader'),
        ('Results', 'ListOfStatusCode'),
        ('DiagnosticInfos', 'ListOfDiagnosticInfo'),
               ]

    def __init__(self):
        self.TypeId = FourByteNodeId(ObjectIds.DeleteSubscriptionsResponse_Encoding_DefaultBinary)
        self.ResponseHeader = ResponseHeader()
        self.Results = []
        self.DiagnosticInfos = []
        self._freeze = True

    def __str__(self):
        return f'DeleteSubscriptionsResponse(TypeId:{self.TypeId}, ResponseHeader:{self.ResponseHeader}, Results:{self.Results}, DiagnosticInfos:{self.DiagnosticInfos})'

    __repr__ = __str__


class BuildInfo(FrozenClass):
    """
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
    :vartype BuildDate: DateTime
    """

    data_type = ObjectIds.BuildInfo

    ua_types = [
        ('ProductUri', 'String'),
        ('ManufacturerName', 'String'),
        ('ProductName', 'String'),
        ('SoftwareVersion', 'String'),
        ('BuildNumber', 'String'),
        ('BuildDate', 'DateTime'),
               ]

    def __init__(self):
        self.ProductUri = None
        self.ManufacturerName = None
        self.ProductName = None
        self.SoftwareVersion = None
        self.BuildNumber = None
        self.BuildDate = datetime.utcnow()
        self._freeze = True

    def __str__(self):
        return f'BuildInfo(ProductUri:{self.ProductUri}, ManufacturerName:{self.ManufacturerName}, ProductName:{self.ProductName}, SoftwareVersion:{self.SoftwareVersion}, BuildNumber:{self.BuildNumber}, BuildDate:{self.BuildDate})'

    __repr__ = __str__


class RedundantServerDataType(FrozenClass):
    """
    :ivar ServerId:
    :vartype ServerId: String
    :ivar ServiceLevel:
    :vartype ServiceLevel: Byte
    :ivar ServerState:
    :vartype ServerState: ServerState
    """

    data_type = ObjectIds.RedundantServerDataType

    ua_types = [
        ('ServerId', 'String'),
        ('ServiceLevel', 'Byte'),
        ('ServerState', 'ServerState'),
               ]

    def __init__(self):
        self.ServerId = None
        self.ServiceLevel = 0
        self.ServerState = ServerState(0)
        self._freeze = True

    def __str__(self):
        return f'RedundantServerDataType(ServerId:{self.ServerId}, ServiceLevel:{self.ServiceLevel}, ServerState:{self.ServerState})'

    __repr__ = __str__


class EndpointUrlListDataType(FrozenClass):
    """
    :ivar EndpointUrlList:
    :vartype EndpointUrlList: String
    """

    data_type = ObjectIds.EndpointUrlListDataType

    ua_types = [
        ('EndpointUrlList', 'ListOfString'),
               ]

    def __init__(self):
        self.EndpointUrlList = []
        self._freeze = True

    def __str__(self):
        return f'EndpointUrlListDataType(EndpointUrlList:{self.EndpointUrlList})'

    __repr__ = __str__


class NetworkGroupDataType(FrozenClass):
    """
    :ivar ServerUri:
    :vartype ServerUri: String
    :ivar NetworkPaths:
    :vartype NetworkPaths: EndpointUrlListDataType
    """

    data_type = ObjectIds.NetworkGroupDataType

    ua_types = [
        ('ServerUri', 'String'),
        ('NetworkPaths', 'ListOfEndpointUrlListDataType'),
               ]

    def __init__(self):
        self.ServerUri = None
        self.NetworkPaths = []
        self._freeze = True

    def __str__(self):
        return f'NetworkGroupDataType(ServerUri:{self.ServerUri}, NetworkPaths:{self.NetworkPaths})'

    __repr__ = __str__


class SamplingIntervalDiagnosticsDataType(FrozenClass):
    """
    :ivar SamplingInterval:
    :vartype SamplingInterval: Double
    :ivar MonitoredItemCount:
    :vartype MonitoredItemCount: UInt32
    :ivar MaxMonitoredItemCount:
    :vartype MaxMonitoredItemCount: UInt32
    :ivar DisabledMonitoredItemCount:
    :vartype DisabledMonitoredItemCount: UInt32
    """

    data_type = ObjectIds.SamplingIntervalDiagnosticsDataType

    ua_types = [
        ('SamplingInterval', 'Double'),
        ('MonitoredItemCount', 'UInt32'),
        ('MaxMonitoredItemCount', 'UInt32'),
        ('DisabledMonitoredItemCount', 'UInt32'),
               ]

    def __init__(self):
        self.SamplingInterval = 0
        self.MonitoredItemCount = 0
        self.MaxMonitoredItemCount = 0
        self.DisabledMonitoredItemCount = 0
        self._freeze = True

    def __str__(self):
        return f'SamplingIntervalDiagnosticsDataType(SamplingInterval:{self.SamplingInterval}, MonitoredItemCount:{self.MonitoredItemCount}, MaxMonitoredItemCount:{self.MaxMonitoredItemCount}, DisabledMonitoredItemCount:{self.DisabledMonitoredItemCount})'

    __repr__ = __str__


class ServerDiagnosticsSummaryDataType(FrozenClass):
    """
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

    data_type = ObjectIds.ServerDiagnosticsSummaryDataType

    ua_types = [
        ('ServerViewCount', 'UInt32'),
        ('CurrentSessionCount', 'UInt32'),
        ('CumulatedSessionCount', 'UInt32'),
        ('SecurityRejectedSessionCount', 'UInt32'),
        ('RejectedSessionCount', 'UInt32'),
        ('SessionTimeoutCount', 'UInt32'),
        ('SessionAbortCount', 'UInt32'),
        ('CurrentSubscriptionCount', 'UInt32'),
        ('CumulatedSubscriptionCount', 'UInt32'),
        ('PublishingIntervalCount', 'UInt32'),
        ('SecurityRejectedRequestsCount', 'UInt32'),
        ('RejectedRequestsCount', 'UInt32'),
               ]

    def __init__(self):
        self.ServerViewCount = 0
        self.CurrentSessionCount = 0
        self.CumulatedSessionCount = 0
        self.SecurityRejectedSessionCount = 0
        self.RejectedSessionCount = 0
        self.SessionTimeoutCount = 0
        self.SessionAbortCount = 0
        self.CurrentSubscriptionCount = 0
        self.CumulatedSubscriptionCount = 0
        self.PublishingIntervalCount = 0
        self.SecurityRejectedRequestsCount = 0
        self.RejectedRequestsCount = 0
        self._freeze = True

    def __str__(self):
        return f'ServerDiagnosticsSummaryDataType(ServerViewCount:{self.ServerViewCount}, CurrentSessionCount:{self.CurrentSessionCount}, CumulatedSessionCount:{self.CumulatedSessionCount}, SecurityRejectedSessionCount:{self.SecurityRejectedSessionCount}, RejectedSessionCount:{self.RejectedSessionCount}, SessionTimeoutCount:{self.SessionTimeoutCount}, SessionAbortCount:{self.SessionAbortCount}, CurrentSubscriptionCount:{self.CurrentSubscriptionCount}, CumulatedSubscriptionCount:{self.CumulatedSubscriptionCount}, PublishingIntervalCount:{self.PublishingIntervalCount}, SecurityRejectedRequestsCount:{self.SecurityRejectedRequestsCount}, RejectedRequestsCount:{self.RejectedRequestsCount})'

    __repr__ = __str__


class ServerStatusDataType(FrozenClass):
    """
    :ivar StartTime:
    :vartype StartTime: DateTime
    :ivar CurrentTime:
    :vartype CurrentTime: DateTime
    :ivar State:
    :vartype State: ServerState
    :ivar BuildInfo:
    :vartype BuildInfo: BuildInfo
    :ivar SecondsTillShutdown:
    :vartype SecondsTillShutdown: UInt32
    :ivar ShutdownReason:
    :vartype ShutdownReason: LocalizedText
    """

    data_type = ObjectIds.ServerStatusDataType

    ua_types = [
        ('StartTime', 'DateTime'),
        ('CurrentTime', 'DateTime'),
        ('State', 'ServerState'),
        ('BuildInfo', 'BuildInfo'),
        ('SecondsTillShutdown', 'UInt32'),
        ('ShutdownReason', 'LocalizedText'),
               ]

    def __init__(self):
        self.StartTime = datetime.utcnow()
        self.CurrentTime = datetime.utcnow()
        self.State = ServerState(0)
        self.BuildInfo = BuildInfo()
        self.SecondsTillShutdown = 0
        self.ShutdownReason = LocalizedText()
        self._freeze = True

    def __str__(self):
        return f'ServerStatusDataType(StartTime:{self.StartTime}, CurrentTime:{self.CurrentTime}, State:{self.State}, BuildInfo:{self.BuildInfo}, SecondsTillShutdown:{self.SecondsTillShutdown}, ShutdownReason:{self.ShutdownReason})'

    __repr__ = __str__


class SessionDiagnosticsDataType(FrozenClass):
    """
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
    :vartype LocaleIds: String
    :ivar ActualSessionTimeout:
    :vartype ActualSessionTimeout: Double
    :ivar MaxResponseMessageSize:
    :vartype MaxResponseMessageSize: UInt32
    :ivar ClientConnectionTime:
    :vartype ClientConnectionTime: DateTime
    :ivar ClientLastContactTime:
    :vartype ClientLastContactTime: DateTime
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

    data_type = ObjectIds.SessionDiagnosticsDataType

    ua_types = [
        ('SessionId', 'NodeId'),
        ('SessionName', 'String'),
        ('ClientDescription', 'ApplicationDescription'),
        ('ServerUri', 'String'),
        ('EndpointUrl', 'String'),
        ('LocaleIds', 'ListOfString'),
        ('ActualSessionTimeout', 'Double'),
        ('MaxResponseMessageSize', 'UInt32'),
        ('ClientConnectionTime', 'DateTime'),
        ('ClientLastContactTime', 'DateTime'),
        ('CurrentSubscriptionsCount', 'UInt32'),
        ('CurrentMonitoredItemsCount', 'UInt32'),
        ('CurrentPublishRequestsInQueue', 'UInt32'),
        ('TotalRequestCount', 'ServiceCounterDataType'),
        ('UnauthorizedRequestCount', 'UInt32'),
        ('ReadCount', 'ServiceCounterDataType'),
        ('HistoryReadCount', 'ServiceCounterDataType'),
        ('WriteCount', 'ServiceCounterDataType'),
        ('HistoryUpdateCount', 'ServiceCounterDataType'),
        ('CallCount', 'ServiceCounterDataType'),
        ('CreateMonitoredItemsCount', 'ServiceCounterDataType'),
        ('ModifyMonitoredItemsCount', 'ServiceCounterDataType'),
        ('SetMonitoringModeCount', 'ServiceCounterDataType'),
        ('SetTriggeringCount', 'ServiceCounterDataType'),
        ('DeleteMonitoredItemsCount', 'ServiceCounterDataType'),
        ('CreateSubscriptionCount', 'ServiceCounterDataType'),
        ('ModifySubscriptionCount', 'ServiceCounterDataType'),
        ('SetPublishingModeCount', 'ServiceCounterDataType'),
        ('PublishCount', 'ServiceCounterDataType'),
        ('RepublishCount', 'ServiceCounterDataType'),
        ('TransferSubscriptionsCount', 'ServiceCounterDataType'),
        ('DeleteSubscriptionsCount', 'ServiceCounterDataType'),
        ('AddNodesCount', 'ServiceCounterDataType'),
        ('AddReferencesCount', 'ServiceCounterDataType'),
        ('DeleteNodesCount', 'ServiceCounterDataType'),
        ('DeleteReferencesCount', 'ServiceCounterDataType'),
        ('BrowseCount', 'ServiceCounterDataType'),
        ('BrowseNextCount', 'ServiceCounterDataType'),
        ('TranslateBrowsePathsToNodeIdsCount', 'ServiceCounterDataType'),
        ('QueryFirstCount', 'ServiceCounterDataType'),
        ('QueryNextCount', 'ServiceCounterDataType'),
        ('RegisterNodesCount', 'ServiceCounterDataType'),
        ('UnregisterNodesCount', 'ServiceCounterDataType'),
               ]

    def __init__(self):
        self.SessionId = NodeId()
        self.SessionName = None
        self.ClientDescription = ApplicationDescription()
        self.ServerUri = None
        self.EndpointUrl = None
        self.LocaleIds = []
        self.ActualSessionTimeout = 0
        self.MaxResponseMessageSize = 0
        self.ClientConnectionTime = datetime.utcnow()
        self.ClientLastContactTime = datetime.utcnow()
        self.CurrentSubscriptionsCount = 0
        self.CurrentMonitoredItemsCount = 0
        self.CurrentPublishRequestsInQueue = 0
        self.TotalRequestCount = ServiceCounterDataType()
        self.UnauthorizedRequestCount = 0
        self.ReadCount = ServiceCounterDataType()
        self.HistoryReadCount = ServiceCounterDataType()
        self.WriteCount = ServiceCounterDataType()
        self.HistoryUpdateCount = ServiceCounterDataType()
        self.CallCount = ServiceCounterDataType()
        self.CreateMonitoredItemsCount = ServiceCounterDataType()
        self.ModifyMonitoredItemsCount = ServiceCounterDataType()
        self.SetMonitoringModeCount = ServiceCounterDataType()
        self.SetTriggeringCount = ServiceCounterDataType()
        self.DeleteMonitoredItemsCount = ServiceCounterDataType()
        self.CreateSubscriptionCount = ServiceCounterDataType()
        self.ModifySubscriptionCount = ServiceCounterDataType()
        self.SetPublishingModeCount = ServiceCounterDataType()
        self.PublishCount = ServiceCounterDataType()
        self.RepublishCount = ServiceCounterDataType()
        self.TransferSubscriptionsCount = ServiceCounterDataType()
        self.DeleteSubscriptionsCount = ServiceCounterDataType()
        self.AddNodesCount = ServiceCounterDataType()
        self.AddReferencesCount = ServiceCounterDataType()
        self.DeleteNodesCount = ServiceCounterDataType()
        self.DeleteReferencesCount = ServiceCounterDataType()
        self.BrowseCount = ServiceCounterDataType()
        self.BrowseNextCount = ServiceCounterDataType()
        self.TranslateBrowsePathsToNodeIdsCount = ServiceCounterDataType()
        self.QueryFirstCount = ServiceCounterDataType()
        self.QueryNextCount = ServiceCounterDataType()
        self.RegisterNodesCount = ServiceCounterDataType()
        self.UnregisterNodesCount = ServiceCounterDataType()
        self._freeze = True

    def __str__(self):
        return f'SessionDiagnosticsDataType(SessionId:{self.SessionId}, SessionName:{self.SessionName}, ClientDescription:{self.ClientDescription}, ServerUri:{self.ServerUri}, EndpointUrl:{self.EndpointUrl}, LocaleIds:{self.LocaleIds}, ActualSessionTimeout:{self.ActualSessionTimeout}, MaxResponseMessageSize:{self.MaxResponseMessageSize}, ClientConnectionTime:{self.ClientConnectionTime}, ClientLastContactTime:{self.ClientLastContactTime}, CurrentSubscriptionsCount:{self.CurrentSubscriptionsCount}, CurrentMonitoredItemsCount:{self.CurrentMonitoredItemsCount}, CurrentPublishRequestsInQueue:{self.CurrentPublishRequestsInQueue}, TotalRequestCount:{self.TotalRequestCount}, UnauthorizedRequestCount:{self.UnauthorizedRequestCount}, ReadCount:{self.ReadCount}, HistoryReadCount:{self.HistoryReadCount}, WriteCount:{self.WriteCount}, HistoryUpdateCount:{self.HistoryUpdateCount}, CallCount:{self.CallCount}, CreateMonitoredItemsCount:{self.CreateMonitoredItemsCount}, ModifyMonitoredItemsCount:{self.ModifyMonitoredItemsCount}, SetMonitoringModeCount:{self.SetMonitoringModeCount}, SetTriggeringCount:{self.SetTriggeringCount}, DeleteMonitoredItemsCount:{self.DeleteMonitoredItemsCount}, CreateSubscriptionCount:{self.CreateSubscriptionCount}, ModifySubscriptionCount:{self.ModifySubscriptionCount}, SetPublishingModeCount:{self.SetPublishingModeCount}, PublishCount:{self.PublishCount}, RepublishCount:{self.RepublishCount}, TransferSubscriptionsCount:{self.TransferSubscriptionsCount}, DeleteSubscriptionsCount:{self.DeleteSubscriptionsCount}, AddNodesCount:{self.AddNodesCount}, AddReferencesCount:{self.AddReferencesCount}, DeleteNodesCount:{self.DeleteNodesCount}, DeleteReferencesCount:{self.DeleteReferencesCount}, BrowseCount:{self.BrowseCount}, BrowseNextCount:{self.BrowseNextCount}, TranslateBrowsePathsToNodeIdsCount:{self.TranslateBrowsePathsToNodeIdsCount}, QueryFirstCount:{self.QueryFirstCount}, QueryNextCount:{self.QueryNextCount}, RegisterNodesCount:{self.RegisterNodesCount}, UnregisterNodesCount:{self.UnregisterNodesCount})'

    __repr__ = __str__


class SessionSecurityDiagnosticsDataType(FrozenClass):
    """
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

    data_type = ObjectIds.SessionSecurityDiagnosticsDataType

    ua_types = [
        ('SessionId', 'NodeId'),
        ('ClientUserIdOfSession', 'String'),
        ('ClientUserIdHistory', 'ListOfString'),
        ('AuthenticationMechanism', 'String'),
        ('Encoding', 'String'),
        ('TransportProtocol', 'String'),
        ('SecurityMode', 'MessageSecurityMode'),
        ('SecurityPolicyUri', 'String'),
        ('ClientCertificate', 'ByteString'),
               ]

    def __init__(self):
        self.SessionId = NodeId()
        self.ClientUserIdOfSession = None
        self.ClientUserIdHistory = []
        self.AuthenticationMechanism = None
        self.Encoding = None
        self.TransportProtocol = None
        self.SecurityMode = MessageSecurityMode(0)
        self.SecurityPolicyUri = None
        self.ClientCertificate = None
        self._freeze = True

    def __str__(self):
        return f'SessionSecurityDiagnosticsDataType(SessionId:{self.SessionId}, ClientUserIdOfSession:{self.ClientUserIdOfSession}, ClientUserIdHistory:{self.ClientUserIdHistory}, AuthenticationMechanism:{self.AuthenticationMechanism}, Encoding:{self.Encoding}, TransportProtocol:{self.TransportProtocol}, SecurityMode:{self.SecurityMode}, SecurityPolicyUri:{self.SecurityPolicyUri}, ClientCertificate:{self.ClientCertificate})'

    __repr__ = __str__


class ServiceCounterDataType(FrozenClass):
    """
    :ivar TotalCount:
    :vartype TotalCount: UInt32
    :ivar ErrorCount:
    :vartype ErrorCount: UInt32
    """

    data_type = ObjectIds.ServiceCounterDataType

    ua_types = [
        ('TotalCount', 'UInt32'),
        ('ErrorCount', 'UInt32'),
               ]

    def __init__(self):
        self.TotalCount = 0
        self.ErrorCount = 0
        self._freeze = True

    def __str__(self):
        return f'ServiceCounterDataType(TotalCount:{self.TotalCount}, ErrorCount:{self.ErrorCount})'

    __repr__ = __str__


class StatusResult(FrozenClass):
    """
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar DiagnosticInfo:
    :vartype DiagnosticInfo: DiagnosticInfo
    """

    ua_types = [
        ('StatusCode', 'StatusCode'),
        ('DiagnosticInfo', 'DiagnosticInfo'),
               ]

    def __init__(self):
        self.StatusCode = StatusCode()
        self.DiagnosticInfo = DiagnosticInfo()
        self._freeze = True

    def __str__(self):
        return f'StatusResult(StatusCode:{self.StatusCode}, DiagnosticInfo:{self.DiagnosticInfo})'

    __repr__ = __str__


class SubscriptionDiagnosticsDataType(FrozenClass):
    """
    :ivar SessionId:
    :vartype SessionId: NodeId
    :ivar SubscriptionId:
    :vartype SubscriptionId: UInt32
    :ivar Priority:
    :vartype Priority: Byte
    :ivar PublishingInterval:
    :vartype PublishingInterval: Double
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

    data_type = ObjectIds.SubscriptionDiagnosticsDataType

    ua_types = [
        ('SessionId', 'NodeId'),
        ('SubscriptionId', 'UInt32'),
        ('Priority', 'Byte'),
        ('PublishingInterval', 'Double'),
        ('MaxKeepAliveCount', 'UInt32'),
        ('MaxLifetimeCount', 'UInt32'),
        ('MaxNotificationsPerPublish', 'UInt32'),
        ('PublishingEnabled', 'Boolean'),
        ('ModifyCount', 'UInt32'),
        ('EnableCount', 'UInt32'),
        ('DisableCount', 'UInt32'),
        ('RepublishRequestCount', 'UInt32'),
        ('RepublishMessageRequestCount', 'UInt32'),
        ('RepublishMessageCount', 'UInt32'),
        ('TransferRequestCount', 'UInt32'),
        ('TransferredToAltClientCount', 'UInt32'),
        ('TransferredToSameClientCount', 'UInt32'),
        ('PublishRequestCount', 'UInt32'),
        ('DataChangeNotificationsCount', 'UInt32'),
        ('EventNotificationsCount', 'UInt32'),
        ('NotificationsCount', 'UInt32'),
        ('LatePublishRequestCount', 'UInt32'),
        ('CurrentKeepAliveCount', 'UInt32'),
        ('CurrentLifetimeCount', 'UInt32'),
        ('UnacknowledgedMessageCount', 'UInt32'),
        ('DiscardedMessageCount', 'UInt32'),
        ('MonitoredItemCount', 'UInt32'),
        ('DisabledMonitoredItemCount', 'UInt32'),
        ('MonitoringQueueOverflowCount', 'UInt32'),
        ('NextSequenceNumber', 'UInt32'),
        ('EventQueueOverFlowCount', 'UInt32'),
               ]

    def __init__(self):
        self.SessionId = NodeId()
        self.SubscriptionId = 0
        self.Priority = 0
        self.PublishingInterval = 0
        self.MaxKeepAliveCount = 0
        self.MaxLifetimeCount = 0
        self.MaxNotificationsPerPublish = 0
        self.PublishingEnabled = True
        self.ModifyCount = 0
        self.EnableCount = 0
        self.DisableCount = 0
        self.RepublishRequestCount = 0
        self.RepublishMessageRequestCount = 0
        self.RepublishMessageCount = 0
        self.TransferRequestCount = 0
        self.TransferredToAltClientCount = 0
        self.TransferredToSameClientCount = 0
        self.PublishRequestCount = 0
        self.DataChangeNotificationsCount = 0
        self.EventNotificationsCount = 0
        self.NotificationsCount = 0
        self.LatePublishRequestCount = 0
        self.CurrentKeepAliveCount = 0
        self.CurrentLifetimeCount = 0
        self.UnacknowledgedMessageCount = 0
        self.DiscardedMessageCount = 0
        self.MonitoredItemCount = 0
        self.DisabledMonitoredItemCount = 0
        self.MonitoringQueueOverflowCount = 0
        self.NextSequenceNumber = 0
        self.EventQueueOverFlowCount = 0
        self._freeze = True

    def __str__(self):
        return f'SubscriptionDiagnosticsDataType(SessionId:{self.SessionId}, SubscriptionId:{self.SubscriptionId}, Priority:{self.Priority}, PublishingInterval:{self.PublishingInterval}, MaxKeepAliveCount:{self.MaxKeepAliveCount}, MaxLifetimeCount:{self.MaxLifetimeCount}, MaxNotificationsPerPublish:{self.MaxNotificationsPerPublish}, PublishingEnabled:{self.PublishingEnabled}, ModifyCount:{self.ModifyCount}, EnableCount:{self.EnableCount}, DisableCount:{self.DisableCount}, RepublishRequestCount:{self.RepublishRequestCount}, RepublishMessageRequestCount:{self.RepublishMessageRequestCount}, RepublishMessageCount:{self.RepublishMessageCount}, TransferRequestCount:{self.TransferRequestCount}, TransferredToAltClientCount:{self.TransferredToAltClientCount}, TransferredToSameClientCount:{self.TransferredToSameClientCount}, PublishRequestCount:{self.PublishRequestCount}, DataChangeNotificationsCount:{self.DataChangeNotificationsCount}, EventNotificationsCount:{self.EventNotificationsCount}, NotificationsCount:{self.NotificationsCount}, LatePublishRequestCount:{self.LatePublishRequestCount}, CurrentKeepAliveCount:{self.CurrentKeepAliveCount}, CurrentLifetimeCount:{self.CurrentLifetimeCount}, UnacknowledgedMessageCount:{self.UnacknowledgedMessageCount}, DiscardedMessageCount:{self.DiscardedMessageCount}, MonitoredItemCount:{self.MonitoredItemCount}, DisabledMonitoredItemCount:{self.DisabledMonitoredItemCount}, MonitoringQueueOverflowCount:{self.MonitoringQueueOverflowCount}, NextSequenceNumber:{self.NextSequenceNumber}, EventQueueOverFlowCount:{self.EventQueueOverFlowCount})'

    __repr__ = __str__


class ModelChangeStructureDataType(FrozenClass):
    """
    :ivar Affected:
    :vartype Affected: NodeId
    :ivar AffectedType:
    :vartype AffectedType: NodeId
    :ivar Verb:
    :vartype Verb: Byte
    """

    data_type = ObjectIds.ModelChangeStructureDataType

    ua_types = [
        ('Affected', 'NodeId'),
        ('AffectedType', 'NodeId'),
        ('Verb', 'Byte'),
               ]

    def __init__(self):
        self.Affected = NodeId()
        self.AffectedType = NodeId()
        self.Verb = 0
        self._freeze = True

    def __str__(self):
        return f'ModelChangeStructureDataType(Affected:{self.Affected}, AffectedType:{self.AffectedType}, Verb:{self.Verb})'

    __repr__ = __str__


class SemanticChangeStructureDataType(FrozenClass):
    """
    :ivar Affected:
    :vartype Affected: NodeId
    :ivar AffectedType:
    :vartype AffectedType: NodeId
    """

    data_type = ObjectIds.SemanticChangeStructureDataType

    ua_types = [
        ('Affected', 'NodeId'),
        ('AffectedType', 'NodeId'),
               ]

    def __init__(self):
        self.Affected = NodeId()
        self.AffectedType = NodeId()
        self._freeze = True

    def __str__(self):
        return f'SemanticChangeStructureDataType(Affected:{self.Affected}, AffectedType:{self.AffectedType})'

    __repr__ = __str__


class Range(FrozenClass):
    """
    :ivar Low:
    :vartype Low: Double
    :ivar High:
    :vartype High: Double
    """

    data_type = ObjectIds.Range

    ua_types = [
        ('Low', 'Double'),
        ('High', 'Double'),
               ]

    def __init__(self):
        self.Low = 0
        self.High = 0
        self._freeze = True

    def __str__(self):
        return f'Range(Low:{self.Low}, High:{self.High})'

    __repr__ = __str__


class EUInformation(FrozenClass):
    """
    :ivar NamespaceUri:
    :vartype NamespaceUri: String
    :ivar UnitId:
    :vartype UnitId: Int32
    :ivar DisplayName:
    :vartype DisplayName: LocalizedText
    :ivar Description:
    :vartype Description: LocalizedText
    """

    data_type = ObjectIds.EUInformation

    ua_types = [
        ('NamespaceUri', 'String'),
        ('UnitId', 'Int32'),
        ('DisplayName', 'LocalizedText'),
        ('Description', 'LocalizedText'),
               ]

    def __init__(self):
        self.NamespaceUri = None
        self.UnitId = 0
        self.DisplayName = LocalizedText()
        self.Description = LocalizedText()
        self._freeze = True

    def __str__(self):
        return f'EUInformation(NamespaceUri:{self.NamespaceUri}, UnitId:{self.UnitId}, DisplayName:{self.DisplayName}, Description:{self.Description})'

    __repr__ = __str__


class ComplexNumberType(FrozenClass):
    """
    :ivar Real:
    :vartype Real: Float
    :ivar Imaginary:
    :vartype Imaginary: Float
    """

    data_type = ObjectIds.ComplexNumberType

    ua_types = [
        ('Real', 'Float'),
        ('Imaginary', 'Float'),
               ]

    def __init__(self):
        self.Real = 0
        self.Imaginary = 0
        self._freeze = True

    def __str__(self):
        return f'ComplexNumberType(Real:{self.Real}, Imaginary:{self.Imaginary})'

    __repr__ = __str__


class DoubleComplexNumberType(FrozenClass):
    """
    :ivar Real:
    :vartype Real: Double
    :ivar Imaginary:
    :vartype Imaginary: Double
    """

    data_type = ObjectIds.DoubleComplexNumberType

    ua_types = [
        ('Real', 'Double'),
        ('Imaginary', 'Double'),
               ]

    def __init__(self):
        self.Real = 0
        self.Imaginary = 0
        self._freeze = True

    def __str__(self):
        return f'DoubleComplexNumberType(Real:{self.Real}, Imaginary:{self.Imaginary})'

    __repr__ = __str__


class AxisInformation(FrozenClass):
    """
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

    data_type = ObjectIds.AxisInformation

    ua_types = [
        ('EngineeringUnits', 'EUInformation'),
        ('EURange', 'Range'),
        ('Title', 'LocalizedText'),
        ('AxisScaleType', 'AxisScaleEnumeration'),
        ('AxisSteps', 'ListOfDouble'),
               ]

    def __init__(self):
        self.EngineeringUnits = EUInformation()
        self.EURange = Range()
        self.Title = LocalizedText()
        self.AxisScaleType = AxisScaleEnumeration(0)
        self.AxisSteps = []
        self._freeze = True

    def __str__(self):
        return f'AxisInformation(EngineeringUnits:{self.EngineeringUnits}, EURange:{self.EURange}, Title:{self.Title}, AxisScaleType:{self.AxisScaleType}, AxisSteps:{self.AxisSteps})'

    __repr__ = __str__


class XVType(FrozenClass):
    """
    :ivar X:
    :vartype X: Double
    :ivar Value:
    :vartype Value: Float
    """

    data_type = ObjectIds.XVType

    ua_types = [
        ('X', 'Double'),
        ('Value', 'Float'),
               ]

    def __init__(self):
        self.X = 0
        self.Value = 0
        self._freeze = True

    def __str__(self):
        return f'XVType(X:{self.X}, Value:{self.Value})'

    __repr__ = __str__


class ProgramDiagnosticDataType(FrozenClass):
    """
    :ivar CreateSessionId:
    :vartype CreateSessionId: NodeId
    :ivar CreateClientName:
    :vartype CreateClientName: String
    :ivar InvocationCreationTime:
    :vartype InvocationCreationTime: DateTime
    :ivar LastTransitionTime:
    :vartype LastTransitionTime: DateTime
    :ivar LastMethodCall:
    :vartype LastMethodCall: String
    :ivar LastMethodSessionId:
    :vartype LastMethodSessionId: NodeId
    :ivar LastMethodInputArguments:
    :vartype LastMethodInputArguments: Argument
    :ivar LastMethodOutputArguments:
    :vartype LastMethodOutputArguments: Argument
    :ivar LastMethodCallTime:
    :vartype LastMethodCallTime: DateTime
    :ivar LastMethodReturnStatus:
    :vartype LastMethodReturnStatus: StatusResult
    """

    data_type = ObjectIds.ProgramDiagnosticDataType

    ua_types = [
        ('CreateSessionId', 'NodeId'),
        ('CreateClientName', 'String'),
        ('InvocationCreationTime', 'DateTime'),
        ('LastTransitionTime', 'DateTime'),
        ('LastMethodCall', 'String'),
        ('LastMethodSessionId', 'NodeId'),
        ('LastMethodInputArguments', 'ListOfArgument'),
        ('LastMethodOutputArguments', 'ListOfArgument'),
        ('LastMethodCallTime', 'DateTime'),
        ('LastMethodReturnStatus', 'StatusResult'),
               ]

    def __init__(self):
        self.CreateSessionId = NodeId()
        self.CreateClientName = None
        self.InvocationCreationTime = datetime.utcnow()
        self.LastTransitionTime = datetime.utcnow()
        self.LastMethodCall = None
        self.LastMethodSessionId = NodeId()
        self.LastMethodInputArguments = []
        self.LastMethodOutputArguments = []
        self.LastMethodCallTime = datetime.utcnow()
        self.LastMethodReturnStatus = StatusResult()
        self._freeze = True

    def __str__(self):
        return f'ProgramDiagnosticDataType(CreateSessionId:{self.CreateSessionId}, CreateClientName:{self.CreateClientName}, InvocationCreationTime:{self.InvocationCreationTime}, LastTransitionTime:{self.LastTransitionTime}, LastMethodCall:{self.LastMethodCall}, LastMethodSessionId:{self.LastMethodSessionId}, LastMethodInputArguments:{self.LastMethodInputArguments}, LastMethodOutputArguments:{self.LastMethodOutputArguments}, LastMethodCallTime:{self.LastMethodCallTime}, LastMethodReturnStatus:{self.LastMethodReturnStatus})'

    __repr__ = __str__


class ProgramDiagnostic2DataType(FrozenClass):
    """
    :ivar CreateSessionId:
    :vartype CreateSessionId: NodeId
    :ivar CreateClientName:
    :vartype CreateClientName: String
    :ivar InvocationCreationTime:
    :vartype InvocationCreationTime: DateTime
    :ivar LastTransitionTime:
    :vartype LastTransitionTime: DateTime
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
    :vartype LastMethodCallTime: DateTime
    :ivar LastMethodReturnStatus:
    :vartype LastMethodReturnStatus: StatusResult
    """

    data_type = ObjectIds.ProgramDiagnostic2DataType

    ua_types = [
        ('CreateSessionId', 'NodeId'),
        ('CreateClientName', 'String'),
        ('InvocationCreationTime', 'DateTime'),
        ('LastTransitionTime', 'DateTime'),
        ('LastMethodCall', 'String'),
        ('LastMethodSessionId', 'NodeId'),
        ('LastMethodInputArguments', 'ListOfArgument'),
        ('LastMethodOutputArguments', 'ListOfArgument'),
        ('LastMethodInputValues', 'ListOfVariant'),
        ('LastMethodOutputValues', 'ListOfVariant'),
        ('LastMethodCallTime', 'DateTime'),
        ('LastMethodReturnStatus', 'StatusResult'),
               ]

    def __init__(self):
        self.CreateSessionId = NodeId()
        self.CreateClientName = None
        self.InvocationCreationTime = datetime.utcnow()
        self.LastTransitionTime = datetime.utcnow()
        self.LastMethodCall = None
        self.LastMethodSessionId = NodeId()
        self.LastMethodInputArguments = []
        self.LastMethodOutputArguments = []
        self.LastMethodInputValues = []
        self.LastMethodOutputValues = []
        self.LastMethodCallTime = datetime.utcnow()
        self.LastMethodReturnStatus = StatusResult()
        self._freeze = True

    def __str__(self):
        return f'ProgramDiagnostic2DataType(CreateSessionId:{self.CreateSessionId}, CreateClientName:{self.CreateClientName}, InvocationCreationTime:{self.InvocationCreationTime}, LastTransitionTime:{self.LastTransitionTime}, LastMethodCall:{self.LastMethodCall}, LastMethodSessionId:{self.LastMethodSessionId}, LastMethodInputArguments:{self.LastMethodInputArguments}, LastMethodOutputArguments:{self.LastMethodOutputArguments}, LastMethodInputValues:{self.LastMethodInputValues}, LastMethodOutputValues:{self.LastMethodOutputValues}, LastMethodCallTime:{self.LastMethodCallTime}, LastMethodReturnStatus:{self.LastMethodReturnStatus})'

    __repr__ = __str__


class Annotation(FrozenClass):
    """
    :ivar Message:
    :vartype Message: String
    :ivar UserName:
    :vartype UserName: String
    :ivar AnnotationTime:
    :vartype AnnotationTime: DateTime
    """

    data_type = ObjectIds.Annotation

    ua_types = [
        ('Message', 'String'),
        ('UserName', 'String'),
        ('AnnotationTime', 'DateTime'),
               ]

    def __init__(self):
        self.Message = None
        self.UserName = None
        self.AnnotationTime = datetime.utcnow()
        self._freeze = True

    def __str__(self):
        return f'Annotation(Message:{self.Message}, UserName:{self.UserName}, AnnotationTime:{self.AnnotationTime})'

    __repr__ = __str__


nid = FourByteNodeId(ObjectIds.KeyValuePair_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = KeyValuePair
extension_object_typeids['KeyValuePair'] = nid
nid = FourByteNodeId(ObjectIds.EndpointType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EndpointType
extension_object_typeids['EndpointType'] = nid
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
nid = FourByteNodeId(ObjectIds.TrustListDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TrustListDataType
extension_object_typeids['TrustListDataType'] = nid
nid = FourByteNodeId(ObjectIds.DecimalDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DecimalDataType
extension_object_typeids['DecimalDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataTypeSchemaHeader_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataTypeSchemaHeader
extension_object_typeids['DataTypeSchemaHeader'] = nid
nid = FourByteNodeId(ObjectIds.DataTypeDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataTypeDescription
extension_object_typeids['DataTypeDescription'] = nid
nid = FourByteNodeId(ObjectIds.StructureDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StructureDescription
extension_object_typeids['StructureDescription'] = nid
nid = FourByteNodeId(ObjectIds.EnumDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumDescription
extension_object_typeids['EnumDescription'] = nid
nid = FourByteNodeId(ObjectIds.SimpleTypeDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SimpleTypeDescription
extension_object_typeids['SimpleTypeDescription'] = nid
nid = FourByteNodeId(ObjectIds.UABinaryFileDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UABinaryFileDataType
extension_object_typeids['UABinaryFileDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetMetaDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetMetaDataType
extension_object_typeids['DataSetMetaDataType'] = nid
nid = FourByteNodeId(ObjectIds.FieldMetaData_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FieldMetaData
extension_object_typeids['FieldMetaData'] = nid
nid = FourByteNodeId(ObjectIds.ConfigurationVersionDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ConfigurationVersionDataType
extension_object_typeids['ConfigurationVersionDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataSetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataSetDataType
extension_object_typeids['PublishedDataSetDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataSetSourceDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataSetSourceDataType
extension_object_typeids['PublishedDataSetSourceDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedVariableDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedVariableDataType
extension_object_typeids['PublishedVariableDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedDataItemsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedDataItemsDataType
extension_object_typeids['PublishedDataItemsDataType'] = nid
nid = FourByteNodeId(ObjectIds.PublishedEventsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PublishedEventsDataType
extension_object_typeids['PublishedEventsDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetWriterDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetWriterDataType
extension_object_typeids['DataSetWriterDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetWriterTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetWriterTransportDataType
extension_object_typeids['DataSetWriterTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetWriterMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetWriterMessageDataType
extension_object_typeids['DataSetWriterMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubGroupDataType
extension_object_typeids['PubSubGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.WriterGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriterGroupDataType
extension_object_typeids['WriterGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.WriterGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriterGroupTransportDataType
extension_object_typeids['WriterGroupTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.WriterGroupMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = WriterGroupMessageDataType
extension_object_typeids['WriterGroupMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConnectionDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConnectionDataType
extension_object_typeids['PubSubConnectionDataType'] = nid
nid = FourByteNodeId(ObjectIds.ConnectionTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ConnectionTransportDataType
extension_object_typeids['ConnectionTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.NetworkAddressDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NetworkAddressDataType
extension_object_typeids['NetworkAddressDataType'] = nid
nid = FourByteNodeId(ObjectIds.NetworkAddressUrlDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = NetworkAddressUrlDataType
extension_object_typeids['NetworkAddressUrlDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReaderGroupDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReaderGroupDataType
extension_object_typeids['ReaderGroupDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReaderGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReaderGroupTransportDataType
extension_object_typeids['ReaderGroupTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.ReaderGroupMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReaderGroupMessageDataType
extension_object_typeids['ReaderGroupMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetReaderDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetReaderDataType
extension_object_typeids['DataSetReaderDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetReaderTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetReaderTransportDataType
extension_object_typeids['DataSetReaderTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DataSetReaderMessageDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataSetReaderMessageDataType
extension_object_typeids['DataSetReaderMessageDataType'] = nid
nid = FourByteNodeId(ObjectIds.SubscribedDataSetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SubscribedDataSetDataType
extension_object_typeids['SubscribedDataSetDataType'] = nid
nid = FourByteNodeId(ObjectIds.TargetVariablesDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = TargetVariablesDataType
extension_object_typeids['TargetVariablesDataType'] = nid
nid = FourByteNodeId(ObjectIds.FieldTargetDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = FieldTargetDataType
extension_object_typeids['FieldTargetDataType'] = nid
nid = FourByteNodeId(ObjectIds.SubscribedDataSetMirrorDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SubscribedDataSetMirrorDataType
extension_object_typeids['SubscribedDataSetMirrorDataType'] = nid
nid = FourByteNodeId(ObjectIds.PubSubConfigurationDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = PubSubConfigurationDataType
extension_object_typeids['PubSubConfigurationDataType'] = nid
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
nid = FourByteNodeId(ObjectIds.DatagramConnectionTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramConnectionTransportDataType
extension_object_typeids['DatagramConnectionTransportDataType'] = nid
nid = FourByteNodeId(ObjectIds.DatagramWriterGroupTransportDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DatagramWriterGroupTransportDataType
extension_object_typeids['DatagramWriterGroupTransportDataType'] = nid
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
nid = FourByteNodeId(ObjectIds.AliasNameDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AliasNameDataType
extension_object_typeids['AliasNameDataType'] = nid
nid = FourByteNodeId(ObjectIds.RolePermissionType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RolePermissionType
extension_object_typeids['RolePermissionType'] = nid
nid = FourByteNodeId(ObjectIds.StructureField_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StructureField
extension_object_typeids['StructureField'] = nid
nid = FourByteNodeId(ObjectIds.StructureDefinition_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = StructureDefinition
extension_object_typeids['StructureDefinition'] = nid
nid = FourByteNodeId(ObjectIds.EnumDefinition_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumDefinition
extension_object_typeids['EnumDefinition'] = nid
nid = FourByteNodeId(ObjectIds.Argument_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Argument
extension_object_typeids['Argument'] = nid
nid = FourByteNodeId(ObjectIds.EnumValueType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumValueType
extension_object_typeids['EnumValueType'] = nid
nid = FourByteNodeId(ObjectIds.EnumField_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EnumField
extension_object_typeids['EnumField'] = nid
nid = FourByteNodeId(ObjectIds.OptionSet_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = OptionSet
extension_object_typeids['OptionSet'] = nid
nid = FourByteNodeId(ObjectIds.Union_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = Union
extension_object_typeids['Union'] = nid
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
nid = FourByteNodeId(ObjectIds.EndpointDescription_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EndpointDescription
extension_object_typeids['EndpointDescription'] = nid
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
nid = FourByteNodeId(ObjectIds.RelativePathElement_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RelativePathElement
extension_object_typeids['RelativePathElement'] = nid
nid = FourByteNodeId(ObjectIds.RelativePath_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = RelativePath
extension_object_typeids['RelativePath'] = nid
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
nid = FourByteNodeId(ObjectIds.ReadEventDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadEventDetails
extension_object_typeids['ReadEventDetails'] = nid
nid = FourByteNodeId(ObjectIds.ReadRawModifiedDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadRawModifiedDetails
extension_object_typeids['ReadRawModifiedDetails'] = nid
nid = FourByteNodeId(ObjectIds.ReadProcessedDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ReadProcessedDetails
extension_object_typeids['ReadProcessedDetails'] = nid
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
nid = FourByteNodeId(ObjectIds.HistoryEvent_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryEvent
extension_object_typeids['HistoryEvent'] = nid
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
nid = FourByteNodeId(ObjectIds.UpdateEventDetails_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = UpdateEventDetails
extension_object_typeids['UpdateEventDetails'] = nid
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
nid = FourByteNodeId(ObjectIds.AggregateConfiguration_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = AggregateConfiguration
extension_object_typeids['AggregateConfiguration'] = nid
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
nid = FourByteNodeId(ObjectIds.DataChangeNotification_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = DataChangeNotification
extension_object_typeids['DataChangeNotification'] = nid
nid = FourByteNodeId(ObjectIds.MonitoredItemNotification_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = MonitoredItemNotification
extension_object_typeids['MonitoredItemNotification'] = nid
nid = FourByteNodeId(ObjectIds.EventNotificationList_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EventNotificationList
extension_object_typeids['EventNotificationList'] = nid
nid = FourByteNodeId(ObjectIds.EventFieldList_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = EventFieldList
extension_object_typeids['EventFieldList'] = nid
nid = FourByteNodeId(ObjectIds.HistoryEventFieldList_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = HistoryEventFieldList
extension_object_typeids['HistoryEventFieldList'] = nid
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
nid = FourByteNodeId(ObjectIds.SessionDiagnosticsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SessionDiagnosticsDataType
extension_object_typeids['SessionDiagnosticsDataType'] = nid
nid = FourByteNodeId(ObjectIds.SessionSecurityDiagnosticsDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = SessionSecurityDiagnosticsDataType
extension_object_typeids['SessionSecurityDiagnosticsDataType'] = nid
nid = FourByteNodeId(ObjectIds.ServiceCounterDataType_Encoding_DefaultBinary)
extension_objects_by_typeid[nid] = ServiceCounterDataType
extension_object_typeids['ServiceCounterDataType'] = nid
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
