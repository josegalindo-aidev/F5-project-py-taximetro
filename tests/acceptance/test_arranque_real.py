# Proyecto: py-taximetro
# fuente: tests/acceptance/test_arranque_real.py
"""Arranque real: se lanza `python -m taximetro` en un proceso aparte, como lo haría una persona."""

import json
import os
import subprocess
import sys
from pathlib import Path


def launch(tmp_path: Path, typed: str, **extra_env: str) -> subprocess.CompletedProcess:
    """Ejecuta `python -m taximetro` con datos y logs temporales y `typed` como entrada."""
    env = {
        **os.environ,
        "TAXIMETRO_DATA_DIR": str(tmp_path / "datos"),
        "TAXIMETRO_LOG_DIR": str(tmp_path / "logs"),
        "PYTHONUTF8": "1",
        **extra_env,
    }
    return subprocess.run(
        [sys.executable, "-m", "taximetro"],
        input=typed,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=30,
    )


def test_el_programa_arranca_muestra_la_ayuda_y_termina_con_codigo_0(tmp_path):
    result = launch(tmp_path, "salir\n")

    assert result.returncode == 0
    assert "Comandos disponibles:" in result.stdout
    assert f"Historial: {tmp_path / 'datos' / 'trips.json'}" in result.stdout
    assert f"Logs: {tmp_path / 'logs'}" in result.stdout
    assert result.stderr == ""


def test_una_carrera_completa_se_guarda_en_la_carpeta_de_datos(tmp_path):
    result = launch(tmp_path, "iniciar\nfinalizar\nsalir\n")

    assert result.returncode == 0
    assert "Total:" in result.stdout
    saved = json.loads((tmp_path / "datos" / "trips.json").read_text(encoding="utf-8"))
    assert len(saved) == 1


def test_con_un_fichero_de_tarifas_inexistente_termina_con_codigo_1_y_el_error_por_stderr(
    tmp_path,
):
    result = launch(tmp_path, "salir\n", TAXIMETRO_RATES=str(tmp_path / "no-existe.toml"))

    assert result.returncode == 1
    assert result.stderr.startswith("Error: No se encuentra el fichero de tarifas")
    assert "Traceback" not in result.stderr
    assert result.stdout == ""
