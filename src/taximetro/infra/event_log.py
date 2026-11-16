# Proyecto: py-taximetro
# fuente: src/taximetro/infra/event_log.py
"""Registro de eventos de operación en ficheros JSON Lines, uno por día."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class FileEventLog:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def record(self, at: datetime, event: str, **data: str) -> None:
        raise NotImplementedError
