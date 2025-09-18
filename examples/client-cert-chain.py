import asyncio
from enum import Enum
from pathlib import Path

from asyncua import Client, ua
from asyncua.crypto import security_policies
from asyncua.crypto.uacrypto import CertProperties

url = "opc.tcp://localhost:4840/freeopcua/server/"
namespace = "http://examples.freeopcua.github.io"

CERT_BASE = Path(__file__).parent / "examples" / "certificates" / "chain"


class CertChain(Enum):
    INTER1 = CERT_BASE / "inter1.cert.pem"
    INTER2 = CERT_BASE / "inter2.cert.pem"
    CLIENT = CERT_BASE / "client.cert.pem"


CLIENT_PRIVATE_KEY = CERT_BASE / "client.key.pem"


async def main():
    print(f"Connecting to {url} ...")
    client = Client(url=url)
    client.application_uri = "urn:example.org:FreeOpcUa:python-opcua-client"

    # Set communication certificates including chain
    await client.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        certificate=CertChain.CLIENT.value,
        private_key=CLIENT_PRIVATE_KEY,
        private_key_password=None,
        server_certificate=None,
        mode=ua.MessageSecurityMode.SignAndEncrypt,
        certificate_chain=[CertChain.INTER2.value, CertChain.INTER1.value],
    )

    # Set user authentication certificates including chain
    await client.load_client_certificate(CertChain.CLIENT.value)
    await client.load_private_key(CLIENT_PRIVATE_KEY)
    await client.load_client_chain(
        [
            CertProperties(CertChain.INTER2.value),
            CertProperties(CertChain.INTER1.value),
        ]
    )

    async with client:
        # Find the namespace index
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")

        # Get the variable node for read / write
        var = await client.nodes.root.get_child(f"0:Objects/{nsidx}:MyObject/{nsidx}:MyVariable")
        value = await var.read_value()
        print(f"Value of MyVariable ({var}): {value}")

        new_value = value - 50
        print(f"Setting value of MyVariable to {new_value} ...")
        await var.write_value(new_value)

        # Calling a method
        res = await client.nodes.objects.call_method(f"{nsidx}:ServerMethod", 5)
        print(f"Calling ServerMethod returned {res}")


if __name__ == "__main__":
    asyncio.run(main())
