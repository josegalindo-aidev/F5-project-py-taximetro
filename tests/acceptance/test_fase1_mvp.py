"""Aceptación de la Fase 1 (MVP CLI): US-01 a US-04, de principio a fin por la consola."""

import pytest

from taximetro.core.trip_service import TripService
from taximetro.ui.cli.app import Cli
from tests.fakes import FakeClock, ScriptedInput


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def session(tariff, clock, steps) -> str:
    out: list[str] = []
    Cli(TripService(tariff, clock), ScriptedInput(clock, steps), out.append).run()
    return "\n".join(out)


def test_us01_iniciar_carrera_con_un_comando(tariff, clock):
    out = session(tariff, clock, [(0, "iniciar"), (0, "estado")])
    assert "Carrera iniciada" in out
    assert "Importe actual: 0,00 €" in out


def test_us02_cambiar_entre_parado_y_en_movimiento(tariff, clock):
    out = session(
        tariff,
        clock,
        [(0, "iniciar"), (10, "mover"), (10, "parar"), (10, "finalizar")],
    )
    # 10 s parado (0,20) + 10 s en movimiento (0,50) + 10 s parado (0,20)
    assert "Total: 0,90 €" in out


def test_us03_finalizar_muestra_el_total_con_dos_decimales(tariff, clock):
    out = session(tariff, clock, [(0, "iniciar"), (0.5, "finalizar")])
    assert "Total: 0,01 €" in out


def test_us04_encadenar_carreras_sin_cerrar_el_programa(tariff, clock):
    out = session(
        tariff,
        clock,
        [
            (0, "iniciar"),
            (10, "finalizar"),  # 0,20
            (5, "iniciar"),     # el tiempo entre carreras no se cobra
            (0, "mover"),
            (10, "finalizar"),  # 0,50
            (0, "salir"),
        ],
    )
    assert "Total: 0,20 €" in out
    assert "Total: 0,50 €" in out
    assert out.count("Carrera iniciada") == 2
