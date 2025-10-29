"""Tests for certificate chain handling in the uacrypto module.

This module tests the enhanced x509_from_der function which now supports:
1. Loading single certificates (original functionality)
2. Loading the first certificate from a certificate chain
3. Proper error handling for invalid certificate data

These tests ensure that the function correctly handles certificate chains
that some OPC UA servers might provide, improving compatibility.
"""

import pytest
from pathlib import Path

from asyncua.crypto import uacrypto
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


BASE_DIR = Path(__file__).parent.parent
EXAMPLE_CERT_PATH = BASE_DIR / "examples" / "certificate-example.der"
EXAMPLE_CERT_3072_PATH = BASE_DIR / "examples" / "certificate-3072-example.der"
PEER_CERT_PATH = BASE_DIR / "examples" / "certificates" / "peer-certificate-example-1.der"


def create_cert_chain():
    """Create a certificate chain for testing.

    This function creates a simulated certificate chain by concatenating
    two different certificates. In a real-world scenario, certificate chains
    would contain a server certificate followed by intermediate CA certificates.

    Returns:
        tuple: (first_cert_data, cert_chain_data)
            - first_cert_data: The DER-encoded data of the first certificate
            - cert_chain_data: The DER-encoded data of the entire certificate chain
    """
    # Load the example certificates
    with open(EXAMPLE_CERT_PATH, "rb") as f:
        cert1_data = f.read()

    with open(PEER_CERT_PATH, "rb") as f:
        cert2_data = f.read()

    # Create a certificate chain by concatenating two different certificates
    cert_chain = cert1_data + cert2_data

    return cert1_data, cert_chain


def test_x509_from_der_single_cert():
    """Test that x509_from_der works with a single certificate."""
    # Test with the standard example certificate
    with open(EXAMPLE_CERT_PATH, "rb") as f:
        cert_data = f.read()

    cert = uacrypto.x509_from_der(cert_data)
    assert cert is not None
    assert isinstance(cert, x509.Certificate)

    # Test with the 3072-bit example certificate
    with open(EXAMPLE_CERT_3072_PATH, "rb") as f:
        cert_data_3072 = f.read()

    cert_3072 = uacrypto.x509_from_der(cert_data_3072)
    assert cert_3072 is not None
    assert isinstance(cert_3072, x509.Certificate)

    # Test with the peer certificate
    with open(PEER_CERT_PATH, "rb") as f:
        peer_cert_data = f.read()

    peer_cert = uacrypto.x509_from_der(peer_cert_data)
    assert peer_cert is not None
    assert isinstance(peer_cert, x509.Certificate)


def test_x509_from_der_cert_chain():
    """Test that x509_from_der works with a certificate chain."""
    first_cert_data, cert_chain = create_cert_chain()

    # Load the certificate chain using x509_from_der
    cert = uacrypto.x509_from_der(cert_chain)

    # Verify that the certificate was loaded correctly
    assert cert is not None
    assert isinstance(cert, x509.Certificate)

    # Verify that the loaded certificate is the first one in the chain
    # by comparing it with the original certificate
    original_cert = x509.load_der_x509_certificate(first_cert_data, default_backend())
    assert cert.public_bytes(serialization.Encoding.DER) == original_cert.public_bytes(serialization.Encoding.DER)


def test_x509_from_der_invalid_data():
    """Test that x509_from_der handles invalid data correctly."""
    # Test with None
    assert uacrypto.x509_from_der(None) is None

    # Test with empty bytes
    assert uacrypto.x509_from_der(b"") is None

    # Test with invalid data that doesn't start with a SEQUENCE tag
    with pytest.raises(ValueError):
        uacrypto.x509_from_der(b"invalid data")

    # Test with data that starts with a SEQUENCE tag but is otherwise invalid
    with pytest.raises(ValueError):
        uacrypto.x509_from_der(b"\x30\x03\x01\x02\x03")
