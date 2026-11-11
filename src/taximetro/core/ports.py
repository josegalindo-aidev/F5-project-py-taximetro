# Proyecto: py-taximetro
# fuente: src/taximetro/core/ports.py
"""Puertos: solo los que tienen más de una implementación real."""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from taximetro.core.trip import Trip


class Clock(Protocol):
    def __call__(self) -> float:
        """Segundos monotónicos: sirven para medir cuánto dura algo."""
        ...


class WallClock(Protocol):
    def __call__(self) -> datetime:
        """Fecha y hora actuales, con zona horaria: sirven para saber cuándo ocurrió algo."""
        ...


class TripRepository(Protocol):
    def save(self, trip: Trip) -> None:
        """Guarda una carrera terminada."""
        ...

    def list_finished(self, day: date) -> list[Trip]:
        """Carreras terminadas en `day`, de la más antigua a la más reciente."""
        ...
