# Proyecto: py-taximetro
# fuente: src/taximetro/infra/event_log.py
"""Registro de eventos de operación en ficheros JSON Lines, uno por día."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class FileEventLog:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def check(self) -> None:
        raise NotImplementedError

    def record(self, at: datetime, event: str, **data: str) -> None:
        line = json.dumps({"ts": at.isoformat(), "evento": event, **data}, ensure_ascii=False)
        self._directory.mkdir(parents=True, exist_ok=True)
        file = self._directory / f"taximetro-{at.date().isoformat()}.jsonl"
        with file.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
