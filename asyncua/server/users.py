"""
Implement user managent here
"""

from enum import Enum
__all__ = ["User"]


class User(Enum):
    """
    Define some default users.
    """
    Admin = 0
    Anonymous = 1
    User = 3
