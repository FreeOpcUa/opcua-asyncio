from asyncua import ua

class UaFile:
    def __init__(self, file_node):
        self._file_node = file_node

    async def read_file(self):
        """
        :param file_node: node of file object (e.g. node = client.get_node("ns=2;s=nameOfNode")
        """
        handle = await self._open_file(ua.OpenFileMode.Read.value)
        size = await self._get_file_size()

        read_node = await self._file_node.get_child("Read")
        arg1 = ua.Variant(handle, ua.VariantType.UInt32)
        arg2 = ua.Variant(size, ua.VariantType.Int32)
        contents = await self._file_node.call_method(read_node, arg1, arg2)
        await self._close_file(handle)
        return contents

    async def _open_file(self, open_mode):
        """ open file method """
        open_node = await self._file_node.get_child("Open")
        arg = ua.Variant(open_mode, ua.VariantType.Byte)
        return await self._file_node.call_method(open_node, arg)

    async def _get_file_size(self):
        """ gets size of file """
        size_node = await self._file_node.get_child("Size")
        return await size_node.read_value()

    async def _close_file(self, handle):
        """ close file method """
        read_node = await self._file_node.get_child("Close")
        arg1 = ua.Variant(handle, ua.VariantType.UInt32)
        return await self._file_node.call_method(read_node, arg1)
