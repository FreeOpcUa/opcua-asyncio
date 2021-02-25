import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IgnoredEnums = ["NodeIdType"]
IgnoredStructs = ["QualifiedName", "NodeId", "ExpandedNodeId", "FilterOperand", "Variant", "DataValue",
                  "ExtensionObject", "XmlElement", "LocalizedText"]


class Primitives1(object):
    SByte = 0
    Int16 = 0
    Int32 = 0
    Int64 = 0
    Char = 0
    Byte = 0
    UInt16 = 0
    UInt32 = 0
    UInt64 = 0
    Boolean = 0
    Double = 0
    Float = 0


class Primitives(Primitives1):
    Null = 0
    String = 0
    Bytes = 0
    ByteString = 0
    CharArray = 0
    DateTime = 0


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
            if 'ExtensionObject' in struct.parents or "DataTypeDefinition" in struct.parents:
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
        self.write('from enum import IntEnum')
        self.write('from typing import Union, List, Optional')
        self.write('from dataclasses import dataclass, field')
        self.write('')
        # self.write('from asyncua.ua.uaerrors import UaError')
        self.write('from asyncua.ua.uatypes import FROZEN')
        self.write('from asyncua.ua.uatypes import SByte, Byte, Bytes, ByteString, Int16, Int32, Int64, UInt16, UInt32, UInt64, Boolean, Float, Double, Null, String, CharArray, DateTime, Guid')
        self.write('from asyncua.ua.uatypes import AccessLevel, EventNotifier  ')
        self.write('from asyncua.ua.uatypes import LocalizedText, Variant, QualifiedName, StatusCode, DataValue')
        self.write('from asyncua.ua.uatypes import NodeId, FourByteNodeId, ExpandedNodeId, ExtensionObject')
        self.write('from asyncua.ua.uatypes import extension_object_typeids, extension_objects_by_typeid')
        self.write('from asyncua.ua.object_ids import ObjectIds')

    def generate_enum_code(self, enum):
        self.write('')
        self.write('')
        self.write(f'class {enum.name}(IntEnum):')
        self.iidx = 1
        self.write('"""')
        if enum.doc:
            self.write(enum.doc)
            self.write("")
        for val in enum.values:
            self.write(f':ivar {val.name}:')
            self.write(f':vartype {val.name}: {val.value}')
        self.write('"""')
        for val in enum.values:
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
            self.write(f':vartype {field.name}: {field.uatype}')
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
            # FIXME; flag optional those that are optional
            if field.length:
                typestring = f"List[{field.uatype}]"
            elif field.switchfield is not None:
                typestring = f"Optional[{field.uatype}]"
            else:
                typestring = field.uatype

            if field.name == field.uatype:
                # variable name and type name are the same. Dataclass do not like it
                print("SELF REFENCING", obj, field)
                hack_names.append(field.name)
                fieldname = field.name + "_"
            else:
                fieldname = field.name

            if field.name == "Encoding":
                val = 0 if not extobj_hack else 1
                self.write(f"{field.name}: Byte = field(default={val}, repr=False, init=False, compare=False)")
            elif field.uatype == obj.name:  # help!!! selv referencing class
                #FIXME: handle better
                self.write(f"{fieldname}: Optional[ExtensionObject] = None")
            elif obj.name not in ("ExtensionObject",) and \
                    field.name == "TypeId":  # and ( obj.name.endswith("Request") or obj.name.endswith("Response")):
                self.write(f"TypeId: NodeId = FourByteNodeId(ObjectIds.{obj.name}_Encoding_DefaultBinary)")
            else:
                self.write(f"{fieldname}: {typestring} = {'field(default_factory=list)' if field.length else self.get_default_value(field)}")

        switch_written = False
        for field in obj.fields:
            if field.switchfield is not None:
                if not switch_written:
                    self.write("")
                    self.write('ua_switches = {')
                    switch_written = True

                bit = obj.bits[field.switchfield]
                self.write(f"    '{field.name}': ('{bit.container}', {bit.idx}),")
            # if field.switchvalue is not None: Not sure we need to handle that one
        if switch_written:
            self.write("}")

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

    def write_unpack_enum(self, name, enum):
        self.write(f"self.{name} = {enum.name}(uabin.Primitives.{enum.uatype}.unpack(data))")

    def get_size_from_uatype(self, uatype):
        if uatype in ("Sbyte", "Byte", "Char", "Boolean"):
            return 1
        elif uatype in ("Int16", "UInt16"):
            return 2
        elif uatype in ("Int32", "UInt32", "Float"):
            return 4
        elif uatype in ("Int64", "UInt64", "Double"):
            return 8
        else:
            raise Exception(f"Cannot get size from type {uatype}")

    def write_unpack_uatype(self, name, uatype):
        if hasattr(Primitives, uatype):
            self.write(f"self.{name} = uabin.Primitives.{uatype}.unpack(data)")
        else:
            self.write(f"self.{name} = {uatype}.from_binary(data))")

    def write_pack_enum(self, listname, name, enum):
        self.write(f"{listname}.append(uabin.Primitives.{enum.uatype}.pack({name}.value))")

    def write_pack_uatype(self, listname, name, uatype):
        if hasattr(Primitives, uatype):
            self.write(f"{listname}.append(uabin.Primitives.{uatype}.pack({name}))")
        else:
            self.write(f"{listname}.append({name}.to_binary())")
            return

    def get_default_value(self, field):
        if field.switchfield:
            return None
        if field.uatype in self.model.enum_list:
            enum = self.model.get_enum(field.uatype)
            return f'{enum.name}.{enum.values[0].name}'
        if field.uatype == 'String':
            return None
        elif field.uatype in ('ByteString', 'CharArray', 'Char'):
            return None
        elif field.uatype == 'Boolean':
            return 'True'
        elif field.uatype == 'DateTime':
            return 'datetime.utcnow()'
        elif field.uatype in ('Int16', 'Int32', 'Int64', 'UInt16', 'UInt32', 'UInt64', 'Double', 'Float', 'Byte'):
            return 0
        elif field.uatype in 'ExtensionObject':
            return 'ExtensionObject()'
        else:
            return f'field(default_factory={field.uatype})'


if __name__ == '__main__':
    import generate_model as gm

    xml_path = os.path.join(BASE_DIR, 'schemas', 'UA-Nodeset-master', 'Schema', 'Opc.Ua.Types.bsd')
    protocol_path = os.path.join(BASE_DIR, "asyncua", "ua", "uaprotocol_auto.py")
    p = gm.Parser(xml_path)
    model = p.parse()
    gm.add_basetype_members(model)
    gm.add_encoding_field(model)
    gm.remove_duplicates(model)
    gm.remove_vector_length(model)
    gm.split_requests(model)
    gm.fix_names(model)
    gm.remove_duplicate_types(model)
    gm.reorder_structs(model)
    c = CodeGenerator(model, protocol_path)
    c.run()
