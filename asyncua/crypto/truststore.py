'''
Functionality for checking a certificate based on:
- trusted (ca) certificates
- crl

Use of cryptography module is prefered, but  doesn't provide functionality for truststores yet, so for some we rely on using pyOpenSSL.

'''
from typing import List
from pathlib import Path
import re
from datetime import datetime
import logging
from cryptography import x509
from OpenSSL import crypto
from asyncua.crypto.uacrypto import get_content, load_certificate

_logger = logging.getLogger("asyncuagds.validate")


class TrustStore:
    '''
    TrustStore is used to validate certificates in two ways:
    - Based on being absent in provided certificate revocation lists
    - The certificate or its issuer being  present in a list of trusted certificates

    It doesn't check other content of extensions of the certificate
    '''

    def __init__(self, trust_locations: List[Path], crl_locations: List[Path]):
        """Constructor of the TrustStore

        Args:
            trust_locations (list[Path]): one or multiple locations that contain trusted (ca) certificates. Type should be DER.
            crl_locations (list[Path]): one or multiple locations that contain CRL. TYpe should be DER.
        """

        self._trust_locations: List[Path] = trust_locations
        self._crl_locations: List[Path] = crl_locations

        self._trust_store: crypto.X509Store = crypto.X509Store()

        self._revoked_list: List[x509.RevokedCertificate] = []

    @property
    def trust_locations(self) -> List[Path]:
        return self._trust_locations

    @property
    def crl_locations(self) -> List[Path]:
        return self._crl_locations

    async def load(self):
        """(re)load both the trusted certificates and revoctions lists"""
        await self.load_trust()
        await self.load_crl()

    async def load_trust(self):
        """(re)load the trusted certificates"""
        self._trust_store: crypto.X509Store = crypto.X509Store()
        for location in self._trust_locations:
            await self._load_trust_location(location)

    async def load_crl(self):
        """(re)load the certificate revocation lists"""
        self._revoked_list.clear()
        for location in self._crl_locations:
            await self._load_crl_location(location)

    def validate(self, certificate: x509.Certificate) -> bool:
        """ Validates if a certificate is trusted, not revoked and lays in valid datarange

        Args:
            certificate (x509.Certificate): Certificate to check

        Returns:
            bool: Returns True when the certificate is valid
        """

        return self.is_trusted(certificate) and self.is_revoked(certificate) is False and self.check_date_range(certificate)

    def check_date_range(self, certificate: x509.Certificate) -> bool:
        """ Checks if the certificate not_valid_before and not_valid_after are valid.

        Args:
            certificate (x509.Certificate): Certificate to check

        Returns:
            bool: Returns True when the now lays in valid range of the certificate
        """
        valid: bool = True
        now = datetime.utcnow()
        if certificate.not_valid_after < now:
            _logger.error('certificate is no longer valid: valid until %s', certificate.not_valid_after)
            valid = False
        if certificate.not_valid_before > now:
            _logger.error('certificate is not yet vaild: valid after %s', certificate.not_valid_before)
            valid = False
        return valid

    def is_revoked(self, certificate: x509.Certificate) -> bool:
        """ Check if the provided certifcate is in the revocation lists

        when not CRLs are present it the certificate is considere not revoked.

        Args:
            certificate (x509.Certificate): Certificate to check

        Returns:
            bool: True when it is on a revocation list. If no list is present also return False.
        """
        is_revoked = False
        for revoked in self._revoked_list:
            if revoked.serial_number == certificate.serial_number:
                subject_cn = certificate.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
                _logger.warning('Found revoked serial "%s" [CN=%s]', hex(certificate.serial_number),  subject_cn)
                is_revoked = True
                break
        return is_revoked

    def is_trusted(self, certificate: x509.Certificate) -> bool:
        """ Check if the provided certifcate is considered trusted
        For a self-signed to be trusted is must be placed in the trusted location
        Args:
            certificate (x509.Certificate): Certificate to check

        Returns:
            bool: True when it is trusted or the trust store is empty.
        """
        # TODO: return True when trust store is empty
        _certificate: crypto.X509 = crypto.X509.from_cryptography(certificate)
        store_ctx = crypto.X509StoreContext(self._trust_store, _certificate)
        try:
            store_ctx.verify_certificate()
            _logger.debug('Use trusted certificate : \'%s\'', _certificate.get_subject().CN)
            return True
        except crypto.X509StoreContextError as exp:
            print(exp)
            _logger.warning('Not trusted certificate used: "%s"', _certificate.get_subject().CN)
        return False

    async def _load_trust_location(self, location: Path):
        """Load from a single directory location the certificates and add those to the truststore

        Args:
            location (Path): location to scan for certificates
        """
        files = Path(location).glob('*.*')
        for file_name in files:
            if re.match('.*(der|pem)', file_name.name.lower()):
                _logger.debug('Add certificate to TrustStore : \'%s\'', file_name)
                trusted_cert: crypto.X509 = crypto.X509.from_cryptography(await load_certificate(file_name))
                self._trust_store.add_cert(trusted_cert)

    async def _load_crl_location(self, location: Path):
        """Load from a single directory location the CRLs and add the revoked serials to the central CRL list.

        Args:
            location (Path): location to scan for crls
        """
        files = Path(location).glob('*.*')
        for file_name in files:
            if re.match('.*(der|pem)', file_name.name.lower()):
                _logger.debug('Add CRL to list : \'%s\'', file_name)
                crl = await self._load_crl(file_name)

                for revoked in crl:
                    self._revoked_list.append(revoked)

    @ staticmethod
    async def _load_crl(crl_file_name: Path) -> x509.CertificateRevocationList:
        """Load a single crl from file

        Args:
            crl_file_name (Path): file to load

        Returns:
            x509.CertificateRevocationList: Return loaded CRL
        """
        content = await get_content(crl_file_name)
        if crl_file_name.suffix.lower() == '.der':
            return x509.load_der_x509_crl(content)

        return x509.load_pem_x509_crl(content)
