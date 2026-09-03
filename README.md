# Network Simplex

Implementacion educativa en Python del algoritmo **Network Simplex** para el
problema de flujo de coste minimo no capacitado:

\[
\min c^\top x \quad \text{sujeto a} \quad Ax=b,\; x\geq0,
\]

donde `A` es la matriz de incidencia nodo-arco de una red dirigida. Se usa la
convencion `salida - entrada = balance`: valores positivos son oferta y valores
negativos son demanda.

## Uso

Instala el paquete en modo editable para ejecutar los ejemplos desde el
repositorio:

```bash
python -m pip install -e .
```

```python
from network_simplex import Arc, Network, NetworkSimplex, Node

network = Network(
    nodes=[Node("s", 5), Node("t", -5)],
    arcs=[Arc("s_t", "s", "t", cost=3)],
)
result = NetworkSimplex(network).solve()

assert result.objective_value == 15
assert result.flows == {"s_t": 5.0}
```

La solucion inicial se construye con un nodo artificial y arcos de gran coste.
Si queda flujo artificial al acabar, el problema es infactible.

Tambien se puede empezar desde una solucion basica factible fuertemente
factible, util para reoptimizacion:

```python
from network_simplex import WarmStart

warm_start = WarmStart(
    root="s",
    basic_arc_ids=frozenset({"s_a", "a_t"}),
    flows={"s_a": 5.0, "a_t": 5.0, "s_t": 0.0},
)
result = NetworkSimplex(network).solve(warm_start=warm_start)
```

Si el resultado termina con una base compuesta solo por arcos originales,
`result.as_warm_start()` lo convierte directamente en un nuevo `WarmStart`.

## Alcance actual

- Flujos no negativos y sin cotas superiores.
- Base de arbol, potenciales, costes reducidos, ciclos fundamentales y pivotes.
- Warm starts fuertemente factibles y actualizacion incremental de potenciales.
- Deteccion de infactibilidad mediante arcos artificiales.

La siguiente extension prevista es `0 <= x_ij <= u_ij`.
