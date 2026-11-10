"""Caso de uso: gestiona la carrera activa y permite encadenar carreras (US-04)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from taximetro.core.errors import TripAlreadyStarted, TripNotStarted
from taximetro.core.ports import Clock
from taximetro.core.tariff import Tariff
from taximetro.core.trip import State, Trip


class TripService:
    def __init__(self, tariff: Tariff, clock: Clock) -> None:
        self._tariff = tariff
        self._clock = clock
        self._active: Trip | None = None

    @property
    def active(self) -> Trip | None:
        return self._active

    def start(self) -> Trip:
        if self._active is not None:
            raise TripAlreadyStarted
        trip = Trip(self._tariff, trip_id=uuid4().hex[:8])
        trip.start(at=self._clock())
        self._active = trip
        return trip

    def set_state(self, state: State) -> None:
        self._require_active().change_state(state, at=self._clock())

    def current_amount(self) -> Decimal:
        return self._require_active().amount_at(self._clock())

    def finish(self) -> Decimal:
        trip = self._require_active()
        total = trip.finish(at=self._clock())
        self._active = None  # libre para la siguiente carrera
        return total

    def _require_active(self) -> Trip:
        if self._active is None:
            raise TripNotStarted
        return self._active
