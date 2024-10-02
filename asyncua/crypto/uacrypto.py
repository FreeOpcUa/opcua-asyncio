from datetime import datetime, timezone
from pathlib import Path
import aiofiles
from typing import Optional, Sequence, Union, List, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import hmac
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes

# We redefine InvalidSignature as part of this module. Do not remove this line.
from cryptography.exceptions import InvalidSignature  # noqa: F811

from dataclasses import dataclass
import logging


_logger = logging.getLogger(__name__)


class InvalidSignature(Exception):  # type: ignore # noqa: F811
    pass


@dataclass
class CertProperties:
    path_or_content: Union[bytes, Path, str]
    extension: Optional[str] = None
    password: Optional[Union[str, bytes]] = None


async def get_content(path_or_content: Union[str, bytes, Path]) -> bytes:
    if isinstance(path_or_content, bytes):
        return path_or_content

    async with aiofiles.open(path_or_content, mode='rb') as f:
        return await f.read()


async def load_certificate(path_or_content: Union[bytes, str, Path], extension: Optional[str] = None):
    if isinstance(path_or_content, str):
        ext = Path(path_or_content).suffix
    elif isinstance(path_or_content, Path):
        ext = path_or_content.suffix
    else:
        ext = ''

    content = await get_content(path_or_content)
    if ext == ".pem" or extension == 'pem' or extension == 'PEM':
        return x509.load_pem_x509_certificate(content, default_backend())
    else:
        return x509.load_der_x509_certificate(content, default_backend())


def x509_from_der(data):
    if not data:
        return None
    return x509.load_der_x509_certificate(data, default_backend())


async def load_private_key(path_or_content: Union[str, Path, bytes],
                           password: Optional[Union[str, bytes]] = None,
                           extension: Optional[str] = None):
    if isinstance(path_or_content, str):
        ext = Path(path_or_content).suffix
    elif isinstance(path_or_content, Path):
        ext = path_or_content.suffix
    else:
        ext = ''
    if isinstance(password, str):
        password = password.encode('utf-8')

    content = await get_content(path_or_content)
    if ext == ".pem" or extension == 'pem' or extension == 'PEM':
        return serialization.load_pem_private_key(content, password=password, backend=default_backend())
    else:
        return serialization.load_der_private_key(content, password=password, backend=default_backend())


def der_from_x509(certificate: x509.Certificate) -> bytes:
    if certificate is None:
        return b""
    return certificate.public_bytes(serialization.Encoding.DER)


def pem_from_key(private_key: rsa.RSAPrivateKey) -> bytes:
    """dumps a private key in PEM format

    Args:
        private_key (rsa.RSAPrivateKey): The privatekey to dump

    Returns:
        bytes: The private as PEM/PKCS8 format
    """
    return private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())


def sign_sha1(private_key: rsa.RSAPrivateKey, data: bytes) -> bytes:
    return private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA1()
    )


def sign_sha256(private_key: rsa.RSAPrivateKey, data: bytes) -> bytes:
    return private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )


def sign_pss_sha256(private_key: rsa.RSAPrivateKey, data: bytes) -> bytes:
    return private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            salt_length=32
        ),
        hashes.SHA256(),
    )


def verify_sha1(certificate: x509.Certificate, data: bytes, signature: bytes) -> None:
    pub_key = certificate.public_key()
    assert isinstance(pub_key,rsa.RSAPublicKey)
    pub_key.verify(
        signature,
        data,
        padding.PKCS1v15(),
        hashes.SHA1()
    )


def verify_sha256(certificate: x509.Certificate, data: bytes, signature: bytes) -> None:
    pub_key = certificate.public_key()
    assert isinstance(pub_key,rsa.RSAPublicKey)
    pub_key.verify(
        signature,
        data,
        padding.PKCS1v15(),
        hashes.SHA256())


def verify_pss_sha256(certificate: x509.Certificate, data: bytes, signature: bytes) -> None:
    pub_key = certificate.public_key()
    assert isinstance(pub_key,rsa.RSAPublicKey)
    pub_key.verify(
        signature,
        data,
        padding.PSS(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            salt_length=32
        ),
        hashes.SHA256(),
    )


def encrypt_basic256(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None)
    )
    return ciphertext


def encrypt_rsa_oaep(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None)
    )
    return ciphertext


def encrypt_rsa_oaep_sha256(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        ),
    )
    return ciphertext


def encrypt_rsa15(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    ciphertext = public_key.encrypt(
        data,
        padding.PKCS1v15()
    )
    return ciphertext


def decrypt_rsa_oaep(private_key: rsa.RSAPrivateKey, data: bytes) -> bytes:
    text = private_key.decrypt(
        bytes(data),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None)
    )
    return text


