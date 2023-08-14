import pytest

from asyncua.ua.object_ids import ObjectIds
from asyncua.ua.uatypes import RelativePath


def test_relative_path():
    """
    The following examples from 1 to 7 are taken from OPC-UA Specification Part 4 - Services, A.2 BNF of RelativePath.

    https://reference.opcfoundation.org/Core/Part4/v105/docs/A.2
    """

    path1 = RelativePath.from_string("/2:Block&.Output")

    assert 1 == len(path1.Elements)
    assert path1.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path1.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HierarchicalReferences
    assert path1.Elements[0].IncludeSubtypes is True
    assert path1.Elements[0].IsInverse is False
    assert path1.Elements[0].TargetName.NamespaceIndex == 2
    assert path1.Elements[0].TargetName.Name == "Block.Output"
    assert path1.to_string() == "/2:Block&.Output"

    path1_1 = RelativePath.from_string(".2:Block&.Output")

    assert 1 == len(path1.Elements)
    assert path1_1.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path1_1.Elements[0].ReferenceTypeId.Identifier == ObjectIds.Aggregates
    assert path1_1.Elements[0].IncludeSubtypes is True
    assert path1_1.Elements[0].IsInverse is False
    assert path1_1.Elements[0].TargetName.NamespaceIndex == 2
    assert path1_1.Elements[0].TargetName.Name == "Block.Output"
    assert path1_1.to_string() == ".2:Block&.Output"

    path2 = RelativePath.from_string("/3:Truck.0:NodeVersion")

    assert 2 == len(path2.Elements)
    assert path2.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path2.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HierarchicalReferences
    assert path2.Elements[0].IncludeSubtypes is True
    assert path2.Elements[0].IsInverse is False
    assert path2.Elements[0].TargetName.NamespaceIndex == 3
    assert path2.Elements[0].TargetName.Name == "Truck"
    assert path2.Elements[1].ReferenceTypeId.NamespaceIndex == 0
    assert path2.Elements[1].ReferenceTypeId.Identifier == ObjectIds.Aggregates
    assert path2.Elements[1].IncludeSubtypes is True
    assert path2.Elements[1].IsInverse is False
    assert path2.Elements[1].TargetName.NamespaceIndex == 0
    assert path2.Elements[1].TargetName.Name == "NodeVersion"
    assert path2.to_string() == "/3:Truck.NodeVersion"

    # TODO: Fix to use <1:ConnectedTo> when the non-standard reference types are supported.
    path3 = RelativePath.from_string("<0:HasChild>1:Boiler/1:HeatSensor")

    assert 2 == len(path3.Elements)
    assert path3.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path3.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path3.Elements[0].IncludeSubtypes is True
    assert path3.Elements[0].IsInverse is False
    assert path3.Elements[0].TargetName.NamespaceIndex == 1
    assert path3.Elements[0].TargetName.Name == "Boiler"
    assert path3.Elements[1].ReferenceTypeId.NamespaceIndex == 0
    assert path3.Elements[1].ReferenceTypeId.Identifier == ObjectIds.HierarchicalReferences
    assert path3.Elements[1].IncludeSubtypes is True
    assert path3.Elements[1].IsInverse is False
    assert path3.Elements[1].TargetName.NamespaceIndex == 1
    assert path3.Elements[1].TargetName.Name == "HeatSensor"
    assert path3.to_string() == "<HasChild>1:Boiler/1:HeatSensor"

    # TODO: Fix to use <1:ConnectedTo> when the non-standard reference types are supported.
    path4 = RelativePath.from_string("<0:HasChild>1:Boiler/")

    assert 2 == len(path4.Elements)
    assert path4.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path4.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path4.Elements[0].IncludeSubtypes is True
    assert path4.Elements[0].IsInverse is False
    assert path4.Elements[0].TargetName.NamespaceIndex == 1
    assert path4.Elements[0].TargetName.Name == "Boiler"
    assert path4.Elements[1].ReferenceTypeId.NamespaceIndex == 0
    assert path4.Elements[1].ReferenceTypeId.Identifier == ObjectIds.HierarchicalReferences
    assert path4.Elements[1].IncludeSubtypes is True
    assert path4.Elements[1].IsInverse is False
    assert path4.Elements[1].TargetName is None
    assert path4.to_string() == "<HasChild>1:Boiler/"

    path5 = RelativePath.from_string("<0:HasChild>2:Wheel")

    assert 1 == len(path5.Elements)
    assert path5.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path5.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path5.Elements[0].IncludeSubtypes is True
    assert path5.Elements[0].IsInverse is False
    assert path5.Elements[0].TargetName.NamespaceIndex == 2
    assert path5.Elements[0].TargetName.Name == "Wheel"
    assert path5.to_string() == "<HasChild>2:Wheel"

    path6 = RelativePath.from_string("<!HasChild>Truck")

    assert 1 == len(path6.Elements)
    assert path6.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path6.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path6.Elements[0].IncludeSubtypes is True
    assert path6.Elements[0].IsInverse is True
    assert path6.Elements[0].TargetName.NamespaceIndex == 0
    assert path6.Elements[0].TargetName.Name == "Truck"
    assert path6.to_string() == "<!HasChild>Truck"

    path7 = RelativePath.from_string("<0:HasChild>")

    assert 1 == len(path7.Elements)
    assert path7.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path7.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path7.Elements[0].IncludeSubtypes is True
    assert path7.Elements[0].IsInverse is False
    assert path7.Elements[0].TargetName is None
    assert path7.to_string() == "<HasChild>"

    path8 = RelativePath.from_string("<#0:HasChild>Truck")

    assert 1 == len(path8.Elements)
    assert path8.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path8.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path8.Elements[0].IncludeSubtypes is False
    assert path8.Elements[0].IsInverse is False
    assert path8.Elements[0].TargetName.NamespaceIndex == 0
    assert path8.Elements[0].TargetName.Name == "Truck"
    assert path8.to_string() == "<#HasChild>Truck"

    path9 = RelativePath.from_string("<#!0:HasChild>Truck")

    assert 1 == len(path9.Elements)
    assert path9.Elements[0].ReferenceTypeId.NamespaceIndex == 0
    assert path9.Elements[0].ReferenceTypeId.Identifier == ObjectIds.HasChild
    assert path9.Elements[0].IncludeSubtypes is False
    assert path9.Elements[0].IsInverse is True
    assert path9.Elements[0].TargetName.NamespaceIndex == 0
    assert path9.Elements[0].TargetName.Name == "Truck"
    assert path9.to_string() == "<#!HasChild>Truck"


def test_relative_path_with_non_standard_reference_type():
    # TODO: Remove after the non-standard reference types are supported.
    with pytest.raises(ValueError):
        RelativePath.from_string("<1:ConnectedTo>1:Boiler/1:HeatSensor")

    with pytest.raises(ValueError):
        RelativePath.from_string("<1:ConnectedTo>1:Boiler/")


def test_relative_path_with_invalid_format():
    with pytest.raises(ValueError):
        RelativePath.from_string("/1:<Boiler")  # Non-escaped '<' is invalid.

    with pytest.raises(ValueError):
        RelativePath.from_string("/1:Boiler&")  # '&' is appeared without a follwing character.

    with pytest.raises(ValueError):
        RelativePath.from_string("/1:Boiler&Output")  # '&' is followed by a non-reserved char.

    with pytest.raises(ValueError):
        RelativePath.from_string("<0:HasChild")  # Closing delimiter '>' is missing.

    with pytest.raises(ValueError):
        RelativePath.from_string("<0:>1:Boiler")  # Empty reference type name
