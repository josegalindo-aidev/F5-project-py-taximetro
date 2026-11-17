# Proyecto: py-taximetro
# fuente: tests/test_quality_gates.py
"""Umbrales de calidad del repositorio (TK-03): la cobertura del núcleo no puede bajar de 90 %.

`python -m pytest --cov` mide `src/taximetro/core` según la configuración de `pyproject.toml`
y falla si la cobertura baja del mínimo. Estos tests impiden que alguien relaje ese umbral
sin que se note.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINIMUM = 90


def coverage_config() -> dict:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject.get("tool", {}).get("coverage", {})


def test_la_cobertura_se_mide_sobre_el_nucleo():
    assert coverage_config().get("run", {}).get("source") == ["src/taximetro/core"]


def test_la_cobertura_cuenta_tambien_las_ramas():
    assert coverage_config().get("run", {}).get("branch") is True


def test_la_cobertura_minima_del_nucleo_es_al_menos_el_90_por_ciento():
    assert coverage_config().get("report", {}).get("fail_under", 0) >= MINIMUM


def test_la_cobertura_incluye_los_procesos_que_lanzan_las_pruebas():
    # Sin esto, la prueba que arranca `python -m taximetro` en un proceso aparte no cuenta.
    assert "subprocess" in coverage_config().get("run", {}).get("patch", [])
