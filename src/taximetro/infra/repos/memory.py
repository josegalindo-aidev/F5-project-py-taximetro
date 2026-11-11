# Proyecto: py-taximetro
# fuente: src/taximetro/infra/repos/memory.py
"""Repositorio de carreras en memoria: se pierde al cerrar el programa."""

from __future__ import annotations

from datetime import date

from taximetro.core.errors import InvalidTripRecord
from taximetro.core.trip import Trip


class InMemoryTripRepository:
    def __init__(self) -> None:
        self._trips: list[Trip] = []

    def save(self, trip: Trip) -> None:
        if not trip.is_finished:
            raise InvalidTripRecord("No se puede guardar una carrera sin terminar.")
        if trip.started_at is None or trip.finished_at is None:
            raise InvalidTripRecord("No se puede guardar una carrera sin fechas.")
        self._trips.append(trip)

    def list_finished(self, day: date) -> list[Trip]:
        of_day = [trip for trip in self._trips if trip.finished_at.date() == day]
        return sorted(of_day, key=lambda trip: trip.finished_at)
