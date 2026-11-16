# Proyecto: py-taximetro
# fuente: src/taximetro/infra/event_log.py
"""Registro de eventos de operación en ficheros JSON Lines, uno por día."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from taximetro.core.errors import EventLogError


class FileEventLog:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def check(self) -> None:
        """Comprueba que la carpeta existe (la crea) y que se puede escribir en ella."""
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=self._directory):
                pass
        except OSError as error:
            reason = error.strerror or error
            raise EventLogError(
                f"No se puede usar la carpeta de logs '{self._directory}': {reason}"
            ) from error

    def record(self, at: datetime, event: str, **data: str) -> None:
        line = json.dumps({"ts": at.isoformat(), "evento": event, **data}, ensure_ascii=False)
        self._directory.mkdir(parents=True, exist_ok=True)
        file = self._directory / f"taximetro-{at.date().isoformat()}.jsonl"
        with file.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
