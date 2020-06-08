"""
Implement user management here.
"""

from enum import Enum


class UserRole(Enum):
    """
    User Roles
    """
    Admin = 0
    Anonymous = 1
    User = 3


class User:
    def __init__(self, role=UserRole.Anonymous, name=None):
        self.role = role
        self.name = name

    def check_privileges(self, typeid):
        return True
