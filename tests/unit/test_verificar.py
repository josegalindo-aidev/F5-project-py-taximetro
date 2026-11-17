# Proyecto: py-taximetro
# fuente: tests/unit/test_verificar.py
"""Script de verificación: la orden que lanza y el veredicto sobre la cobertura."""

import pytest

from scripts.verificar import Options, coverage_failures, parse_total_percent, pytest_command

PY = "python"
BASE = [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
COVERAGE = ["--cov=src/taximetro", "--cov-branch", "--cov-report="]


def test_por_defecto_lanza_toda_la_suite_con_cobertura_de_ramas():
    assert pytest_command(PY, Options()) == BASE + COVERAGE


def test_en_modo_rapido_lanza_las_pruebas_sin_cobertura():
    assert pytest_command(PY, Options(fast=True)) == BASE


def test_con_rutas_lanza_solo_esas_pruebas_y_conserva_la_cobertura():
    command = pytest_command(PY, Options(paths=("tests/unit/core", "tests/contract")))

    assert command == BASE + COVERAGE + ["tests/unit/core", "tests/contract"]


def test_rapido_y_rutas_se_combinan():
    command = pytest_command(PY, Options(fast=True, paths=("tests/unit",)))

    assert command == BASE + ["tests/unit"]


def test_la_ejecucion_con_rutas_es_parcial_y_sin_rutas_es_completa():
    assert Options(paths=("tests/unit",)).partial
    assert not Options().partial


REPORT = """Name                          Stmts   Miss Branch BrPart    Cover
-------------------------------------------------------------------
src/taximetro/core/trip.py       50      0     10      0  100.00%
-------------------------------------------------------------------
TOTAL                           221      3     20      1   98.76%
"""


def test_lee_el_porcentaje_de_la_linea_total_del_informe():
    assert parse_total_percent(REPORT) == pytest.approx(98.76)


def test_lee_tambien_un_porcentaje_entero():
    assert parse_total_percent("TOTAL   10   0   2   0   100%\n") == 100.0


def test_un_informe_sin_linea_total_es_un_error():
    with pytest.raises(ValueError, match="TOTAL"):
        parse_total_percent("No data to report.\n")


def test_con_la_cobertura_en_o_sobre_los_minimos_no_hay_fallos():
    assert coverage_failures(80.0, 90.0) == []


def test_la_cobertura_del_proyecto_por_debajo_del_minimo_es_un_fallo():
    failures = coverage_failures(79.99, 95.0)

    assert len(failures) == 1
    assert "proyecto" in failures[0]
    assert "79.99" in failures[0]


def test_la_cobertura_del_nucleo_por_debajo_del_minimo_es_un_fallo():
    failures = coverage_failures(95.0, 89.5)

    assert len(failures) == 1
    assert "núcleo" in failures[0]


def test_si_fallan_los_dos_se_informa_de_los_dos():
    assert len(coverage_failures(10.0, 10.0)) == 2


def test_los_minimos_se_pueden_cambiar():
    assert coverage_failures(50.0, 60.0, min_project=50.0, min_core=60.0) == []
