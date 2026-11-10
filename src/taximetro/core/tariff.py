# Proyecto: py-taximetro
# fuente: src/taximetro/core/tariff.py
"""Tarifas: precio por segundo según el estado del taxi."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from taximetro.core.errors import InvalidTariff
from taximetro.core.state import State


@dataclass(frozen=True)
class Tariff:
    """Precio en euros por segundo, parado y en movimiento."""

    stopped: Decimal
    moving: Decimal

    def __post_init__(self) -> None:
        if self.stopped < 0 or self.moving < 0:
            raise InvalidTariff("Las tarifas no pueden ser negativas.")

    def rate_for(self, state: State) -> Decimal:
        return self.moving if state is State.MOVING else self.stopped


# Zona EMT Madrid (junio 2025). Pasará a un fichero de configuración en la Fase 2 (US-07).
DEFAULT_TARIFF = Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))
