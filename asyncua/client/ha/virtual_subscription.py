from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from sortedcontainers import SortedDict  # type: ignore

from asyncua import ua

TypeSubHandler = Any


@dataclass(frozen=True)
class NodeAttr:
    attr: ua.AttributeIds | None = None
    queuesize: int = 0


@dataclass
class VirtualSubscription:
    period: int
    handler: TypeSubHandler
    publishing: bool
    monitoring: ua.MonitoringMode
    # type annotation (not supported yet): Sorteddict[str, NodeAttr]
    # see: https://github.com/grantjenks/python-sortedcontainers/pull/107
    nodes: SortedDict = field(default_factory=SortedDict)

    def subscribe_data_change(self, nodes: Iterable[str], attr: ua.AttributeIds, queuesize: int) -> None:
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

    def get_nodes(self) -> set[str]:
        return set(self.nodes)
