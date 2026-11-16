# Proyecto: py-taximetro
# fuente: tests/integration/test_logging.py
"""Registro de eventos de operación en disco (US-06)."""

import json
from datetime import datetime, timedelta, timezone

from taximetro.infra.event_log import FileEventLog

MADRID = timezone(timedelta(hours=1))


def read_events(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_registra_un_evento_como_una_linea_json_en_el_fichero_del_dia(tmp_path):
    folder = tmp_path / "logs"
    log = FileEventLog(folder)

    at = datetime(2026, 11, 16, 10, 5, 0, tzinfo=MADRID)

    log.record(at, "carrera_iniciada", carrera="a1b2c3d4")

    assert read_events(folder / "taximetro-2026-11-16.jsonl") == [
        {"ts": "2026-11-16T10:05:00+01:00", "evento": "carrera_iniciada", "carrera": "a1b2c3d4"}
    ]
