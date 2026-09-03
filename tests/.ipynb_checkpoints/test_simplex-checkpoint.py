import pytest

from network_simplex import Arc, InfeasibleProblemError, Network, NetworkSimplex, Node


def test_solves_a_minimum_cost_flow_problem() -> None:
    network = Network(
        nodes=[Node("s", -5), Node("a", 0), Node("t", 5)],
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
        nodes=[Node("s", -1), Node("t", 1)],
        arcs=[Arc("wrong_direction", "t", "s", 1)],
    )

    with pytest.raises(InfeasibleProblemError):
        NetworkSimplex(network).solve()


def test_uses_the_cheapest_route_through_a_transshipment_node() -> None:
    network = Network(
        nodes=[Node("s", -4), Node("a", 0), Node("b", 0), Node("t", 4)],
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
