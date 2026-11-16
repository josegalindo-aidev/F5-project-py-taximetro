# Proyecto: py-taximetro
# fuente: tests/integration/test_logging.py
"""Registro de eventos de operación en disco (US-06)."""

import json
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from taximetro.core.errors import EventLogError
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


def test_los_eventos_se_añaden_en_orden_y_cada_dia_tiene_su_fichero(tmp_path):
    folder = tmp_path / "logs"
    log = FileEventLog(folder)
    day = datetime(2026, 11, 16, 23, 59, 0, tzinfo=MADRID)
    next_day = day + timedelta(minutes=2)

    log.record(day, "carrera_iniciada", carrera="a")
    log.record(day + timedelta(seconds=30), "carrera_finalizada", carrera="a", total="0.20")
    log.record(next_day, "carrera_iniciada", carrera="b")

    first = read_events(folder / "taximetro-2026-11-16.jsonl")
    second = read_events(folder / "taximetro-2026-11-17.jsonl")
    assert [e["evento"] for e in first] == ["carrera_iniciada", "carrera_finalizada"]
    assert [e["carrera"] for e in second] == ["b"]
    assert sorted(f.name for f in folder.iterdir()) == [
        "taximetro-2026-11-16.jsonl",
        "taximetro-2026-11-17.jsonl",
    ]


def test_los_acentos_y_la_enie_se_escriben_legibles(tmp_path):
    folder = tmp_path / "logs"
    log = FileEventLog(folder)

    at = datetime(2026, 11, 16, 10, 0, tzinfo=MADRID)

    log.record(at, "estado_cambiado", estado="en movimiento ñandú")

    text = (folder / "taximetro-2026-11-16.jsonl").read_text(encoding="utf-8")
    assert "ñandú" in text
    assert "u00f1" not in text  # sin la secuencia de escape de JSON para la ñ


# Comprobación al arrancar: la carpeta de logs debe poder usarse, o el programa no arranca.
@pytest.mark.parametrize("subcarpetas", [[], ["2026", "logs"]], ids=["directa", "anidada"])
def test_una_carpeta_de_logs_que_es_un_fichero_se_rechaza_nombrandola(tmp_path, subcarpetas):
    no_es_carpeta = tmp_path / "no-soy-carpeta"
    no_es_carpeta.write_text("esto es un fichero", encoding="utf-8")
    log = FileEventLog(no_es_carpeta.joinpath(*subcarpetas))

    with pytest.raises(EventLogError) as info:
        log.check()

    assert "carpeta de logs" in str(info.value)
    assert "no-soy-carpeta" in str(info.value)
    assert no_es_carpeta.read_text(encoding="utf-8") == "esto es un fichero"  # no se toca


def test_una_carpeta_de_logs_valida_se_crea_y_no_deja_ficheros(tmp_path):
    folder = tmp_path / "datos" / "logs"

    FileEventLog(folder).check()

    assert folder.is_dir()
    assert list(folder.iterdir()) == []  # la comprobación no deja restos


def test_la_comprobacion_prueba_a_escribir_dentro_de_la_carpeta_de_logs(tmp_path, monkeypatch):
    folder = tmp_path / "logs"
    real_temporary_file = tempfile.TemporaryFile

    def temporary_file(*args, dir=None, **kwargs):
        if dir == folder:  # solo en la carpeta de logs no hay permiso de escritura
            raise PermissionError(13, "Permission denied")
        return real_temporary_file(*args, dir=dir, **kwargs)

    monkeypatch.setattr(tempfile, "TemporaryFile", temporary_file)

    with pytest.raises(EventLogError) as info:
        FileEventLog(folder).check()

    assert "Permission denied" in str(info.value)
    assert str(folder) in str(info.value)
