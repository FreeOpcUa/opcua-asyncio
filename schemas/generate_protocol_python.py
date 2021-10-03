import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IgnoredEnums = ["NodeIdType"]
IgnoredStructs = ["QualifiedName", "NodeId", "ExpandedNodeId", "FilterOperand", "Variant", "DataValue",
                  "ExtensionObject", "XmlElement", "LocalizedText"]


class CodeGenerator:

    def __init__(self, model, output):
        self.model = model
        self.output_path = output
        self.output_file = None
        self.indent = '    '
        self.iidx = 0  # indent index

    def run(self):
        print('Writting python protocol code to ', self.output_path)
        self.output_file = open(self.output_path, 'w', encoding='utf-8')
        self.make_header()
        for alias in self.model.aliases.values():
            self.write("")
            self.write("")
            self.write(f"{alias.name} = {alias.real_type}")
        for enum in self.model.enums:
            if enum.name not in IgnoredEnums:
                self.generate_enum_code(enum)
        for struct in self.model.structs:
            if struct.name in IgnoredStructs:
                continue
            if struct.name.endswith('Node') or struct.name.endswith('NodeId'):
                continue
            self.generate_struct_code(struct)

        self.iidx = 0
        self.write("")
        self.write("")
        for struct in self.model.structs:
            if struct.name in IgnoredStructs:
                continue
            if struct.name.endswith('Node') or struct.name.endswith('NodeId'):
                continue
            if struct.do_not_register:
                continue
            self.write(f"nid = FourByteNodeId(ObjectIds.{struct.name}_Encoding_DefaultBinary)")
            self.write(f"extension_objects_by_typeid[nid] = {struct.name}")
            self.write(f"extension_object_typeids['{struct.name}'] = nid")

    def write(self, line):
        if line:
            line = f'{self.indent * self.iidx}{line}'
        self.output_file.write(f'{line}\n')

    def make_header(self):
        self.write('"""')
        self.write(f'Autogenerate code from xml spec\nDate:{datetime.datetime.now()}')
        self.write('"""')
        self.write('')
        self.write('from datetime import datetime')
        self.write('from enum import IntEnum, IntFlag')
        self.write('from typing import Union, List, Optional')
        self.write('from dataclasses import dataclass, field')
        self.write('')
        self.write('from asyncua.ua.uatypes import FROZEN')
        self.write('from asyncua.ua.uatypes import SByte, Byte, Bytes, ByteString, Int16, Int32, Int64, UInt16, UInt32')
        self.write('from asyncua.ua.uatypes import UInt64, Boolean, Float, Double, Null, String, CharArray, DateTime, Guid')
        self.write('from asyncua.ua.uatypes import AccessLevel, EventNotifier  ')
        self.write('from asyncua.ua.uatypes import LocalizedText, Variant, QualifiedName, StatusCode, DataValue')
        self.write('from asyncua.ua.uatypes import NodeId, FourByteNodeId, ExpandedNodeId, ExtensionObject, DiagnosticInfo')
        self.write('from asyncua.ua.uatypes import extension_object_typeids, extension_objects_by_typeid')
        self.write('from asyncua.ua.object_ids import ObjectIds')

    def generate_enum_code(self, enum):
        self.write('')
        self.write('')
        if enum.is_option_set:
            self.write(f'class {enum.name}(IntFlag):')
            self.iidx = 1
            self.write('"""')
            if enum.doc:
                self.write(enum.doc)
                self.write("")
            for val in enum.fields:
                self.write(f':ivar {val.name}:')
                self.write(f':vartype {val.name}: Bit: {val.value}')
            self.write('"""')
            for val in enum.fields:
                self.write(f'{val.name} = 1<<{val.value}')
            self.iidx = 0
        else:
            self.write(f'class {enum.name}(IntEnum):')
            self.iidx = 1
            self.write('"""')
            if enum.doc:
                self.write(enum.doc)
                self.write("")
            for val in enum.fields:
                self.write(f':ivar {val.name}:')
                self.write(f':vartype {val.name}: {val.value}')
            self.write('"""')
            for val in enum.fields:
                self.write(f'{val.name} = {val.value}')
            self.iidx = 0

    def generate_struct_code(self, obj):
        self.write('')
        self.write('')
        self.iidx = 0
        self.write('@dataclass(frozen=FROZEN)')
        self.write(f'class {obj.name}:')
        self.iidx += 1
        self.write('"""')
        if obj.doc:
            self.write(obj.doc)
            self.write("")
        for field in obj.fields:
            self.write(f':ivar {field.name}:')
            self.write(f':vartype {field.name}: {field.data_type}')
        self.write('"""')

        # FIXME: next line is a weak way to find out if object is a datatype or not...
        if "Parameter" not in obj.name and "Result" not in obj.name:
            self.write('')
            self.write(f'data_type = NodeId(ObjectIds.{obj.name})')

        if obj.fields:
            self.write('')
        # hack extension object stuff
        extobj_hack = False
        if "BodyLength" in [f.name for f in obj.fields]:
            extobj_hack = True

        hack_names = []

        for field in obj.fields:
            typestring = field.data_type
            if field.is_array():
                typestring = f"List[{typestring}]"
            if field.is_optional:
                typestring = f"Optional[{typestring}]"

            if field.name == field.data_type:
                # variable name and type name are the same. Dataclass do not like it
                hack_names.append(field.name)
                fieldname = field.name + "_"
            else:
                fieldname = field.name

            if field.name == "Encoding":
                val = 0 if not extobj_hack else 1
                self.write(f"{field.name}: Byte = field(default={val}, repr=False, init=False, compare=False)")
            elif field.data_type == obj.name:  # help!!! selv referencing class
                # FIXME: Might not be good enough
                self.write(f"{fieldname}: Optional[ExtensionObject] = None")
            elif obj.name not in ("ExtensionObject",) and \
                    field.name == "TypeId":  # and ( obj.name.endswith("Request") or obj.name.endswith("Response")):
                self.write(f"TypeId: NodeId = FourByteNodeId(ObjectIds.{obj.name}_Encoding_DefaultBinary)")
            else:
                self.write(f"{fieldname}: {typestring} = {'field(default_factory=list)' if field.is_array() else self.get_default_value(field)}")

        if hack_names:
            self.write("")
        for name in hack_names:
            self.write("@property")
            self.write(f"def {name}(self):")
            self.write(f"    return self.{name}_")
            self.write("")
            self.write(f"@{name}.setter")
            self.write(f"def {name}(self, val):")
            self.write(f"    self.{name}_ = val")

        self.iidx = 0

    def get_default_value(self, field):
        if field.is_optional:
            return None
        dtype = field.data_type
        if dtype in self.model.enum_list:
            enum = self.model.get_enum(dtype)
            return f'{enum.name}.{enum.fields[0].name}'

        al = self.model.get_alias(dtype)
        if al is not None:
            dtype = al.real_type

        if dtype == 'String':
            return None
        if dtype in ('ByteString', 'CharArray', 'Char'):
            return None
        if dtype == 'Boolean':
            return 'True'
        if dtype == "Guid":
            return 'Guid(int=0)'
        if dtype == 'DateTime':
            return 'field(default_factory=datetime.utcnow)'
        if dtype in ('Int16', 'Int32', 'Int64', 'UInt16', 'UInt32', 'UInt64', 'Double', 'Float', 'Byte'):
            return 0
        if dtype in 'ExtensionObject':
            return 'ExtensionObject()'
        return f'field(default_factory={dtype})'


if __name__ == '__main__':
    import generate_model_from_nodeset as gm

    xml_path = os.path.join(BASE_DIR, 'schemas', 'UA-Nodeset-master', 'Schema', 'Opc.Ua.NodeSet2.Services.xml')
    protocol_path = os.path.join(BASE_DIR, "asyncua", "ua", "uaprotocol_auto.py")
    p = gm.Parser(xml_path)
    model = p.parse()
    gm.nodeid_to_names(model)
    gm.split_requests(model)
    gm.fix_names(model)
    gm.reorder_structs(model)
    c = CodeGenerator(model, protocol_path)
    c.run()