def decrypt_rsa_oaep_sha256(private_key: rsa.RSAPrivateKey, data: bytes) -> bytes:
    text = private_key.decrypt(
        bytes(data),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        ),
    )
    return text


def decrypt_rsa15(private_key: rsa.RSAPrivateKey, data: bytes) -> bytes:
    text = private_key.decrypt(
        bytes(data),
        padding.PKCS1v15()
    )
    return text


def cipher_aes_cbc(key: bytes, init_vec: bytes) -> Cipher:
    # FIXME sonarlint reports critical vulnerability (python:S5542)
    return Cipher(algorithms.AES(key), modes.CBC(init_vec), default_backend())


def cipher_encrypt(cipher: Cipher, data: bytes) -> bytes:
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


def cipher_decrypt(cipher: Cipher, data: bytes) -> bytes:
    decryptor = cipher.decryptor()
    return decryptor.update(data) + decryptor.finalize()


def hmac_sha1(key: bytes, message: bytes) -> bytes:
    hasher = hmac.HMAC(key, hashes.SHA1(), backend=default_backend())
    hasher.update(message)
    return hasher.finalize()


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    hasher = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    hasher.update(message)
    return hasher.finalize()


def sha1_size():
    return hashes.SHA1.digest_size


def sha256_size():
    return hashes.SHA256.digest_size


def p_sha1(secret: bytes, seed: bytes, sizes: Sequence[int]=()) -> Tuple[bytes,...]:
    """
    Derive one or more keys from secret and seed.
    (See specs part 6, 6.7.5 and RFC 2246 - TLS v1.0)
    Lengths of keys will match sizes argument
    """
    full_size = 0
    for size in sizes:
        full_size += size

    result = b''
    accum = seed
    while len(result) < full_size:
        accum = hmac_sha1(secret, accum)
        result += hmac_sha1(secret, accum + seed)

    parts: List[bytes] = []
    for size in sizes:
        parts.append(result[:size])
        result = result[size:]
    return tuple(parts)


def p_sha256(secret: bytes, seed: bytes, sizes: Sequence[int]=()) -> Tuple[bytes,...]:
    """
    Derive one or more keys from secret and seed.
    (See specs part 6, 6.7.5 and RFC 2246 - TLS v1.0)
    Lengths of keys will match sizes argument
    """
    full_size = 0
    for size in sizes:
        full_size += size

    result = b''
    accum = seed
    while len(result) < full_size:
        accum = hmac_sha256(secret, accum)
        result += hmac_sha256(secret, accum + seed)

    parts: List[bytes] = []
    for size in sizes:
        parts.append(result[:size])
        result = result[size:]
    return tuple(parts)


def x509_name_to_string(name: x509.Name) -> str:
    parts = [f"{attr.oid._name}={str(attr.value)}" for attr in name]
    return ', '.join(parts)


def x509_to_string(cert: x509.Certificate) -> str:
    """
    Convert x509 certificate to human-readable string
    """
    if cert.subject == cert.issuer:
        issuer = ' (self-signed)'
    else:
        issuer = f', issuer: {x509_name_to_string(cert.issuer)}'
    # TODO: show more information
    return f"{x509_name_to_string(cert.subject)}{issuer}, {cert.not_valid_before_utc} - {cert.not_valid_after_utc}"


def check_certificate(cert: x509.Certificate, application_uri: str, hostname: Optional[str] = None) -> bool:
    """
    check certificate if it matches the application_uri and log errors.
    """
    err = False
    now = datetime.now(timezone.utc)
    if cert.not_valid_after_utc < now:
        _logger.error("certificate is no longer valid: valid until %s", cert.not_valid_after_utc)
        err = True
    if cert.not_valid_before_utc > now:
        _logger.error("certificate is not yet vaild: valid after %s", cert.not_valid_before_utc)
        err = True
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        san_uri = san.value.get_values_for_type(x509.UniformResourceIdentifier)
        if application_uri not in san_uri:
            _logger.warning('certificate does not contain the application uri (%s). Most applications will reject a connection without it.', application_uri)
            err = True
        if hostname is not None:
            san_dns_names = san.value.get_values_for_type(x509.DNSName)
            if hostname not in san_dns_names:
                _logger.warning('certificate does not contain the hostname in DNSNames %s. Some applications will check this.', hostname)
                err = True
    except x509.ExtensionNotFound:
        _logger.warning('certificate has no SubjectAlternativeName this is need for application verification!')
        err = True
    return err
