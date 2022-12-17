"""
add nodes defined in XML to address space
format is the one from opc-ua specification
"""
import logging
import uuid
from typing import Union, Dict, List, Tuple
from dataclasses import fields, is_dataclass

from asyncua import ua
from asyncua.ua.uatypes import type_is_union, types_from_union, type_is_list, type_from_list
from .xmlparser import XMLParser, ua_type_to_python
from ..ua.uaerrors import UaError

_logger = logging.getLogger(__name__)

def _parse_version(version_string: str) -> List[int]:
    return [int(v) for v in version_string.split('.')]

class XmlImporter:

    def __init__(self, server, strict_mode=True):
        '''
        strict_mode: stop on an error, if False only an error message is logged,
                     but the import continues
        '''
        self.parser = None
        self.session = server
        self.namespaces: Dict[int, int] = {}  # Dict[IndexInXml, IndexInServer]
        self.aliases: Dict[str, ua.NodeId] = {}
        self._unmigrated_aliases: Dict[str, str] = {}  # Dict[name, nodeId string]
        self.refs = None
        self.strict_mode = strict_mode

    async def _map_namespaces(self):
        """
        creates a mapping between the namespaces in the xml file and in the server.
        if not present the namespace is registered.
        """
        xml_uris = self.parser.get_used_namespaces()
        server_uris = await self.session.get_namespace_array()
        namespaces_map = {}
        for ns_index, ns_uri in enumerate(xml_uris):
            ns_index += 1  # since namespaces start at 1 in xml files
            if ns_uri in server_uris:
                namespaces_map[ns_index] = server_uris.index(ns_uri)
            else:
                ns_server_index = await self.session.register_namespace(ns_uri)
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
        server_namespaces_node = await self.session.nodes.namespaces.get_children()
        for model_node in server_namespaces_node:
            server_model_list.append({
                "ModelUri": await (await model_node.get_child("NamespaceUri")).read_value(),
                "Version": await (await model_node.get_child("NamespaceVersion")).read_value(),
                "PublicationDate": (await (await model_node.get_child("NamespacePublicationDate")).read_value()).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
        return server_model_list

    async def _check_required_models(self, xmlpath=None, xmlstring=None):
        req_models = self.parser.list_required_models(xmlpath, xmlstring)
        if not req_models:
            return None
        server_model_list = await self._get_existing_model_in_namespace()
        for model in server_model_list:
            for req_model in req_models:
                if (model["ModelUri"] == req_model["ModelUri"] and model["PublicationDate"] >= req_model["PublicationDate"]):
                    if "Version" in model and "Version" in req_model:
                        if _parse_version(model["Version"]) >= _parse_version(req_model["Version"]):
                            req_models.remove(req_model)
                    else:
                        req_models.remove(req_model)
        if req_models:
            for missing_model in req_models:
                _logger.warning(
                    "Model is missing: %s - Version: %s - PublicationDate: %s or newer",
                    missing_model["ModelUri"],
                    missing_model["Version"],
                    missing_model["PublicationDate"],
                )
            raise ValueError("Server doesn't satisfy required XML-Models. Import them first!")
        return None

    async def _check_if_namespace_meta_information_is_added(self):
        """
        check if the NamespaceMetadata objects in server namespaces exists otherwise add them
        to prevent errors when other nodesets depend on this namespace.
        """
        descs = await self.session.nodes.namespaces.get_children_descriptions()
        ns_objs = [n.BrowseName.Name for n in descs]
        for uri, version, pub_date in self.parser.get_nodeset_namespaces():
            if uri not in ns_objs:
                idx = await self.session.register_namespace(uri)
                obj = await self.session.nodes.namespaces.add_object(idx, uri, ua.ObjectIds.NamespaceMetadataType, False)
                ns_uri = await obj.get_child('NamespaceUri')
                await ns_uri.write_value(uri, ua.VariantType.String)
                ns_ver = await obj.get_child('NamespaceVersion')
                await ns_ver.write_value(version, ua.VariantType.String)
                ns_date = await obj.get_child('NamespacePublicationDate')
                await ns_date.write_value(pub_date)
                ns_subset = await obj.get_child('IsNamespaceSubset')
                await ns_subset.write_value(True)

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
        self._unmigrated_aliases = self.parser.get_aliases()        # these nodeids are not migrated to server namespace indexes
        self.aliases = self._map_aliases(self._unmigrated_aliases)  # these nodeids are already migrated to server namespace indexes
        self.refs = []
        dnodes = self.parser.get_node_datas()
        dnodes = self.make_objects(dnodes)
        self._add_missing_parents(dnodes)
        nodes_parsed = self._sort_nodes_by_parentid(dnodes)
        nodes = []
        for nodedata in nodes_parsed:  # self.parser:
            try:
                node = await self._add_node_data(nodedata, no_namespace_migration=True)
                nodes.append(node)
            except Exception as e:
                _logger.warning("failure adding node %s %s", nodedata, e)
                if self.strict_mode:
                    raise
        self.refs, remaining_refs = [], self.refs
        await self._add_references(remaining_refs)
        missing_nodes = await self._add_missing_reverse_references(nodes)
        if missing_nodes:
            _logger.warning("The following references exist, but the Nodes are missing: %s", missing_nodes)
        if self.refs:
            _logger.warning(
                "The following references could not be imported and are probably broken: %s",
                self.refs,
            )
        await self._check_if_namespace_meta_information_is_added()
        return nodes

    async def _add_missing_reverse_references(self, new_nodes):
        __unidirectional_types = {ua.ObjectIds.GuardVariableType, ua.ObjectIds.HasGuard,
                                  ua.ObjectIds.TransitionVariableType, ua.ObjectIds.StateMachineType,
                                  ua.ObjectIds.StateVariableType, ua.ObjectIds.TwoStateVariableType,
                                  ua.ObjectIds.StateType, ua.ObjectIds.TransitionType,
                                  ua.ObjectIds.FiniteTransitionVariableType, ua.ObjectIds.HasInterface}
        dangling_refs_to_missing_nodes = set(new_nodes)

        RefSpecKey = Tuple[ua.NodeId, ua.NodeId, ua.NodeId] # (source_node_id, target_node_id, ref_type_id)
        node_reference_map: Dict[RefSpecKey, ua.ReferenceDescription] = {}

        for new_node_id in new_nodes:
            node = self.session.get_node(new_node_id)
            node_ref_list: List[ua.ReferenceDescription] = await node.get_references()

            for ref in node_ref_list:
                dangling_refs_to_missing_nodes.discard(new_node_id)
                dangling_refs_to_missing_nodes.discard(ref.NodeId)

                if ref.ReferenceTypeId.NamespaceIndex != 0 or ref.ReferenceTypeId.Identifier not in __unidirectional_types:
                    ref_key = (new_node_id, ref.NodeId, ref.ReferenceTypeId)
                    node_reference_map[ref_key] = ref

        for node in dangling_refs_to_missing_nodes:
            _logger.warning("Node %s has no references, so it does not exist in Server!", node)

        reference_fixes = []

        for ref_spec, ref in node_reference_map.items():
            source_node_id, target_node_id, ref_type = ref_spec
            reverse_ref_spec = (target_node_id, source_node_id, ref_type)
            if reverse_ref_spec not in node_reference_map:

                _logger.debug("Adding missing reference: %s <-> %s (%s)", target_node_id, source_node_id, ref.ReferenceTypeId)

                new_ref = ua.AddReferencesItem(SourceNodeId=target_node_id, TargetNodeId=source_node_id,
                    ReferenceTypeId=ref_type, IsForward=(not ref.IsForward))
                reference_fixes.append(new_ref)
        await self._add_references(reference_fixes)

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
                            self.session.nodes.HasComponent.nodeid,
                            self.session.nodes.HasProperty.nodeid]:
                        # if a node has several links, the last one will win
                        if ref.target in childs:
                            _logger.warning(
                                "overwriting parent target %s, shouldbe fixed %s %s %s",
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

    async def _add_node_data(self, nodedata, no_namespace_migration=False) -> ua.NodeId:
        if nodedata.nodetype == "UAObject":
            node = await self.add_object(nodedata, no_namespace_migration)
        elif nodedata.nodetype == "UAObjectType":
            node = await self.add_object_type(nodedata, no_namespace_migration)
        elif nodedata.nodetype == "UAVariable":
            node = await self.add_variable(nodedata, no_namespace_migration)
        elif nodedata.nodetype == "UAVariableType":
            node = await self.add_variable_type(nodedata, no_namespace_migration)
        elif nodedata.nodetype == "UAReferenceType":
            node = await self.add_reference_type(nodedata, no_namespace_migration)
        elif nodedata.nodetype == "UADataType":
            node = await self.add_datatype(nodedata, no_namespace_migration)
        elif nodedata.nodetype == "UAMethod":
            node = await self.add_method(nodedata, no_namespace_migration)
        else:
            raise ValueError(f"Not implemented node type: {nodedata.nodetype} ")
        return node

    def _get_server(self):
        if hasattr(self.session, "iserver"):
            return self.session.iserver.isession
        return self.session.uaclient

    async def _add_references(self, refs):
        res = await self._get_server().add_references(refs)

        for sc, ref in zip(res, refs):
            if not sc.is_good():
                self.refs.append(ref)

    def make_objects(self, node_data):
        new_nodes = []
        for node_datum in node_data:
            node_datum.nodeid = self._to_migrated_nodeid(node_datum.nodeid)
            node_datum.browsename = self._migrate_ns(ua.QualifiedName.from_string(node_datum.browsename))
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

    def _migrate_ns(self, obj: Union[ua.NodeId, ua.QualifiedName]) -> Union[ua.NodeId, ua.QualifiedName]:
        """
        Check if the index of nodeid or browsename  given in the xml model file
        must be converted to an already existing namespace id based on the files
        namespace uri

        :returns: NodeId (str)
        """
        if isinstance(obj, ua.NodeId):
            if obj.NamespaceIndex in self.namespaces:
                obj = ua.NodeId(Identifier=obj.Identifier, NamespaceIndex=self.namespaces[obj.NamespaceIndex], NodeIdType=obj.NodeIdType)
        if isinstance(obj, ua.QualifiedName):
            if obj.NamespaceIndex in self.namespaces:
                obj = ua.QualifiedName(Name=obj.Name, NamespaceIndex=self.namespaces[obj.NamespaceIndex])
        return obj

    def _get_add_node_item(self, obj, no_namespace_migration=False):
        node = ua.AddNodesItem()
        node.NodeClass = getattr(ua.NodeClass, obj.nodetype[2:])
        if no_namespace_migration:
            node.RequestedNewNodeId = obj.nodeid
            node.BrowseName = obj.browsename
            if obj.parent and obj.parentlink:
                node.ParentNodeId = obj.parent
                node.ReferenceTypeId = obj.parentlink
            if obj.typedef:
                node.TypeDefinition = obj.typedef
        else:
            node.RequestedNewNodeId = self._migrate_ns(obj.nodeid)
            node.BrowseName = self._migrate_ns(obj.browsename)
            if obj.parent and obj.parentlink:
                node.ParentNodeId = self._migrate_ns(obj.parent)
                node.ReferenceTypeId = self._migrate_ns(obj.parentlink)
            if obj.typedef:
                node.TypeDefinition = self._migrate_ns(obj.typedef)
        _logger.info(
            "Importing xml node (%s, %s) as (%s %s)",
            obj.browsename,
            obj.nodeid,
            node.BrowseName,
            node.RequestedNewNodeId)
        return node

    def _to_migrated_nodeid(self, nodeid: Union[ua.NodeId, None, str]) -> Union[ua.NodeId, ua.QualifiedName]:
        nodeid = self._to_nodeid(nodeid)
        return self._migrate_ns(nodeid)

    def _to_nodeid(self, nodeid: Union[ua.NodeId, None, str]) -> ua.NodeId:
        if isinstance(nodeid, ua.NodeId):
            return nodeid
        if not nodeid:
            return ua.NodeId(ua.ObjectIds.String)
        if "=" in nodeid:
            return ua.NodeId.from_string(nodeid)
        if hasattr(ua.ObjectIds, nodeid):
            return ua.NodeId(getattr(ua.ObjectIds, nodeid))
        if nodeid in self._unmigrated_aliases:
            return ua.NodeId.from_string(self._unmigrated_aliases[nodeid])
        return ua.NodeId(getattr(ua.ObjectIds, nodeid))

    async def add_object(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
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

    async def add_object_type(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
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

    async def add_variable(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
        attrs = ua.VariableAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        attrs.DataType = obj.datatype
        if obj.value is not None:
            attrs.Value = await self._add_variable_value(obj, )
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
        if name in self.aliases.keys():
            nodeid = self.aliases[name]
            class_type = ua.uatypes.get_extensionobject_class_type(nodeid)
            if class_type:
                return class_type
            raise Exception("Error no extension class registered ", name, nodeid)
        raise Exception("Error no alias found for extension class", name)

    async def _make_ext_obj(self, obj):
        try:
            extclass = self._get_ext_class(obj.objname)
        except Exception:
            await self.session.load_data_type_definitions()      # load new data type definitions since a customn class should be created
            extclass = self._get_ext_class(obj.objname)
        args = {}
        for name, val in obj.body:
            if not isinstance(val, list):
                raise Exception(
                    "Error val should be a list, this is a python-asyncua bug",
                    name,
                    type(val),
                    val,
                )
            for attname, v in val:
                atttype = self._get_val_type(extclass, attname)
                self._set_attr(atttype, args, attname, v)
        return extclass(**args)

    def _get_val_type(self, objclass, attname: str):
        for field in fields(objclass):
            if field.name == attname:
                return field.type
        raise UaError(f"Attribute '{attname}' defined in xml is not found in object '{objclass}'")

    def _set_attr(self, atttype, fargs, attname: str, val):
        # tow possible values:
        # either we get value directly
        # or a dict if it s an object or a list
        if type_is_union(atttype):
            atttype = types_from_union(atttype)[0]
        if isinstance(val, str):
            pval = ua_type_to_python(val, atttype.__name__)
            fargs[attname] = pval
            return
        # so we have either an object or a list...
        if type_is_list(atttype):
            atttype = type_from_list(atttype)
            my_list = []
            for vtype, v2 in val:
                if isinstance(v2, str):
                    my_list.append(ua_type_to_python(v2, vtype))
                else:
                    my_list.append(v2)
            fargs[attname] = my_list

        elif issubclass(atttype, ua.NodeId):  # NodeId representation does not follow common rules!!
            for attname2, v2 in val:
                if attname2 == "Identifier":
                    if hasattr(ua.ObjectIds, v2):
                        obj2 = ua.NodeId(getattr(ua.ObjectIds, v2))
                    else:
                        obj2 = ua.NodeId.from_string(v2)
                    fargs[attname] = self._migrate_ns(obj2)
                    break
        elif is_dataclass(atttype):
            subargs = {}
            for attname2, v2 in val:
                sub_atttype = self._get_val_type(atttype, attname2)
                self._set_attr(sub_atttype, subargs, attname2, v2)
            if "Encoding" in subargs:
                del subargs["Encoding"]
            fargs[attname] = atttype(**subargs)
        else:
            raise RuntimeError(f"Could not handle type {atttype} of type {type(atttype)}")

    async def _add_variable_value(self, obj):
        """
        Returns the value for a Variable based on the objects value type.
        """
        _logger.debug("Setting value with type %s and value %s", obj.valuetype, obj.value)
        if obj.valuetype == "ListOfExtensionObject":
            values = []
            for ext in obj.value:
                extobj = await self._make_ext_obj(ext)
                values.append(extobj)
            return ua.Variant(values, ua.VariantType.ExtensionObject)
        if obj.valuetype == "ListOfGuid":
            return ua.Variant([uuid.UUID(guid) for guid in obj.value], getattr(ua.VariantType, obj.valuetype[6:]))
        if obj.valuetype.startswith("ListOf"):
            vtype = obj.valuetype[6:]
            if hasattr(ua.ua_binary.Primitives, vtype):
                return ua.Variant(obj.value, getattr(ua.VariantType, vtype))
            if vtype == "LocalizedText":
                return ua.Variant([ua.LocalizedText(Text=item["Text"], Locale=item["Locale"]) for item in obj.value])
            if vtype in ["ExpandedNodeId", "QualifiedName", "XmlElement", "StatusCode"]:
                return ua.Variant(obj.value)
            return ua.Variant([getattr(ua, vtype)(v) for v in obj.value])
        if obj.valuetype == "ExtensionObject":
            extobj = await self._make_ext_obj(obj.value)
            return ua.Variant(extobj, getattr(ua.VariantType, obj.valuetype))
        if obj.valuetype == "Guid":
            return ua.Variant(uuid.UUID(obj.value), getattr(ua.VariantType, obj.valuetype))
        if obj.valuetype == "LocalizedText":
            myargs = dict(obj.value)
            if "Encoding" in myargs:
                del myargs["Encoding"]
            ltext = ua.LocalizedText(**dict(obj.value))
            return ua.Variant(ltext, ua.VariantType.LocalizedText)
        if obj.valuetype == "NodeId":
            return ua.Variant(ua.NodeId.from_string(obj.value))
        return ua.Variant(obj.value, getattr(ua.VariantType, obj.valuetype))

    async def add_variable_type(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
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
        else:
            attrs.IsAbstract = False
        if obj.dimensions:
            attrs.ArrayDimensions = obj.dimensions
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_method(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
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

    async def add_reference_type(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
        attrs = ua.ReferenceTypeAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        if obj.inversename:
            attrs.InverseName = ua.LocalizedText(obj.inversename)
        if obj.abstract:
            attrs.IsAbstract = obj.abstract
        else:
            attrs.IsAbstract = False
        if obj.symmetric:
            attrs.Symmetric = obj.symmetric
        node.NodeAttributes = attrs
        res = await self._get_server().add_nodes([node])
        await self._add_refs(obj)
        res[0].StatusCode.check()
        return res[0].AddedNodeId

    async def add_datatype(self, obj, no_namespace_migration=False):
        node = self._get_add_node_item(obj, no_namespace_migration)
        attrs = ua.DataTypeAttributes()
        if obj.desc:
            attrs.Description = ua.LocalizedText(obj.desc)
        attrs.DisplayName = ua.LocalizedText(obj.displayname)
        if obj.abstract:
            attrs.IsAbstract = obj.abstract
        else:
            attrs.IsAbstract = False
        if not obj.definitions:
            pass
        else:
            if obj.parent == self.session.nodes.enum_data_type.nodeid:
                attrs.DataTypeDefinition = self._get_edef(obj)
            elif obj.parent == self.session.nodes.base_structure_type.nodeid:
                attrs.DataTypeDefinition = self._get_sdef(obj)
            else:
                parent_node = self.session.get_node(obj.parent)
                path = await parent_node.get_path()
                if self.session.nodes.option_set_type in path:
                    # nodes below option_set_type are enums, not structs
                    attrs.DataTypeDefinition = self._get_edef(obj)
                elif self.session.nodes.base_structure_type in path:
                    attrs.DataTypeDefinition = self._get_sdef(obj)
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

    def _get_edef(self, obj):
        if not obj.definitions:
            return None
        edef = ua.EnumDefinition()
        for field in obj.definitions:
            f = ua.EnumField()
            f.Name = field.name
            if field.dname:
                f.DisplayName = ua.LocalizedText(Text=field.dname)
            else:
                f.DisplayName = ua.LocalizedText(Text=field.name)
            f.Value = field.value
            f.Description = ua.LocalizedText(Text=field.desc)
            edef.Fields.append(f)
        return edef

    def _get_sdef(self, obj):
        if not obj.definitions:
            return None
        sdef = ua.StructureDefinition()
        if obj.parent:
            sdef.BaseDataType = obj.parent
        for refdata in obj.refs:
            if refdata.reftype == self.session.nodes.HasEncoding.nodeid:
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
            f.MaxStringLength = field.max_str_len
            if f.IsOptional:
                optional = True
            if field.arraydim is None:
                f.ArrayDimensions = field.arraydim
            else:
                f.ArrayDimensions = [int(i) for i in field.arraydim.split(",")]
            f.Description = ua.LocalizedText(Text=field.desc)
            sdef.Fields.append(f)
        if obj.struct_type == "IsUnion":
            sdef.StructureType = ua.StructureType.Union
        elif optional or obj.struct_type == "IsOptional":
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
        sorted_nodes_ids = set()
        all_node_ids = set(data.nodeid for data in ndatas)
        while len(sorted_nodes_ids) < len(ndatas):
            for ndata in ndatas:
                if ndata.nodeid in sorted_nodes_ids:
                    continue
                elif (ndata.parent is None or ndata.parent not in all_node_ids):
                    sorted_ndatas.append(ndata)
                    sorted_nodes_ids.add(ndata.nodeid)
                else:
                    # Check if the nodes parent is already in the list of
                    # inserted nodes
                    if ndata.parent in sorted_nodes_ids:
                        sorted_ndatas.append(ndata)
                        sorted_nodes_ids.add(ndata.nodeid)
        return sorted_ndatas
