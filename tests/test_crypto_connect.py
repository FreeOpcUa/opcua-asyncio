import os
import pytest
import asyncio

from asyncio import TimeoutError
from asyncua import Client
from asyncua import Server
from asyncua import ua
from asyncua.server.user_managers import CertificateUserManager
from asyncua.crypto.security_policies import Verifier, Decryptor

try:
    from asyncua.crypto import uacrypto
    from asyncua.crypto import security_policies
except ImportError:
    print("WARNING: CRYPTO NOT AVAILABLE, CRYPTO TESTS DISABLED!!")
    disable_crypto_tests = True
else:
    disable_crypto_tests = False

pytestmark = pytest.mark.asyncio

port_num1 = 48515
port_num2 = 48512
port_num3 = 48516
uri_crypto = "opc.tcp://127.0.0.1:{0:d}".format(port_num1)
uri_no_crypto = "opc.tcp://127.0.0.1:{0:d}".format(port_num2)
uri_crypto_cert = "opc.tcp://127.0.0.1:{0:d}".format(port_num3)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXAMPLE_PATH = os.path.join(BASE_DIR, "examples") + os.sep
srv_crypto_params = [(f"{EXAMPLE_PATH}private-key-example.pem",
                      f"{EXAMPLE_PATH}certificate-example.der"),
                     (f"{EXAMPLE_PATH}private-key-3072-example.pem",
                      f"{EXAMPLE_PATH}certificate-3072-example.der")]

peer_creds = {
    "certificate": f"{EXAMPLE_PATH}certificates/peer-certificate-example-1.der",
    "private_key": f"{EXAMPLE_PATH}certificates/peer-private-key-example-1.pem"
}

unauthorized_peer_creds = {
    "certificate": f"{EXAMPLE_PATH}certificates/peer-certificate-example-2.der",
    "private_key": f"{EXAMPLE_PATH}certificates/peer-private-key-example-2.pem"
}

encrypted_private_key_peer_creds = {
    "private_key": f"{EXAMPLE_PATH}certificates/peer-private-key-example-encrypted-private-key.pem",
    "certificate": f"{EXAMPLE_PATH}certificates/peer-certificate-example-encrypted-private-key.der",
    "password": b"password"
}


@pytest.fixture(params=srv_crypto_params)
async def srv_crypto_encrypted_key_one_cert(request):
    peer_certificate = encrypted_private_key_peer_creds["certificate"]
    user_manager = CertificateUserManager()
    key, cert = request.param
    await user_manager.add_admin(peer_certificate, 'test1')

    srv = Server(user_manager=user_manager)

    await srv.init()
    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    await srv.start()
    yield srv, cert
    # stop the server
    await srv.stop()


@pytest.fixture(params=srv_crypto_params)
async def srv_crypto_all_certs(request):
    # start our own server
    srv = Server()
    key, cert = request.param
    await srv.init()
    srv.set_endpoint(uri_crypto)
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    await srv.start()
    yield srv, cert
    # stop the server
    await srv.stop()


@pytest.fixture(params=srv_crypto_params)
async def srv_crypto_one_cert(request):
    peer_certificate = peer_creds["certificate"]
    user_manager = CertificateUserManager()
    key, cert = request.param
    await user_manager.add_admin(peer_certificate, 'test1')

    srv = Server(user_manager=user_manager)

    await srv.init()
    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    await srv.start()
    yield srv, cert
    # stop the server
    await srv.stop()


@pytest.fixture()
async def srv_no_crypto():
    # start our own server
    srv = Server()
    await srv.init()
    srv.set_endpoint(uri_no_crypto)
    await srv.start()
    yield srv
    # stop the server
    await srv.stop()


async def test_nocrypto(srv_no_crypto):
    clt = Client(uri_no_crypto)
    async with clt:
        await clt.nodes.objects.get_children()


async def test_nocrypto_fail(srv_no_crypto):
    clt = Client(uri_no_crypto)
    with pytest.raises(ua.UaError):
        await clt.set_security_string(
            f"Basic256Sha256,Sign,{EXAMPLE_PATH}certificate-example.der,{EXAMPLE_PATH}private-key-example.pem")


async def test_basic256(srv_crypto_all_certs):
    _, cert = srv_crypto_all_certs
    clt = Client(uri_crypto)
    await clt.set_security_string(
        f"Basic256Sha256,Sign,{EXAMPLE_PATH}certificate-example.der,{EXAMPLE_PATH}private-key-example.pem,{cert}"
    )
    async with clt:
        assert await clt.nodes.objects.get_children()


