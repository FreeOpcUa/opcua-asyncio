import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

from asyncua import ua
from asyncua.client.rc import RCClient, RCServer
from asyncua.crypto import security_policies

namespace = "http://examples.freeopcua.github.io"

CERT_BASE = Path(__file__).parent / "examples" / "certificates" / "chain"


CLIENT_CERT = CERT_BASE / "client.cert.pem"
CLIENT_PRIVATE_KEY = CERT_BASE / "client.key.pem"
SERVER_CERT = CERT_BASE / "server.cert.pem"


async def single_client_per_server():
    """Creating a single RC client."""
    client = RCClient(RCServer("127.0.0.1", 60555))
    await client.set_security(
        security_policies.SecurityPolicyBasic256Sha256,
        certificate=CLIENT_CERT,
        private_key=CLIENT_PRIVATE_KEY,
        private_key_password=None,
        server_certificate=SERVER_CERT,  # IMPORTANT: make sure to set server certificate
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    await client.load_client_certificate(CLIENT_CERT)
    await client.load_private_key(CLIENT_PRIVATE_KEY)

    async with client:
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")


async def _callback(c: RCClient) -> None:
    nsidx = await c.get_namespace_index(namespace)
    print(f"Namespace Index for '{namespace}': {nsidx}")


async def multiple_clients_per_server() -> None:
    """Creating a single RC server and creating new RC clients as connections come."""
    tasks: list[asyncio.Task] = []  # for python>=3.11 use asyncio.TaskGroup
    # use exit stack for dynamic context management
    async with AsyncExitStack() as stack, RCServer("127.0.0.1", 60555) as server:
        while True:
            client = RCClient(server, rc_timeout=None)
            await client.set_security(
                security_policies.SecurityPolicyBasic256Sha256,
                certificate=CLIENT_CERT,
                private_key=CLIENT_PRIVATE_KEY,
                private_key_password=None,
                server_certificate=SERVER_CERT,  # IMPORTANT: make sure to set server certificate
                mode=ua.MessageSecurityMode.SignAndEncrypt,
            )

            await client.load_client_certificate(CLIENT_CERT)
            await client.load_private_key(CLIENT_PRIVATE_KEY)

            await stack.enter_async_context(client)
            tasks.append(asyncio.create_task(_callback(client)))


async def main() -> None:
    await single_client_per_server()
    await multiple_clients_per_server()


if __name__ == "__main__":
    asyncio.run(main())
