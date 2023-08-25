from typing import Callable, Awaitable, Optional
import logging
from datetime import datetime
from enum import Flag, auto
from cryptography import x509
from cryptography.x509.oid import ExtendedKeyUsageOID
from asyncua import ua
from asyncua.common.utils import ServiceError
from asyncua.ua import ApplicationDescription
from asyncua.crypto.truststore import TrustStore

_logger = logging.getLogger(__name__)

# Use for storing method that can validate a certificate on a create_session
CertificateValidatorMethod = Callable[[x509.Certificate, ApplicationDescription], Awaitable[None]]

class CertificateValidatorOptions(Flag):
    """
    Flags for which certificate validation should be performed

    Three default sets of flags are provided:
    - BASIC_VALIDATION
    - EXT_VALIDATION
    - TRUSTED_VALIDATION
    """
    TIME_RANGE = auto()
    URI = auto()
    KEY_USAGE = auto()
    EXT_KEY_USAGE = auto()
    TRUSTED = auto()
    REVOKED = auto()

    PEER_CLIENT = auto()
    """Expect role of the peer is client (mutal exclusive with PEER_SERVER)"""
    PEER_SERVER = auto()
    """Expect role of the peer is server (mutal exclusive with PEER_CLIENT)"""

    BASIC_VALIDATION = TIME_RANGE | URI
    """Option set with: Only check time range and uri"""
    EXT_VALIDATION = TIME_RANGE | URI | KEY_USAGE | EXT_KEY_USAGE
    """Option set with: Check time, uri, key usage and extended key usage"""
    TRUSTED_VALIDATION = TIME_RANGE | URI | KEY_USAGE | EXT_KEY_USAGE | TRUSTED | REVOKED
    """Option set with: Check time, uri, key usage, extended key usage, is trusted (direct or by CA) and not revoked (CRL)"""


class CertificateValidator:
    """
    CertificateValidator contains a basic certificate validator including trusted store with revocation list support.
    The CertificateValidator can be used as a CertificateValidatorMethod.

    Default CertificateValidatorOptions.BASIC_VALIDATION is used.
    """

    def __init__(self, options: CertificateValidatorOptions = CertificateValidatorOptions.BASIC_VALIDATION | CertificateValidatorOptions.PEER_CLIENT, trust_store: Optional[TrustStore] = None):
        self._options = options
        self._trust_store: Optional[TrustStore] = trust_store

    def set_validate_options(self, options: CertificateValidatorOptions):
        """ Change the use validation options at runtime"""

        self._options = options

    async def validate(self, cert: x509.Certificate, app_description: ua.ApplicationDescription):
        """ Validate if a certificate is valid based on the validation options.
        When not valid is raises a ServiceError with an UA Result Code.

        Args:
            cert (x509.Certificate): certificate to check
            app_description (ua.ApplicationDescription): application descriptor of the client/server

        Raises:
            BadCertificateTimeInvalid: When current time is not in the time range of the certificate
            BadCertificateUriInvalid: Uri from certificate doesn't match application descriptor uri
            BadCertificateUseNotAllowed: KeyUsage or ExtendedKeyUsage fields mismatch
            BadCertificateInvalid: General when part of certifcate fields can't be found
            BadCertificateUntrusted: Not trusted by TrustStore
            ApplicationDescription: Certifacate in CRL of the TrustStore
        """

        if CertificateValidatorOptions.TIME_RANGE in self._options:
            now = datetime.utcnow()
            if cert.not_valid_after < now:
                raise ServiceError(ua.StatusCodes.BadCertificateTimeInvalid)
            elif cert.not_valid_before > now:
                raise ServiceError(ua.StatusCodes.BadCertificateTimeInvalid)
        try:
            san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            if CertificateValidatorOptions.URI in self._options:
                san_uri = san.value.get_values_for_type(x509.UniformResourceIdentifier)
                if app_description.ApplicationUri not in san_uri:
                    raise ServiceError(ua.StatusCodes.BadCertificateUriInvalid)
            if CertificateValidatorOptions.KEY_USAGE in self._options:

                key_usage = cert.extensions.get_extension_for_class(x509.KeyUsage).value
                if key_usage.data_encipherment is False or \
                key_usage.digital_signature is False or \
                key_usage.content_commitment is False or \
                key_usage.key_encipherment is False:
                    raise ServiceError(ua.StatusCodes.BadCertificateUseNotAllowed)
            if CertificateValidatorOptions.EXT_KEY_USAGE in self._options:
                oid = ExtendedKeyUsageOID.SERVER_AUTH if CertificateValidatorOptions.PEER_SERVER in self._options else ExtendedKeyUsageOID.CLIENT_AUTH

                if oid not in cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value:
                    raise ServiceError(ua.StatusCodes.BadCertificateUseNotAllowed)

                if CertificateValidatorOptions.PEER_SERVER in self._options and \
                    app_description.ApplicationType not in [ua.ApplicationType.Server, ua.ApplicationType.ClientAndServer]:
                    _logger.warning('mismatch between application type and certificate ExtendedKeyUsage')
                    raise ServiceError(ua.StatusCodes.BadCertificateUseNotAllowed)
                elif CertificateValidatorOptions.PEER_CLIENT in self._options and \
                    app_description.ApplicationType not in [ua.ApplicationType.Client, ua.ApplicationType.ClientAndServer]:
                    _logger.warning('mismatch between application type and certificate ExtendedKeyUsage')
                    raise ServiceError(ua.StatusCodes.BadCertificateUseNotAllowed)


            # if hostname is not None:
            #     san_dns_names = san.value.get_values_for_type(x509.DNSName)
            #     if hostname not in san_dns_names:
            #         raise ServiceError(ua.StatusCodes.BadCertificateHostNameInvalid) from exc
        except x509.ExtensionNotFound as exc:
            raise ServiceError(ua.StatusCodes.BadCertificateInvalid) from exc

        if CertificateValidatorOptions.TRUSTED in self._options or CertificateValidatorOptions.REVOKED in self._options:

            if CertificateValidatorOptions.TRUSTED in self._options:
                if self._trust_store and not self._trust_store.is_trusted(cert):
                    raise ServiceError(ua.StatusCodes.BadCertificateUntrusted)
            if CertificateValidatorOptions.REVOKED in self._options:
                if self._trust_store and self._trust_store.is_revoked(cert):
                    raise ServiceError(ua.StatusCodes.BadCertificateRevoked)

    async def __call__(self, cert: x509.Certificate, app_description: ua.ApplicationDescription):
        return await self.validate(cert, app_description)
