# Proyecto: py-taximetro
# fuente: src/taximetro/__main__.py
"""Punto de arranque: conecta las piezas y lanza la CLI (`python -m taximetro`)."""

import os
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from taximetro.core.day_report import DayReport
from taximetro.core.errors import EventLogError, TariffFileError, TripHistoryError
from taximetro.core.ports import Clock, EventLog, TripRepository, WallClock
from taximetro.core.trip_service import TripService
from taximetro.infra.event_log import FileEventLog
from taximetro.infra.repos.json_file import JsonTripRepository
from taximetro.infra.tariff_loader import load_tariff
from taximetro.settings import Settings
from taximetro.ui.cli.app import Cli


def local_now() -> datetime:
    """Fecha y hora actuales en la zona horaria del ordenador."""
    return datetime.now().astimezone()


def build_service(
    rates_path: Path,
    repository: TripRepository,
    event_log: EventLog,
    clock: Clock = time.monotonic,
    wall_clock: WallClock = local_now,
) -> TripService:
    return TripService(load_tariff(rates_path), clock, wall_clock, repository, event_log)


def main(
    rates_path: Path | None = None,
    data_dir: Path | None = None,
    *,
    clock: Clock = time.monotonic,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    settings = Settings.from_environment(os.environ, rates_path=rates_path, data_dir=data_dir)
    repository = JsonTripRepository(settings.trips_file)
    event_log = FileEventLog(settings.log_dir)
    try:
        service = build_service(settings.rates_path, repository, event_log, clock)
        # Lee el historial una vez: si está dañado, se avisa ahora y no al cobrar una carrera.
        repository.list_finished(local_now().date())
        event_log.check()  # la auditoría es obligatoria: sin carpeta de logs usable no se arranca
    except (TariffFileError, TripHistoryError, EventLogError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    report = DayReport(repository, local_now)
    notes = [f"Historial: {settings.trips_file}", f"Logs: {settings.log_dir}"]
    Cli(service, report, input_fn, output_fn, notes).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
