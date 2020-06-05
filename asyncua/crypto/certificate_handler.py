from asyncua.crypto import uacrypto
import sys
import logging
from asyncua.server.users import UserRole, User
sys.path.append('..')


class CertificateHandler:
    def __init__(self):
        self._trusted_certificates = {}

    async def trust_certificate(self, certificate_path: str, format: str = None, label: str = None, user_role=UserRole.User):
        certificate = await uacrypto.load_certificate(certificate_path, format)
        if label is None:
            label = certificate_path
        user = User(role=user_role, name=label)
        if label in self._trusted_certificates:
            logging.warning(f"certificate with label {label} "
                            f"attempted to be added multiple times, only the last version will be kept.")
        self._trusted_certificates[label] = {'certificate':uacrypto.der_from_x509(certificate), 'user':user}

    def __contains__(self, certificate):
        return any(certificate == prospective_cert['certificate']
                   for prospective_cert
                   in self._trusted_certificates.values())

    def get_user(self, certificate):
        correct_users = [prospective_certificate['user'] for prospective_certificate in self._trusted_certificates.values()
                         if certificate == prospective_certificate['certificate']]
        if len(correct_users) == 0:
            return None
        else:
            return correct_users[0]
