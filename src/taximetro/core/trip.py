"""Carrera: acumula el importe por tramos según el estado del taxi.

Decisión de diseño: `Trip` NO conoce ningún reloj. Recibe el instante (`at`, en
segundos) en cada operación; quien llama (el servicio) lee el `Clock`. Así el
cálculo es determinista y se prueba sin esperas.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from taximetro.core.errors import (
    InvalidTimestamp,
    TripAlreadyFinished,
    TripAlreadyStarted,
    TripNotStarted,
)
from taximetro.core.state import State
from taximetro.core.tariff import Tariff

__all__ = ["State", "Trip"]

CENT = Decimal("0.01")


def _seconds(start: float, end: float) -> Decimal:
    """Diferencia exacta en segundos (evita el ruido binario de restar floats)."""
    return Decimal(str(end)) - Decimal(str(start))


class Trip:
    def __init__(self, tariff: Tariff, trip_id: str | None = None) -> None:
        self.tariff = tariff
        self.id = trip_id
        self._state: State | None = None
        self._last_at: float | None = None
        self._accumulated = Decimal(0)
        self._finished = False
        self.total: Decimal | None = None

    @property
    def state(self) -> State | None:
        return self._state

    @property
    def is_finished(self) -> bool:
        return self._finished

    def start(self, at: float) -> None:
        if self._finished:
            raise TripAlreadyFinished
        if self._state is not None:
            raise TripAlreadyStarted
        self._state = State.STOPPED
        self._last_at = at

    def change_state(self, state: State, at: float) -> None:
        self._accumulated = self._close_segment(at)
        self._state = state
        self._last_at = at

    def amount_at(self, at: float) -> Decimal:
        """Importe acumulado hasta `at`, sin cerrar la carrera."""
        return self._close_segment(at).quantize(CENT, rounding=ROUND_HALF_UP)

    def finish(self, at: float) -> Decimal:
        self._accumulated = self._close_segment(at)
        self._last_at = at
        self._finished = True
        self.total = self._accumulated.quantize(CENT, rounding=ROUND_HALF_UP)
        return self.total

    def _close_segment(self, at: float) -> Decimal:
        """Importe acumulado más el tramo actual hasta `at` (sin modificar el estado)."""
        if self._finished:
            raise TripAlreadyFinished
        if self._state is None or self._last_at is None:
            raise TripNotStarted
        if at < self._last_at:
            raise InvalidTimestamp
        return self._accumulated + _seconds(self._last_at, at) * self.tariff.rate_for(self._state)
