from asyncua.server.users import User, UserRole
from asyncua.crypto.certificate_handler import CertificateHandler


class UserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        raise NotImplementedError


class PermissiveUserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        """
        Default user_manager, does nothing much but check for admin
        """
        if username and iserver.allow_remote_admin and username in ("admin", "Admin"):
            return User(role=UserRole.Admin)
        else:
            return User(role=UserRole.User)


class CertificateUserManager:
    """
    Certificate user manager, takes a certificate handler with its associated users and provides those users.
    """
    def __init__(self, certificate_handler: CertificateHandler):
        self.certificate_handler = certificate_handler

    def get_user(self, iserver, username=None, password=None, certificate=None):
        if certificate is None:
            return None
        return self.certificate_handler.get_user(certificate)
