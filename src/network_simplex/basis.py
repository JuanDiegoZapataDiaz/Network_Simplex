from __future__ import annotations

from collections import deque
from typing import Hashable, Iterable

from .arc import Arc


class Basis:
    """The spanning-tree basis used by the primal Network Simplex method."""

    def __init__(self, node_ids: Iterable[Hashable], arc_ids: Iterable[Hashable], arcs: dict[Hashable, Arc]) -> None:
        self.node_ids = set(node_ids)
        self.arc_ids = set(arc_ids)
        self.arcs = arcs
        self._validate_tree()

    def _validate_tree(self) -> None:
        # H1:  exactly |V|-1 arcs
        if len(self.arc_ids) != len(self.node_ids) - 1:
            raise ValueError("A basis must contain |V| - 1 arcs.")
        # H2: connected graph 
        if not self.node_ids:
            return
        seen = {next(iter(self.node_ids))}
        queue = deque(seen)
        adjacency = self._adjacency()
        while queue:
            node = queue.popleft()
            for neighbor, _ in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        if seen != self.node_ids:
            raise ValueError("Basis arcs must form a connected tree.")
        # Theorem: if a digraph stisfy H1 + H2 -> there is no cycles in de Digraph
    def _adjacency(self) -> dict[Hashable, list[tuple[Hashable, Hashable]]]:
        adjacency = {node: [] for node in self.node_ids}
        for arc_id in self.arc_ids:
            arc = self.arcs[arc_id]
            adjacency[arc.tail].append((arc.head, arc_id))
            adjacency[arc.head].append((arc.tail, arc_id))
        return adjacency

    def path(self, start: Hashable, end: Hashable) -> list[tuple[Hashable, Hashable, Hashable]]:
        """Return tree path segments as ``(from_node, to_node, arc_id)``."""
        adjacency = self._adjacency()
        parent: dict[Hashable, tuple[Hashable, Hashable]] = {}
        queue = deque([start])
        while queue and end not in parent and start != end:
            current = queue.popleft()
            for neighbor, arc_id in adjacency[current]:
                if neighbor != start and neighbor not in parent:
                    parent[neighbor] = (current, arc_id)
                    queue.append(neighbor)
        if start != end and end not in parent:
            raise RuntimeError("The basis tree contains no path between two nodes.")
        result = []
        current = end
        while current != start:
            previous, arc_id = parent[current]
            result.append((previous, current, arc_id))
            current = previous
        return list(reversed(result))

    def component_after_removing(self, arc_id: Hashable, start: Hashable) -> set[Hashable]:
        """Nodes in ``start``'s component after removing one tree arc."""
        adjacency = self._adjacency()
        arc = self.arcs[arc_id]
        adjacency[arc.tail] = [(node, edge) for node, edge in adjacency[arc.tail] if edge != arc_id]
        adjacency[arc.head] = [(node, edge) for node, edge in adjacency[arc.head] if edge != arc_id]
        component = {start}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor, _ in adjacency[node]:
                if neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
        return component

    def is_strongly_feasible(self, root: Hashable, tolerance: float) -> bool:
        """Whether every zero-flow tree arc points away from ``root``."""
        if root not in self.node_ids:
            return False
        adjacency = self._adjacency()
        parent: dict[Hashable, Hashable | None] = {root: None}
        queue = deque([root])
        while queue:
            node = queue.popleft()
            for neighbor, arc_id in adjacency[node]:
                if neighbor in parent:
                    continue
                arc = self.arcs[arc_id]
                if arc.flow <= tolerance and not (arc.tail == node and arc.head == neighbor):
                    return False
                parent[neighbor] = node
                queue.append(neighbor)
        return len(parent) == len(self.node_ids)

    def replace(self, leaving: Hashable, entering: Hashable) -> None:
        self.arc_ids.remove(leaving)
        self.arc_ids.add(entering)
        self._validate_tree()
