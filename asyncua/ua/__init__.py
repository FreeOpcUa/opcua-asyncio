# the order is important, some classes are overriden
from .attribute_ids import AttributeIds
from .object_ids import ObjectIds
from .object_ids import ObjectIdNames
from .status_codes import StatusCodes
from .uaprotocol_auto import *
from .uaprotocol_hand import *
from .uatypes import *  # TODO: This should be renamed to uatypes_hand
from .uaerrors import UaStatusCodeErrors

# Autogen registers types directly into `extension_objects_by_typeid` (encoding_id -> class)
# without going through `register_extension_object`. Mirror those into typeid_by_extension_objects
# so the encoder's class-keyed lookup covers spec types too.
from .uatypes import typeid_by_extension_objects as _typeid_by_extension_objects
from .uatypes import extension_objects_by_typeid as _extension_objects_by_typeid

for _enc_id, _cls in _extension_objects_by_typeid.items():
    _typeid_by_extension_objects.setdefault(_cls, _enc_id)
del _typeid_by_extension_objects, _extension_objects_by_typeid, _enc_id, _cls
