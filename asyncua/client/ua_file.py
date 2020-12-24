from asyncua import ua


class UaFile:

    def __init__(self, file_node):
        self._file_node = file_node
        self._handle = None

    async def open(self, open_mode):
        """ open file method """
        open_node = await self._file_node.get_child("Open")
        arg = ua.Variant(open_mode, ua.VariantType.Byte)
        return await self._file_node.call_method(open_node, arg)

    async def close(self):
        """ close file method """
        read_node = await self._file_node.get_child("Close")
        arg1 = ua.Variant(self._handle, ua.VariantType.UInt32)
        return await self._file_node.call_method(read_node, arg1)


class UaFileRead(UaFile):
    def __init__(self, file_node):
        super().__init__(file_node)

    async def __aenter__(self):
        self._handle = await self.open(ua.OpenFileMode.Read.value)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self.close()

    async def read(self):
        """ reads file contents """
        size = await self.get_size()
        read_node = await self._file_node.get_child("Read")
        arg1 = ua.Variant(self._handle, ua.VariantType.UInt32)
        arg2 = ua.Variant(size, ua.VariantType.Int32)
        return await self._file_node.call_method(read_node, arg1, arg2)

    async def get_size(self):
        """ gets size of file """
        size_node = await self._file_node.get_child("Size")
        return await size_node.read_value()

