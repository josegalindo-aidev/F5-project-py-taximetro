# Proyecto: py-taximetro
# fuente: src/taximetro/infra/repos/memory.py
"""Repositorio de carreras en memoria: se pierde al cerrar el programa."""

from __future__ import annotations

from datetime import date

from taximetro.core.trip import Trip
from taximetro.infra.repos.validation import ensure_can_be_saved


class InMemoryTripRepository:
    def __init__(self) -> None:
        self._trips: list[Trip] = []

    def save(self, trip: Trip) -> None:
        ensure_can_be_saved(trip)
        self._trips.append(trip)

    def list_finished(self, day: date) -> list[Trip]:
        of_day = [trip for trip in self._trips if trip.finished_at.date() == day]
        return sorted(of_day, key=lambda trip: trip.finished_at)
