from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .arc import Arc
from .cycle import CycleSegment
from .exceptions import UnboundedProblemError


@dataclass(frozen=True, slots=True)
class Pivot:
    leaving_arc_id: Hashable
    theta: float


def choose_pivot(cycle: list[CycleSegment], arcs: dict[Hashable, Arc], tolerance: float) -> Pivot:
    decreasing = [segment.arc_id for segment in cycle if not segment.increases]
    if not decreasing:
        raise UnboundedProblemError("The improving cycle has no blocking arc.")
    theta = min(arcs[arc_id].flow for arc_id in decreasing)
    candidates = [arc_id for arc_id in decreasing if abs(arcs[arc_id].flow - theta) <= tolerance]
    return Pivot(min(candidates, key=str), theta)


def apply_pivot(cycle: list[CycleSegment], arcs: dict[Hashable, Arc], theta: float, tolerance: float) -> None:
    for segment in cycle:
        arc = arcs[segment.arc_id]
        arc.flow += theta if segment.increases else -theta
        if abs(arc.flow) <= tolerance:
            arc.flow = 0.0
