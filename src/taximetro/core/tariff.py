"""Tarifas. Pendiente de implementar (ciclo TDD en rojo)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taximetro.core.trip import State


@dataclass(frozen=True)
class Tariff:
    """Precio por segundo según el estado del taxi."""

    stopped: Decimal
    moving: Decimal

    def rate_for(self, state: State) -> Decimal:
        raise NotImplementedError
