from asyncua.crypto import uacrypto
import sys
import logging
sys.path.append('..')


class CertificateHandler:
    def __init__(self):
        self._trusted_certificates = {}

    async def trust_certificate(self, certificate_path: str, format: str = None, label: str = None):
        certificate = await uacrypto.load_certificate(certificate_path, format)
        if label is None:
            label = certificate_path
        if label in self._trusted_certificates:
            logging.warning(f"certificate with label {label} "
                            f"attempted to be added multiple times, only the last version will be kept.")
        self._trusted_certificates[label] = uacrypto.der_from_x509(certificate)

    def __contains__(self, certificate):
        return any(certificate == prospective_cert
                   for prospective_cert
                   in self._trusted_certificates.values())