async def test_basic256_encrypt(srv_crypto_all_certs):
    _, cert = srv_crypto_all_certs
    clt = Client(uri_crypto)
    await clt.set_security_string(
        f"Basic256Sha256,SignAndEncrypt,{EXAMPLE_PATH}certificate-example.der,{EXAMPLE_PATH}private-key-example.pem,{cert}")
    async with clt:
        assert await clt.nodes.objects.get_children()


async def test_basic256_encrypt_success(srv_crypto_all_certs):
    clt = Client(uri_crypto)
    _, cert = srv_crypto_all_certs
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        f"{EXAMPLE_PATH}certificate-example.der",
        f"{EXAMPLE_PATH}private-key-example.pem",
        None,
        cert,
        ua.MessageSecurityMode.SignAndEncrypt
    )

    async with clt:
        assert await clt.nodes.objects.get_children()


@pytest.mark.skip("# FIXME: how to make it fail???")
async def test_basic256_encrypt_fail(srv_crypto_all_certs):
    # FIXME: how to make it fail???
    _, cert = srv_crypto_all_certs
    clt = Client(uri_crypto)
    with pytest.raises(ua.UaError):
        await clt.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            f"{EXAMPLE_PATH}certificate-example.der",
            f"{EXAMPLE_PATH}private-key-example.pem",
            None,
            None,
            mode=ua.MessageSecurityMode.None_
        )


async def test_certificate_handling_success(srv_crypto_one_cert):
    _, cert = srv_crypto_one_cert
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        peer_creds['certificate'],
        peer_creds['private_key'],
        None,
        cert,
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    async with clt:
        assert await clt.get_objects_node().get_children()


async def test_encrypted_private_key_handling_success(srv_crypto_encrypted_key_one_cert):
    _, cert = srv_crypto_encrypted_key_one_cert
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        encrypted_private_key_peer_creds['certificate'],
        encrypted_private_key_peer_creds['private_key'],
        encrypted_private_key_peer_creds['password'],
        cert,
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    async with clt:
        assert await clt.get_objects_node().get_children()


async def test_encrypted_private_key_handling_success_with_cert_props(srv_crypto_encrypted_key_one_cert):
    _, cert = srv_crypto_encrypted_key_one_cert
    clt = Client(uri_crypto_cert)
    user_cert = uacrypto.CertProperties(encrypted_private_key_peer_creds['certificate'], "DER")
    user_key = uacrypto.CertProperties(
        path=encrypted_private_key_peer_creds['private_key'],
        password=encrypted_private_key_peer_creds['password'],
        extension="PEM",
    )
    server_cert = uacrypto.CertProperties(cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        user_cert,
        user_key,
        server_certificate=server_cert,
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    async with clt:
        assert await clt.get_objects_node().get_children()


async def test_certificate_handling_failure(srv_crypto_one_cert):
    _, cert = srv_crypto_one_cert
    clt = Client(uri_crypto_cert)

    with pytest.raises(ua.uaerrors.BadUserAccessDenied):
        await clt.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            unauthorized_peer_creds['certificate'],
            unauthorized_peer_creds['private_key'],
            None,
            mode=ua.MessageSecurityMode.SignAndEncrypt
        )

        async with clt:
            assert await clt.get_objects_node().get_children()


async def test_encrypted_private_key_handling_failure(srv_crypto_one_cert):
    _, cert = srv_crypto_one_cert
    clt = Client(uri_crypto_cert)

    with pytest.raises(ua.uaerrors.BadUserAccessDenied):
        await clt.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            unauthorized_peer_creds['certificate'],
            unauthorized_peer_creds['private_key'],
            None,  # Pass None for an empty password to test incorrect password.
            cert,
            mode=ua.MessageSecurityMode.SignAndEncrypt
        )
        async with clt:
            assert await clt.get_objects_node().get_children()


async def test_certificate_handling_mismatched_creds(srv_crypto_one_cert):
    _, cert = srv_crypto_one_cert
    clt = Client(uri_crypto_cert)
    with pytest.raises((AttributeError, TimeoutError)):
        # either exception can be raise, depending on used python version
        # and crypto library version
        await clt.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            peer_creds['certificate'],
            unauthorized_peer_creds['private_key'],
            None,
            cert,
            mode=ua.MessageSecurityMode.SignAndEncrypt
        )
        async with clt:
            assert await clt.get_objects_node().get_children()


