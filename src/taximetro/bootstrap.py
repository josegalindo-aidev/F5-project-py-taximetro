# Proyecto: py-taximetro
# fuente: src/taximetro/bootstrap.py
"""Montaje de la aplicación: crea las piezas reales a partir de los ajustes y las conecta."""

from __future__ import annotations

from dataclasses import dataclass

from taximetro.core.day_report import DayReport
from taximetro.core.ports import Clock, WallClock
from taximetro.core.trip_service import TripService
from taximetro.settings import Settings


@dataclass(frozen=True)
class Application:
    """Lo que necesita una interfaz (consola, web...) para manejar el taxímetro."""

    service: TripService
    report: DayReport
    notes: tuple[str, ...]


def build_application(settings: Settings, clock: Clock, wall_clock: WallClock) -> Application:
    """Monta la aplicación; lanza `TariffFileError`, `TripHistoryError` o `EventLogError`
    si algo impide arrancar (tarifas ilegibles, historial dañado, carpeta de logs inutilizable)."""
    raise NotImplementedError
