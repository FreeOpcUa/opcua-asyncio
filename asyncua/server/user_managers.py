from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asyncua.crypto import uacrypto
from asyncua.crypto.permission_rules import User, UserRole

if TYPE_CHECKING:
    from .internal_server import InternalServer


class UserManager:
    def get_user(
        self,
        iserver: "InternalServer",
        username: str | None = None,
        password: str | None = None,
        certificate: Any = None,
    ) -> User | None:
        raise NotImplementedError


class PermissiveUserManager:
    def get_user(
        self,
        iserver: "InternalServer",
        username: str | None = None,
        password: str | None = None,
        certificate: Any = None,
    ) -> User | None:
        """
        Default user_manager, does nothing much but check for admin
        """
        if username and iserver.allow_remote_admin and username in ("admin", "Admin"):
            return User(role=UserRole.Admin)
        return User(role=UserRole.User)


class CertificateUserManager:
    """
    Certificate user manager, takes a certificate handler with its associated users and provides those users.
    """

    def __init__(self) -> None:
        self._trusted_certificates: dict[str, dict[str, Any]] = {}

    async def add_role(
        self,
        certificate_path: Path,
        user_role: UserRole,
        name: str,
        format: str | None = None,
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
        iserver: "InternalServer",
        username: str | None = None,
        password: str | None = None,
        certificate: Any = None,
    ) -> User | None:
        if certificate is None:
            return None
        correct_users = [
            prospective_certificate["user"]
            for prospective_certificate in self._trusted_certificates.values()
            if certificate == prospective_certificate["certificate"]
        ]
        if len(correct_users) == 0:
            return None
        return correct_users[0]

    async def add_user(self, certificate_path: Path, name: str, format: str | None = None) -> None:
        await self.add_role(certificate_path=certificate_path, user_role=UserRole.User, name=name, format=format)

    async def add_admin(self, certificate_path: Path, name: str, format: str | None = None) -> None:
        await self.add_role(certificate_path=certificate_path, user_role=UserRole.Admin, name=name, format=format)