@pytest.mark.skip("That test fails and hangs randomly on github so disabling for now")
async def test_secure_channel_key_expiration(srv_crypto_one_cert, mocker):
    timeout = 1
    _, cert = srv_crypto_one_cert
    clt = Client(uri_crypto_cert)
    clt.secure_channel_timeout = timeout * 1000
    user_cert = uacrypto.CertProperties(peer_creds['certificate'], "DER")
    user_key = uacrypto.CertProperties(
        path=peer_creds['private_key'],
        extension="PEM",
    )
    server_cert = uacrypto.CertProperties(cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        user_cert,
        user_key,
        server_certificate=server_cert,
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    async with clt:
        assert clt.uaclient.security_policy.symmetric_cryptography.Prev_Verifier is None
        assert clt.uaclient.security_policy.symmetric_cryptography.Prev_Decryptor is None

        await asyncio.sleep(timeout * 1.2)
        sym_crypto = clt.uaclient.security_policy.symmetric_cryptography
        prev_verifier = sym_crypto.Prev_Verifier
        prev_decryptor = sym_crypto.Prev_Decryptor
        assert isinstance(prev_verifier, Verifier)
        assert isinstance(prev_decryptor, Decryptor)

        mock_decry_reset = mocker.patch.object(prev_verifier, "reset", wraps=prev_verifier.reset)
        mock_verif_reset = mocker.patch.object(prev_decryptor, "reset", wraps=prev_decryptor.reset)
        assert mock_decry_reset.call_count == 0
        assert mock_verif_reset.call_count == 0

        await asyncio.sleep(timeout * 0.3)
        assert await clt.get_objects_node().get_children()

        assert sym_crypto.key_expiration > 0
        assert sym_crypto.prev_key_expiration > 0
        assert sym_crypto.key_expiration > sym_crypto.prev_key_expiration

        assert mock_decry_reset.call_count == 1
        assert mock_verif_reset.call_count == 1
        assert clt.uaclient.security_policy.symmetric_cryptography.Prev_Verifier is None
        assert clt.uaclient.security_policy.symmetric_cryptography.Prev_Decryptor is None


async def test_always_catch_new_cert_on_set_security():
    """
    Test client reconnection after server cert update.
    This could be useful when we prefer to keep a unique
    client instance (i.e HaClient).
    """
    # Client connecting with encryption to server
    srv = Server()
    await srv.init()
    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    key, cert = srv_crypto_params[0]
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    await srv.start()
    clt = Client(uri_crypto_cert)
    peer_cert = peer_creds["certificate"]
    peer_key = peer_creds["private_key"]
    security_string = f"Basic256Sha256,SignAndEncrypt,{peer_cert},{peer_key}"
    await clt.set_security_string(security_string)
    assert await clt.connect_and_get_server_endpoints()
    srv_original_cert = clt.security_policy.peer_certificate
    await srv.stop()

    # Simulation of a server cert renewal
    srv = Server()
    await srv.init()
    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    key, cert = srv_crypto_params[1]
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    await srv.start()
    # The same client instance fails to open a SecureChannel because the
    # security_policy contains the previous SecurityMode and server certificate.
    with pytest.raises(TimeoutError):
        await clt.connect_and_get_server_endpoints()

    assert clt.security_policy == clt.uaclient.security_policy
    assert clt.security_policy.peer_certificate == srv_original_cert

    # If the server cert isn't passed to set_security we clear the security_policy
    await clt.set_security_string(security_string)
    assert await clt.connect_and_get_server_endpoints()
    assert clt.security_policy == clt.uaclient.security_policy
    assert clt.security_policy.peer_certificate
    assert clt.security_policy.peer_certificate != srv_original_cert
    await srv.stop()


async def test_anonymous_rejection():
    peer_certificate = peer_creds["certificate"]
    user_manager = CertificateUserManager()
    key, cert = srv_crypto_params[0]
    await user_manager.add_admin(peer_certificate, 'test1')

    srv = Server(user_manager=user_manager)

    await srv.init()
    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    srv.set_security_IDs(["Username", "Basic256Sha256"])
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    await srv.start()
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        peer_creds['certificate'],
        peer_creds['private_key'],
        None,
        cert,
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    with pytest.raises(ua.uaerrors.BadIdentityTokenRejected):
        await clt.connect()
    await srv.stop()
