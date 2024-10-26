"""
Low level implementation of OPC UA File Transfer.
This module contains the mandatory functionality specified
by the OPC Foundation.

See also:
OPC 10000-5: OPC Unified Architecture V1.04
Part 5: Information Model - Annex C (normative) File Transfer
https://reference.opcfoundation.org/Core/docs/Part5/C.1/
"""

import logging
from typing import Tuple

from asyncua.common.node import Node
from asyncua.ua import NodeId, OpenFileMode, Variant, VariantType


_logger = logging.getLogger(__name__)


class UaFile:
    """
    Provides the functionality to work with "C.2 FileType".
    """

    def __init__(self, file_node: Node, open_mode: OpenFileMode = OpenFileMode.Read.value):
        """
        Initializes a new instance of the UaFile class.
        :param file_node: The node of the file to open.
        :param open_mode: The open mode, see: asyncua.ua.OpenFileMode.
        """
        self._file_node = file_node
        self._open_mode = open_mode

        self._file_handle = None
        self._read_node = None
        self._write_node = None
        self._get_position_node = None
        self._set_position_node = None

    async def __aenter__(self):
        await self.open(self._open_mode)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self.close()

    async def open(self, open_mode: OpenFileMode = None) -> None:
        """
        Open is used to open a file represented by an Object of FileType.
        The open mode of OPC UA differs significantly from the
        python build-in functionality.
        => See the OPC UA specification for more information.
        :param open_mode: Open mode defined in C.2.1.
        :return: The file handle.
        """
        _logger.debug("Request to open file %s in mode: %s", self._file_node, OpenFileMode)
        open_node = await self._file_node.get_child("Open")
        arg1_mode = Variant(open_mode or self._open_mode, VariantType.Byte)
        self._file_handle = await self._file_node.call_method(open_node, arg1_mode)

    async def close(self) -> None:
        """
        Close is used to close a file represented by a FileType.
        When a client closes a file the handle becomes invalid.
        """
        _logger.debug("Request to close file %s", self._file_node)
        read_node = await self._file_node.get_child("Close")
        arg1_file_handle = Variant(self._file_handle, VariantType.UInt32)
        await self._file_node.call_method(read_node, arg1_file_handle)

    async def read(self) -> bytes:
        """
        Read is used to read a part of the file starting from the current file position.
        The file position is advanced by the number of bytes read.
        :return: Contains the returned data of the file.
        If the ByteString is empty it indicates that the end of the file is reached.
        """
        _logger.debug("Request to read from file %s", self._file_node)
        size = await self.get_size()
        if self._read_node is None:
            self._read_node = await self._file_node.get_child("Read")
        arg1_file_handle = Variant(self._file_handle, VariantType.UInt32)
        arg2_length = Variant(size, VariantType.Int32)
        return await self._file_node.call_method(self._read_node, arg1_file_handle, arg2_length)

    async def write(self, data: bytes) -> None:
        """
        Write is used to write a part of the file starting from the current file position.
        The file position is advanced by the number of bytes written.
        :param data: Contains the data to be written at the position of the file.
        It is server-dependent whether the written data are persistently
        stored if the session is ended without calling the Close Method with the fileHandle.
        Writing an empty or null ByteString returns a Good result code without any
        effect on the file.
        """
        _logger.debug("Request to write to file %s", self._file_node)
        if self._write_node is None:
            self._write_node = await self._file_node.get_child("Write")
        arg1_file_handle = Variant(self._file_handle, VariantType.UInt32)
        arg2_data = Variant(data, VariantType.ByteString)
        await self._file_node.call_method(self._write_node, arg1_file_handle, arg2_data)

    async def get_position(self) -> int:
        """
        GetPosition is used to provide the current position of the file handle.
        :return: The position of the fileHandle in the file.
        If a Read or Write is called it starts at that position.
        """
        _logger.debug("Request to get position from file %s", self._file_node)
        if self._get_position_node is None:
            self._get_position_node = await self._file_node.get_child("GetPosition")
        arg1_file_handle = Variant(self._file_handle, VariantType.UInt32)
        return await self._file_node.call_method(self._get_position_node, arg1_file_handle)

    async def set_position(self, position: int) -> None:
        """
        SetPosition is used to set the current position of the file handle.
        :param position: The position to be set for the fileHandle in the file.
        If a Read or Write is called it starts at that position.
        If the position is higher than the file size the position is set to the end of the file.
        """
        _logger.debug("Request to set position in file %s", self._file_node)
        if self._set_position_node is None:
            self._set_position_node = await self._file_node.get_child("SetPosition")
        arg1_file_handle = Variant(self._file_handle, VariantType.UInt32)
        arg2_position = Variant(position, VariantType.UInt64)
        return await self._file_node.call_method(self._set_position_node, arg1_file_handle, arg2_position)

    async def get_size(self) -> int:
        """
        Size defines the size of the file in Bytes.
        When a file is opened for write the size might not be accurate.
        :return: The size of the file in Bytes.
        """
        _logger.debug("Request to get size of file %s", self._file_node)
        size_node = await self._file_node.get_child("Size")
        return await size_node.read_value()

    async def get_writable(self) -> bool:
        """
        Writable indicates whether the file is writable.
        It does not take any user access rights into account, i.e. although the file
        is writable this may be restricted to a certain user / user group.
        The Property does not take into account whether the file is currently
        opened for writing by another client and thus currently locked and not writable by others.
        :return:
        """
        _logger.debug("Request to get writable of file %s", self._file_node)
        writable_node = await self._file_node.get_child("Writable")
        return await writable_node.read_value()

    async def get_user_writable(self) -> bool:
        """
        UserWritable indicates whether the file is writable taking user access rights into account.
        The Property does not take into account whether the file is currently opened
        for writing by another client and thus currently locked and not writable by others.
        :return: Indicates whether the file is writable taking user access rights into account
        """
        _logger.debug("Request to get user writable of file %s", self._file_node)
        user_writable_node = await self._file_node.get_child("UserWritable")
        return await user_writable_node.read_value()

    async def get_open_count(self):
        """
        OpenCount indicates the number of currently valid file handles on the file.
        :return: Amount of currently valid file handles on the file
        """
        _logger.debug("Request to get open count of file %s", self._file_node)
        open_count_node = await self._file_node.get_child("OpenCount")
        return await open_count_node.read_value()


