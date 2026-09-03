from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping

from .arc import Arc
from .basis import Basis
from .cycle import fundamental_cycle
from .exceptions import InfeasibleProblemError
from .network import Network
from .pivot import apply_pivot, choose_pivot
from .potentials import compute_potentials, reduced_cost, update_potentials_after_pivot


@dataclass(frozen=True, slots=True)
class WarmStart:
    """A rooted, strongly feasible basic solution supplied by the caller.

    ``basic_arc_ids`` must be a spanning tree. ``flows`` contains every
    original arc id; nonbasic arcs must have zero flow.
    """

    root: Hashable
    basic_arc_ids: frozenset[Hashable]
    flows: Mapping[Hashable, float]


@dataclass(frozen=True, slots=True)
class SolveResult:
    objective_value: float
    flows: dict[Hashable, float]
    potentials: dict[Hashable, float]
    iterations: int
    basic_arc_ids: frozenset[Hashable] | None = None
    root: Hashable | None = None

    def as_warm_start(self) -> WarmStart:
        """Reuse this solution after changing costs or other arc parameters.

        A cold start may retain zero-flow artificial arcs in a degenerate
        basis; in that case a user-provided original spanning-tree basis is
        required instead.
        """
        if self.basic_arc_ids is None or self.root is None:
            raise ValueError("This result has no all-original basis to reuse as a warm start.")
        return WarmStart(self.root, self.basic_arc_ids, self.flows)


class NetworkSimplex:
    """Primal Network Simplex for min c'x subject to Ax=b and x >= 0.

    ``A`` is represented implicitly by the node-arc incidence of ``Network``.
    This initial implementation has no upper capacities.
    """

    def __init__(self, network: Network, *, tolerance: float = 1e-9, max_iterations: int = 10_000) -> None:
        self.network = network.copy()
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def solve(self, warm_start: WarmStart | None = None) -> SolveResult:
        arcs, basis, root, original_ids = (
            self._warm_start(warm_start) if warm_start is not None else self._initial_basis()
        )
        potentials = compute_potentials(basis, arcs, root)
        for iteration in range(self.max_iterations + 1):
            entering = self._choose_entering(arcs, basis, potentials)
            if entering is None:
                self._assert_feasible(arcs)
                return SolveResult(
                    objective_value=sum(arcs[arc_id].cost * arcs[arc_id].flow for arc_id in original_ids),
                    flows={arc_id: arcs[arc_id].flow for arc_id in original_ids},
                    potentials={node_id: value for node_id, value in potentials.items() if node_id != root},
                    iterations=iteration,
                    basic_arc_ids=(frozenset(basis.arc_ids) if basis.arc_ids <= original_ids else None),
                    root=(root if basis.arc_ids <= original_ids else None),
                )
            cycle = fundamental_cycle(entering, basis, arcs)
            pivot = choose_pivot(cycle, arcs, self.tolerance, basis=basis, entering=entering, root=root)
            update_potentials_after_pivot(potentials, basis, entering, pivot.leaving_arc_id, root)
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
            if node.balance <= 0:
                arc = Arc(id=arc_id, 
                          tail=root, 
                          head=node.id, 
                          cost=artificial_cost, 
                          flow= -node.balance, 
                          artificial=True)
            else:
                arc = Arc(id=arc_id, 
                          tail=node.id, 
                          head=root, 
                          cost=artificial_cost, 
                          flow= node.balance, 
                          artificial=True)
            arcs[arc_id] = arc
            artificial_ids.append(arc_id)
        basis = Basis([*self.network.nodes, root], artificial_ids, arcs)
        return arcs, basis, root, original_ids

    def _warm_start(self, warm_start: WarmStart) -> tuple[dict[Hashable, Arc], Basis, Hashable, set[Hashable]]:
        if warm_start.root not in self.network.nodes:
            raise ValueError("The warm-start root must be a network node.")
        arcs = {arc_id: arc.copy() for arc_id, arc in self.network.arcs.items()}
        if set(warm_start.flows) != set(arcs):
            raise ValueError("Warm-start flows must specify every arc exactly once.")
        for arc_id, flow in warm_start.flows.items():
            if flow < -self.tolerance:
                raise ValueError("Warm-start flows must be non-negative.")
            arcs[arc_id].flow = 0.0 if abs(flow) <= self.tolerance else float(flow)
        basis = Basis(self.network.nodes, warm_start.basic_arc_ids, arcs)
        if any(arcs[arc_id].flow > self.tolerance for arc_id in arcs if arc_id not in basis.arc_ids):
            raise ValueError("A warm-start nonbasic arc must have zero flow.")
        self._validate_flow_balance(arcs)
        if not basis.is_strongly_feasible(warm_start.root, self.tolerance):
            raise ValueError("Warm start must be strongly feasible for its declared root.")
        return arcs, basis, warm_start.root, set(arcs)

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

    def _validate_flow_balance(self, arcs: dict[Hashable, Arc]) -> None:
        balance = {node_id: 0.0 for node_id in self.network.nodes}
        for arc in arcs.values():
            balance[arc.tail] += arc.flow
            balance[arc.head] -= arc.flow
        for node_id, node in self.network.nodes.items():
            if abs(balance[node_id] - node.balance) > self.tolerance:
                raise ValueError(f"Warm-start flow does not satisfy balance at node {node_id!r}.")
