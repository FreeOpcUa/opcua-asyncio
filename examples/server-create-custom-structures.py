from asyncua import ua, Server
from asyncua.common.type_dictionary_buider import DataTypeDictionaryBuilder, get_ua_class
from IPython import embed


class DemoServer:

    def __init__(self):
        self.server = Server()

        self.server.set_endpoint('opc.tcp://0.0.0.0:51210/UA/SampleServer')
        self.server.set_server_name('Custom structure demo server')
        # idx name will be used later for creating the xml used in data type dictionary
        self._idx_name = 'http://examples.freeopcua.github.io'
        self.idx = self.server.register_namespace(self._idx_name)

        self.dict_builder = DataTypeDictionaryBuilder(self.server, self.idx, self._idx_name, 'MyDictionary')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        quit()

    def start_server(self):
        self.server.start()

    def create_structure(self, name):
        # save the created data type
        return self.dict_builder.create_data_type(name)

    def complete_creation(self):
        self.dict_builder.set_dict_byte_string()


if __name__ == '__main__':

    with DemoServer() as ua_server:
        # add one basic structure
        basic_struct_name = 'basic_structure'
        basic_struct = ua_server.create_structure(basic_struct_name)
        basic_struct.add_field('ID', ua.VariantType.Int32)
        basic_struct.add_field('Gender', ua.VariantType.Boolean)
        basic_struct.add_field('Comments', ua.VariantType.String)

        # add an advance structure which uses our basic structure
        nested_struct_name = 'nested_structure'
        nested_struct = ua_server.create_structure(nested_struct_name)
        nested_struct.add_field('Name', ua.VariantType.String)
        nested_struct.add_field('Surname', ua.VariantType.String)
        # add simple structure as field
        nested_struct.add_field('Stuff', basic_struct)

        # this operation will write the OPC dict string to our new data type dictionary
        # namely the 'MyDictionary'
        ua_server.complete_creation()

        # get the working classes
        ua_server.server.load_type_definitions()

        # Create one test structure
        basic_var = ua_server.server.nodes.objects.add_variable(ua.NodeId(namespaceidx=ua_server.idx), 'BasicStruct',
                                                                ua.Variant(None, ua.VariantType.Null),
                                                                datatype=basic_struct.data_type)

        basic_var.set_writable()
        basic_msg = get_ua_class(basic_struct_name)()
        basic_msg.ID = 3
        basic_msg.Gender = True
        basic_msg.Comments = 'Test string'
        basic_var.write(basic_msg)

        # Create one advance test structure
        nested_var = ua_server.server.nodes.objects.add_variable(ua.NodeId(namespaceidx=ua_server.idx), 'NestedStruct',
                                                                 ua.Variant(None, ua.VariantType.Null),
                                                                 datatype=nested_struct.data_type)

        nested_var.set_writable()
        nested_msg = get_ua_class(nested_struct_name)()
        nested_msg.Stuff = basic_msg
        nested_msg.Name = 'Max'
        nested_msg.Surname = 'Karl'
        nested_var.write(nested_msg)

        ua_server.start_server()

        # see the xml value in our customized dictionary 'MyDictionary', only for debugging use
        print(getattr(ua_server.dict_builder, '_type_dictionary').get_dict_value())

        # values can be write back and retrieved with the codes below.
        basic_result = basic_var.read()
        nested_result = nested_var.read()

        embed()
