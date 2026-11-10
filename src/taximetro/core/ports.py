"""Puertos: solo los que tienen más de una implementación real."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from taximetro.core.trip import Trip


class Clock(Protocol):
    def __call__(self) -> float:
        """Segundos monotónicos."""
        ...


class TripRepository(Protocol):
    def save(self, trip: Trip) -> None:
        """Guarda o actualiza una carrera (en curso o terminada)."""
        ...

    def get(self, trip_id: str) -> Trip: ...

    def list_finished(self, day: date) -> list[Trip]: ...
