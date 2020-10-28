from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Set
from asyncua import ua
from sortedcontainers import SortedDict


TypeSubHandler = Any


@dataclass(frozen=True)
class NodeAttr:
    attr: Optional[ua.AttributeIds] = None
    queuesize: int = 0


@dataclass
class VirtualSubscription:
    period: int
    handler: TypeSubHandler
    publishing: bool
    monitoring: ua.MonitoringMode
    # full type: SortedDict[str, NodeAttr]
    nodes: SortedDict = field(default_factory=SortedDict)

    def subscribe_data_change(
        self, nodes: Iterable[str], attr: ua.AttributeIds, queuesize: int
    ) -> None:
        for node in nodes:
            self.nodes[node] = NodeAttr(attr, queuesize)

    def unsubscribe(self, nodes: Iterable[str]) -> None:
        for node in nodes:
            if self.nodes.get(node):
                self.nodes.pop(node)

    def set_monitoring_mode(self, mode: ua.MonitoringMode) -> None:
        self.monitoring = mode

    def set_publishing_mode(self, mode: bool) -> None:
        self.publishing = mode

    def get_nodes(self) -> Set[str]:
        return set(self.nodes)
