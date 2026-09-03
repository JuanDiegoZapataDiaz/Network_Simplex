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
    """Return the signed cycle after increasing the entering arc by one unit."""
    segments = [CycleSegment(entering.id, True)]
    for start, end, arc_id in basis.path(entering.head, entering.tail):
        arc = arcs[arc_id]
        segments.append(CycleSegment(arc_id, arc.tail == start and arc.head == end))
    return segments
