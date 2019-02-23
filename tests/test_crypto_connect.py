import os
import pytest
from asyncua import Client
from asyncua import Server
from asyncua import ua

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
uri_crypto = "opc.tcp://127.0.0.1:{0:d}".format(port_num1)
uri_no_crypto = "opc.tcp://127.0.0.1:{0:d}".format(port_num2)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXAMPLE_PATH = os.path.join(BASE_DIR, "examples") + os.sep


@pytest.fixture()
async def srv_crypto():
    # start our own server
    srv = Server()
    await srv.init()
    srv.set_endpoint(uri_crypto)
    await srv.load_certificate(f"{EXAMPLE_PATH}certificate-example.der")
    await srv.load_private_key(f"{EXAMPLE_PATH}private-key-example.pem")
    await srv.start()
    yield srv
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
        await clt.get_objects_node().get_children()


async def test_nocrypto_fail(srv_no_crypto):
    clt = Client(uri_no_crypto)
    with pytest.raises(ua.UaError):
        await clt.set_security_string(f"Basic256Sha256,Sign,{EXAMPLE_PATH}certificate-example.der,{EXAMPLE_PATH}private-key-example.pem")


async def test_basic256(srv_crypto):
    clt = Client(uri_crypto)
    await clt.set_security_string(f"Basic256Sha256,Sign,{EXAMPLE_PATH}certificate-example.der,{EXAMPLE_PATH}private-key-example.pem")
    async with clt:
        assert await clt.get_objects_node().get_children()


async def test_basic256_encrypt(srv_crypto):
    clt = Client(uri_crypto)
    await clt.set_security_string(
            f"Basic256Sha256,SignAndEncrypt,{EXAMPLE_PATH}certificate-example.der,{EXAMPLE_PATH}private-key-example.pem")
    async with clt:
        assert await clt.get_objects_node().get_children()


async def test_basic256_encrypt_success(srv_crypto):
    clt = Client(uri_crypto)
    await clt.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            f"{EXAMPLE_PATH}certificate-example.der",
            f"{EXAMPLE_PATH}private-key-example.pem",
            None,
            ua.MessageSecurityMode.SignAndEncrypt
        )
    async with clt:
        assert await clt.get_objects_node().get_children()


async def test_basic256_encrypt_fail(srv_crypto):
    # FIXME: how to make it fail???
    clt = Client(uri_crypto)
    with pytest.raises(ua.UaError):
        await clt.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            f"{EXAMPLE_PATH}certificate-example.der",
            f"{EXAMPLE_PATH}private-key-example.pem",
            None,
            ua.MessageSecurityMode.None_
        )
