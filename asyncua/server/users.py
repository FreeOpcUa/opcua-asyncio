"""
Implement user management here.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


'''

TODO for Roles and Permissions:

https://reference.opcfoundation.org/v104/Core/docs/Part3/4.8.2/

Anonymous 	The Role has very limited access for use when a Session has anonymous credentials.
AuthenticatedUser 	The Role has limited access for use when a Session has valid non-anonymous credentials but has not been explicitly granted access to a Role.
Observer 	The Role is allowed to browse, read live data, read historical data/events or subscribe to data/events.
Operator 	The Role is allowed to browse, read live data, read historical data/events or subscribe to data/events.
In addition, the Session is allowed to write some live data and call some Methods.
Engineer 	The Role is allowed to browse, read/write configuration data, read historical data/events, call Methods or subscribe to data/events.
Supervisor 	The Role is allowed to browse, read live data, read historical data/events, call Methods or subscribe to data/events.
ConfigureAdmin 	The Role is allowed to change the non-security related configuration settings.
SecurityAdmin 	The Role is allowed to change security related settings.

https://github.com/FreeOpcUa/opcua-asyncio/blob/master/asyncua/ua/uaprotocol_auto.py#L862

A user needs:
-a "Role" e.g. Operator
-a list of "Permissions" e.g. [ua.PermissionType.Write]

Step1 would be to cleanup the UserRoles to the "Well-Known Roles" with the Spec. default PermissionType's
Step2(future development) could be to implementing
-the Evaluating (https://reference.opcfoundation.org/v104/Core/docs/Part3/4.8.3/) 
-RolePermissions (https://reference.opcfoundation.org/v104/Core/docs/Part3/5.2.9/)

'''


class UserRole(Enum):
    """
    User Roles
    """
    Admin = 0
    Anonymous = 1
    User = 3


@dataclass
class User:
    role: UserRole = UserRole.Anonymous
    name: Optional[str] = None
