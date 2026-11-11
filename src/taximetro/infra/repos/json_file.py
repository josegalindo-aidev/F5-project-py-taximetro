# Proyecto: py-taximetro
# fuente: src/taximetro/infra/repos/json_file.py
"""Repositorio de carreras en un fichero JSON: sobrevive al cierre del programa."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from taximetro.core.errors import InvalidTripRecord, TripHistoryError
from taximetro.core.trip import Trip


class JsonTripRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, trip: Trip) -> None:
        if not trip.is_finished:
            raise InvalidTripRecord("No se puede guardar una carrera sin terminar.")
        if trip.started_at is None or trip.finished_at is None:
            raise InvalidTripRecord("No se puede guardar una carrera sin fechas.")
        records = self._read()
        records.append(_to_record(trip))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def list_finished(self, day: date) -> list[Trip]:
        try:
            trips = [_from_record(record) for record in self._read()]
        except (KeyError, TypeError, ValueError, ArithmeticError) as error:
            raise self._damaged(f"registro no válido ({error!r})") from error
        of_day = [trip for trip in trips if trip.finished_at.date() == day]
        return sorted(of_day, key=lambda trip: trip.finished_at)

    def _read(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            records = json.loads(self._path.read_text(encoding="utf-8"))
        except ValueError as error:  # JSON mal formado o texto que no es UTF-8
            raise self._damaged(str(error)) from error
        if not isinstance(records, list):
            raise self._damaged("se esperaba una lista de carreras")
        return records

    def _damaged(self, reason: str) -> TripHistoryError:
        return TripHistoryError(f"El historial '{self._path}' está dañado: {reason}")


def _to_record(trip: Trip) -> dict:
    return {
        "id": trip.id,
        "started_at": trip.started_at.isoformat(),
        "finished_at": trip.finished_at.isoformat(),
        "stopped_seconds": str(trip.stopped_seconds),
        "moving_seconds": str(trip.moving_seconds),
        "total": str(trip.total),
    }


def _from_record(record: dict) -> Trip:
    return Trip.restore(
        record["id"],
        datetime.fromisoformat(record["started_at"]),
        datetime.fromisoformat(record["finished_at"]),
        Decimal(record["stopped_seconds"]),
        Decimal(record["moving_seconds"]),
        Decimal(record["total"]),
    )
