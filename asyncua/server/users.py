"""
Implement user management here.
"""

from enum import Enum


class User(Enum):
    """
    Define some default users.
    """
    Admin = 0
    Anonymous = 1
    User = 3
