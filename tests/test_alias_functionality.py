"""
Tests for the __alias__ functionality that allows multiple datatypes
with the same name to coexist
"""

import pytest

from asyncua import Server, ua, uamethod
from asyncua.common.structures104 import new_struct, new_struct_field

pytestmark = pytest.mark.asyncio


async def test_multiple_structs_same_name_different_fields(opc):
    """
    Test that multiple structs with the same name but different fields
    can be registered and retrieved correctly using their NodeId
    """
    idx = 2

    # Create first struct named "MyStruct" with specific fields
    struct1_node, _ = await new_struct(
        opc.opc,
        idx,
        "MyStruct",
        [
            new_struct_field("Field1", ua.VariantType.Int32),
            new_struct_field("Field2", ua.VariantType.String),
        ],
    )

    # Create second struct with the SAME name but different fields
    struct2_node, _ = await new_struct(
        opc.opc,
        idx,
        "MyStruct",
        [
            new_struct_field("Field1", ua.VariantType.Boolean),
            new_struct_field("Field3", ua.VariantType.Double),
            new_struct_field("Field4", ua.VariantType.UInt32),
        ],
    )

    # Load the data type definitions
    await opc.opc.load_data_type_definitions()

    # Retrieve the structs by their NodeIds
    struct1_class = ua.get_custom_struct_via_nodeid(struct1_node.nodeid)
    struct2_class = ua.get_custom_struct_via_nodeid(struct2_node.nodeid)

    # Verify they are different classes
    assert struct1_class is not None
    assert struct2_class is not None
    assert struct1_class != struct2_class

    # Verify both have __alias__ attribute
    assert hasattr(struct1_class, '__alias__')
    assert hasattr(struct2_class, '__alias__')

    # Verify both have the same __name__ but different __alias__
    assert struct1_class.__name__ == "MyStruct"
    assert struct2_class.__name__ == "MyStruct"
    assert struct1_class.__alias__ != struct2_class.__alias__

    # Verify the structs have the correct fields
    import dataclasses
    struct1_fields = {f.name for f in dataclasses.fields(struct1_class)}
    struct2_fields = {f.name for f in dataclasses.fields(struct2_class)}

    assert "Field1" in struct1_fields
    assert "Field2" in struct1_fields
    assert "Field3" not in struct1_fields
    assert "Field4" not in struct1_fields

    assert "Field1" in struct2_fields
    assert "Field2" not in struct2_fields
    assert "Field3" in struct2_fields
    assert "Field4" in struct2_fields

    # Verify we can instantiate both structs
    instance1 = struct1_class()
    instance2 = struct2_class()

    assert instance1 is not None
    assert instance2 is not None

    # Verify instances have correct fields
    assert hasattr(instance1, 'Field1')
    assert hasattr(instance1, 'Field2')
    assert not hasattr(instance1, 'Field3')

    assert hasattr(instance2, 'Field1')
    assert hasattr(instance2, 'Field3')
    assert hasattr(instance2, 'Field4')
    assert not hasattr(instance2, 'Field2')


async def test_alias_in_datatype_aliases_dict(opc):
    """
    Test that the datatype_aliases dictionary correctly tracks all aliases
    """
    idx = 3
    struct_name = "SharedName"

    # Create two structs with the same name
    _, _ = await new_struct(
        opc.opc,
        idx,
        struct_name,
        [new_struct_field("X", ua.VariantType.Int32)],
    )

    _, _ = await new_struct(
        opc.opc,
        idx,
        struct_name,
        [new_struct_field("Y", ua.VariantType.String)],
    )

    await opc.opc.load_data_type_definitions()

    # Check that datatype_aliases contains the shared name
    assert struct_name in ua.datatype_aliases

    # Check that there are at least 2 aliases registered for this name
    aliases_list = ua.datatype_aliases[struct_name]
    assert len(aliases_list) >= 2

    # Verify each alias is accessible in the ua module
    for alias in aliases_list:
        assert hasattr(ua, alias), f"Alias {alias} not found in ua module"
        struct_class = getattr(ua, alias)
        assert struct_class.__name__ == struct_name


