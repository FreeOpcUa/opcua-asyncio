"""
Implement user management here.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


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
