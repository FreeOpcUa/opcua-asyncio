import asyncio
import logging
import sys
import socket
from pathlib import Path
sys.path.insert(0, "..")
from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")


cert_idx = 4
cert_base = Path(__file__).parent
cert = Path(cert_base / f"certificates/peer-certificate-example-{cert_idx}.der")
private_key = Path(cert_base / f"certificates/peer-private-key-example-{cert_idx}.pem")

async def task(loop):
    host_name = socket.gethostname()
    client_app_uri = f"urn:{host_name}:foobar:myselfsignedclient"
    url = "opc.tcp://127.0.0.1:4840/freeopcua/server/"

    await setup_self_signed_certificate(private_key,
                                        cert,
                                        client_app_uri,
                                        host_name,
                                        [ExtendedKeyUsageOID.CLIENT_AUTH],
                                        {
                                            'countryName': 'CN',
                                            'stateOrProvinceName': 'AState',
                                            'localityName': 'Foo',
                                            'organizationName': "Bar Ltd",
                                        })
    client = Client(url=url)
    client.application_uri = client_app_uri
    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=str(cert),
        private_key=str(private_key),
        server_certificate="certificate-example.der"
    )
    async with client:
        objects = client.nodes.objects
        child = await objects.get_child(['0:MyObject', '0:MyVariable'])
        print(await child.get_value())
        await child.set_value(42)
        print(await child.get_value())


def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(task(loop))
    loop.close()


if __name__ == "__main__":
    main()