class UaDirectory:
    """
    Provides the functionality to work with "C.3 File System".
    """

    def __init__(self, directory_node):
        self._directory_node = directory_node

    async def create_directory(self, directory_name: str) -> NodeId:
        """
        CreateDirectory is used to create a new FileDirectoryType Object organized by this Object.
        :param directory_name: The name of the directory to create.
        The name is used for the BrowseName and DisplayName of the directory object and also
        for the directory in the file system.
        For the BrowseName, the directoryName is used for the name part of the QualifiedName.
        The namespace index is Server specific.
        For the DisplayName, the directoryName is used for the text part of the LocalizedText.
        The locale part is Server specific.
        :return: The NodeId of the created directory Object.
        """
        _logger.debug("Request to create directory %s in %s", directory_name, self._directory_node)
        create_directory_node = await self._directory_node.get_child("CreateDirectory")
        arg1_directory_name = Variant(directory_name, VariantType.String)
        return await self._directory_node.call_method(create_directory_node, arg1_directory_name)

    async def create_file(self, file_name: str, request_file_open: bool) -> Tuple[NodeId, int]:
        """
        CreateFile is used to create a new FileType Object organized by this Object.
        The created file can be written using the Write Method of the FileType.
        :param file_name: The name of the file to create. The name is used for the
        BrowseName and DisplayName of the file object and also for the file in the
        file system.
        For the BrowseName, the fileName is used for the name part of the QualifiedName.
        The namespace index is Server specific. For the DisplayName, the fileName is
        used for the text part of the LocalizedText. The locale part is Server specific.
        :param request_file_open: Flag indicating if the new file should be opened
        with the Write and Read bits set in the open mode after the creation of the file.
        If the flag is set to True, the file is created and opened for writing.
        If the flag is set to False, the file is just created.
        :return: The NodeId of the created file Object.
        The fileHandle is returned if the requestFileOpen is set to True.
        The fileNodeId and the fileHandle can be used to access the new file
        through the FileType Object representing the new file.
        If requestFileOpen is set to False, the returned value shall be 0
        and shall be ignored by the caller.
        """
        _logger.debug("Request to create file %s in %s", file_name, self._directory_node)
        print(f"Request to create file {file_name} in {self._directory_node}")
        create_file_node = await self._directory_node.get_child("CreateFile")
        arg1_file_name = Variant(file_name, VariantType.String)
        arg2_request_file_open = Variant(request_file_open, VariantType.Boolean)
        return await self._directory_node.call_method(create_file_node, arg1_file_name, arg2_request_file_open)

    async def delete(self, object_to_delete: NodeId) -> None:
        """
        Delete is used to delete a file or directory organized by this Object.
        :param object_to_delete: The NodeId of the file or directory to delete.
        In the case of a directory, all file and directory Objects below the
        directory to delete are deleted recursively.
        """
        _logger.debug("Request to delete file %s from %s", object_to_delete, self._directory_node)
        delete_node = await self._directory_node.get_child("Delete")
        await self._directory_node.call_method(delete_node, object_to_delete)

    async def move_or_copy(
        self, object_to_move_or_copy: NodeId, target_directory: NodeId, create_copy: bool, new_name: str
    ) -> NodeId:
        """
        MoveOrCopy is used to move or copy a file or directory organized by this Object
        to another directory or to rename a file or directory.
        :param object_to_move_or_copy: The NodeId of the file or directory to move or copy.
        :param target_directory: The NodeId of the target directory of the move or copy command.
        If the file or directory is just renamed, the targetDirectory matches the ObjectId
        passed to the method call.
        :param create_copy: A flag indicating if a copy of the file or directory should be
        created at the target directory.
        :param new_name: The new name of the file or directory in the new location.
        If the string is empty, the name is unchanged.
        :return: The NodeId of the moved or copied object. Even if the Object is moved,
        the Server may return a new NodeId.
        """
        _logger.debug(
            "Request to %s%s file system object %s from %s to %s, new name=%s",
            "" if create_copy else "move",
            "copy" if create_copy else "",
            object_to_move_or_copy,
            self._directory_node,
            target_directory,
            new_name,
        )
        move_or_copy_node = await self._directory_node.get_child("MoveOrCopy")
        arg3_create_copy = Variant(create_copy, VariantType.Boolean)
        arg4_new_name = Variant(new_name, VariantType.String)
        return await self._directory_node.call_method(
            move_or_copy_node, object_to_move_or_copy, target_directory, arg3_create_copy, arg4_new_name
        )
