""" test certificate truststore"""
import datetime
import shutil
from pathlib import Path
import socket
import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from asyncua.crypto.uacrypto import load_certificate
from asyncua.crypto.truststore import TrustStore
from asyncua.crypto.cert_gen import generate_private_key, generate_self_signed_app_certificate, dump_private_key_as_pem, \
    generate_app_certificate_signing_request, sign_certificate_request

# pylint: disable=redefined-outer-name,missing-function-docstring, missing-module-docstring, missing-class-docstring

CA_CERT_FILE = 'ca_cert.der'
SERVER_CERT_FILE = 'myserver_cert.der'
SERVER_CERT_SELF_SIGNED_FILE = 'myserver_cert_selfsigned.der'


@pytest.fixture(scope="session")
def cert_files(tmp_path_factory) -> Path:
    ''' session based fixure to generate certifcates to test'''
    tmp_path_factory.mktemp("data")

    store_base: Path = tmp_path_factory.mktemp("pkistore")
    trusted_cert: Path = store_base / 'trusted' / 'certs'
    trusted_crl: Path = store_base / 'trusted' / 'crl'

    own_certs: Path = store_base / 'own' / 'certs'
    own_private: Path = store_base / 'own' / 'private'

    trusted_cert.mkdir(parents=True, exist_ok=True)
    trusted_crl.mkdir(parents=True, exist_ok=True)
    own_certs.mkdir(parents=True, exist_ok=True)
    own_private.mkdir(parents=True, exist_ok=True)

    hostname: str = socket.gethostname()

    names = {
        'countryName': 'NL',
        'stateOrProvinceName': 'ZH',
        'localityName': 'Foo',
        'organizationName': "Bar Ltd",
    }
    subject_alt_names: list[x509.GeneralName] = [x509.UniformResourceIdentifier(f"urn:{hostname}:foobar:myserver"),
                                                 x509.DNSName(f"{hostname}")]

    extended = [ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.SERVER_AUTH]

    # gen CA
    key_ca: RSAPrivateKey = generate_private_key()
    issuer: x509.Certificate = generate_self_signed_app_certificate(key_ca,
                                                                    "Application CA",
                                                                    names,
                                                                    subject_alt_names,
                                                                    extended=[],  # keep this one empty when generating an application CA
                                                                    days=365)

    # gen server private key
    server_key: RSAPrivateKey = generate_private_key()

    # gen server self signed cert
    cert_self_signed: x509.Certificate = generate_self_signed_app_certificate(server_key,
                                                                              f"myserver@{hostname}",
                                                                              names,
                                                                              subject_alt_names,
                                                                              extended=[],  # keep this one empty when generating an application CA
                                                                              days=365)

    # gen server CSR
    csr: x509.CertificateSigningRequest = generate_app_certificate_signing_request(server_key,
                                                                                   f"myserver@{hostname}",
                                                                                   names,
                                                                                   subject_alt_names,
                                                                                   extended=extended)

    # sign CSR
    cert: x509.Certificate = sign_certificate_request(csr, issuer, key_ca, days=30)

    (own_private / 'ca_key.pem').write_bytes(dump_private_key_as_pem(key_ca))
    (own_certs / CA_CERT_FILE).write_bytes(issuer.public_bytes(encoding=Encoding.DER))

    (own_private / 'myserver_key.pem').write_bytes(dump_private_key_as_pem(server_key))
    (own_certs / SERVER_CERT_FILE).write_bytes(cert.public_bytes(encoding=Encoding.DER))
    (own_certs / SERVER_CERT_SELF_SIGNED_FILE).write_bytes(cert_self_signed.public_bytes(encoding=Encoding.DER))

    one_day = datetime.timedelta(1, 0, 0)

    builder = x509.CertificateRevocationListBuilder()
    builder = builder.issuer_name(x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'Application CA'),
    ]))
    builder = builder.last_update(datetime.datetime.today())
    builder = builder.next_update(datetime.datetime.today() + one_day)

    crl_empty = builder.sign(
        private_key=key_ca, algorithm=hashes.SHA256(),
    )

    (own_certs / 'ca_empty_crl.der').write_bytes(crl_empty.public_bytes(encoding=Encoding.DER))

    revoked_cert = x509.RevokedCertificateBuilder().serial_number(
        cert.serial_number
    ).revocation_date(
        datetime.datetime.today()
    ).build()
    builder = builder.add_revoked_certificate(revoked_cert)
    crl = builder.sign(
        private_key=key_ca, algorithm=hashes.SHA256(),
    )
    (own_certs / 'ca_crl.der').write_bytes(crl.public_bytes(encoding=Encoding.DER))

    return own_certs


