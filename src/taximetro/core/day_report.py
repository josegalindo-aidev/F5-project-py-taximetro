# Proyecto: py-taximetro
# fuente: src/taximetro/core/day_report.py
"""Caso de uso de consulta: el resumen de las carreras terminadas de un día (US-05)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from taximetro.core.ports import TripRepository, WallClock
from taximetro.core.trip import Trip


@dataclass(frozen=True)
class DaySummary:
    day: date
    trips: tuple[Trip, ...]

    @property
    def count(self) -> int:
        raise NotImplementedError

    @property
    def total(self) -> Decimal:
        raise NotImplementedError


class DayReport:
    def __init__(self, repository: TripRepository, wall_clock: WallClock) -> None:
        self._repository = repository
        self._wall_clock = wall_clock

    def today(self) -> date:
        raise NotImplementedError

    def for_day(self, day: date | None = None) -> DaySummary:
        raise NotImplementedError
