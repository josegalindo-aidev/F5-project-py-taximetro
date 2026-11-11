# Proyecto: py-taximetro
# fuente: src/taximetro/core/trip.py
"""Carrera: acumula el importe por tramos según el estado del taxi.

Decisión de diseño: `Trip` NO conoce ningún reloj. Recibe el instante (`at`, en
segundos) en cada operación; quien llama (el servicio) lee el `Clock`. Así el
cálculo es determinista y se prueba sin esperas.
"""

from __future__ import annotations

from datetime import datetime
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
    def __init__(self, tariff: Tariff | None, trip_id: str | None = None) -> None:
        self.tariff = tariff
        self.id = trip_id
        self._state: State | None = None
        self._last_at: float | None = None
        self._accumulated = Decimal(0)
        self._stopped_seconds = Decimal(0)
        self._moving_seconds = Decimal(0)
        self._started_at: datetime | None = None
        self._finished_at: datetime | None = None
        self._finished = False
        self.total: Decimal | None = None

    @classmethod
    def restore(
        cls,
        trip_id: str,
        started_at: datetime,
        finished_at: datetime,
        stopped_seconds: Decimal,
        moving_seconds: Decimal,
        total: Decimal,
    ) -> Trip:
        """Reconstruye una carrera ya terminada a partir de datos guardados."""
        trip = cls(tariff=None, trip_id=trip_id)
        trip._started_at = started_at
        trip._finished_at = finished_at
        trip._stopped_seconds = stopped_seconds
        trip._moving_seconds = moving_seconds
        trip.total = total
        trip._finished = True
        return trip

    @property
    def state(self) -> State | None:
        return self._state

    @property
    def is_finished(self) -> bool:
        return self._finished

    @property
    def stopped_seconds(self) -> Decimal:
        return self._stopped_seconds

    @property
    def moving_seconds(self) -> Decimal:
        return self._moving_seconds

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def finished_at(self) -> datetime | None:
        return self._finished_at

    def start(self, at: float, when: datetime | None = None) -> None:
        if self._finished:
            raise TripAlreadyFinished
        if self._state is not None:
            raise TripAlreadyStarted
        self._state = State.STOPPED
        self._last_at = at
        self._started_at = when

    def change_state(self, state: State, at: float) -> None:
        self._accumulated = self._close_segment(at)
        self._add_seconds(at)
        self._state = state
        self._last_at = at

    def amount_at(self, at: float) -> Decimal:
        """Importe acumulado hasta `at`, sin cerrar la carrera."""
        return self._close_segment(at).quantize(CENT, rounding=ROUND_HALF_UP)

    def finish(self, at: float, when: datetime | None = None) -> Decimal:
        self._accumulated = self._close_segment(at)
        self._add_seconds(at)
        self._last_at = at
        self._finished_at = when
        self._finished = True
        self.total = self._accumulated.quantize(CENT, rounding=ROUND_HALF_UP)
        return self.total

    def _add_seconds(self, at: float) -> None:
        """Suma la duración del tramo que se cierra al acumulador de su estado."""
        seconds = _seconds(self._last_at, at)
        if self._state is State.MOVING:
            self._moving_seconds += seconds
        else:
            self._stopped_seconds += seconds

    def _close_segment(self, at: float) -> Decimal:
        """Importe acumulado más el tramo actual hasta `at` (sin modificar el estado)."""
        if self._finished:
            raise TripAlreadyFinished
        if self._state is None or self._last_at is None:
            raise TripNotStarted
        if at < self._last_at:
            raise InvalidTimestamp
        return self._accumulated + _seconds(self._last_at, at) * self.tariff.rate_for(self._state)
