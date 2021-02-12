"""
add nodes defined in XML to address space
format is the one from opc-ua specification
"""
import logging
import uuid
from typing import Union, Dict
from copy import copy

from asyncua import ua
from .xmlparser import XMLParser, ua_type_to_python
from ..ua.uaerrors import UaError


_logger = logging.getLogger(__name__)


class XmlImporter:
    def __init__(self, server):
        self.parser = None
        self.server = server
        self.namespaces: Dict[int, int] = {}  # Dict[IndexInXml, IndexInServer]
        self.aliases: Dict[str, ua.NodeId] = {}
        self.refs = None

    async def _map_namespaces(self):
        """
        creates a mapping between the namespaces in the xml file and in the server.
        if not present the namespace is registered.
        """
        xml_uris = self.parser.get_used_namespaces()
        server_uris = await self.server.get_namespace_array()
        namespaces_map = {}
        for ns_index, ns_uri in enumerate(xml_uris):
            ns_index += 1  # since namespaces start at 1 in xml files
            if ns_uri in server_uris:
                namespaces_map[ns_index] = server_uris.index(ns_uri)
            else:
                ns_server_index = await self.server.register_namespace(ns_uri)
                namespaces_map[ns_index] = ns_server_index
        return namespaces_map

    def _map_aliases(self, aliases: dict):
        """
        maps the import aliases to the correct namespaces
        """
        aliases_mapped = {}
        for alias, node_id in aliases.items():
            aliases_mapped[alias] = self._to_migrated_nodeid(node_id)
        return aliases_mapped

    async def _get_existing_model_in_namespace(self):
        server_model_list = []
        server_namespaces_node = await self.server.nodes.namespaces.get_children()
        for model_node in server_namespaces_node:
            server_model_list.append(
                {
                    "ModelUri": await (await model_node.get_child("NamespaceUri")).read_value(),
                    "Version": await (await model_node.get_child("NamespaceVersion")).read_value(),
                    "PublicationDate": (
                        await (await model_node.get_child("NamespacePublicationDate")).read_value()
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )
        return server_model_list

    async def _check_required_models(self, xmlpath=None, xmlstring=None):
        req_models = self.parser.list_required_models(xmlpath, xmlstring)
        if not req_models:
            return None
        server_model_list = await self._get_existing_model_in_namespace()
        for model in server_model_list:
            for req_model in req_models:
                if (
                    model["ModelUri"] == req_model["ModelUri"]
                    and model["PublicationDate"] >= req_model["PublicationDate"]
                ):
                    if "Version" in model and "Version" in req_model:
                        if model["Version"] >= req_model["Version"]:
                            req_models.remove(req_model)
                    else:
                        req_models.remove(req_model)
        if len(req_models):
            for missing_model in req_models:
                _logger.warning(
                    "Model is missing: %s - Version: %s - PublicationDate: %s or newer",
                    missing_model["ModelUri"],
                    missing_model["Version"],
                    missing_model["PublicationDate"],
                )
            raise ValueError("Server doesn't satisfy required XML-Models. Import them first!")
        return None

    async def import_xml(self, xmlpath=None, xmlstring=None):
        """
        import xml and return added nodes
        """
        if (xmlpath is None and xmlstring is None) or (xmlpath and xmlstring):
            raise ValueError("Expected either xmlpath or xmlstring, not both or neither.")
        _logger.info("Importing XML file %s", xmlpath)
        self.parser = XMLParser()
        await self._check_required_models(xmlpath, xmlstring)
        await self.parser.parse(xmlpath, xmlstring)
        self.namespaces = await self._map_namespaces()
        _logger.info("namespace map: %s", self.namespaces)
        self.aliases = self._map_aliases(self.parser.get_aliases())
        self.refs = []
        dnodes = self.parser.get_node_datas()
        dnodes = self.make_objects(dnodes)
        self._add_missing_parents(dnodes)
        nodes_parsed = self._sort_nodes_by_parentid(dnodes)
        nodes = []
        for nodedata in nodes_parsed:  # self.parser:
            try:
                node = await self._add_node_data(nodedata)
            except Exception:
                _logger.warning("failure adding node %s", nodedata)
                raise
            nodes.append(node)
        self.refs, remaining_refs = [], self.refs
        await self._add_references(remaining_refs)
        missing_nodes = await self._add_missing_reverse_references(nodes)
        if missing_nodes:
            _logger.warning(f"The following references exist, but the Nodes are missing: {missing_nodes}")
        if len(self.refs):
            _logger.warning("The following references could not be imported and are probably broken: %s", self.refs,)
        return nodes

    async def _add_missing_reverse_references(self, new_nodes):
        __unidirectional_types = {ua.ObjectIds.GuardVariableType, ua.ObjectIds.HasGuard,
                                  ua.ObjectIds.TransitionVariableType, ua.ObjectIds.StateMachineType,
                                  ua.ObjectIds.StateVariableType, ua.ObjectIds.TwoStateVariableType,
                                  ua.ObjectIds.StateType, ua.ObjectIds.TransitionType,
                                  ua.ObjectIds.FiniteTransitionVariableType, ua.ObjectIds.HasInterface}
        dangling_refs_to_missing_nodes = set()
        for new_node_id in new_nodes:
            new_n = self.server.get_node(new_node_id)
            new_n_refs = await new_n.get_references()
            if len(new_n_refs) == 0:
                _logger.warning(f"Node {new_node_id} has no references, so it does not exist in Server!")
                continue
            for ref in new_n_refs:
                if ref.ReferenceTypeId not in __unidirectional_types:
                    n = self.server.get_node(ref.NodeId)
                    n_refs = await n.get_references()
                    if len(n_refs) == 0:
                        _logger.warning(f"Node {ref.NodeId} has no references, so it does not exist in Server!")
                        dangling_refs_to_missing_nodes.add(ref.NodeId)
                        continue
                    for n_ref in n_refs:
                        if new_node_id == n_ref.NodeId and n_ref.ReferenceTypeId == ref.ReferenceTypeId:
                            break
                    else:
                        await n.add_reference(new_node_id, ref.ReferenceTypeId, not ref.IsForward)
        return dangling_refs_to_missing_nodes

    def _add_missing_parents(self, dnodes):
        missing = []
        childs = {}
        for nd in dnodes:
            if not nd.parent or nd.parent == nd.nodeid:
                missing.append(nd)
            for ref in nd.refs:
                if ref.forward:
                    if ref.reftype in [
                        self.server.nodes.HasComponent.nodeid,
                        self.server.nodes.HasProperty.nodeid,
                        self.server.nodes.Organizes.nodeid,
                    ]:
                        # if a node has several links, the last one will win
                        if ref.target in childs:
                            _logger.warning(
                                "overwriting parent target, shouldbe fixed",
                                ref.target,
                                nd.nodeid,
                                ref.reftype,
                                childs[ref.target],
                            )
                        childs[ref.target] = (nd.nodeid, ref.reftype)
        for nd in missing:
            if nd.nodeid in childs:
                target, reftype = childs[nd.nodeid]
                nd.parent = target
                nd.parentlink = reftype

    async def _add_node_data(self, nodedata) -> ua.NodeId:
        if nodedata.nodetype == "UAObject":
            node = await self.add_object(nodedata)
        elif nodedata.nodetype == "UAObjectType":
            node = await self.add_object_type(nodedata)
        elif nodedata.nodetype == "UAVariable":
            node = await self.add_variable(nodedata)
        elif nodedata.nodetype == "UAVariableType":
            node = await self.add_variable_type(nodedata)
        elif nodedata.nodetype == "UAReferenceType":
            node = await self.add_reference_type(nodedata)
        elif nodedata.nodetype == "UADataType":
            node = await self.add_datatype(nodedata)
        elif nodedata.nodetype == "UAMethod":
            node = await self.add_method(nodedata)
        else:
            raise ValueError(f"Not implemented node type: {nodedata.nodetype} ")
        return node

    def _get_server(self):
        if hasattr(self.server, "iserver"):
            return self.server.iserver.isession
        else:
            return self.server.uaclient

    async def _add_references(self, refs):
        res = await self._get_server().add_references(refs)

        for sc, ref in zip(res, refs):
            if not sc.is_good():
                self.refs.append(ref)

    def make_objects(self, node_data):
        new_nodes = []
        for node_datum in node_data:
            node_datum.nodeid = self._to_migrated_nodeid(node_datum.nodeid)
            node_datum.browsename = ua.QualifiedName.from_string(node_datum.browsename)
            if node_datum.parent:
                node_datum.parent = self._to_migrated_nodeid(node_datum.parent)
            if node_datum.parentlink:
                node_datum.parentlink = self._to_migrated_nodeid(node_datum.parentlink)
            if node_datum.typedef:
                node_datum.typedef = self._to_migrated_nodeid(node_datum.typedef)
            if node_datum.datatype:
                node_datum.datatype = self._to_migrated_nodeid(node_datum.datatype)
            new_nodes.append(node_datum)
            for ref in node_datum.refs:
                ref.reftype = self._to_migrated_nodeid(ref.reftype)
                ref.target = self._to_migrated_nodeid(ref.target)
            for field in node_datum.definitions:
                if field.datatype:
                    field.datatype = self._to_migrated_nodeid(field.datatype)
        return new_nodes

    def _migrate_ns(self, nodeid: ua.NodeId) -> ua.NodeId:
        """
        Check if the index of nodeid or browsename  given in the xml model file
        must be converted to a already existing namespace id based on the files
        namespace uri

        :returns: NodeId (str)
        """
        if nodeid.NamespaceIndex in self.namespaces:
            nodeid = copy(nodeid)
            nodeid.NamespaceIndex = self.namespaces[nodeid.NamespaceIndex]
        return nodeid

    def _get_add_node_item(self, obj):
        node = ua.AddNodesItem()
        node.RequestedNewNodeId = self._migrate_ns(obj.nodeid)
        node.BrowseName = self._migrate_ns(obj.browsename)
        _logger.info(
            "Importing xml node (%s, %s) as (%s %s)",
            obj.browsename,
            obj.nodeid,
            node.BrowseName,
            node.RequestedNewNodeId,
        )
        node.NodeClass = getattr(ua.NodeClass, obj.nodetype[2:])
        if obj.parent and obj.parentlink:
            node.ParentNodeId = self._migrate_ns(obj.parent)
            node.ReferenceTypeId = self._migrate_ns(obj.parentlink)
        if obj.typedef:
            node.TypeDefinition = self._migrate_ns(obj.typedef)
        return node

    def _to_migrated_nodeid(self, nodeid: Union[ua.NodeId, None, str]) -> ua.NodeId:
        nodeid = self._to_nodeid(nodeid)
        return self._migrate_ns(nodeid)

    def _to_nodeid(self, nodeid: Union[ua.NodeId, None, str]) -> ua.NodeId:
        if isinstance(nodeid, ua.NodeId):
            return nodeid
        elif not nodeid:
            return ua.NodeId(ua.ObjectIds.String)
        elif "=" in nodeid:
            return ua.NodeId.from_string(nodeid)
        elif hasattr(ua.ObjectIds, nodeid):
            return ua.NodeId(getattr(ua.ObjectIds, nodeid))
        else:
            if nodeid in self.aliases:
                return self.aliases[nodeid]
            else:
                return ua.NodeId(getattr(ua.ObjectIds, nodeid))

    async def add_object(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.ObjectAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        attrs.EventNotifier = obj.eventnotifier
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_object_type(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.ObjectTypeAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        attrs.IsAbstract = obj.abstract
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_variable(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.VariableAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        attrs.DataType = obj.datatype
        if obj.value is not None:
            attrs.Value = self._add_variable_value(
                obj,
            )
        if obj.rank:
            attrs.ValueRank = obj.rank
        if obj.accesslevel:
            attrs.AccessLevel = obj.accesslevel
        if obj.useraccesslevel:
            attrs.UserAccessLevel = obj.useraccesslevel
        if obj.minsample:
            attrs.MinimumSamplingInterval = obj.minsample
        if obj.dimensions:
            attrs.ArrayDimensions = obj.dimensions
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    def _get_ext_class(self, name: str):
        if hasattr(ua, name):
            return getattr(ua, name)
        elif name in self.aliases.keys():
            nodeid = self.aliases[name]
            class_type = ua.uatypes.get_extensionobject_class_type(nodeid)
            if class_type:
                return class_type
            else:
                raise Exception("Error no extension class registered ", name, nodeid)
        else:
            raise Exception("Error no alias found for extension class", name)

    def _make_ext_obj(self, obj):
        ext = self._get_ext_class(obj.objname)()
        for name, val in obj.body:
            if not isinstance(val, list):
                raise Exception(
                    "Error val should be a list, this is a python-asyncua bug",
                    name,
                    type(val),
                    val,
                )
            else:
                for attname, v in val:
                    self._set_attr(ext, attname, v)
        return ext

    def _get_val_type(self, obj, attname: str):
        for name, uatype in obj.ua_types:
            if name == attname:
                return uatype
        raise UaError(f"Attribute '{attname}' defined in xml is not found in object '{obj}'")

    def _set_attr(self, obj, attname: str, val):
        # tow possible values:
        # either we get value directly
        # or a dict if it s an object or a list
        if isinstance(val, str):
            pval = ua_type_to_python(val, self._get_val_type(obj, attname))
            setattr(obj, attname, pval)
        else:
            # so we have either an object or a list...
            obj2 = getattr(obj, attname)
            if isinstance(obj2, ua.NodeId):  # NodeId representation does not follow common rules!!
                for attname2, v2 in val:
                    if attname2 == "Identifier":
                        if hasattr(ua.ObjectIds, v2):
                            obj2 = ua.NodeId(getattr(ua.ObjectIds, v2))
                        else:
                            obj2 = ua.NodeId.from_string(v2)
                        setattr(obj, attname, self._migrate_ns(obj2))
                        break
            elif not hasattr(obj2, "ua_types"):
                # we probably have a list
                my_list = []
                for vtype, v2 in val:
                    my_list.append(ua_type_to_python(v2, vtype))
                setattr(obj, attname, my_list)
            else:
                for attname2, v2 in val:
                    self._set_attr(obj2, attname2, v2)
                setattr(obj, attname, obj2)

    def _add_variable_value(self, obj):
        """
        Returns the value for a Variable based on the objects value type.
        """
        _logger.debug("Setting value with type %s and value %s", obj.valuetype, obj.value)
        if obj.valuetype == "ListOfExtensionObject":
            values = []
            for ext in obj.value:
                extobj = self._make_ext_obj(ext)
                values.append(extobj)
            return ua.Variant(values, ua.VariantType.ExtensionObject)
        elif obj.valuetype == "ListOfGuid":
            return ua.Variant(
                [uuid.UUID(guid) for guid in obj.value], getattr(ua.VariantType, obj.valuetype[6:])
            )
        elif obj.valuetype.startswith("ListOf"):
            vtype = obj.valuetype[6:]
            if hasattr(ua.ua_binary.Primitives, vtype):
                return ua.Variant(obj.value, getattr(ua.VariantType, vtype))
            elif vtype == "LocalizedText":
                return ua.Variant(
                    [
                        getattr(ua, vtype)(text=item["Text"], locale=item["Locale"])
                        for item in obj.value
                    ]
                )
            else:
                return ua.Variant([getattr(ua, vtype)(v) for v in obj.value])
        elif obj.valuetype == "ExtensionObject":
            extobj = self._make_ext_obj(obj.value)
            return ua.Variant(extobj, getattr(ua.VariantType, obj.valuetype))
        elif obj.valuetype == "Guid":
            return ua.Variant(uuid.UUID(obj.value), getattr(ua.VariantType, obj.valuetype))
        elif obj.valuetype == "LocalizedText":
            ltext = ua.LocalizedText()
            for name, val in obj.value:
                if name == "Text":
                    ltext.Text = val
                elif name == "Locale":
                    ltext.Locale = val
                else:
                    _logger.warning(
                        "While parsing localizedText value, unkown element: %s with val: %s",
                        name,
                        val,
                    )
            return ua.Variant(ltext, ua.VariantType.LocalizedText)
        elif obj.valuetype == "NodeId":
            return ua.Variant(ua.NodeId.from_string(obj.value))
        else:
            return ua.Variant(obj.value, getattr(ua.VariantType, obj.valuetype))

    async def add_variable_type(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.VariableTypeAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        attrs.DataType = obj.datatype
        if obj.value and len(obj.value) == 1:
            attrs.Value = obj.value[0]
        if obj.rank:
            attrs.ValueRank = obj.rank
        if obj.abstract:
            attrs.IsAbstract = obj.abstract
        if obj.dimensions:
            attrs.ArrayDimensions = obj.dimensions
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_method(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.MethodAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        if obj.accesslevel:
            attrs.AccessLevel = obj.accesslevel
        if obj.useraccesslevel:
            attrs.UserAccessLevel = obj.useraccesslevel
        if obj.minsample:
            attrs.MinimumSamplingInterval = obj.minsample
        if obj.dimensions:
            attrs.ArrayDimensions = obj.dimensions
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_reference_type(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.ReferenceTypeAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        if obj.inversename:
            attrs.InverseName = ua.LocalizedText(obj.inversename)
        if obj.abstract:
            attrs.IsAbstract = obj.abstract
        if obj.symmetric:
            attrs.Symmetric = obj.symmetric
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_datatype(self, obj):
        node = self._get_add_node_item(obj)
        attrs = ua.DataTypeAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        if obj.abstract:
            attrs.IsAbstract = obj.abstract
        if not obj.definitions:
            pass
        else:
            if obj.parent == self.server.nodes.enum_data_type.nodeid:
                attrs.DataTypeDefinition = self._get_edef(node, obj)
            elif obj.parent == self.server.nodes.base_structure_type.nodeid:
                attrs.DataTypeDefinition = self._get_sdef(node, obj)
            else:
                parent_node = self.server.get_node(obj.parent)
                path = await parent_node.get_path()
                if self.server.nodes.base_structure_type in path:
                    attrs.DataTypeDefinition = self._get_sdef(node, obj)
                else:
                    _logger.warning(
                        "%s has datatypedefinition and path %s"
                        " but we could not find out if this is a struct",
                        obj,
                        path,
                    )
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        res[0].StatusCode.check()
        await self._add_refs(obj)
        return res[0].AddedNodeId

    async def _add_refs(self, obj):
        if not obj.refs:
            return
        refs = []
        for data in obj.refs:
            ref = ua.AddReferencesItem()
            ref.IsForward = data.forward
            ref.ReferenceTypeId = data.reftype
            ref.SourceNodeId = obj.nodeid
            ref.TargetNodeId = data.target
            refs.append(ref)
        await self._add_references(refs)

    def _get_edef(self, node, obj):
        if not obj.definitions:
            return None
        edef = ua.EnumDefinition()
        for field in obj.definitions:
            f = ua.EnumField()
            f.Name = field.name
            if field.dname:
                f.DisplayName = ua.LocalizedText(text=field.dname)
            else:
                f.DisplayName = ua.LocalizedText(text=field.name)
            f.Value = field.value
            f.Description = ua.LocalizedText(text=field.desc)
            edef.Fields.append(f)
        return edef

    def _get_sdef(self, node, obj):
        if not obj.definitions:
            return None
        sdef = ua.StructureDefinition()
        if obj.parent:
            sdef.BaseDataType = obj.parent
        for refdata in obj.refs:
            if refdata.reftype == self.server.nodes.HasEncoding.nodeid:
                # supposing that default encoding is the first one...
                sdef.DefaultEncodingId = refdata.target
                break
        optional = False
        for field in obj.definitions:
            f = ua.StructureField()
            f.Name = field.name
            f.DataType = field.datatype
            f.ValueRank = field.valuerank
            f.IsOptional = field.optional
            if f.IsOptional:
                optional = True
            f.ArrayDimensions = field.arraydim
            f.Description = ua.LocalizedText(text=field.desc)
            sdef.Fields.append(f)
        if optional:
            sdef.StructureType = ua.StructureType.StructureWithOptionalFields
        else:
            sdef.StructureType = ua.StructureType.Structure
        return sdef

    def _sort_nodes_by_parentid(self, ndatas):
        """
        Sort the list of nodes according their parent node in order to respect
        the dependency between nodes.

        :param nodes: list of NodeDataObjects
        :returns: list of sorted nodes
        """

        sorted_ndatas = []
        sorted_nodes_ids = []
        all_node_ids = [data.nodeid for data in ndatas]
        while ndatas:
            for ndata in ndatas[:]:
                if (
                    ndata.nodeid.NamespaceIndex not in self.namespaces.values()
                    or ndata.parent is None
                    or ndata.parent not in all_node_ids
                ):
                    sorted_ndatas.append(ndata)
                    sorted_nodes_ids.append(ndata.nodeid)
                    ndatas.remove(ndata)
                else:
                    # Check if the nodes parent is already in the list of
                    # inserted nodes
                    if ndata.parent in sorted_nodes_ids:
                        sorted_ndatas.append(ndata)
                        sorted_nodes_ids.append(ndata.nodeid)
                        ndatas.remove(ndata)
        return sorted_ndatas
