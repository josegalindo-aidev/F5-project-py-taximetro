# Proyecto: py-taximetro
# fuente: src/taximetro/infra/repos/validation.py
"""Reglas que toda carrera debe cumplir para guardarse en cualquier repositorio."""

from taximetro.core.errors import InvalidTripRecord
from taximetro.core.trip import Trip


def ensure_can_be_saved(trip: Trip) -> None:
    if not trip.is_finished:
        raise InvalidTripRecord("No se puede guardar una carrera sin terminar.")
    if trip.started_at is None or trip.finished_at is None:
        raise InvalidTripRecord("No se puede guardar una carrera sin fechas.")
