from __future__ import annotations

from collections import deque
from typing import Hashable

from .arc import Arc
from .basis import Basis


def compute_potentials(basis: Basis, arcs: dict[Hashable, Arc], root: Hashable) -> dict[Hashable, float]:
    """Compute node potentials satisfying pi[head] - pi[tail] = cost on tree arcs."""
    potentials = {root: 0.0}
    adjacency = basis._adjacency()
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for neighbor, arc_id in adjacency[node]:
            if neighbor in potentials:
                continue
            arc = arcs[arc_id]
            if node == arc.tail:
                potentials[neighbor] = potentials[node] + arc.cost
            else:
                potentials[neighbor] = potentials[node] - arc.cost
            queue.append(neighbor)
    return potentials


def reduced_cost(arc: Arc, potentials: dict[Hashable, float]) -> float:
    return arc.cost + potentials[arc.tail] - potentials[arc.head]
