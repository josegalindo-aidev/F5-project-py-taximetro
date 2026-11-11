# Proyecto: py-taximetro
# fuente: tests/integration/test_main.py
"""Arranque del programa: conecta las tarifas del fichero con el servicio (US-07)."""

from decimal import Decimal
from pathlib import Path

import pytest

from taximetro.__main__ import build_service, default_rates_path, default_trips_path, main
from taximetro.core.tariff import Tariff
from taximetro.infra.tariff_loader import load_tariff
from tests.fakes import FakeClock, ScriptedInput

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_la_ruta_de_tarifas_sale_de_la_variable_de_entorno():
    environ = {"TAXIMETRO_RATES": "/otra/ruta/rates.toml"}

    assert default_rates_path(environ) == Path("/otra/ruta/rates.toml")


def test_sin_variable_de_entorno_se_usa_el_fichero_del_proyecto():
    assert default_rates_path({}) == PROJECT_ROOT / "config" / "rates.toml"


@pytest.mark.parametrize("value", ["", "   "], ids=["vacia", "solo-espacios"])
def test_una_variable_de_entorno_vacia_se_trata_como_no_definida(value):
    assert default_rates_path({"TAXIMETRO_RATES": value}) == PROJECT_ROOT / "config" / "rates.toml"


# TK-04: dónde se guarda el historial de carreras
def test_la_ruta_del_historial_sale_de_la_variable_de_entorno():
    environ = {"TAXIMETRO_TRIPS": "/otra/ruta/trips.json"}

    assert default_trips_path(environ) == Path("/otra/ruta/trips.json")


def test_sin_variable_de_entorno_el_historial_va_a_la_carpeta_data_del_proyecto():
    assert default_trips_path({}) == PROJECT_ROOT / "data" / "trips.json"


@pytest.mark.parametrize("value", ["", "   "], ids=["vacia", "solo-espacios"])
def test_una_variable_vacia_del_historial_se_trata_como_no_definida(value):
    assert default_trips_path({"TAXIMETRO_TRIPS": value}) == PROJECT_ROOT / "data" / "trips.json"


def test_el_fichero_de_tarifas_del_proyecto_es_valido():
    tariff = load_tariff(PROJECT_ROOT / "config" / "rates.toml")

    assert tariff == Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))


def test_el_servicio_cobra_con_las_tarifas_del_fichero(tmp_path):
    path = tmp_path / "rates.toml"
    path.write_text('[rates]\nstopped = "0.10"\nmoving = "0.20"\n', encoding="utf-8")
    clock = FakeClock()

    service = build_service(path, clock)
    service.start()
    clock.advance(10)

    assert service.finish() == Decimal("1.00")  # 10 s parado a 0,10 EUR/s, no a 0,02


def test_con_un_fichero_de_tarifas_erroneo_muestra_el_error_y_devuelve_1(tmp_path, capsys):
    path = tmp_path / "rates.toml"
    path.write_text('[rates]\nstopped = "abc"\nmoving = "0.05"\n', encoding="utf-8")

    code = main(path)

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.startswith("Error: ")
    assert "'stopped'" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""  # el error va por stderr, no por la salida normal


def test_con_un_fichero_valido_lanza_la_cli_con_esas_tarifas_y_devuelve_0(tmp_path):
    path = tmp_path / "rates.toml"
    path.write_text('[rates]\nstopped = "0.10"\nmoving = "0.20"\n', encoding="utf-8")
    clock = FakeClock()
    steps = [(0, "iniciar"), (10, "finalizar"), (0, "salir")]
    out: list[str] = []

    code = main(
        path,
        clock=clock,
        input_fn=ScriptedInput(clock, steps),
        output_fn=out.append,
    )

    assert code == 0
    assert "Total: 1,00 €" in "\n".join(out)  # 10 s parado a 0,10 EUR/s
