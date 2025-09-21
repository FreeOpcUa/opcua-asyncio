import logging
from enum import Enum
from pathlib import Path
from collections.abc import Iterator

import pytest

from asyncua import Client, Server, ua
from asyncua.crypto import security_policies
from asyncua.crypto.uacrypto import CertProperties

_logger = logging.getLogger("asyncua.server.address_space")
_logger.setLevel(logging.WARNING)
pytestmark = pytest.mark.asyncio
uri_crypto = "opc.tcp://127.0.0.1:48515"

BASE_DIR = Path(__file__).parent.parent
CHAIN_PATH = BASE_DIR / "examples" / "certificates" / "chain"


class CertChain(Enum):
    ROOT = CHAIN_PATH / "root.cert.pem"
    ROOT_DER = CHAIN_PATH / "root.cert.der"
    INTER1 = CHAIN_PATH / "inter1.cert.pem"
    INTER2 = CHAIN_PATH / "inter2.cert.pem"
    CLIENT = CHAIN_PATH / "client.cert.pem"
    SERVER = CHAIN_PATH / "server.cert.pem"


class PrivateKeys(Enum):
    ROOT = CHAIN_PATH / "root.key.pem"
    INTER1 = CHAIN_PATH / "inter1.key.pem"
    INTER2 = CHAIN_PATH / "inter2.key.pem"
    CLIENT = CHAIN_PATH / "client.key.pem"
    SERVER = CHAIN_PATH / "server.key.pem"


@pytest.fixture()
async def _server(request) -> Iterator[None]:
    srv = Server()
    await srv.init()
    srv.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    srv.set_endpoint(uri_crypto)
    await srv.load_certificate(CertChain.SERVER.value)
    await srv.load_private_key(PrivateKeys.SERVER.value)

    async with srv:
        yield


@pytest.mark.usefixtures("_server")
async def test_client_communication_chain_no_ver():
    """Checks that including multiple certificates into the communication chain does not break the server which does not verify the chain."""
    client = Client(uri_crypto)
    client.application_uri = "urn:example.org:FreeOpcUa:python-opcua-client"
    await client.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        CertChain.CLIENT.value,
        PrivateKeys.CLIENT.value,
        None,
        CertChain.SERVER.value,
        ua.MessageSecurityMode.SignAndEncrypt,
        certificate_chain=[CertChain.INTER2.value, CertChain.INTER1.value],
    )

    async with client:
        assert await client.nodes.objects.get_children()


@pytest.mark.usefixtures("_server")
async def test_client_user_cert_no_ver():
    """Checks that including multiple certificates into the user chain does not break the server which does not verify the chain."""
    client = Client(uri_crypto)
    client.application_uri = "urn:example.org:FreeOpcUa:python-opcua-client"
    await client.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        CertChain.CLIENT.value,
        PrivateKeys.CLIENT.value,
        None,
        CertChain.SERVER.value,
        ua.MessageSecurityMode.SignAndEncrypt,
        certificate_chain=[CertChain.INTER2.value, CertChain.INTER1.value],
    )

    await client.load_client_certificate(CertChain.CLIENT.value)
    await client.load_private_key(PrivateKeys.CLIENT.value)
    await client.load_client_chain([CertProperties(CertChain.INTER2.value), CertProperties(CertChain.INTER1.value)])

    async with client:
        assert await client.nodes.objects.get_children()
