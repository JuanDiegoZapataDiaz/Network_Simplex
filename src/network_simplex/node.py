from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable


@dataclass(frozen=True, slots=True)
class Node:
    """A network node.

    ``balance`` follows the convention outgoing flow minus incoming flow. Positive values are supplies and negative values are demands.
    """

    id: Hashable
    balance: float = 0.0
