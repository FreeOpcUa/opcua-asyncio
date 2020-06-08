import asyncio
import logging
import sys
sys.path.insert(0, "..")
from asyncua import Client, Node, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("asyncua")

cert = "certificates/peer-certificate-example-1.der"
private_key = "certificates/peer-private-key-example-1.pem"


async def task(loop):
    url = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
    try:
        client = Client(url=url)
        await client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate_path=cert,
            private_key_path=private_key
        )
        await client.connect()
        root = client.nodes.objects
        child = await root.get_child(['0:MyObject', '0:MyVariable'])
        print(await child.get_value())
        await child.set_value(42)
        print(await child.get_value())
    except Exception:
        _logger.exception('error')
    finally:
        await client.disconnect()


def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(task(loop))
    loop.close()


if __name__ == "__main__":
    main()
