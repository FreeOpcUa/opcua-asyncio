"""
    crypothelper contains helper functions to isolate the lower level cryto stuff from the GDS client.
"""
from typing import Dict
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat._oid import _OID_NAMES as OID_NAMES
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.extensions import _key_identifier_from_public_key as key_identifier_from_public_key

ONE_DAY = datetime.timedelta(1, 0, 0)
""" Shorthand for delta of 1 day """

OID_NAME_MAP: Dict[str, x509.ObjectIdentifier] = {name: oid for oid, name in OID_NAMES.items()}
""" Create lookup table for x509.ObjectIdentifier based on textual name, by swapping key<>value of the available mapping"""


def _names_to_nameattributes(names: Dict[str, str]) -> list[x509.NameAttribute]:
    """Convert a dict with key/value of an x509.NameAttribute list

    Args:
        names (dict[str,str]): key is the textual name of a NameOID, value is the of the attribute

    Returns:
        list[x509.NameAttribute]: Coverted list with NameAttributes
    """
    return [x509.NameAttribute(OID_NAME_MAP[key], value) for key, value in names.items()]


def generate_private_key() -> rsa.RSAPrivateKey:
    """Generate a private key for certifacte signing and requesting

    Returns:
        rsa.RSAPrivateKey: The generated private key
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())
    return private_key


def dump_private_key_as_pem(private_key: rsa.RSAPrivateKey) -> bytes:
    """dumps a private key in PEM format

    Args:
        private_key (rsa.RSAPrivateKey): The privatekey to dump

    Returns:
        bytes: The private as PEM/PKCS8 format
    """
    return private_key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.PKCS8, encryption_algorithm=NoEncryption())


def generate_self_signed_app_certificate(private_key: rsa.RSAPrivateKey,
                                         common_name: str,
                                         names: Dict[str, str],
                                         subject_alt_names: list[x509.GeneralName],
                                         extended: list[x509.ObjectIdentifier],
                                         days: int = 365) -> x509.Certificate:
    """Generate a self signed certificate for OPC UA client/server application that is according to OPC 10000-4 6.1 / OPC 10000-6 6.2.2

    Args:
        private_key (rsa.RSAPrivateKey): private key used to sign the certificate
        common_name (str): common name (CN) for the subject, matches to the applications name
        names (dict[str,str]): additional fields (like O,C,L) for the subject
        subject_alt_names (list[x509.GeneralName]): uri,dns ip entires
        extended (list[x509.ObjectIdentifier]): Indicates use of certificate (ExtendedKeyUsageOID.CLIENT_AUTH and/or ExtendedKeyUsageOID.SERVER_AUTH).
                                                When empty assumes to generate a CA
        days (int, optional): How long the certificate is valid. Defaults to 365.

    Returns:
        x509.Certificate: The generated certificate.
    """
    generate_ca = len(extended) == 0
    name_attributes: list[x509.NameAttribute] = _names_to_nameattributes(names)
    name_attributes.insert(0, x509.NameAttribute(NameOID.COMMON_NAME, common_name))

    public_key = private_key.public_key()
    serial_number: int = x509.random_serial_number()

    builder = x509.CertificateBuilder()
    builder = builder.subject_name(x509.Name(name_attributes))
    builder = builder.issuer_name(x509.Name(name_attributes))
    builder = builder.not_valid_before(datetime.datetime.utcnow())
    builder = builder.not_valid_after(datetime.datetime.utcnow() + (ONE_DAY * days))
    builder = builder.serial_number(serial_number)
    builder = builder.public_key(public_key)
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
        critical=False
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier(key_identifier_from_public_key(private_key.public_key()),
                                    [x509.DirectoryName(x509.Name(name_attributes))],
                                    serial_number),
        critical=False
    )
    builder = builder.add_extension(
        x509.SubjectAlternativeName(subject_alt_names),
        critical=False
    )
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=0),
        critical=False
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=True,
            key_encipherment=True,
            data_encipherment=not (generate_ca),
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=generate_ca,
            encipher_only=False,
            decipher_only=False),
        critical=False
    )
    if not generate_ca:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage(extended),
            critical=False
        )

    certificate = builder.sign(
        private_key=private_key, algorithm=hashes.SHA256(),
    )

    return certificate


def generate_app_certificate_signing_request(private_key: rsa.RSAPrivateKey,
                                             common_name: str,
                                             names: Dict[str, str],
                                             subject_alt_names: list[x509.GeneralName],
                                             extended: list[x509.ObjectIdentifier]
                                             ) -> x509.CertificateSigningRequest:
    """Generate a certificate signing request for a OPC UA client/server application that is according to OPC 10000-4 6.1 / OPC 10000-6 6.2.2

    Args:
        private_key (rsa.RSAPrivateKey): private key used to sign the certificate
        common_name (str): common name (CN) for the subject, matches to the applications name
        names (dict[str,str]): additional fields (like O,C,L) for the subject
        subject_alt_names (list[x509.GeneralName]): uri,dns ip entires
        extended (list[x509.ObjectIdentifier]): Indicates use of certificate (ExtendedKeyUsageOID.CLIENT_AUTH and/or ExtendedKeyUsageOID.SERVER_AUTH)

    Returns:
        x509.CertificateSigningRequest: The generated certificate signing request
    """

    name_attributes: list[x509.NameAttribute] = _names_to_nameattributes(names)
    name_attributes.insert(0, x509.NameAttribute(NameOID.COMMON_NAME, common_name))

    builder = x509.CertificateSigningRequestBuilder()
    builder = builder.subject_name(x509.Name(name_attributes))
    builder = builder.add_extension(
        x509.SubjectAlternativeName(subject_alt_names),
        critical=False
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=True,
            key_encipherment=True,
            data_encipherment=True,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False),
        critical=False
    )

    builder = builder.add_extension(
        x509.ExtendedKeyUsage(extended),
        critical=False
    )
    csr = builder.sign(
        private_key=private_key, algorithm=hashes.SHA256(),
    )

    return csr


def sign_certificate_request(csr: x509.CertificateSigningRequest,
                             issuer: x509.Certificate,
                             private_key: rsa.RSAPrivateKey, days=365) -> x509.Certificate:
    """Create certficate based on certificate signing request and ca

    Args:
        csr (x509.CertificateSigningRequest): certificate signing request
        issuer (x509.Certificate): certificate used a CA
        private_key (rsa.RSAPrivateKey): private key of the issuer
        days (int, optional): Days valid. Defaults to 365.

    Returns:
        x509.Certificate: Signed certificate
    """
    public_key = csr.public_key()
    serial_number: int = x509.random_serial_number()

    builder = x509.CertificateBuilder()
    builder = builder.subject_name(csr.subject)
    builder = builder.issuer_name(issuer.subject)
    builder = builder.not_valid_before(datetime.datetime.utcnow())
    builder = builder.not_valid_after(datetime.datetime.utcnow() + (ONE_DAY * days))
    builder = builder.serial_number(serial_number)
    builder = builder.public_key(public_key)
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
        critical=False
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier(key_identifier_from_public_key(issuer.public_key()),
                                    [x509.DirectoryName(issuer.subject)],
                                    issuer.serial_number),
        critical=False
    )
    builder = builder.add_extension(
        csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value,
        critical=False
    )
    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=False
    )
    builder = builder.add_extension(
        csr.extensions.get_extension_for_class(x509.KeyUsage).value,
        critical=False
    )
    builder = builder.add_extension(
        csr.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value,
        critical=False
    )

    certificate: x509.Certificate = builder.sign(
        private_key=private_key, algorithm=hashes.SHA256(),
    )

    return certificate
