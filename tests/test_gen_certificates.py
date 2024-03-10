""" Several tests for certificate /signing request generation"""
from typing import List
from datetime import datetime, timedelta, UTC
import socket
from cryptography import x509
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.x509.extensions import _key_identifier_from_public_key as key_identifier_from_public_key
from asyncua.crypto.cert_gen import generate_private_key, generate_app_certificate_signing_request, generate_self_signed_app_certificate, sign_certificate_request


async def test_create_self_signed_app_certificate() -> None:
    """ Checks if the self signed certificate complies to OPC 10000-6 6.2.2"""

    hostname = socket.gethostname()

    names = {
        'countryName': 'NL',
        'stateOrProvinceName': 'ZH',
        'localityName': 'Foo',
        'organizationName': "Bar Ltd",
    }
    subject_alt_names: List[x509.GeneralName] = [x509.UniformResourceIdentifier(f"urn:{hostname}:foobar:myserver"),
                                                 x509.DNSName(f"{hostname}")]

    extended = [ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.SERVER_AUTH]

    days_valid = 100

    key: RSAPrivateKey = generate_private_key()
    dt_before_generation = datetime.now(UTC)
    dt_before_generation -= timedelta(microseconds=dt_before_generation.microsecond)
    cert: x509.Certificate = generate_self_signed_app_certificate(key,
                                                                  f"myserver@{hostname}",
                                                                  names,
                                                                  subject_alt_names,
                                                                  extended=extended,
                                                                  days=days_valid)
    dt_after_generation = datetime.now(UTC)
    dt_after_generation -= timedelta(microseconds=dt_after_generation.microsecond)

    # check if it is version 3
    assert cert.version.name == "v3"

    # check subject
    assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == f"myserver@{hostname}"
    assert cert.subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value == "NL"
    assert cert.subject.get_attributes_for_oid(NameOID.STATE_OR_PROVINCE_NAME)[0].value == "ZH"
    assert cert.subject.get_attributes_for_oid(NameOID.LOCALITY_NAME)[0].value == "Foo"
    assert cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value == "Bar Ltd"

    # check valid time range
    assert dt_before_generation <= cert.not_valid_before <= dt_after_generation
    assert (dt_before_generation + timedelta(days_valid)) <= cert.not_valid_after <= (dt_after_generation + timedelta(days_valid))

    # check issuer
    assert cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == f"myserver@{hostname}"

    # check Subject Key Indentifier
    assert cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest == key_identifier_from_public_key(key.public_key())

    # check Authority Key Identifier
    auth_key_identifier: x509.AuthorityKeyIdentifier = cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value
    assert auth_key_identifier
    assert isinstance(auth_key_identifier.authority_cert_issuer, list)
    assert len(auth_key_identifier.authority_cert_issuer) > 0
    issuer: x509.Name = auth_key_identifier.authority_cert_issuer[0].value
    assert issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == f"myserver@{hostname}"
    assert auth_key_identifier.authority_cert_serial_number == cert.serial_number
    assert auth_key_identifier.key_identifier == key_identifier_from_public_key(key.public_key())

    # check subject alternative name
    assert cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)[0] == hostname
    assert cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(
        x509.UniformResourceIdentifier)[0] == f"urn:{hostname}:foobar:myserver"

    assert cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca is True

    assert cert.extensions.get_extension_for_class(x509.KeyUsage).value == x509.KeyUsage(
        digital_signature=True,
        content_commitment=True,
        key_encipherment=True,
        data_encipherment=True,
        key_agreement=False,
        key_cert_sign=True,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False)

    assert cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value == x509.ExtendedKeyUsage(extended)


async def test_app_create_certificate_signing_request() -> None:
    """ Checks if the self signed certificate complies to OPC 10000-6 6.2.2"""

    hostname = socket.gethostname()

    names = {
        'countryName': 'NL',
        'stateOrProvinceName': 'ZH',
        'localityName': 'Foo',
        'organizationName': "Bar Ltd",
    }
    subject_alt_names: List[x509.GeneralName] = [x509.UniformResourceIdentifier(f"urn:{hostname}:foobar:myserver"),
                                                 x509.DNSName(f"{hostname}")]

    extended = [ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.SERVER_AUTH]

    key: RSAPrivateKey = generate_private_key()
    csr: x509.CertificateSigningRequest = generate_app_certificate_signing_request(key,
                                                                                   f"myserver@{hostname}",
                                                                                   names,
                                                                                   subject_alt_names,
                                                                                   extended=extended)

    # check subject
    assert csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == f"myserver@{hostname}"
    assert csr.subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value == "NL"
    assert csr.subject.get_attributes_for_oid(NameOID.STATE_OR_PROVINCE_NAME)[0].value == "ZH"
    assert csr.subject.get_attributes_for_oid(NameOID.LOCALITY_NAME)[0].value == "Foo"
    assert csr.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value == "Bar Ltd"

    # check subject alternative name
    assert csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)[0] == hostname
    assert csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(
        x509.UniformResourceIdentifier)[0] == f"urn:{hostname}:foobar:myserver"

    assert csr.extensions.get_extension_for_class(x509.KeyUsage).value == x509.KeyUsage(
        digital_signature=True,
        content_commitment=True,
        key_encipherment=True,
        data_encipherment=True,
        key_agreement=False,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False)

    assert csr.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value == x509.ExtendedKeyUsage(extended)


async def test_app_sign_certificate_request() -> None:
    """Check the correct signing of certificate signing request"""
    hostname = socket.gethostname()

    names = {
        'countryName': 'NL',
        'stateOrProvinceName': 'ZH',
        'localityName': 'Foo',
        'organizationName': "Bar Ltd",
    }
    subject_alt_names: List[x509.GeneralName] = [x509.UniformResourceIdentifier(f"urn:{hostname}:foobar:myserver"),
                                                 x509.DNSName(f"{hostname}")]

    extended = [ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.SERVER_AUTH]

    key_ca: RSAPrivateKey = generate_private_key()
    issuer: x509.Certificate = generate_self_signed_app_certificate(key_ca,
                                                                    "Application CA",
                                                                    names,
                                                                    subject_alt_names,
                                                                    extended=[],  # keep this one empty when generating an application CA
                                                                    days=365)

    key_server: RSAPrivateKey = generate_private_key()
    csr: x509.CertificateSigningRequest = generate_app_certificate_signing_request(key_server,
                                                                                   f"myserver@{hostname}",
                                                                                   names,
                                                                                   subject_alt_names,
                                                                                   extended=extended)

    cert: x509.Certificate = sign_certificate_request(csr, issuer, key_ca, days=30)

    assert cert.subject == csr.subject

    # check subject key identifier
    assert cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest == key_identifier_from_public_key(key_server.public_key())

    # check authority Key Identifier
    auth_key_identifier: x509.AuthorityKeyIdentifier = cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value
    assert auth_key_identifier
    assert isinstance(auth_key_identifier.authority_cert_issuer, list)
    assert len(auth_key_identifier.authority_cert_issuer) > 0
    assert auth_key_identifier.authority_cert_issuer[0].value == issuer.subject
    assert auth_key_identifier.authority_cert_serial_number == issuer.serial_number
    assert auth_key_identifier.key_identifier == key_identifier_from_public_key(key_ca.public_key())

    assert cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca is False

    assert cert.extensions.get_extension_for_class(
        x509.SubjectAlternativeName).value == csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value

    assert cert.extensions.get_extension_for_class(
        x509.KeyUsage).value == csr.extensions.get_extension_for_class(x509.KeyUsage).value

    assert cert.extensions.get_extension_for_class(
        x509.ExtendedKeyUsage).value == csr.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
