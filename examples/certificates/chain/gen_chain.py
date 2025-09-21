"""
Generates the certificate chain looking like:
root
|
| - server
|
| - inter1
    |
    | - inter 2
        |
        | - client

"""

from datetime import UTC, datetime, timedelta
from pathlib import Path


from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

OUT_DIR = Path(".")

ROOT_CA_DAYS = 365 * 10
INTERMEDIATE_CA_DAYS = 365 * 10
LEAF_CERT_DAYS = 365 * 10
VALIDITY_OFFSET = timedelta(days=1)

ORG_NAME = "OPC UA"
COUNTRY = "CZ"
STATE = "Some State"
CITY = "Some City"
ORG_UNIT = "Lib"

COMMON_NAME_ROOT = "Python OPC UA Root"
COMMON_NAME_INTERMEDIATE1 = "Python OPC UA Inter 1"
COMMON_NAME_INTERMEDIATE2 = "Python OPC UA Inter 2"


def save_key_pem(key: rsa.RSAPrivateKey, file: Path) -> None:
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    file.with_suffix(".key.pem").write_bytes(pem)


def save_cert_pem(cert: x509.Certificate, file: Path) -> None:
    file.with_suffix(".cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def save_cert_der(cert: x509.Certificate, file: Path) -> None:
    file.with_suffix(".cert.der").write_bytes(cert.public_bytes(serialization.Encoding.DER))


def generate_private_rsa_key() -> rsa.RSAPrivateKey:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    return private_key


def create_subject_name(common_name) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE),
            x509.NameAttribute(NameOID.LOCALITY_NAME, CITY),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORG_NAME),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ORG_UNIT),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )


def generate_root_certificate() -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    private_key = generate_private_rsa_key()

    public_key = private_key.public_key()
    builder = x509.CertificateBuilder()

    subject_name = create_subject_name(COMMON_NAME_ROOT)
    builder = builder.subject_name(subject_name)
    builder = builder.issuer_name(subject_name)

    builder = builder.not_valid_before(datetime.now(UTC) - VALIDITY_OFFSET)
    builder = builder.not_valid_after(datetime.now(UTC) - VALIDITY_OFFSET + timedelta(days=ROOT_CA_DAYS))

    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)

    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(public_key),
        critical=False,
    )
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )

    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
    )

    return certificate, private_key


def generate_inter_certificate(
    issuer_cert: x509.Certificate,
    issuer_cert_private_key: rsa.RSAPrivateKey,
    common_name: str,
) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    private_key = generate_private_rsa_key()

    public_key = private_key.public_key()
    builder = x509.CertificateBuilder()

    builder = builder.subject_name(create_subject_name(common_name))

    builder = builder.issuer_name(issuer_cert.subject)

    builder = builder.not_valid_before(datetime.now(UTC) - VALIDITY_OFFSET)
    builder = builder.not_valid_after(datetime.now(UTC) - VALIDITY_OFFSET + timedelta(days=INTERMEDIATE_CA_DAYS))

    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)

    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )
    ski_ext = issuer_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski_ext.value),
        critical=False,
    )
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_cert_sign=True,
            crl_sign=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )

    certificate = builder.sign(
        private_key=issuer_cert_private_key,
        algorithm=hashes.SHA256(),
    )

    return certificate, private_key


def generate_leaf_certificate(
    issuer_cert: x509.Certificate,
    issuer_cert_private_key: rsa.RSAPrivateKey,
    common_name: str,
    uris: list[str] | None = None,
) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    private_key = generate_private_rsa_key()

    public_key = private_key.public_key()
    builder = x509.CertificateBuilder()

    builder = builder.subject_name(create_subject_name(common_name))
    builder = builder.issuer_name(issuer_cert.subject)

    builder = builder.not_valid_before(datetime.now(UTC) - VALIDITY_OFFSET)
    builder = builder.not_valid_after(datetime.now(UTC) - VALIDITY_OFFSET + timedelta(days=LEAF_CERT_DAYS))

    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)

    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )
    ski_ext = issuer_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski_ext.value),
        critical=False,
    )

    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )

    sans: list[x509.GeneralName] = [x509.UniformResourceIdentifier(uri) for uri in uris] if uris else []
    if sans:
        builder = builder.add_extension(x509.SubjectAlternativeName(sans), critical=False)

    certificate = builder.sign(
        private_key=issuer_cert_private_key,
        algorithm=hashes.SHA256(),
    )

    return certificate, private_key


def main():
    root, root_key = generate_root_certificate()
    server, server_key = generate_leaf_certificate(
        root, root_key, "python-opcua-server.example.com", ["urn:example.org:FreeOpcUa:python-opcua-server"]
    )
    inter1, inter1_key = generate_inter_certificate(root, root_key, COMMON_NAME_INTERMEDIATE1)
    inter2, inter2_key = generate_inter_certificate(inter1, inter1_key, COMMON_NAME_INTERMEDIATE2)
    client, client_key = generate_leaf_certificate(
        inter2, inter2_key, "python-opcua-client.example.com", ["urn:example.org:FreeOpcUa:python-opcua-client"]
    )

    save_cert_pem(root, OUT_DIR / "root")
    save_cert_der(root, OUT_DIR / "root")
    save_key_pem(root_key, OUT_DIR / "root")

    save_cert_pem(server, OUT_DIR / "server")
    save_key_pem(server_key, OUT_DIR / "server")

    save_cert_pem(inter1, OUT_DIR / "inter1")
    save_key_pem(inter1_key, OUT_DIR / "inter1")
    save_cert_pem(inter2, OUT_DIR / "inter2")
    save_key_pem(inter2_key, OUT_DIR / "inter2")

    save_cert_pem(client, OUT_DIR / "client")
    save_key_pem(client_key, OUT_DIR / "client")


if __name__ == "__main__":
    main()
