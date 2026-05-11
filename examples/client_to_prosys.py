import asyncio
import logging

from asyncua import Client


async def main() -> None:
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer"
    client = Client(url=url)
    await client.load_client_certificate("my_cert.der")
    async with client:
        await client.load_data_type_definitions(overwrite_existing=True)
        print("Root children are", await client.nodes.root.get_children())


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
