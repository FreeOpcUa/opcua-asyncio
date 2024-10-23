"""
In the following you will find examples for the use of the
classes UaFile and UaDirectory and how to handle typical uaerrors.
see: ./asyncua/client/ua_file_transfer.py.

The two classes are close to OPC UA File Transfer. This means they
have to be operated "OPC UA typical" and not "Python typical".
The advantage of this case is, that you can use the maximum
range of functions of OPC UA File Transfer.
See: https://reference.opcfoundation.org/Core/docs/Part5/C.1/

IMPORTANT NOTE:
In order to to test the functions from UaFile and UaDiretory,
you need an OPC UA server that offers the required File Transfer functionality.
However, in this project there is currently no demo server containing
file transfer capabilities.
"""

import asyncio
import logging

from asyncua import Client
from asyncua.client.ua_file_transfer import UaFile, UaDirectory
from asyncua.ua import OpenFileMode
from asyncua.ua import uaerrors

_logger = logging.getLogger("asyncua")


async def task():
    """All communication takes place within this task.
    For the sake of simplicity, all (OPC UA) calls are executed purely sequentially.
    """
    url = "opc.tcp://localhost:4840/freeopcua/server/"

    async with Client(url=url) as client:
        uri = "http://examples.freeopcua.github.io"
        idx = await client.get_namespace_index(uri)

        remote_file_system = await client.nodes.objects.get_child([f"{idx}:FileSystem"])
        remote_file_name = "test.txt"
        remote_file_node = await remote_file_system.get_child([f"{idx}:{remote_file_name}"])

        # Read file from server
        remote_file_content = None
        async with UaFile(remote_file_node, OpenFileMode.Read.value) as remote_file:
            remote_file_content = await remote_file.read()
        print("File content:")
        print(remote_file_content, end="\n\n")

        # Create file on server
        new_file_name = "new_file.txt"
        ua_dir = UaDirectory(remote_file_system)
        try:
            await ua_dir.create_file(new_file_name, False)
        except uaerrors.BadBrowseNameDuplicated:
            _logger.warning("=> File '%s' already exists on server.", new_file_name)

        # Write to file on server
        file_content = ("I am a random file\n" * 3).encode("utf-8")
        # In order to write to a file, it must already exist on the target system. (OPC UA typical)
        remote_file_node = await remote_file_system.get_child(f"{uri}:{new_file_name}")
        # In order to write to a file, you need the OpenFileModes "Write"
        # and one of the following "Append" or "EraseExisting". (OPC UA typical too)
        async with UaFile(remote_file_node, OpenFileMode.Write + OpenFileMode.EraseExisting) as remote_file:
            await remote_file.write(file_content)

        # Append to file on server
        file_content = ("I am appended text\n" * 3).encode("utf-8")
        remote_file_node = await remote_file_system.get_child(f"{uri}:{new_file_name}")
        async with UaFile(remote_file_node, OpenFileMode.Write + OpenFileMode.Append) as remote_file:
            await remote_file.write(file_content)

        # Get size of remote file
        file_size = await UaFile(remote_file_node).get_size()
        print(f"Size of file node '{remote_file_node}' = {file_size} byte")

        # Delete file from server
        try:
            await ua_dir.delete(remote_file_node.nodeid)
        except uaerrors.BadNotFound:
            _logger.warning("File %s not found on server.", remote_file_node)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(task())
