import asyncio
import sys

import logging
sys.path.insert(0, "..")
from asyncua.crypto.certificate_handler import CertificateHandler
from asyncua import Server
from asyncua import ua
from asyncua.crypto.permission_rules import SimpleRoleRuleset
from asyncua.server.users import UserRole
from asyncua.server.user_managers import CertificateUserManager

logging.basicConfig(level=logging.INFO)


async def main():

    cert_handler = CertificateHandler()
    await cert_handler.trust_certificate("certificates/peer-certificate-example-1.der", user_role=UserRole.User)

    server = Server(user_manager=CertificateUserManager(cert_handler))

    await server.init()

    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt],
                               certificate_handler=cert_handler,
                               permission_ruleset=SimpleRoleRuleset())
    # load server certificate and private key. This enables endpoints
    # with signing and encryption.

    await server.load_certificate("certificate-example.der")
    await server.load_private_key("private-key-example.pem")

    idx = 0

    # populating our address space
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 0.0)
    await myvar.set_writable()  # Set MyVariable to be writable by clients

    # starting!

    async with server:
        while True:
            await asyncio.sleep(1)
            current_val = await myvar.get_value()
            count = current_val + 0.1
            await myvar.write_value(count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
