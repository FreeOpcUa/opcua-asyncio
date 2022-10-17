import asyncio
import logging
import sys
sys.path.insert(0, "..")
from asyncua import Client, Node, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")

cert_idx = 1
cert = f"certificates/peer-certificate-example-{cert_idx}.der"
private_key = f"certificates/peer-private-key-example-{cert_idx}.pem"


async def task(loop):
    url = "opc.tcp://127.0.0.1:4840/freeopcua/server/"
    client = Client(url=url)
    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=cert,
        private_key=private_key,
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
