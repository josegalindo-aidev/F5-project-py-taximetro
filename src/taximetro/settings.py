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
        return self.data_dir / TRIPS_FILENAME

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str],
        *,
        rates_path: Path | None = None,
        data_dir: Path | None = None,
        log_dir: Path | None = None,
    ) -> Settings:
        return cls(
            rates_path=rates_path or _path_from(environ, "TAXIMETRO_RATES", "config", "rates.toml"),
            data_dir=data_dir or _path_from(environ, "TAXIMETRO_DATA_DIR", "data"),
            log_dir=log_dir or _path_from(environ, "TAXIMETRO_LOG_DIR", "logs"),
        )


def _path_from(environ: Mapping[str, str], name: str, *default: str) -> Path:
    """Ruta de la variable de entorno `name`; si está vacía o ausente, la del proyecto."""
    configured = environ.get(name, "").strip()
    return Path(configured) if configured else PROJECT_ROOT.joinpath(*default)
