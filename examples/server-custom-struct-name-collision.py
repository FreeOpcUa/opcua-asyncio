"""
Show what happens when two custom structures in different namespaces share
the same browse name, and how to access the type that did not win the
ua.<Name> attribute.

The binding is first-wins: ua.MyStruct stays bound to the first registered
type and a "Browsename collision" warning is logged for the second one.
Both types remain fully usable through the NodeId-keyed registries, so
ua.get_type(node_id) is the reliable lookup when names collide.
"""

import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.structures104 import new_struct, new_struct_field


async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    idx_a = await server.register_namespace("http://example.org/lineA")
    idx_b = await server.register_namespace("http://example.org/lineB")

    node_a, _ = await new_struct(
        server,
        idx_a,
        "MyStruct",
        [
            new_struct_field("Temperature", ua.VariantType.Double),
        ],
    )
    node_b, _ = await new_struct(
        server,
        idx_b,
        "MyStruct",
        [
            new_struct_field("SerialNumber", ua.VariantType.String),
        ],
    )

    # The second MyStruct triggers a "Browsename collision" warning:
    # it is registered in the NodeId-keyed lookup dicts but not as ua.MyStruct
    custom_types = await server.load_data_type_definitions()

    print("ua.MyStruct is bound to the first registered type:", ua.MyStruct, ua.MyStruct.data_type)

    # The dict returned by load_data_type_definitions is keyed by name,
    # so one colliding type shadows the other there as well
    print("load_data_type_definitions returned a single 'MyStruct':", custom_types["MyStruct"])

    # ua.get_type resolves by DataType NodeId and works for both
    type_a = ua.get_type(node_a.nodeid)
    type_b = ua.get_type(node_b.nodeid)
    print("Type in lineA namespace:", type_a, type_a.data_type)
    print("Type in lineB namespace:", type_b, type_b.data_type)

    async with server:
        # Encoding is NodeId-keyed, so the type that lost the name round-trips fine
        var = await server.nodes.objects.add_variable(
            idx_b,
            "my_struct_b",
            ua.Variant(type_b(SerialNumber="SN-1234"), ua.VariantType.ExtensionObject),
        )
        value = await var.read_value()
        print("Read back:", value, type(value))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
