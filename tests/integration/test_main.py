# Proyecto: py-taximetro
# fuente: tests/integration/test_main.py
"""Arranque del programa: conecta las tarifas del fichero con el servicio (US-07)."""

import json
from decimal import Decimal
from pathlib import Path

from taximetro.__main__ import main
from taximetro.core.tariff import Tariff
from taximetro.infra.tariff_loader import load_tariff
from taximetro.settings import PROJECT_ROOT
from tests.fakes import FakeClock, ScriptedInput


def test_el_fichero_de_tarifas_del_proyecto_es_valido():
    tariff = load_tariff(PROJECT_ROOT / "config" / "rates.toml")

    assert tariff == Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))


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


def test_al_arrancar_el_programa_indica_donde_guarda_el_historial(tmp_path):
    data_dir = tmp_path / "datos"
    clock = FakeClock()
    out: list[str] = []

    main(
        write_rates(tmp_path),
        data_dir,
        clock=clock,
        input_fn=ScriptedInput(clock, [(0, "salir")]),
        output_fn=out.append,
    )

    assert f"Historial: {data_dir / 'trips.json'}" in out


def test_con_un_historial_ilegible_muestra_el_error_y_devuelve_1_sin_arrancar_la_cli(
    tmp_path, capsys
):
    data_dir = tmp_path / "datos"
    (data_dir / "trips.json").mkdir(parents=True)  # existe, pero no es un fichero legible
    clock = FakeClock()
    out: list[str] = []

    code = main(
        write_rates(tmp_path),
        data_dir,
        clock=clock,
        input_fn=ScriptedInput(clock, [(0, "iniciar")]),
        output_fn=out.append,
    )

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.startswith("Error: No se pudo leer el historial")
    assert "Traceback" not in captured.err
    assert out == []  # la CLI no llegó a arrancar


def test_si_la_carpeta_de_datos_es_un_fichero_muestra_el_error_y_devuelve_1(tmp_path, capsys):
    no_es_carpeta = tmp_path / "no-soy-carpeta"
    no_es_carpeta.write_text("esto es un fichero", encoding="utf-8")
    clock = FakeClock()
    out: list[str] = []

    code = main(
        write_rates(tmp_path),
        no_es_carpeta,
        clock=clock,
        input_fn=ScriptedInput(clock, [(0, "iniciar")]),
        output_fn=out.append,
    )

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.startswith("Error: ")
    assert "no es una carpeta" in captured.err
    assert "Traceback" not in captured.err
    assert out == []  # la CLI no llegó a arrancar


# US-06: si la carpeta de logs no se puede usar, el programa no arranca
def test_si_la_carpeta_de_logs_es_un_fichero_muestra_el_error_y_devuelve_1(
    tmp_path, capsys, monkeypatch
):
    no_es_carpeta = tmp_path / "no-soy-carpeta"
    no_es_carpeta.write_text("esto es un fichero", encoding="utf-8")
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(no_es_carpeta))
    clock = FakeClock()
    out: list[str] = []

    code = main(
        write_rates(tmp_path),
        tmp_path / "datos",
        clock=clock,
        input_fn=ScriptedInput(clock, [(0, "iniciar")]),
        output_fn=out.append,
    )

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.startswith("Error: ")
    assert "carpeta de logs" in captured.err
    assert "no-soy-carpeta" in captured.err
    assert "Traceback" not in captured.err
    assert out == []  # la CLI no llegó a arrancar
    assert no_es_carpeta.read_text(encoding="utf-8") == "esto es un fichero"  # no se toca


def test_al_arrancar_el_programa_indica_donde_guarda_los_logs(tmp_path, monkeypatch):
    logs = tmp_path / "mis-logs"
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(logs))
    clock = FakeClock()
    out: list[str] = []

    main(
        write_rates(tmp_path),
        tmp_path / "datos",
        clock=clock,
        input_fn=ScriptedInput(clock, [(0, "salir")]),
        output_fn=out.append,
    )

    help_at = next(i for i, line in enumerate(out) if line.startswith("Comandos disponibles:"))
    assert f"Logs: {logs}" in out
    assert out.index(f"Logs: {logs}") < help_at  # va con las notas, antes de la ayuda
