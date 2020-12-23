from asyncua import ua


class UaFile:

    def __init__(self, file_node):
        self._file_node = file_node

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return exc_type is None

    async def open(self, open_mode):
        """ open file method """
        open_node = await self._file_node.get_child("Open")
        arg = ua.Variant(open_mode, ua.VariantType.Byte)
        return await self._file_node.call_method(open_node, arg)

    async def get_size(self):
        """ gets size of file """
        size_node = await self._file_node.get_child("Size")
        return await size_node.read_value()

    async def close(self, handle):
        """ close file method """
        read_node = await self._file_node.get_child("Close")
        arg1 = ua.Variant(handle, ua.VariantType.UInt32)
        return await self._file_node.call_method(read_node, arg1)

    async def read(self, handle, size):
        """
        :param handle: handle from open()
        :param size: size of file from from get_size()
        """
        read_node = await self._file_node.get_child("Read")
        arg1 = ua.Variant(handle, ua.VariantType.UInt32)
        arg2 = ua.Variant(size, ua.VariantType.Int32)
        return await self._file_node.call_method(read_node, arg1, arg2)

    async def read_once(self):
        """ open, read, close in one operation """
        handle = await self.open(ua.OpenFileMode.Read.value)
        size = await self.get_size()
        contents = await self.read(handle, size)
        await self.close(handle)
        return contents
