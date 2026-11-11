# Proyecto: py-taximetro
# fuente: src/taximetro/__main__.py
"""Punto de arranque: conecta las piezas y lanza la CLI (`python -m taximetro`)."""

import os
import sys
import time
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from taximetro.core.errors import TariffFileError
from taximetro.core.ports import Clock, TripRepository, WallClock
from taximetro.core.trip_service import TripService
from taximetro.infra.repos.memory import InMemoryTripRepository
from taximetro.infra.tariff_loader import load_tariff
from taximetro.ui.cli.app import Cli

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def default_rates_path(environ: Mapping[str, str]) -> Path:
    configured = environ.get("TAXIMETRO_RATES", "").strip()
    if configured:
        return Path(configured)
    return PROJECT_ROOT / "config" / "rates.toml"


def default_trips_path(environ: Mapping[str, str]) -> Path:
    configured = environ.get("TAXIMETRO_TRIPS", "").strip()
    if configured:
        return Path(configured)
    return PROJECT_ROOT / "data" / "trips.json"


def local_now() -> datetime:
    """Fecha y hora actuales en la zona horaria del ordenador."""
    return datetime.now().astimezone()


def build_service(
    rates_path: Path,
    clock: Clock = time.monotonic,
    wall_clock: WallClock = local_now,
    repository: TripRepository | None = None,
) -> TripService:
    return TripService(
        load_tariff(rates_path),
        clock,
        wall_clock,
        repository if repository is not None else InMemoryTripRepository(),
    )


def main(
    rates_path: Path | None = None,
    *,
    clock: Clock = time.monotonic,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    path = rates_path or default_rates_path(os.environ)
    try:
        service = build_service(path, clock)
    except TariffFileError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    Cli(service, input_fn, output_fn).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
