from asyncua.crypto import uacrypto
from uuid import uuid4
from cryptography.hazmat.primitives import serialization
import sys
from pprint import pprint as pp
sys.path.append('..')


class CertificateHandler:
    def __init__(self):
        self._trusted_certificates = {}

    async def trust_certificate(self, certificate_path: str, format: str = None):
        certificate = await uacrypto.load_certificate(certificate_path, format)

        self._trusted_certificates[certificate_path] = uacrypto.der_from_x509(certificate)

    def __contains__(self, certificate):
        return any(certificate == prospective_cert
                   for prospective_cert
                   in self._trusted_certificates.values())
