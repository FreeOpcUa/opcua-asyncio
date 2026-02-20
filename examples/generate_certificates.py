"""Example of several certficate creation helpers"""

import asyncio
import socket
from pathlib import Path

import anyio
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import Encoding  # , load_pem_private_key
from cryptography.x509.oid import ExtendedKeyUsageOID

from asyncua.crypto.cert_gen import (
    dump_private_key_as_pem,
    generate_app_certificate_signing_request,
    generate_private_key,
    generate_self_signed_app_certificate,
    sign_certificate_request,
)
from asyncua.crypto.uacrypto import load_certificate, load_private_key

HOSTNAME: str = socket.gethostname()

# used for subject common part
NAMES: dict[str, str] = {
    "countryName": "NL",
    "stateOrProvinceName": "ZH",
    "localityName": "Foo",
    "organizationName": "Bar Ltd",
}

CLIENT_SERVER_USE = [ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH]

# setup the paths for the certs, keys and csr
base = Path("certs-example")
base_csr: Path = base / "csr"
base_private: Path = base / "private"
base_certs: Path = base / "certs"
base_csr.mkdir(parents=True, exist_ok=True)
base_private.mkdir(parents=True, exist_ok=True)
base_certs.mkdir(parents=True, exist_ok=True)


def generate_private_key_for_myserver():
    key: RSAPrivateKey = generate_private_key()
    key_file = base_private / "myserver.pem"
    key_file.write_bytes(dump_private_key_as_pem(key))


async def generate_self_signed_certificate():
    subject_alt_names: list[x509.GeneralName] = [
        x509.UniformResourceIdentifier(f"urn:{HOSTNAME}:foobar:myselfsignedserver"),
        x509.DNSName(f"{HOSTNAME}"),
    ]

    # key: RSAPrivateKey = generate_private_key()
    key = await load_private_key(base_private / "myserver.pem")

    cert: x509.Certificate = generate_self_signed_app_certificate(
        key, f"myselfsignedserver@{HOSTNAME}", NAMES, subject_alt_names, extended=CLIENT_SERVER_USE
    )

    cert_file = base_certs / "myserver-selfsigned.der"
    cert_file.write_bytes(cert.public_bytes(encoding=Encoding.DER))


def generate_applicationgroup_ca():
    subject_alt_names: list[x509.GeneralName] = [
        x509.UniformResourceIdentifier(f"urn:{HOSTNAME}:foobar:myserver"),
        x509.DNSName(f"{HOSTNAME}"),
    ]

    key: RSAPrivateKey = generate_private_key()
    cert: x509.Certificate = generate_self_signed_app_certificate(
        key, "Application CA", NAMES, subject_alt_names, extended=[]
    )

    key_file = base_private / "ca_application.pem"
    cert_file = base_certs / "ca_application.der"

    key_file.write_bytes(dump_private_key_as_pem(key))
    cert_file.write_bytes(cert.public_bytes(encoding=Encoding.DER))


async def generate_csr():
    subject_alt_names: list[x509.GeneralName] = [
        x509.UniformResourceIdentifier(f"urn:{HOSTNAME}:foobar:myserver"),
        x509.DNSName(f"{HOSTNAME}"),
    ]

    key: RSAPrivateKey = generate_private_key()
    key = await load_private_key(base_private / "myserver.pem")
    csr: x509.CertificateSigningRequest = generate_app_certificate_signing_request(
        key, f"myserver@{HOSTNAME}", NAMES, subject_alt_names, extended=CLIENT_SERVER_USE
    )

    # key_file = base_private / 'myserver.pem'
    csr_file = base_csr / "myserver.csr"

    # key_file.write_bytes(dump_private_key_as_pem(key))
    async with await anyio.open_file(str(csr_file), "wb") as f:
        await f.write(csr.public_bytes(encoding=Encoding.PEM))


async def sign_csr():
    issuer = await load_certificate(base_certs / "ca_application.der")
    key_ca = await load_private_key(base_private / "ca_application.pem")
    csr_file: Path = base_csr / "myserver.csr"
    async with await anyio.open_file(str(csr_file), "rb") as f:
        csr = x509.load_pem_x509_csr(f.read_file())

    cert: x509.Certificate = sign_certificate_request(csr, issuer, key_ca, days=30)

    async with await anyio.open_file(str(base_certs / "myserver.der"), "wb") as f:
        await f.write(csr.public_bytes(encoding=Encoding.PEM))


async def main():
    # create key and reuse it for self_signed and generate_csr
    generate_private_key_for_myserver()

    # generate self signed certificate for myserver-selfsigned
    await generate_self_signed_certificate()

    # generate certificate signing request and sign it with the ca for myserver
    generate_applicationgroup_ca()
    await generate_csr()
    await sign_csr()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exp:
        print(exp)
