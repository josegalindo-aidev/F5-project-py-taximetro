# Proyecto: py-taximetro
# fuente: tests/integration/test_main.py
"""Arranque del programa: conecta las tarifas del fichero con el servicio (US-07)."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from taximetro.__main__ import build_service, default_data_dir, default_rates_path, main
from taximetro.core.tariff import Tariff
from taximetro.infra.repos.memory import InMemoryTripRepository
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


# TK-04: carpeta de datos (historial). Se configura como directorio, no como fichero, para poder
# montarla aparte en producción: la escritura atómica necesita crear un temporal a su lado.
def test_la_carpeta_de_datos_sale_de_la_variable_de_entorno():
    environ = {"TAXIMETRO_DATA_DIR": "/otra/ruta/datos"}

    assert default_data_dir(environ) == Path("/otra/ruta/datos")


def test_sin_variable_de_entorno_los_datos_van_a_la_carpeta_data_del_proyecto():
    assert default_data_dir({}) == PROJECT_ROOT / "data"


@pytest.mark.parametrize("value", ["", "   "], ids=["vacia", "solo-espacios"])
def test_una_variable_vacia_de_la_carpeta_de_datos_se_trata_como_no_definida(value):
    assert default_data_dir({"TAXIMETRO_DATA_DIR": value}) == PROJECT_ROOT / "data"


def test_el_fichero_de_tarifas_del_proyecto_es_valido():
    tariff = load_tariff(PROJECT_ROOT / "config" / "rates.toml")

    assert tariff == Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))


def test_el_servicio_cobra_con_las_tarifas_del_fichero(tmp_path):
    path = tmp_path / "rates.toml"
    path.write_text('[rates]\nstopped = "0.10"\nmoving = "0.20"\n', encoding="utf-8")
    clock = FakeClock()

    service = build_service(path, InMemoryTripRepository(), clock)
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
        tmp_path,
        clock=clock,
        input_fn=ScriptedInput(clock, steps),
        output_fn=out.append,
    )

    assert code == 0
    assert "Total: 1,00 €" in "\n".join(out)  # 10 s parado a 0,10 EUR/s


# TK-04: el programa real guarda las carreras en disco
def run_one_trip(rates: Path, data_dir: Path | None) -> int:
    clock = FakeClock()
    steps = [(0, "iniciar"), (10, "finalizar"), (0, "salir")]
    return main(
        rates,
        data_dir,
        clock=clock,
        input_fn=ScriptedInput(clock, steps),
        output_fn=lambda _: None,
    )


def write_rates(tmp_path: Path) -> Path:
    path = tmp_path / "rates.toml"
    path.write_text('[rates]\nstopped = "0.10"\nmoving = "0.20"\n', encoding="utf-8")
    return path


def test_el_programa_guarda_la_carrera_finalizada_en_trips_json_de_la_carpeta_de_datos(tmp_path):
    data_dir = tmp_path / "datos"

    code = run_one_trip(write_rates(tmp_path), data_dir)

    assert code == 0
    saved = json.loads((data_dir / "trips.json").read_text(encoding="utf-8"))
    assert [record["total"] for record in saved] == ["1.00"]


def test_sin_ruta_explicita_los_datos_van_donde_dice_la_variable(tmp_path, monkeypatch):
    data_dir = tmp_path / "del-entorno"
    monkeypatch.setenv("TAXIMETRO_DATA_DIR", str(data_dir))

    run_one_trip(write_rates(tmp_path), None)

    assert len(json.loads((data_dir / "trips.json").read_text(encoding="utf-8"))) == 1


def test_con_un_historial_danado_muestra_el_error_y_devuelve_1_sin_arrancar_la_cli(
    tmp_path, capsys
):
    trips = tmp_path / "datos" / "trips.json"
    trips.parent.mkdir()
    trips.write_text("{esto no es json", encoding="utf-8")
    clock = FakeClock()
    out: list[str] = []

    code = main(
        write_rates(tmp_path),
        trips.parent,
        clock=clock,
        input_fn=ScriptedInput(clock, [(0, "iniciar")]),
        output_fn=out.append,
    )

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.startswith("Error: ")
    assert "trips.json" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""
    assert out == []  # la CLI no llegó a arrancar
    assert trips.read_text(encoding="utf-8") == "{esto no es json"  # no se toca
