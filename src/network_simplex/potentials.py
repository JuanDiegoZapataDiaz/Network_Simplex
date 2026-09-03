from __future__ import annotations

from collections import deque
from typing import Hashable

from .arc import Arc
from .basis import Basis


def compute_potentials(basis: Basis, arcs: dict[Hashable, Arc], root: Hashable) -> dict[Hashable, float]:
    """Compute node potentials satisfying pi[tail] - pi[head] = cost on tree arcs."""
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
                potentials[neighbor] = potentials[node] - arc.cost
            else:
                potentials[neighbor] = potentials[node] + arc.cost
            queue.append(neighbor)
    return potentials


def reduced_cost(arc: Arc, potentials: dict[Hashable, float]) -> float:
    return arc.cost - potentials[arc.tail] + potentials[arc.head]


def update_potentials_after_pivot(
    potentials: dict[Hashable, float],
    basis: Basis,
    entering: Arc,
    leaving_arc_id: Hashable,
    root: Hashable) -> None:
    """
    Update potentials after a pivot without full tree traversal.

    After removing leaving_arc, the tree splits into two components.
    Only one component needs its potentials shifted by a constant.

    Let a_e = reduced_cost(entering) = c_e - π[tail] + π[head].
    
    If root is in the component containing entering.tail:
        shift the OTHER component by -a_e
    Else:
        shift the component containing entering.tail by a_e

    This preserves π[root] = 0 and satisfies all tree arc equations.
    """
    reduced = reduced_cost(entering, potentials)
    tail_component = basis.component_after_removing(leaving_arc_id, entering.tail)
    if root in tail_component:
        shifted_nodes = set(basis.node_ids) - tail_component
        shift = -reduced
    else:
        shifted_nodes = tail_component
        shift = reduced
    for node_id in shifted_nodes:
        potentials[node_id] += shift
