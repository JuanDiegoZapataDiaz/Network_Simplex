# Network Simplex

An educational Python implementation of the **primal Network Simplex**
algorithm for the uncapacitated minimum-cost flow problem:

\[
\min c^\top x
\quad \text{subject to} \quad
Ax=b,\; x\geq0,
\]

where \(A\) is the node-arc incidence matrix of a directed network.

## Conventions

This project uses the following node-balance convention:

\[
\text{outgoing flow} - \text{incoming flow} = b_i.
\]

Therefore, a positive balance represents supply and a negative balance
represents demand.

## Features

- Uncapacitated minimum-cost flow: \(x_{ij}\geq0\).
- Big-M artificial-root initialization to obtain an initial basic feasible
  solution or detect infeasibility.
- Spanning-tree basis, node potentials, reduced costs, fundamental cycles, and
  primal pivots.
- Incremental potential updates after a pivot.
- Strongly feasible warm starts for reoptimization.
- A coupling-node leaving-arc rule to preserve strong feasibility.
- A NetworkX comparison notebook with correctness checks and local timing
  benchmarks.

## Installation

Install the package in editable mode from the repository root:

```bash
python -m pip install -e .
```

To run the NetworkX comparison notebook, install the optional example
dependency as well:

```bash
python -m pip install -e ".[examples]"
```

## Quick start

```python
from network_simplex import Arc, Network, NetworkSimplex, Node

network = Network(
    nodes=[Node("source", balance=5), Node("sink", balance=-5)],
    arcs=[Arc("source_sink", "source", "sink", cost=3)],
)

result = NetworkSimplex(network).solve()

assert result.objective_value == 15
assert result.flows == {"source_sink": 5.0}
```

The solver builds an initial artificial star basis. Artificial arcs have a
large penalty cost, so the algorithm removes their flow whenever the original
network is feasible. Remaining artificial flow indicates that the original
problem is infeasible.

## Warm starts

You can reoptimize after changing arc costs or other model parameters by
providing a rooted, strongly feasible basic solution:

```python
from network_simplex import WarmStart

warm_start = WarmStart(
    root="source",
    basic_arc_ids=frozenset({"source_sink"}),
    flows={"source_sink": 5.0},
)

result = NetworkSimplex(network).solve(warm_start=warm_start)
```

If a result has an all-original final basis, `result.as_warm_start()` converts
it directly into a reusable `WarmStart`.

## Comparison with NetworkX

[`examples/compare_with_networkx.ipynb`](examples/compare_with_networkx.ipynb)
solves equivalent instances with this project and
[`networkx.network_simplex`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.flow.network_simplex.html).
It verifies the objective value and includes a reproducible local execution-time
benchmark over increasingly large generated networks.

NetworkX uses the opposite convention,
`incoming flow - outgoing flow = demand`; equivalent node values are converted
with `demand = -balance`.

## Current scope and limitations

This is an educational implementation rather than a production solver. The
current scope is limited to nonnegative, uncapacitated arc flows. In particular,
upper bounds \(x_{ij}\leq u_{ij}\), integer-specialized data structures, and a
separate numerical Phase I procedure are not implemented yet.

The natural next extension is the capacitated model:

\[
0\leq x_{ij}\leq u_{ij}.
\]
