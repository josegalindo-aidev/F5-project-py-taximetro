"""Carrera. Pendiente de implementar (ciclo TDD en rojo).

Decisión de diseño: `Trip` NO conoce ningún reloj. Recibe el instante (`at`)
en cada operación; quien llama (el servicio) lee el `Clock`.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from taximetro.core.tariff import Tariff


class State(Enum):
    STOPPED = "stopped"
    MOVING = "moving"


class Trip:
    def __init__(self, tariff: Tariff, trip_id: str | None = None) -> None:
        self.tariff = tariff
        self.id = trip_id

    def start(self, at: float) -> None:
        raise NotImplementedError

    def change_state(self, state: State, at: float) -> None:
        raise NotImplementedError

    def finish(self, at: float) -> Decimal:
        raise NotImplementedError
