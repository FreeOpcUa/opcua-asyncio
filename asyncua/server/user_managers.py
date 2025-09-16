import logging
from pathlib import Path
from typing import Optional
from cryptography.x509 import Certificate

from asyncua.crypto import uacrypto
from asyncua.crypto.permission_rules import User, UserRole
from asyncua.server.base import AbstractUserManager, AbstractInternalServer


class PermissiveUserManager(AbstractUserManager):
    def get_user(
        self,
        iserver: AbstractInternalServer,
        username: Optional[str] = None,
        password: Optional[str] = None,
        certificate: Optional[Certificate] = None,
    ) -> User:
        """
        Default user_manager, does nothing much but check for admin
        """
        if username and iserver.allow_remote_admin and username in ("admin", "Admin"):
            return User(role=UserRole.Admin)
        else:
            return User(role=UserRole.User)


class CertificateUserManager(AbstractUserManager):
    """
    Certificate user manager, takes a certificate handler with its associated users and provides those users.
    """

    def __init__(self) -> None:
        self._trusted_certificates: dict[str, dict] = {}

    async def add_role(
        self,
        certificate_path: Path,
        user_role: UserRole,
        name: str,
        format: Optional[str] = None,
    ) -> None:
        certificate = await uacrypto.load_certificate(certificate_path, format)
        if name is None:
            raise KeyError

        user = User(role=user_role, name=name)

        if name in self._trusted_certificates:
            logging.warning(
                "certificate with name %s attempted to be added multiple times, only the last version will be kept.",
                name,
            )
        self._trusted_certificates[name] = {"certificate": uacrypto.der_from_x509(certificate), "user": user}

    def get_user(
        self,
        iserver: AbstractInternalServer,
        username: Optional[str] = None,
        password: Optional[str] = None,
        certificate: Optional[Certificate] = None,
    ) -> Optional[User]:
        if certificate is None:
            return None
        correct_users: list[User] = [
            prospective_certificate["user"]
            for prospective_certificate in self._trusted_certificates.values()
            if certificate == prospective_certificate["certificate"]
        ]
        if len(correct_users) == 0:
            return None
        else:
            return correct_users[0]

    async def add_user(self, certificate_path: Path, name: str, format: Optional[str] = None):
        await self.add_role(certificate_path=certificate_path, user_role=UserRole.User, name=name, format=format)

    async def add_admin(self, certificate_path: Path, name: str, format: Optional[str] = None):
        await self.add_role(certificate_path=certificate_path, user_role=UserRole.Admin, name=name, format=format)
