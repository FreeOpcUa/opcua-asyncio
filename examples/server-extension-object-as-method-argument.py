from asyncua import Server, ua, uamethod
import asyncio


async def main():
    @uamethod
    async def callback(parent, in_extobj):
        out_extobj = ua.uaprotocol_auto.AxisInformation()  # get new instanace of AxisInformation
        out_extobj.EngineeringUnits = in_extobj.EngineeringUnits
        out_extobj.EURange.Low = in_extobj.EURange.Low
        out_extobj.EURange.High = in_extobj.EURange.High
        out_extobj.Title = in_extobj.Title
        out_extobj.AxisScaleType = in_extobj.AxisScaleType
        out_extobj.AxisSteps = in_extobj.AxisSteps

        await axis_info.set_value(out_extobj)  # write values to variable

        ret = (ua.Variant(out_extobj, ua.VariantType.ExtensionObject), ua.Variant("test", ua.VariantType.String))

        return ret

    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    obj = server.get_objects_node()
    idx = await server.register_namespace("http://examples.freeopcua.github.io")

    await server.load_data_type_definitions()

    inarg_extobj = ua.Argument()
    inarg_extobj.Name = "In"
    inarg_extobj.DataType = ua.NodeId(12079, 0)
    inarg_extobj.ValueRank = -1
    inarg_extobj.ArrayDimensions = []
    inarg_extobj.Description = ua.LocalizedText("Wanted AxisInformation")

    outarg_extobj = ua.Argument()
    outarg_extobj.Name = "Out"
    outarg_extobj.DataType = ua.NodeId(12079, 0)
    outarg_extobj.ValueRank = -1
    outarg_extobj.ArrayDimensions = []
    outarg_extobj.Description = ua.LocalizedText("Actual AxisInformation")

    status = ua.Argument()
    status.Name = "Status"
    status.DataType = ua.NodeId(12, 0)
    status.ValueRank = -1
    status.ArrayDimensions = []
    status.Description = ua.LocalizedText("MSG")

    method_parent = await obj.add_object(idx, "Methods")
    method_node = await method_parent.add_method(
        idx, "SetAxisInformation", callback, [inarg_extobj], [outarg_extobj, status]
    )

    # add a variable of type AxisInformation
    axis_info = await obj.add_variable(
        idx, "AxisInformation", ua.uaprotocol_auto.AxisInformation(), varianttype=ua.VariantType.ExtensionObject
    )

    async with server:
        while 1:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
