# Proyecto: py-taximetro
# fuente: tests/acceptance/test_us06_logs.py
"""Aceptación de US-06: el responsable puede auditar el uso con los logs de operación."""

import json
from datetime import datetime

from taximetro.__main__ import main
from tests.acceptance.helpers import run_program, write_rates


def read_log(logs) -> list[dict]:
    """Eventos del único fichero de log que hay en la carpeta, en el orden en que se escribieron."""
    files = sorted(logs.glob("taximetro-*.jsonl"))
    assert len(files) == 1, files
    return [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()]


def test_us06_una_carrera_deja_inicio_cambio_de_estado_y_fin_con_marca_de_tiempo(
    tmp_path, monkeypatch
):
    logs = tmp_path / "logs"
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(logs))

    run_program(
        write_rates(tmp_path),
        tmp_path / "datos",
        [(0, "iniciar"), (10, "mover"), (10, "finalizar"), (0, "salir")],
    )

    events = read_log(logs)
    assert [e["evento"] for e in events] == [
        "carrera_iniciada",
        "estado_cambiado",
        "carrera_finalizada",
    ]
    assert len({e["carrera"] for e in events}) == 1  # las tres son de la misma carrera
    assert events[1]["estado"] == "moving"
    assert events[2]["total"] == "0.70"  # 10 s parado (0,20) + 10 s en movimiento (0,50)
    times = [datetime.fromisoformat(e["ts"]) for e in events]
    assert all(t.tzinfo is not None for t in times)  # con zona horaria
    assert times == sorted(times)


def test_us06_los_eventos_se_acumulan_aunque_se_reinicie_el_programa(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(logs))
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"

    run_program(rates, data_dir, [(0, "iniciar"), (5, "finalizar"), (0, "salir")])
    run_program(rates, data_dir, [(0, "iniciar"), (5, "finalizar"), (0, "salir")])

    events = read_log(logs)
    assert [e["evento"] for e in events] == ["carrera_iniciada", "carrera_finalizada"] * 2
    assert len({e["carrera"] for e in events}) == 2  # el segundo arranque no pisó el primero


def test_us06_una_carrera_sin_finalizar_deja_constancia_de_que_empezo(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(logs))

    run_program(write_rates(tmp_path), tmp_path / "datos", [(0, "iniciar"), (5, "salir")])

    assert [e["evento"] for e in read_log(logs)] == ["carrera_iniciada"]


def test_us06_sin_una_carpeta_de_logs_usable_el_programa_no_arranca(
    tmp_path, monkeypatch, capsys
):
    no_es_carpeta = tmp_path / "no-soy-carpeta"
    no_es_carpeta.write_text("esto es un fichero", encoding="utf-8")
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(no_es_carpeta))

    code = main(
        write_rates(tmp_path),
        tmp_path / "datos",
        input_fn=lambda _: "salir",
        output_fn=lambda _: None,
    )

    assert code == 1
    assert "carpeta de logs" in capsys.readouterr().err
