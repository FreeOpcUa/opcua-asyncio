'''
    top level of PubSub, similar to the Client/Server
'''
import asyncio
from typing import List, Optional
from asyncua.ua import String, PubSubConfigurationDataType
from .dataset import PublishedDataSet
from .connection import PubSubConnection


class PubSub(PubSubInformationModel):
    '''
    Top Level PubSub Entry. Manages DataSets and Connections.
    """

    def __init__(
        self, cfg: PubSubConfigurationDataType = None, server: Server = None
    ) -> None:
        super().__init__()
        self._running = False
        self._pds: List[PublishedDataSet] = []
        self._con: List[PubSubConnection] = []
        self._enabled = False
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
        if self._node is None:
            self._node = self._server.get_node(NodeId(ObjectIds.PublishSubscribe))
            await self._init_node(self._node, self._server)
            for pds in self._pds:
                await pds._init_information_model(
                    await self._node.get_child("0:PublishedDataSets"), self._server
                )
            for con in self._con:
                await con._init_information_model(self._server)

    def get_config(self) -> PubSubConfigurationDataType:
        '''
        Returns the PubSub Configuration.
        '''
        return PubSubConfigurationDataType(
            [pds.get_config() for pds in self._pds],
            [c.get_config() for c in self._con],
            self._enabled
        )

    def add_published_dataset(self, pds: PublishedDataSet) -> None:
        self._pds.append(pds)

    async def add_connection(self, con: PubSubConnection) -> None:
        con.set_if(self)
        self._con.append(con)

    def get_connection(self, name: String) -> Optional[PubSubConnection]:
        return next((c for c in self._con if c._cfg.Name == name), None)

    def get_published_dataset(self, name: String) -> Optional[PublishedDataSet]:
        return next((pds for pds in self._pds if pds.Name == name), None)

    def remove_published_dataset(self, name: String) -> None:
        elm = self.get_published_dataset(name)
        if elm is None:
            raise ValueError(f"Unkown Published Dataset {name}")
        else:
            del elm

    def remove_connection(self, name: String) -> None:
        elm = self.get_connection(name)
        if elm is None:
            raise ValueError(f"Unkown Connection {name}")
        else:
            del elm

    async def start(self) -> None:
        '''
        Starts the pubsub applications. All writer and reader will publish and subscripe message from now on.
        """
        if not self._running:
            self._enabled = True
            await self._set_state(PubSubState.Operational)
            await asyncio.wait([asyncio.create_task(t.start()) for t in self._con])
            self._running = True

    async def stop(self) -> None:
        '''
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