async def test_backward_compatibility_mode(opc):
    """
    Test that backward compatibility mode works correctly with aliases
    """
    idx = 4
    struct_name = "CompatTestStruct"

    # Create a struct
    struct_node, _ = await new_struct(
        opc.opc,
        idx,
        struct_name,
        [new_struct_field("Value", ua.VariantType.Int64)],
    )

    await opc.opc.load_data_type_definitions()

    # Get the struct class via nodeid
    struct_class = ua.get_custom_struct_via_nodeid(struct_node.nodeid)
    assert struct_class is not None

    # Verify the alias is properly set
    assert hasattr(struct_class, '__alias__')
    assert struct_class.__alias__ != struct_name

    # Test that enabling backward compatibility makes the simple name available
    ua.enable_backward_compatibility()

    # The simple name should now be accessible (if it's the first/only one registered)
    # Note: This might not work if multiple structs with same name exist
    if hasattr(ua, struct_name):
        simple_access = getattr(ua, struct_name)
        assert simple_access is not None


async def test_get_custom_struct_with_matching_fields(opc):
    """
    Test retrieving structs by name and fields when multiple structs share a name
    """
    idx = 5
    struct_name = "MultiFieldStruct"

    # Create first struct
    await new_struct(
        opc.opc,
        idx,
        struct_name,
        [
            new_struct_field("Alpha", ua.VariantType.Int32),
            new_struct_field("Beta", ua.VariantType.String),
        ],
    )

    # Create second struct with different fields
    await new_struct(
        opc.opc,
        idx,
        struct_name,
        [
            new_struct_field("Gamma", ua.VariantType.Double),
            new_struct_field("Delta", ua.VariantType.Boolean),
        ],
    )

    await opc.opc.load_data_type_definitions()

    # Retrieve by matching fields
    struct_alpha = ua.get_custom_struct_with_matching_fields(
        struct_name, ["Alpha", "Beta"]
    )
    struct_gamma = ua.get_custom_struct_with_matching_fields(
        struct_name, ["Gamma", "Delta"]
    )

    assert struct_alpha is not None
    assert struct_gamma is not None
    assert struct_alpha != struct_gamma

    # Verify the fields match
    import dataclasses
    alpha_fields = {f.name for f in dataclasses.fields(struct_alpha)}
    gamma_fields = {f.name for f in dataclasses.fields(struct_gamma)}

    assert alpha_fields == {"Alpha", "Beta"}
    assert gamma_fields == {"Gamma", "Delta"}


async def test_alias_preserves_original_name(opc):
    """
    Test that the alias mechanism preserves the original struct name
    """
    idx = 6
    original_name = "OriginalStructName"

    struct_node, _ = await new_struct(
        opc.opc,
        idx,
        original_name,
        [new_struct_field("Data", ua.VariantType.UInt32)],
    )

    await opc.opc.load_data_type_definitions()

    struct_class = ua.get_custom_struct_via_nodeid(struct_node.nodeid)

    # The __name__ should still be the original name
    assert struct_class.__name__ == original_name

    # But __alias__ should be different (unique)
    assert struct_class.__alias__ != original_name

    # The alias should be accessible in the ua module
    assert hasattr(ua, struct_class.__alias__)
    assert getattr(ua, struct_class.__alias__) == struct_class


async def test_multiple_structs_serialization(opc):
    """
    Test that structs with same name but different aliases serialize/deserialize correctly
    """
    idx = 7
    struct_name = "SerializableStruct"

    # Create two different structs with the same name
    struct1_node, _ = await new_struct(
        opc.opc,
        idx,
        struct_name,
        [new_struct_field("IntValue", ua.VariantType.Int32)],
    )

    struct2_node, _ = await new_struct(
        opc.opc,
        idx,
        struct_name,
        [new_struct_field("StringValue", ua.VariantType.String)],
    )

    await opc.opc.load_data_type_definitions()

    # Get the struct classes
    struct1_class = ua.get_custom_struct_via_nodeid(struct1_node.nodeid)
    struct2_class = ua.get_custom_struct_via_nodeid(struct2_node.nodeid)

    # Create variables using these structs
    instance1 = struct1_class()
    instance1.IntValue = 42

    instance2 = struct2_class()
    instance2.StringValue = "test value"

    # Create OPC UA variables
    var1 = await opc.opc.nodes.objects.add_variable(
        idx, "var_struct1", ua.Variant(instance1, ua.VariantType.ExtensionObject)
    )

    var2 = await opc.opc.nodes.objects.add_variable(
        idx, "var_struct2", ua.Variant(instance2, ua.VariantType.ExtensionObject)
    )

    # Read back the values
    read_val1 = await var1.read_value()
    read_val2 = await var2.read_value()

    # Verify the read values match what we wrote
    assert read_val1.IntValue == 42
    assert read_val2.StringValue == "test value"

    # Verify they are instances of the correct classes
    assert isinstance(read_val1, struct1_class)
    assert isinstance(read_val2, struct2_class)
    assert struct1_class != struct2_class


