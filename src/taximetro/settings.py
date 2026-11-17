# Proyecto: py-taximetro
# fuente: src/taximetro/settings.py
"""Ajustes del programa: de dónde salen las tarifas, los datos y los logs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRIPS_FILENAME = "trips.json"


@dataclass(frozen=True)
class Settings:
    rates_path: Path
    data_dir: Path
    log_dir: Path

    @property
    def trips_file(self) -> Path:
        raise NotImplementedError

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str],
        *,
        rates_path: Path | None = None,
        data_dir: Path | None = None,
        log_dir: Path | None = None,
    ) -> Settings:
        raise NotImplementedError
