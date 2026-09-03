from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable

from .arc import Arc
from .node import Node


@dataclass(slots=True)
class Network:
    """Validated directed network for an uncapacitated min-cost flow problem."""

    nodes: dict[Hashable, Node]
    arcs: dict[Hashable, Arc]

    def __init__(self, nodes: Iterable[Node], arcs: Iterable[Arc]) -> None:
        node_list = list(nodes)
        arc_list = list(arcs)
        self.nodes = {node.id: node for node in node_list}
        self.arcs = {arc.id: arc.copy() for arc in arc_list}
        if len(self.nodes) != len(node_list):
            raise ValueError("Duplicate node identifiers are not allowed.")
        if len(self.arcs) != len(arc_list):
            raise ValueError("Duplicate arc identifiers are not allowed.")
        self._validate()

    def _validate(self) -> None:
        if not self.nodes:
            raise ValueError("A network needs at least one node.")
        if abs(sum(node.balance for node in self.nodes.values())) > 1e-9:
            raise ValueError("Node balances must sum to zero.")
        if len(self.arcs) == 0 and len(self.nodes) > 1:
            raise ValueError("A multi-node network needs arcs.")
        for arc in self.arcs.values():
            if arc.tail not in self.nodes or arc.head not in self.nodes:
                raise ValueError(f"Arc {arc.id!r} references an unknown node.")
            if arc.tail == arc.head:
                raise ValueError("Self-loops are not supported.")
            if arc.flow < 0:
                raise ValueError("Initial flows must be non-negative.")

    def copy(self) -> "Network":
        return Network(self.nodes.values(), self.arcs.values())
