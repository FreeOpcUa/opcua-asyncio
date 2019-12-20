'''
  This example demonstrates the use of custom enums by:
  - Create a custom enum type
  - Create an object that contains a variable of this type
'''
import sys
sys.path.insert(0, "..")

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()

interactive = True


from asyncua import ua, Server
from asyncua.common import node
from enum import IntEnum

# Not required just for convenience
# Because this example is based on EnumStrings, the values should start at 0 and no gaps are allowed.
class MyEnum(IntEnum):
    ok = 0
    idle = 1

# helper method to automatically create string list
def enum_to_stringlist(a_enum):
    items = []
    for value in a_enum:
        items.append(ua.LocalizedText(value.name))
    return items

if __name__ == "__main__":
    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    nsidx = server.register_namespace(uri)

    # --------------------------------------------------------
    # create custom enum data type
    # --------------------------------------------------------
    enums = server.get_root_node().get_child(["0:Types", "0:DataTypes", "0:BaseDataType", "0:Enumeration"])

    # 1.
    # Create Enum Type
    myenum_type = enums.add_data_type(nsidx, 'MyEnum')

    # 2.
    # Add enumerations as EnumStrings (Not yet tested with EnumValues)
    # Essential to use namespace 0 for EnumStrings !

    # By hand
    #     es = myenum_type.add_variable(0, "EnumStrings" , [ua.LocalizedText("ok"),
    #                                                       ua.LocalizedText("idle")])

    # Or convert the existing IntEnum MyEnum
    es = myenum_type.add_property(0, "EnumStrings" , enum_to_stringlist(MyEnum))

    es.write_rank(1)
    es.set_array_dimensions([0])

    # --------------------------------------------------------
    # create object with enum variable
    # --------------------------------------------------------
    # get Objects node, this is where we should put our custom stuff
    objects = server.get_objects_node()

    # create object
    myobj = objects.add_object(nsidx, 'MyObjectWithEnumVar')

    # add var with as type the custom enumeration
    myenum_var = myobj.add_variable(nsidx, 'MyEnum2Var', MyEnum.ok, datatype = myenum_type.nodeid)
    myenum_var.set_writable()
    myenum_var.write(MyEnum.idle)  # change value of enumeration

    server.start()
    try:
        if interactive:
            embed()
        else:
            while True:
                time.sleep(0.5)

    except IOError:
        pass
    finally:
        server.stop()
        print("done")
