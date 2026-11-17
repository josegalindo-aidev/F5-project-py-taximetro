# Proyecto: py-taximetro
# fuente: tests/acceptance/test_us05_historico.py
"""Aceptación de US-05: el taxista ve el histórico del día y persiste entre sesiones."""

import re

from taximetro.bootstrap import local_now
from tests.acceptance.helpers import run_program, write_rates

TWO_TRIPS = [
    (0, "iniciar"),
    (10, "finalizar"),  # 10 s parado: 0,20 €
    (0, "iniciar"),
    (0, "mover"),
    (10, "finalizar"),  # 10 s en movimiento: 0,50 €
    (0, "salir"),
]


def test_us05_el_historico_del_dia_conserva_las_carreras_al_reiniciar(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"
    run_program(rates, data_dir, TWO_TRIPS)  # se cierra el programa

    out = run_program(rates, data_dir, [(0, "historico"), (0, "salir")])  # se vuelve a abrir

    assert "Carreras de hoy:" in out
    assert re.search(r"1\. \d\d:\d\d - \d\d:\d\d  0,20 €", out)
    assert re.search(r"2\. \d\d:\d\d - \d\d:\d\d  0,50 €", out)
    assert "Total del día: 2 carreras, 0,70 €" in out


def test_us05_el_historico_acepta_un_dia_concreto(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"
    run_program(rates, data_dir, TWO_TRIPS)
    today = local_now().date()

    out = run_program(
        rates,
        data_dir,
        [(0, f"historico {today}"), (0, "historico 1999-01-01"), (0, "salir")],
    )

    assert f"Carreras del {today}:" in out
    assert "Total del día: 2 carreras, 0,70 €" in out
    assert "El 1999-01-01 no hubo carreras finalizadas." in out


def test_us05_sin_carreras_el_historico_lo_dice(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"

    out = run_program(rates, data_dir, [(0, "historico"), (0, "salir")])

    assert "Hoy no hay carreras finalizadas." in out
    assert not data_dir.exists()  # consultar no crea nada en disco


def test_us05_una_carrera_sin_finalizar_no_aparece_en_el_historico(tmp_path):
    rates, data_dir = write_rates(tmp_path), tmp_path / "datos"
    run_program(rates, data_dir, [(0, "iniciar"), (10, "finalizar"), (0, "iniciar"), (5, "salir")])

    out = run_program(rates, data_dir, [(0, "historico"), (0, "salir")])

    assert "Total del día: 1 carrera, 0,20 €" in out  # la carrera sin cobrar no cuenta
