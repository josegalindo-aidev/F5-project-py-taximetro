# Proyecto: py-taximetro
# fuente: tests/acceptance/helpers.py
"""Utilidades compartidas por las pruebas de aceptación que arrancan el programa entero."""

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
