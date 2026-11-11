# Proyecto: py-taximetro
# fuente: tests/acceptance/test_fase2_historial.py
"""Aceptación de TK-04 (Fase 2): el historial de carreras sobrevive al cierre del programa."""

import json
from pathlib import Path

from taximetro.__main__ import main
from tests.fakes import FakeClock, ScriptedInput


def write_rates(tmp_path: Path) -> Path:
    path = tmp_path / "rates.toml"
    path.write_text('[rates]\nstopped = "0.02"\nmoving = "0.05"\n', encoding="utf-8")
    return path


def run_program(rates: Path, data_dir: Path, steps) -> str:
    """Arranca el programa entero (como `python -m taximetro`) y devuelve lo que muestra."""
    clock = FakeClock()
    out: list[str] = []
    code = main(
        rates,
        data_dir,
        clock=clock,
        input_fn=ScriptedInput(clock, steps),
        output_fn=out.append,
    )
    assert code == 0
    return "\n".join(out)


def saved_totals(data_dir: Path) -> list[str]:
    records = json.loads((data_dir / "trips.json").read_text(encoding="utf-8"))
    return [record["total"] for record in records]


def test_las_carreras_terminadas_se_conservan_al_reiniciar_el_programa(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"

    first = run_program(
        rates,
        data_dir,
        [
            (0, "iniciar"),
            (10, "finalizar"),  # 10 s parado: 0,20
            (0, "iniciar"),
            (0, "mover"),
            (10, "finalizar"),  # 10 s en movimiento: 0,50
            (0, "salir"),
        ],
    )
    assert "Total: 0,20 €" in first and "Total: 0,50 €" in first
    assert saved_totals(data_dir) == ["0.20", "0.50"]

    # Se cierra el programa y se vuelve a abrir sobre la misma carpeta de datos.
    second = run_program(rates, data_dir, [(0, "iniciar"), (5, "finalizar"), (0, "salir")])

    assert "Total: 0,10 €" in second
    assert saved_totals(data_dir) == ["0.20", "0.50", "0.10"]  # nada se perdió, en orden


def test_una_carrera_sin_finalizar_no_se_guarda(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"

    out = run_program(rates, data_dir, [(0, "iniciar"), (10, "salir")])

    assert "La carrera en curso no se ha cobrado" in out
    assert not (data_dir / "trips.json").exists()


def test_el_programa_dice_donde_guarda_el_historial_en_cada_arranque(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"

    for _ in range(2):
        out = run_program(rates, data_dir, [(0, "salir")])
        assert f"Historial: {data_dir / 'trips.json'}" in out
