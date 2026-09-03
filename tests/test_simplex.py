import pytest

from network_simplex import Arc, InfeasibleProblemError, Network, NetworkSimplex, Node, WarmStart
from network_simplex.basis import Basis
from network_simplex.cycle import fundamental_cycle
from network_simplex.pivot import choose_pivot


def test_solves_a_minimum_cost_flow_problem() -> None:
    network = Network(
        nodes=[Node("s", 5), Node("a", 0), Node("t", -5)],
        arcs=[
            Arc("sa", "s", "a", 2),
            Arc("at", "a", "t", 3),
            Arc("st", "s", "t", 8),
        ],
    )

    result = NetworkSimplex(network).solve()

    assert result.objective_value == pytest.approx(25)
    assert result.flows == {"sa": pytest.approx(5), "at": pytest.approx(5), "st": pytest.approx(0)}
    assert result.iterations > 0


def test_detects_an_infeasible_problem() -> None:
    network = Network(
        nodes=[Node("s", 1), Node("t", -1)],
        arcs=[Arc("wrong_direction", "t", "s", 1)],
    )

    with pytest.raises(InfeasibleProblemError):
        NetworkSimplex(network).solve()


def test_uses_the_cheapest_route_through_a_transshipment_node() -> None:
    network = Network(
        nodes=[Node("s", 4), Node("a", 0), Node("b", 0), Node("t", -4)],
        arcs=[
            Arc("sa", "s", "a", 1),
            Arc("at", "a", "t", 5),
            Arc("sb", "s", "b", 2),
            Arc("bt", "b", "t", 1),
            Arc("ab", "a", "b", 1),
        ],
    )

    result = NetworkSimplex(network).solve()

    assert result.objective_value == pytest.approx(12)
    assert result.flows["sa"] + result.flows["sb"] == pytest.approx(4)
    assert result.flows["bt"] == pytest.approx(4)


def test_improves_a_strongly_feasible_warm_start() -> None:
    network = Network(
        nodes=[Node("s", 5), Node("a", 0), Node("t", -5)],
        arcs=[
            Arc("sa", "s", "a", 2),
            Arc("at", "a", "t", 3),
            Arc("st", "s", "t", 1),
        ],
    )
    warm_start = WarmStart(
        root="s",
        basic_arc_ids=frozenset({"sa", "at"}),
        flows={"sa": 5, "at": 5, "st": 0},
    )

    result = NetworkSimplex(network).solve(warm_start=warm_start)

    assert result.objective_value == pytest.approx(5)
    assert result.flows == {"sa": pytest.approx(0), "at": pytest.approx(0), "st": pytest.approx(5)}
    assert result.iterations == 1
    assert result.as_warm_start().basic_arc_ids == frozenset({"sa", "st"})


def test_leaving_arc_is_first_blocker_from_the_coupling_node() -> None:
    # The cycle is a -> b -> c -> a. The root path r -> c -> a reaches the
    # cycle first at c, so ``ac`` is encountered before ``bc``. Both block.
    arcs = {
        "rc": Arc("rc", "r", "c", 0, flow=1),
        "bc": Arc("bc", "c", "b", 0, flow=1),
        "ac": Arc("ac", "a", "c", 0, flow=1),
        "enter": Arc("enter", "a", "b", -1),
    }
    basis = Basis({"r", "a", "b", "c"}, {"rc", "bc", "ac"}, arcs)
    cycle = fundamental_cycle(arcs["enter"], basis, arcs)

    pivot = choose_pivot(cycle, arcs, 1e-9, basis=basis, entering=arcs["enter"], root="r")

    assert pivot.theta == pytest.approx(1)
    assert pivot.leaving_arc_id == "ac"
