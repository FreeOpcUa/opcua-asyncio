from ..ua import ObjectIds
from .node import Node


class Shortcuts:
    """
    This object contains Node objects to some commonly used nodes
    """
    def __init__(self, server):
        self.root = Node(server, ObjectIds.RootFolder)
        self.objects = Node(server, ObjectIds.ObjectsFolder)
        self.server = Node(server, ObjectIds.Server)
        self.base_object_type = Node(server, ObjectIds.BaseObjectType)
        self.base_data_type = Node(server, ObjectIds.BaseDataType)
        self.base_event_type = Node(server, ObjectIds.BaseEventType)
        self.base_variable_type = Node(server, ObjectIds.BaseVariableType)
        self.folder_type = Node(server, ObjectIds.FolderType)
        self.enum_data_type = Node(server, ObjectIds.Enumeration)
        self.types = Node(server, ObjectIds.TypesFolder)
        self.data_types = Node(server, ObjectIds.DataTypesFolder)
        self.event_types = Node(server, ObjectIds.EventTypesFolder)
        self.reference_types = Node(server, ObjectIds.ReferenceTypesFolder)
        self.variable_types = Node(server, ObjectIds.VariableTypesFolder)
        self.object_types = Node(server, ObjectIds.ObjectTypesFolder)
        self.namespace_array = Node(server, ObjectIds.Server_NamespaceArray)
        self.namespaces = Node(server, ObjectIds.Server_Namespaces)
        self.opc_binary = Node(server, ObjectIds.OPCBinarySchema_TypeSystem)
        self.base_structure_type = Node(server, ObjectIds.Structure)
        self.server_state = Node(server, ObjectIds.Server_ServerStatus_State)
        self.service_level = Node(server, ObjectIds.Server_ServiceLevel)
        self.HasComponent = Node(server, ObjectIds.HasComponent)
        self.HasProperty = Node(server, ObjectIds.HasProperty)
        self.Organizes = Node(server, ObjectIds.Organizes)
        self.HasEncoding = Node(server, ObjectIds.HasEncoding)