@ pytest.fixture
def trust_store(tmp_path) -> TrustStore:
    """ fixture to generate clean trust store per test"""
    base_trust_store: Path = tmp_path / 'truststore'
    trusted_certs: Path = base_trust_store / 'certs'
    trusted_crls: Path = base_trust_store / 'crl'

    trusted_certs.mkdir(parents=True, exist_ok=True)
    trusted_crls.mkdir(parents=True, exist_ok=True)

    _trust_store = TrustStore([trusted_certs], [trusted_crls])
    return _trust_store


async def test_selfsigned_not_in_trust_store(cert_files, trust_store) -> None:
    cert_self_signed: x509.Certificate = await load_certificate(cert_files / SERVER_CERT_SELF_SIGNED_FILE)
    assert trust_store.is_trusted(cert_self_signed) is False


async def test_selfsigned_in_trust_store(cert_files, trust_store) -> None:
    shutil.copyfile(cert_files / SERVER_CERT_SELF_SIGNED_FILE, trust_store.trust_locations[0] / SERVER_CERT_SELF_SIGNED_FILE)
    await trust_store.load()

    cert_self_signed: x509.Certificate = await load_certificate(cert_files / SERVER_CERT_SELF_SIGNED_FILE)
    assert trust_store.is_trusted(cert_self_signed) is True


async def test_ca_not_in_trust_store(cert_files, trust_store) -> None:
    cert_self_signed: x509.Certificate = await load_certificate(cert_files / SERVER_CERT_SELF_SIGNED_FILE)
    assert trust_store.is_trusted(cert_self_signed) is False


async def test_ca_in_trust_store(cert_files, trust_store) -> None:
    shutil.copyfile(cert_files / CA_CERT_FILE, trust_store.trust_locations[0] / CA_CERT_FILE)
    await trust_store.load()

    cert_server: x509.Certificate = await load_certificate(cert_files / SERVER_CERT_FILE)
    assert trust_store.is_trusted(cert_server) is True


async def test_empty_crl(cert_files, trust_store) -> None:
    shutil.copyfile(cert_files / CA_CERT_FILE, trust_store.trust_locations[0] / CA_CERT_FILE)
    shutil.copyfile(cert_files / 'ca_empty_crl.der', trust_store.crl_locations[0] / 'ca_empty_crl.der')
    await trust_store.load()

    cert_server: x509.Certificate = await load_certificate(cert_files / SERVER_CERT_FILE)

    assert trust_store.is_trusted(cert_server) is True
    assert trust_store.is_revoked(cert_server) is False
    assert trust_store.check_date_range(cert_server) is True

    assert trust_store.validate(cert_server) is True


async def test_cert_in_crl(cert_files, trust_store) -> None:
    shutil.copyfile(cert_files / CA_CERT_FILE, trust_store.trust_locations[0] / CA_CERT_FILE)
    shutil.copyfile(cert_files / 'ca_crl.der', trust_store.crl_locations[0] / 'ca_crl.der')
    await trust_store.load()

    cert_server: x509.Certificate = await load_certificate(cert_files / SERVER_CERT_FILE)

    assert trust_store.is_trusted(cert_server) is True
    assert trust_store.is_revoked(cert_server) is True
    assert trust_store.check_date_range(cert_server) is True

    assert trust_store.validate(cert_server) is False
