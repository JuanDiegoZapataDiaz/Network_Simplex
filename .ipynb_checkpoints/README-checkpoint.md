# Network Simplex

Implementación educativa en Python del algoritmo **Network Simplex** para el
problema de flujo de coste mínimo no capacitado:

\[
\min c^\top x \quad \text{sujeto a} \quad Ax=b,\; x\geq0,
\]

donde `A` es la matriz de incidencia nodo--arco de una red dirigida. Se usa la
convención `entrada - salida = balance`: valores negativos son oferta y valores
positivos son demanda.

## Uso

Instala el paquete en modo editable para ejecutar los ejemplos desde el
repositorio:

```bash
python -m pip install -e .
```

```python
from network_simplex import Arc, Network, NetworkSimplex, Node

network = Network(
    nodes=[Node("s", -5), Node("t", 5)],
    arcs=[Arc("s_t", "s", "t", cost=3)],
)
result = NetworkSimplex(network).solve()

assert result.objective_value == 15
assert result.flows == {"s_t": 5.0}
```

La solución inicial se construye con un nodo artificial y arcos de gran coste.
Si queda flujo artificial al acabar, el problema es infactible.

## Alcance actual

- Flujos no negativos y sin cotas superiores.
- Base de árbol, potenciales, costes reducidos, ciclos fundamentales y pivotes.
- Detección de infactibilidad mediante arcos artificiales.

La siguiente extensión prevista es `0 <= x_ij <= u_ij`.
