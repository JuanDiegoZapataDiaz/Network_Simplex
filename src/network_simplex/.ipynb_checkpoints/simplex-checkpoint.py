from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .arc import Arc
from .basis import Basis
from .cycle import fundamental_cycle
from .exceptions import InfeasibleProblemError
from .network import Network
from .pivot import apply_pivot, choose_pivot
from .potentials import compute_potentials, reduced_cost


@dataclass(frozen=True, slots=True)
class SolveResult:
    objective_value: float
    flows: dict[Hashable, float]
    potentials: dict[Hashable, float]
    iterations: int


class NetworkSimplex:
    """Primal Network Simplex for min c'x subject to Ax=b and x >= 0.

    ``A`` is represented implicitly by the node-arc incidence of ``Network``.
    This initial implementation has no upper capacities.
    """

    def __init__(self, network: Network, *, tolerance: float = 1e-9, max_iterations: int = 10_000) -> None:
        self.network = network.copy()
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def solve(self) -> SolveResult:
        arcs, basis, root, original_ids = self._initial_basis()
        for iteration in range(self.max_iterations + 1):
            potentials = compute_potentials(basis, arcs, root)
            entering = self._choose_entering(arcs, basis, potentials)
            if entering is None:
                self._assert_feasible(arcs)
                return SolveResult(
                    objective_value=sum(arcs[arc_id].cost * arcs[arc_id].flow for arc_id in original_ids),
                    flows={arc_id: arcs[arc_id].flow for arc_id in original_ids},
                    potentials={node_id: value for node_id, value in potentials.items() if node_id != root},
                    iterations=iteration,
                )
            cycle = fundamental_cycle(entering, basis, arcs)
            pivot = choose_pivot(cycle, arcs, self.tolerance)
            apply_pivot(cycle, arcs, pivot.theta, self.tolerance)
            basis.replace(pivot.leaving_arc_id, entering.id)
        raise RuntimeError(f"Maximum iteration limit ({self.max_iterations}) reached.")

    def _initial_basis(self) -> tuple[dict[Hashable, Arc], Basis, Hashable, set[Hashable]]:
        root = object()
        arcs = {arc_id: arc.copy() for arc_id, arc in self.network.arcs.items()}
        original_ids = set(arcs)
        # Any simple tree path has at most |V|-1 original arcs.  This bound
        # makes one unit of artificial flow more expensive than rerouting it
        # through any original simple path during the Big-M initialization.
        artificial_cost = 1.0 + len(self.network.nodes) * sum(abs(arc.cost) for arc in arcs.values())
        artificial_ids = []
        for index, node in enumerate(self.network.nodes.values()):
            arc_id = ("__artificial__", index)
            if node.balance >= 0:
                arc = Arc(arc_id, root, node.id, artificial_cost, node.balance, True)
            else:
                arc = Arc(arc_id, node.id, root, artificial_cost, -node.balance, True)
            arcs[arc_id] = arc
            artificial_ids.append(arc_id)
        basis = Basis([*self.network.nodes, root], artificial_ids, arcs)
        return arcs, basis, root, original_ids

    def _choose_entering(self, arcs: dict[Hashable, Arc], basis: Basis, potentials: dict[Hashable, float]) -> Arc | None:
        candidates = (
            arc for arc_id, arc in arcs.items()
            if arc_id not in basis.arc_ids and reduced_cost(arc, potentials) < -self.tolerance
        )
        return min(candidates, key=lambda arc: str(arc.id), default=None)

    def _assert_feasible(self, arcs: dict[Hashable, Arc]) -> None:
        artificial_flow = sum(arc.flow for arc in arcs.values() if arc.artificial)
        if artificial_flow > self.tolerance:
            raise InfeasibleProblemError("No feasible flow satisfies the node balances.")
