"""
top level of PubSub, similar to the Client/Server
"""

from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING, Union

import aiofiles

from ..common.utils import Buffer
from ..ua import String, PubSubConfigurationDataType
from ..ua.object_ids import ObjectIds
from ..ua.uaerrors import BadInvalidArgument, UaError
from ..ua.ua_binary import extensionobject_from_binary, to_binary
from ..ua.uaprotocol_auto import PubSubState, UABinaryFileDataType
from ..ua.uatypes import NodeId, Variant

from .dataset import PublishedDataSet
from .connection import PubSubConnection
from .information_model import PubSubInformationModel

if TYPE_CHECKING:
    from ..server.server import Server

logger = logging.getLogger(__name__)


class PubSub(PubSubInformationModel):
    """
    Top Level PubSub Entry. Manages DataSets and Connections.
    """

    def __init__(self, cfg: PubSubConfigurationDataType = None, server: Server = None) -> None:
        super().__init__()
        self._running = False
        self._pds: List[PublishedDataSet] = []
        self._con: List[PubSubConnection] = []
        self._enabled = False
        self._server = server
        self._node = None
        if cfg is not None:
            self._pds = [PublishedDataSet(pds) for pds in cfg.PublishedDataSets]
            self._con = [PubSubConnection(c) for c in cfg.Connections]

    @classmethod
    def new(
        cls,
        connections: Optional[List[PubSubConnection]] = None,
        datasets: Optional[List[PublishedDataSet]] = None,
    ):
        o = cls()
        if connections is not None:
            o._con = connections
        if datasets is not None:
            o._pds = datasets
        return o

    async def init_information_model(self) -> None:
        """
        Inits the Information Model
        """
        if self._server is None:
            raise RuntimeError("Server is not initialized")
        if self._node is None:
            self._node = self._server.get_node(NodeId(ObjectIds.PublishSubscribe))
            await self._init_node(self._node, self._server)
        node = self._node
        if node is None:
            raise RuntimeError("Node is not initialized")
        published_data_sets_node = await node.get_child("0:PublishedDataSets")
        for pds in self._pds:
            await pds._init_information_model(published_data_sets_node, self._server)
            for con in self._con:
                await con._init_information_model(self._server)

    def get_config(self) -> PubSubConfigurationDataType:
        """
        Returns the PubSub Configuration.
        """
        return PubSubConfigurationDataType(
            [pds.get_config() for pds in self._pds],
            [c.get_config() for c in self._con],
            self._enabled,
        )

    async def add_published_dataset(self, pds: PublishedDataSet) -> None:
        self._pds.append(pds)
        if self._node is not None:
            await pds._init_information_model(self._node, self._server)

    async def add_connection(self, con: PubSubConnection) -> None:
        con.set_if(self)
        self._con.append(con)
        if self._node is not None:
            await con._init_information_model(self._server)

    def get_connection(self, name: String) -> Optional[PubSubConnection]:
        print([c._cfg.Name for c in self._con])
        return next((c for c in self._con if c._cfg.Name == name), None)

    def get_published_dataset(self, name: String) -> Optional[PublishedDataSet]:
        return next((pds for pds in self._pds if pds.get_name() == name), None)

    async def remove_published_dataset(self, name: String) -> None:
        elm = self.get_published_dataset(name)
        if elm is None:
            raise ValueError(f"Unknown Published Dataset {name}")
        else:
            if self._node is not None:
                elm._node.delete()
            del elm

    async def remove_connection(self, name: String) -> None:
        elm = self.get_connection(name)
        if elm is None:
            raise ValueError(f"Unknown Connection {name}")
        else:
            del elm
            if self._node is not None:
                elm._node.delete()

    async def start(self) -> None:
        """
        Starts the pubsub applications. All writer and reader will publish and subscribe message from now on.
        """
        if not self._running:
            self._enabled = True
            await self._set_state(PubSubState.Operational)
            await asyncio.wait([asyncio.create_task(t.start()) for t in self._con])
            self._running = True

    async def stop(self) -> None:
        """
        Stops the pubsub application.
        """
        if self._running:
            self._enabled = False
            await self._set_state(PubSubState.Disabled)
            await asyncio.wait([asyncio.create_task(t.stop()) for t in self._con])
            self._running = False

    async def __aenter__(self) -> None:
        await self.start()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    async def load_binary_file(self, file: Union[str, Path]) -> None:
        async with aiofiles.open(file, mode="rb") as f:
            buf = Buffer(await f.read())
        # ex_obj = extensionobject_from_binary(buf)
        ex_obj: UABinaryFileDataType = extensionobject_from_binary(buf)
        if ex_obj.data_type == UABinaryFileDataType.data_type:
            ex_obj = ex_obj.Body.Value
            if isinstance(ex_obj, PubSubConfigurationDataType):
                cfg: PubSubConfigurationDataType = ex_obj
                # When loading a configuration file, it should replace any existing
                # datasets or connections rather than append to the current state.
                # Previous runs may have populated ``self._pds`` and ``self._con``
                # via ``server.get_pubsub()``, so make sure we start from a clean
                # slate before instantiating objects from the file.
                self._pds.clear()
                self._con.clear()
                self._enabled = cfg.Enabled
                for ds in cfg.PublishedDataSets:
                    await self.add_published_dataset(PublishedDataSet(ds))
                for con in cfg.Connections:
                    await self.add_connection(PubSubConnection(con))
                return
            else:
                logger.error("File has ExtensionObject of type: %s instead of UABinaryFileDataType", ex_obj)
        else:
            logger.error("File has ExtensionObject of type: %s instead of UABinaryFileDataType", ex_obj)
        raise UaError(BadInvalidArgument)

    async def save_binary_file(self, file: Union[str, Path]) -> None:  # @TODO save structs and enums, namespaces
        cfg = PubSubConfigurationDataType(
            [pds._data for pds in self._pds], [con._cfg for con in self._con], self._enabled
        )
        data = to_binary(UABinaryFileDataType, UABinaryFileDataType(Body=Variant(cfg)))
        async with aiofiles.open(file, mode="wb") as f:
            await f.write(data)
