import logging
import asyncio

from asyncua import ua, Server
from asyncua.common.type_dictionary_builder import DataTypeDictionaryBuilder


async def main():
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/UA/SampleServer')
    server.set_server_name('Custom structure demo server')

    # idx name will be used later for creating the xml used in data type dictionary
    url = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(url)

    dict_builder = DataTypeDictionaryBuilder(server, idx, url, 'MyDictionary')
    await dict_builder.init()

    # add one basic structure
    basic_struct_name = 'BasicStructure'
    basic_struct = await dict_builder.create_data_type(basic_struct_name)
    basic_struct.add_field('ID', ua.VariantType.Int32)
    basic_struct.add_field('Gender', ua.VariantType.Boolean)
    basic_struct.add_field('Comments', ua.VariantType.String)

    # add an advance structure which uses our basic structure
    nested_struct_name = 'NestedStructure'
    nested_struct = await dict_builder.create_data_type(nested_struct_name)
    nested_struct.add_field('Name', ua.VariantType.String)
    nested_struct.add_field('Surname', ua.VariantType.String)
    # add a list of simple structure as field
    nested_struct.add_field('StuffArray', basic_struct, is_array=True)

    # this operation will write the OPC dict string to our new data type dictionary
    # namely the 'MyDictionary'

    await dict_builder.set_dict_byte_string()

    # get the working classes
    await server.load_type_definitions()


    # Create one test structure in our address space
    basic_var = await server.nodes.objects.add_variable(
        idx,
        'BasicStruct',
        None,
        datatype=basic_struct.data_type,
    )

    await basic_var.set_writable()
    var = ua.BasicStructure()
    var.ID = 3
    var.Gender = True
    var.Comments = 'Test string'
    await basic_var.write_value(var)

    # Create one advance test structure
    nested_var = await server.nodes.objects.add_variable(
        idx,
        'NestedStruct',
        None,
        datatype=nested_struct.data_type,
    )

    await nested_var.set_writable()
    var2 = ua.NestedStructure()
    var2.StuffArray = [var, var]
    var2.Name = 'Max'
    var2.Surname = 'Karl'
    await nested_var.write_value(var2)

    async with server:
        # see the xml value in our customized dictionary 'MyDictionary', only for debugging use
        print(getattr(dict_builder, '_type_dictionary').get_dict_value())

        # values can be write back and retrieved with the codes below.
        v1 = await basic_var.read_value()
        v2 = await nested_var.read_value()

        #embed()
        while True:
            await asyncio.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