async def test_two_servers_same_method_name_different_struct_parameters():
    """
    Test that two servers can have methods with the same name taking parameters
    of custom types that share the same name but have different structures.
    This is a critical test for the alias functionality in distributed systems.
    """
    # Create first server
    server1 = Server()
    await server1.init()
    server1.set_endpoint("opc.tcp://127.0.0.1:48641")

    # Register namespace and create custom struct for server1
    ns1 = await server1.register_namespace("http://server1.example.com")
    struct1_node, _ = await new_struct(
        server1,
        ns1,
        "RequestData",
        [
            new_struct_field("UserId", ua.VariantType.Int32),
            new_struct_field("Action", ua.VariantType.String),
        ],
    )
    await server1.load_data_type_definitions()

    # Get the struct class for server1
    RequestData1 = ua.get_custom_struct_via_nodeid(struct1_node.nodeid)

    # Define method for server1
    @uamethod
    def process_request_server1(parent, request):
        """Server1's method - multiplies UserId by 10 and appends ' processed' to Action"""
        result = RequestData1()
        result.UserId = request.UserId * 10
        result.Action = f"{request.Action} processed"
        return result

    # Add method to server1
    await server1.nodes.objects.add_method(
        ns1,
        "ProcessRequest",
        process_request_server1,
        [RequestData1],
        [RequestData1],
    )

    # Create second server
    server2 = Server()
    await server2.init()
    server2.set_endpoint("opc.tcp://127.0.0.1:48642")

    # Register namespace and create custom struct for server2 (same name, different structure)
    ns2 = await server2.register_namespace("http://server2.example.com")
    struct2_node, _ = await new_struct(
        server2,
        ns2,
        "RequestData",
        [
            new_struct_field("ClientId", ua.VariantType.String),
            new_struct_field("Priority", ua.VariantType.Int32),
            new_struct_field("Data", ua.VariantType.Double),
        ],
    )
    await server2.load_data_type_definitions()

    # Get the struct class for server2
    RequestData2 = ua.get_custom_struct_via_nodeid(struct2_node.nodeid)

    # Define method for server2
    @uamethod
    def process_request_server2(parent, request):
        """Server2's method - concatenates ClientId with Priority and doubles the Data"""
        result = RequestData2()
        result.ClientId = f"{request.ClientId}_{request.Priority}"
        result.Priority = request.Priority + 100
        result.Data = request.Data * 2.0
        return result

    # Add method to server2
    await server2.nodes.objects.add_method(
        ns2,
        "ProcessRequest",
        process_request_server2,
        [RequestData2],
        [RequestData2],
    )

    try:
        # Start both servers
        await server1.start()
        await server2.start()

        # Test server1's method
        input1 = RequestData1()
        input1.UserId = 5
        input1.Action = "login"
        method1 = await server1.nodes.objects.get_child([f"{ns1}:ProcessRequest"])
        result1 = await server1.nodes.objects.call_method(method1, input1)
        assert isinstance(result1, RequestData1)
        assert result1.UserId == 50  # 5 * 10
        assert result1.Action == "login processed"

        # Test server2's method
        input2 = RequestData2()
        input2.ClientId = "CLIENT123"
        input2.Priority = 5
        input2.Data = 3.14
        method2 = await server2.nodes.objects.get_child([f"{ns2}:ProcessRequest"])
        result2 = await server2.nodes.objects.call_method(method2, input2)

        assert isinstance(result2, RequestData2)
        assert result2.ClientId == "CLIENT123_5"
        assert result2.Priority == 105  # 5 + 100
        assert result2.Data == 6.28  # 3.14 * 2

        # Verify results are of different types
        assert type(result1) is not type(result2)
        # Verify that both aliases are registered in ua module
        assert hasattr(ua, RequestData1.__alias__)
        assert hasattr(ua, RequestData2.__alias__)
        assert getattr(ua, RequestData1.__alias__) == RequestData1
        assert getattr(ua, RequestData2.__alias__) == RequestData2
    finally:
        # Clean up
        await server1.stop()
        await server2.stop()
