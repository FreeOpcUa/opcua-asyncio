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
    def __init__(self, role=UserRole.Anonymous):
        self.role = role
