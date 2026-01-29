# the order is important, some classes are overriden
from .attribute_ids import AttributeIds
from .object_ids import ObjectIds
from .object_ids import ObjectIdNames
from .status_codes import StatusCodes
from .uaprotocol_auto import *
from .uaprotocol_hand import *
from .uatypes import *  # TODO: This should be renamed to uatypes_hand
from .uatypes import get_extensionobject_class_type
from .uaerrors import UaStatusCodeErrors
import dataclasses
from typing import Any

import sys
_current_module = sys.modules[__name__]

def get_real(name):
    if name in _current_module.__dict__:
        return _current_module.__dict__[name]
    return None

def delete_custom_struct_via_name(name: str):
    if name in _current_module.__dict__:
        del _current_module.__dict__[name]
    # substring fallback
    found_key = None
    for key, value in _current_module.__dict__.items():
        if name in key and name == value.__name__:
            found_key = key
            break

    del _current_module.__dict__[found_key]

def get_custom_struct_via_name(name: str) -> Any | None:
    """Return the closest found custom struct for the given name

    Args:
        name (str): Name of the custom_struct

    Returns:
        Any | None: Associated class or None if nothing was found

    ..warning::
        It is not recommended to use this function because, in case of custom structs that
        share the same name, only the first found will be returned.
        Use instead `ua.get_custom_struct_via_nodeid`

    """
    # exact match
    if name in _current_module.__dict__:
        return _current_module.__dict__[name]
    # substring fallback
    for key, val in _current_module.__dict__.items():
        if name in key and name == val.__name__:
            return val
    return None

def get_custom_struct_with_matching_fields(name: str, fields: list[str]) -> Any | None:
    """Return the first found custom struct that matches the given name and list of fields

    Args:
        name (str): Name of the custom_struct
        fields (list[str]): List of expected fields the custom struct should have.

    Returns:
        Any | None: The finding custom struct. Else None.
    """
    found_classes = []
    for key, val in _current_module.__dict__.items():
        if name in key and name == val.__name__:
            found_classes.append(val)

    for clazz in found_classes:
        clazz_fields = [field.name for field in dataclasses.fields(clazz)]
        if set(clazz_fields) == set(fields):
            return clazz
    # If you reach here, no match was found. We now search for a dataclass that contains the fields
    for clazz in found_classes:
        clazz_fields = [field.name for field in dataclasses.fields(clazz)]
        if set(fields).issubset(set(clazz_fields)):
            return clazz
    return None

def get_custom_struct_via_nodeid(node_id: ObjectIds) -> Any | None:
    """Return the custom struct associated to the node id

    Args:
        node_id (ObjectIds): NodeId

    Returns:
        Any | None: Class if found
    """
    return get_extensionobject_class_type(node_id)
