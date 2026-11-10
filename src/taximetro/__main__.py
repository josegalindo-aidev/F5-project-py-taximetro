"""Punto de arranque: conecta las piezas y lanza la CLI (`python -m taximetro`)."""

import time

from taximetro.core.tariff import DEFAULT_TARIFF
from taximetro.core.trip_service import TripService
from taximetro.ui.cli.app import Cli


def main() -> None:
    service = TripService(DEFAULT_TARIFF, time.monotonic)
    Cli(service).run()


if __name__ == "__main__":
    main()
