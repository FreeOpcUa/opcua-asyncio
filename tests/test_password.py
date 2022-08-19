import pytest

from asyncua import Client, Server, ua
from asyncua.server.users import UserRole, User

uri = "opc.tcp://127.0.0.1:48517/baz/server"
uri_creds = "opc.tcp://foobar:hR%26yjjGhP%246%40nQ4e@127.0.0.1:48517/baz/server"
uri_wrong_creds = "opc.tcp://foobar:wrong@127.0.0.1:48517/baz/server"


class UserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        if username == "foobar" and password == "hR&yjjGhP$6@nQ4e":
            return User(role=UserRole.User)
        return None


@pytest.fixture()
async def srv_user():
    srv = Server(user_manager=UserManager())
    srv.set_endpoint(uri)
    srv.set_security_IDs(["Username"])

    await srv.init()
    await srv.start()
    yield srv
    await srv.stop()


async def test_creds(srv_user):
    clt = Client(uri)
    clt.set_user("foobar")
    clt.set_password("hR&yjjGhP$6@nQ4e")
    await clt.connect()
    await clt.disconnect()


async def test_wrong_creds(srv_user):
    clt = Client(uri)
    clt.set_user("foobar")
    clt.set_password("wrong")
    with pytest.raises(ua.uaerrors.BadUserAccessDenied):
        await clt.connect()
    await clt.disconnect()


async def test_creds_in_uri(srv_user):
    clt = Client(uri_creds)
    # check if credentials got removed
    assert clt.server_url.geturl() == uri
    await clt.connect()
    await clt.disconnect()


async def test_wrong_creds_in_uri(srv_user):
    clt = Client(uri_wrong_creds)
    with pytest.raises(ua.uaerrors.BadUserAccessDenied):
        await clt.connect()
    await clt.disconnect()
