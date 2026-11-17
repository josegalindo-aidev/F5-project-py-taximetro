# Proyecto: py-taximetro
# fuente: src/taximetro/__main__.py
"""Punto de arranque: conecta las piezas y lanza la CLI (`python -m taximetro`)."""

import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from taximetro.bootstrap import build_application, local_now
from taximetro.core.errors import EventLogError, TariffFileError, TripHistoryError
from taximetro.core.ports import Clock
from taximetro.settings import Settings
from taximetro.ui.cli.app import Cli


def main(
    rates_path: Path | None = None,
    data_dir: Path | None = None,
    *,
    clock: Clock = time.monotonic,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    settings = Settings.from_environment(os.environ, rates_path=rates_path, data_dir=data_dir)
    try:
        app = build_application(settings, clock, local_now)
    except (TariffFileError, TripHistoryError, EventLogError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    Cli(app.service, app.report, input_fn, output_fn, app.notes).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
