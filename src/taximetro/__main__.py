# Proyecto: py-taximetro
# fuente: src/taximetro/__main__.py
"""Punto de arranque: conecta las piezas y lanza la CLI (`python -m taximetro`)."""

import os
import sys
import time
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from taximetro.core.errors import TariffFileError, TripHistoryError
from taximetro.core.ports import Clock, TripRepository, WallClock
from taximetro.core.trip_service import TripService
from taximetro.infra.repos.json_file import JsonTripRepository
from taximetro.infra.tariff_loader import load_tariff
from taximetro.ui.cli.app import Cli

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRIPS_FILENAME = "trips.json"


def _path_from_environment(environ: Mapping[str, str], name: str, default: Path) -> Path:
    """Ruta de la variable de entorno `name`; vacía o ausente, usa `default`."""
    configured = environ.get(name, "").strip()
    return Path(configured) if configured else default


def default_rates_path(environ: Mapping[str, str]) -> Path:
    default = PROJECT_ROOT / "config" / "rates.toml"
    return _path_from_environment(environ, "TAXIMETRO_RATES", default)


def default_data_dir(environ: Mapping[str, str]) -> Path:
    return _path_from_environment(environ, "TAXIMETRO_DATA_DIR", PROJECT_ROOT / "data")


def local_now() -> datetime:
    """Fecha y hora actuales en la zona horaria del ordenador."""
    return datetime.now().astimezone()


def build_service(
    rates_path: Path,
    repository: TripRepository,
    clock: Clock = time.monotonic,
    wall_clock: WallClock = local_now,
) -> TripService:
    return TripService(load_tariff(rates_path), clock, wall_clock, repository)


def main(
    rates_path: Path | None = None,
    data_dir: Path | None = None,
    *,
    clock: Clock = time.monotonic,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    path = rates_path or default_rates_path(os.environ)
    trips_file = (data_dir or default_data_dir(os.environ)) / TRIPS_FILENAME
    repository = JsonTripRepository(trips_file)
    try:
        service = build_service(path, repository, clock)
        # Lee el historial una vez: si está dañado, se avisa ahora y no al cobrar una carrera.
        repository.list_finished(local_now().date())
    except (TariffFileError, TripHistoryError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    Cli(service, input_fn, output_fn, [f"Historial: {trips_file}"]).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
