# Proyecto: py-taximetro
# fuente: src/taximetro/bootstrap.py
"""Montaje de la aplicación: crea las piezas reales a partir de los ajustes y las conecta."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from taximetro.core.day_report import DayReport
from taximetro.core.ports import Clock, WallClock
from taximetro.core.trip_service import TripService
from taximetro.infra.event_log import FileEventLog
from taximetro.infra.repos.json_file import JsonTripRepository
from taximetro.infra.tariff_loader import load_tariff
from taximetro.settings import Settings


def local_now() -> datetime:
    """Fecha y hora actuales en la zona horaria del ordenador."""
    return datetime.now().astimezone()


@dataclass(frozen=True)
class Application:
    """Lo que necesita una interfaz (consola, web...) para manejar el taxímetro."""

    service: TripService
    report: DayReport
    notes: tuple[str, ...]


def build_application(settings: Settings, clock: Clock, wall_clock: WallClock) -> Application:
    """Monta la aplicación; lanza `TariffFileError`, `TripHistoryError` o `EventLogError`
    si algo impide arrancar (tarifas ilegibles, historial dañado, carpeta de logs inutilizable)."""
    repository = JsonTripRepository(settings.trips_file)
    event_log = FileEventLog(settings.log_dir)
    service = TripService(
        load_tariff(settings.rates_path), clock, wall_clock, repository, event_log
    )
    # Se comprueba todo ahora: un historial dañado o unos logs inutilizables se avisan al arrancar
    # y no a mitad de una carrera. La auditoría es obligatoria, así que sin logs no se arranca.
    repository.check()
    event_log.check()
    notes = (f"Historial: {settings.trips_file}", f"Logs: {settings.log_dir}")
    return Application(service, DayReport(repository, wall_clock), notes)
