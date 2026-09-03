from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .arc import Arc
from .basis import Basis
from .cycle import CycleSegment, coupling_node, cycle_from_coupling
from .exceptions import UnboundedProblemError


@dataclass(frozen=True, slots=True)
class Pivot:
    leaving_arc_id: Hashable
    theta: float


def choose_pivot(
    cycle: list[CycleSegment],
    arcs: dict[Hashable, Arc],
    tolerance: float,
    *,
    basis: Basis,
    entering: Arc,
    root: Hashable,
) -> Pivot:
    decreasing = [segment.arc_id for segment in cycle if not segment.increases]
    if not decreasing:
        raise UnboundedProblemError("The improving cycle has no blocking arc.")
    theta = min(arcs[arc_id].flow for arc_id in decreasing)
    # Strong-feasibility rule: begin at the coupling node (the first cycle
    # node on root -> tail(entering)), then follow the cycle in the direction
    # of the entering arc and select the first blocking arc.
    coupling = coupling_node(entering, cycle, basis, arcs, root)
    traversal = cycle_from_coupling(cycle, arcs, coupling)
    leaving = next(
        segment.arc_id
        for segment in traversal
        if not segment.increases and abs(arcs[segment.arc_id].flow - theta) <= tolerance
    )
    return Pivot(leaving, theta)


def apply_pivot(cycle: list[CycleSegment], arcs: dict[Hashable, Arc], theta: float, tolerance: float) -> None:
    for segment in cycle:
        arc = arcs[segment.arc_id]
        arc.flow += theta if segment.increases else -theta
        if abs(arc.flow) <= tolerance:
            arc.flow = 0.0
