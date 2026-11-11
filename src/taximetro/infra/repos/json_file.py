# Proyecto: py-taximetro
# fuente: src/taximetro/infra/repos/json_file.py
"""Repositorio de carreras en un fichero JSON: sobrevive al cierre del programa."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from taximetro.core.trip import Trip


class JsonTripRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, trip: Trip) -> None:
        raise NotImplementedError

    def list_finished(self, day: date) -> list[Trip]:
        raise NotImplementedError
