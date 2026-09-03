from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable


@dataclass(slots=True)
class Arc:
    """A directed arc with a non-negative flow variable."""

    id: Hashable
    tail: Hashable
    head: Hashable
    cost: float
    flow: float = 0.0
    artificial: bool = False

    def copy(self) -> "Arc":
        return Arc(self.id, self.tail, self.head, self.cost, self.flow, self.artificial)
