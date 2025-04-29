from pathlib import Path
import pytest

from asyncua import Client
from asyncua import Server
from asyncua import ua
from asyncua.crypto.permission_rules import UserRole
from asyncua.server.user_managers import CertificateUserManager
from asyncua.crypto import security_policies

pytestmark = pytest.mark.asyncio

uri_crypto_cert = "opc.tcp://127.0.0.1:48516"
BASE_DIR = Path(__file__).parent.parent
EXAMPLE_PATH = BASE_DIR / "examples"
srv_crypto_params = (EXAMPLE_PATH / "private-key-example.pem", EXAMPLE_PATH / "certificate-example.der")

admin_peer_creds = {
    "certificate": EXAMPLE_PATH / "certificates/peer-certificate-example-1.der",
    "private_key": EXAMPLE_PATH / "certificates/peer-private-key-example-1.pem",
}

user_peer_creds = {
    "certificate": EXAMPLE_PATH / "certificates/peer-certificate-example-2.der",
    "private_key": EXAMPLE_PATH / "certificates/peer-private-key-example-2.pem",
}

anonymous_peer_creds = {
    "certificate": EXAMPLE_PATH / "certificates/peer-certificate-example-3.der",
    "private_key": EXAMPLE_PATH / "certificates/peer-private-key-example-3.pem",
}


@pytest.fixture(scope="module")
async def srv_crypto_one_cert(request):
    cert_user_manager = CertificateUserManager()
    admin_peer_certificate = admin_peer_creds["certificate"]
    user_peer_certificate = user_peer_creds["certificate"]
    anonymous_peer_certificate = anonymous_peer_creds["certificate"]
    key, cert = srv_crypto_params
    await cert_user_manager.add_admin(admin_peer_certificate, name="Admin")
    await cert_user_manager.add_user(user_peer_certificate, name="User")
    await cert_user_manager.add_role(anonymous_peer_certificate, name="Anonymous", user_role=UserRole.Anonymous)
    srv = Server(user_manager=cert_user_manager)

    srv.set_endpoint(uri_crypto_cert)
    srv.set_security_policy([ua.SecurityPolicyType.NoSecurity, ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
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
    await srv.delete_nodes([myobj, myvar])
    await srv.stop()


async def test_client_admin(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        admin_peer_creds["certificate"],
        admin_peer_creds["private_key"],
        None,
        server_certificate=srv_crypto_params[1],
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    async with clt:
        assert await clt.get_objects_node().get_children()
        objects = clt.nodes.objects
        child = await objects.get_child(["0:MyObject", "0:MyVariable"])
        await child.set_value(42.0)
        assert await child.read_value() == 42.0
        await child.add_property(0, "MyProperty1", 3)


async def test_client_user(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        user_peer_creds["certificate"],
        user_peer_creds["private_key"],
        None,
        server_certificate=srv_crypto_params[1],
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )
    async with clt:
        assert await clt.get_objects_node().get_children()
        objects = clt.nodes.objects
        child = await objects.get_child(["0:MyObject", "0:MyVariable"])
        await child.set_value(44.0)
        assert await child.read_value() == 44.0
        with pytest.raises(ua.uaerrors.BadUserAccessDenied):
            await child.add_property(0, "MyProperty2", 3)


async def test_client_anonymous(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        anonymous_peer_creds["certificate"],
        anonymous_peer_creds["private_key"],
        None,
        server_certificate=srv_crypto_params[1],
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )
    async with clt:
        await clt.get_endpoints()
        with pytest.raises(ua.uaerrors.BadUserAccessDenied):
            await clt.nodes.objects.get_children()


async def test_x509identity_user(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.load_client_certificate(user_peer_creds["certificate"])
    await clt.load_private_key(user_peer_creds["private_key"])
    async with clt:
        assert await clt.get_objects_node().get_children()
        objects = clt.nodes.objects
        child = await objects.get_child(["0:MyObject", "0:MyVariable"])
        await child.set_value(46.0)
        assert await child.read_value() == 46.0
        with pytest.raises(ua.uaerrors.BadUserAccessDenied):
            await child.add_property(0, "MyProperty3", 3)


async def test_x509identity_anonymous(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.load_client_certificate(anonymous_peer_creds["certificate"])
    await clt.load_private_key(anonymous_peer_creds["private_key"])
    async with clt:
        await clt.get_endpoints()
        with pytest.raises(ua.uaerrors.BadUserAccessDenied):
            await clt.nodes.objects.get_children()


async def test_client_user_x509identity_admin(srv_crypto_one_cert):
    clt = Client(uri_crypto_cert)
    await clt.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        user_peer_creds["certificate"],
        user_peer_creds["private_key"],
        None,
        server_certificate=srv_crypto_params[1],
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )
    await clt.load_client_certificate(admin_peer_creds["certificate"])
    await clt.load_private_key(admin_peer_creds["private_key"])
    async with clt:
        assert await clt.get_objects_node().get_children()
        objects = clt.nodes.objects
        child = await objects.get_child(["0:MyObject", "0:MyVariable"])
        await child.set_value(48.0)
        assert await child.read_value() == 48.0
        await child.add_property(0, "MyProperty4", 3)
