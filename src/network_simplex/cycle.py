from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .arc import Arc
from .basis import Basis


@dataclass(frozen=True, slots=True)
class CycleSegment:
    arc_id: Hashable
    increases: bool


def fundamental_cycle(entering: Arc, basis: Basis, arcs: dict[Hashable, Arc]) -> list[CycleSegment]:
    """Return the cycle with an indicator True if the arc is forward in the direction of the entering node, False if backward."""
    segments = [CycleSegment(entering.id, True)]
    for start, end, arc_id in basis.path(entering.head, entering.tail):
        arc = arcs[arc_id]
        segments.append(CycleSegment(arc_id, arc.tail == start and arc.head == end))
    return segments


def coupling_node(
    entering: Arc,
    cycle: list[CycleSegment],
    basis: Basis,
    arcs: dict[Hashable, Arc],
    root: Hashable) -> Hashable:
    """First cycle node found on the simple path from ``root`` to ``tail(e)``."""
    cycle_nodes = {
        node
        for segment in cycle
        for node in (arcs[segment.arc_id].tail, arcs[segment.arc_id].head)
    }
    root_to_tail = [root, *(end for _, end, _ in basis.path(root, entering.tail))]
    return next(node for node in root_to_tail if node in cycle_nodes)


def cycle_from_coupling(
    cycle: list[CycleSegment], 
    arcs: dict[Hashable, Arc], 
    coupling: Hashable) -> list[CycleSegment]:
    """Rotate the directed fundamental cycle to begin at ``coupling``.

    ``cycle`` is directed with the entering arc, so the returned ordering is
    precisely the cycle traversal in that direction starting at the coupling.
    """
    def segment_start(segment: CycleSegment) -> Hashable:
        arc = arcs[segment.arc_id]
        return arc.tail if segment.increases else arc.head

    start_index = next(index for index, segment in enumerate(cycle) if segment_start(segment) == coupling)
    return [*cycle[start_index:], *cycle[:start_index]]
