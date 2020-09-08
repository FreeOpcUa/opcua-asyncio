import os
import pytest
import sys

from asyncua import Client
from asyncua import Server
from asyncua import ua
from asyncua.crypto.permission_rules import SimpleRoleRuleset
from asyncua.server.users import UserRole
from asyncua.server.user_managers import CertificateUserManager

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
                      f"{EXAMPLE_PATH}certificate-example.der"),]

admin_peer_creds = {
    "certificate": f"{EXAMPLE_PATH}certificates/peer-certificate-example-1.der",
    "private_key": f"{EXAMPLE_PATH}certificates/peer-private-key-example-1.pem"
}

user_peer_creds = {
    "certificate": f"{EXAMPLE_PATH}certificates/peer-certificate-example-2.der",
    "private_key": f"{EXAMPLE_PATH}certificates/peer-private-key-example-2.pem"
}

anonymous_peer_creds = {
    "certificate": f"{EXAMPLE_PATH}certificates/peer-certificate-example-3.der",
    "private_key": f"{EXAMPLE_PATH}certificates/peer-private-key-example-3.pem"
}


@pytest.fixture(params=srv_crypto_params)
async def srv_crypto_one_cert(request):
    cert_user_manager = CertificateUserManager()
    admin_peer_certificate = admin_peer_creds["certificate"]
    user_peer_certificate = user_peer_creds["certificate"]
    anonymous_peer_certificate = anonymous_peer_creds["certificate"]
    key, cert = request.param
    await cert_user_manager.add_admin(admin_peer_certificate, name='Admin')
    await cert_user_manager.add_user(user_peer_certificate, name='User')
    await cert_user_manager.add_role(anonymous_peer_certificate, name='Anonymous', user_role=UserRole.Anonymous)
    srv = Server(user_manager=cert_user_manager)

    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt],
                            permission_ruleset=SimpleRoleRuleset())
    await srv.init()
    await srv.load_certificate(cert)
    await srv.load_private_key(key)
    idx = 0
    myobj = await srv.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 0.0)
    await myvar.set_writable()  # Set MyVariable to be writable by clients

    await srv.start()
    yield srv
    # stop the server
    await srv.stop()


async def test_permissions_admin(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        admin_peer_creds['certificate'],
        admin_peer_creds['private_key'],
        None,
        server_certificate=srv_crypto_params[0][1],
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )

    async with clt:
        assert await clt.get_objects_node().get_children()
        objects = clt.nodes.objects
        child = await objects.get_child(['0:MyObject', '0:MyVariable'])
        await child.read_value()
        await child.set_value(42)


async def test_permissions_user(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        user_peer_creds['certificate'],
        user_peer_creds['private_key'],
        None,
        server_certificate=srv_crypto_params[0][1],
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    async with clt:
        assert await clt.get_objects_node().get_children()
        objects = clt.nodes.objects
        child = await objects.get_child(['0:MyObject', '0:MyVariable'])
        await child.read_value()
        with pytest.raises(ua.uaerrors.BadUserAccessDenied):
            await child.set_value(42)


async def test_permissions_anonymous(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        anonymous_peer_creds['certificate'],
        anonymous_peer_creds['private_key'],
        None,
        server_certificate=srv_crypto_params[0][1],
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    await clt.connect()
    await clt.get_endpoints()
