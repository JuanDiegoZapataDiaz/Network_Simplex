from network_simplex import Arc, Network, NetworkSimplex, Node


network = Network(
    nodes=[Node("warehouse", balance=5), Node("market", balance=-5)],
    arcs=[Arc("ship", "warehouse", "market", cost=3)],
)

result = NetworkSimplex(network).solve()
print(result.objective_value)  # 15
print(result.flows)            # {'ship': 5.0}
