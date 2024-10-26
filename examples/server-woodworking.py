# Sample on instantiating objects from imported nodesets into a server

import os.path
import asyncio
import logging
import random
from asyncua import ua, Server
from asyncua.common.instantiate_util import instantiate


class HelloServer:
    def __init__(self, endpoint, name, model_filepath):
        self.server = Server()

        self.model_filepath = model_filepath
        self.server.set_server_name(name)
        self.server.set_endpoint(endpoint)

    async def init(self):
        await self.server.init()

        #  This need to be imported at the start or else it will overwrite the data
        await self.server.import_xml(os.path.join(self.model_filepath, "../nodeset/DI/Opc.Ua.Di.NodeSet2.xml"))
        await self.server.import_xml(
            os.path.join(self.model_filepath, "../nodeset/Machinery/Opc.Ua.Machinery.NodeSet2.xml")
        )
        await self.server.import_xml(
            os.path.join(self.model_filepath, "../nodeset/Woodworking/Opc.Ua.Woodworking.NodeSet2.xml")
        )

        # instantiate mandatory objects in server
        self.device = await instantiate(
            await self.server.nodes.objects.get_child("3:Machines"),
            await self.server.nodes.base_object_type.get_child("4:WwMachineType"),
            bname="test_Server_OPC_UA",
            dname=ua.LocalizedText("Planing Machine"),
            idx=4,
            instantiate_optional=False,
        )

        # write values to mandatory nodes
        await self.server.get_node("ns=4;i=7821").write_value("ProfilingMachine")  # DeviceClass
        await self.server.get_node("ns=4;i=7822").write_value(
            ua.LocalizedText("Manufacturer Name", "de_CH")
        )  # Manufacturer
        await self.server.get_node("ns=4;i=7823").write_value(ua.LocalizedText("Machine Model", "de_CH"))  # Model
        await self.server.get_node("ns=4;i=7824").write_value("Product_Instance_Uri")  # ProductInstanceUri
        await self.server.get_node("ns=4;i=7825").write_value("422111516848641789")  # SerialNumber
        await self.server.get_node("ns=4;i=7826").write_value(
            ua.Variant(1972, ua.VariantType.UInt16)
        )  # YearOfConstruction

    async def __aenter__(self):
        await self.init()
        await self.server.start()
        return self.server

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.server.stop()


async def main():
    script_dir = os.path.dirname(__file__)
    async with HelloServer(
        "opc.tcp://0.0.0.0:4840",
        "FreeOpcUa Example Server",
        script_dir,
    ) as server:
        while True:
            await asyncio.sleep(1)
            a, b = random.randint(0, 5), random.randint(0, 4)
            # Update variables
            await server.get_node("ns=4;i=7830").write_value(a)  # CurrentMode
            await server.get_node("ns=4;i=7831").write_value(b)  # CurrentState
            await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
