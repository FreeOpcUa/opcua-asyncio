import os

import aiofiles
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import hmac
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes


async def load_certificate(path, format=None):
    _, ext = os.path.splitext(path)
    async with aiofiles.open(path, mode='rb') as f:
        if ext == ".pem" or format == 'pem' or format == 'PEM':
            return x509.load_pem_x509_certificate(await f.read(), default_backend())
        else:
            return x509.load_der_x509_certificate(await f.read(), default_backend())


def x509_from_der(data):
    if not data:
        return None
    return x509.load_der_x509_certificate(data, default_backend())


async def load_private_key(path, format=None):
    _, ext = os.path.splitext(path)
    async with aiofiles.open(path, mode='rb') as f:
        if ext == ".pem" or format == 'pem' or format == 'PEM':
            return serialization.load_pem_private_key(await f.read(), password=None, backend=default_backend())
        else:
            return serialization.load_der_private_key(await f.read(), password=None, backend=default_backend())


def der_from_x509(certificate):
    if certificate is None:
        return b""
    return certificate.public_bytes(serialization.Encoding.DER)


def sign_sha1(private_key, data):
    return private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA1()
    )

def sign_sha256(private_key, data):
    return private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

def verify_sha1(certificate, data, signature):
    certificate.public_key().verify(
        signature,
        data,
        padding.PKCS1v15(),
        hashes.SHA1()
    )


def verify_sha256(certificate, data, signature):
    certificate.public_key().verify(
        signature,
        data,
        padding.PKCS1v15(),
        hashes.SHA256())

def encrypt_basic256(public_key, data):
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None)
    )
    return ciphertext


def encrypt_rsa_oaep(public_key, data):
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None)
    )
    return ciphertext


def encrypt_rsa15(public_key, data):
    ciphertext = public_key.encrypt(
        data,
        padding.PKCS1v15()
    )
    return ciphertext


def decrypt_rsa_oaep(private_key, data):
    text = private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None)
    )
    return text


def decrypt_rsa15(private_key, data):
    text = private_key.decrypt(
        data,
        padding.PKCS1v15()
    )
    return text


def cipher_aes_cbc(key, init_vec):
    return Cipher(algorithms.AES(key), modes.CBC(init_vec), default_backend())


def cipher_encrypt(cipher, data):
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


def cipher_decrypt(cipher, data):
    decryptor = cipher.decryptor()
    return decryptor.update(data) + decryptor.finalize()


def hmac_sha1(key, message):
    hasher = hmac.HMAC(key, hashes.SHA1(), backend=default_backend())
    hasher.update(message)
    return hasher.finalize()

def hmac_sha256(key, message):
    hasher = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    hasher.update(message)
    return hasher.finalize()

def sha1_size():
    return hashes.SHA1.digest_size

def sha256_size():
    return hashes.SHA256.digest_size

def p_sha1(secret, seed, sizes=()):
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

    parts = []
    for size in sizes:
        parts.append(result[:size])
        result = result[size:]
    return tuple(parts)

def p_sha256(secret, seed, sizes=()):
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

    parts = []
    for size in sizes:
        parts.append(result[:size])
        result = result[size:]
    return tuple(parts)

def x509_name_to_string(name):
    parts = ["{0}={1}".format(attr.oid._name, attr.value) for attr in name]
    return ', '.join(parts)


def x509_to_string(cert):
    """
    Convert x509 certificate to human-readable string
    """
    if cert.subject == cert.issuer:
        issuer = ' (self-signed)'
    else:
        issuer = ', issuer: {0}'.format(x509_name_to_string(cert.issuer))
    # TODO: show more information
    return "{0}{1}, {2} - {3}".format(x509_name_to_string(cert.subject), issuer, cert.not_valid_before, cert.not_valid_after)
