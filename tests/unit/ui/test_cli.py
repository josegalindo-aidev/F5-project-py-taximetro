# Proyecto: py-taximetro
# fuente: tests/unit/ui/test_cli.py
from decimal import Decimal

import pytest

from taximetro.core.day_report import DayReport
from taximetro.core.trip_service import TripService
from taximetro.infra.repos.memory import InMemoryTripRepository
from taximetro.ui.cli.app import Cli
from taximetro.ui.cli.format import format_euros
from tests.fakes import (
    BrokenRepository,
    FakeClock,
    FakeEventLog,
    FakeWallClock,
    ScriptedInput,
    UnreadableHistoryRepository,
    saved_trip,
)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def run_cli(tariff, clock, steps, repository=None, notes=()) -> str:
    """Ejecuta la CLI con una consola simulada y devuelve todo lo impreso."""
    out: list[str] = []
    repository = repository if repository is not None else InMemoryTripRepository()
    wall_clock = FakeWallClock()
    service = TripService(tariff, clock, wall_clock, repository, FakeEventLog())
    report = DayReport(repository, wall_clock)
    Cli(service, report, ScriptedInput(clock, steps), out.append, notes).run()
    return "\n".join(out)


@pytest.mark.parametrize(
    ("amount", "text"),
    [
        (Decimal("0"), "0,00 €"),
        (Decimal("0.7"), "0,70 €"),
        (Decimal("12.345"), "12,35 €"),
        (Decimal("1234.5"), "1234,50 €"),
    ],
)
def test_format_euros(amount, text):
    assert format_euros(amount) == text


# TK-02: instrucciones de uso al arrancar
def test_muestra_instrucciones_al_arrancar(tariff, clock):
    out = run_cli(tariff, clock, [])
    commands = ("iniciar", "parar", "mover", "estado", "finalizar", "historico", "ayuda", "salir")
    for command in commands:
        assert command in out


def test_la_ayuda_explica_que_historico_admite_un_dia(tariff, clock):
    out = run_cli(tariff, clock, [(0, "ayuda")])

    assert "historico AAAA-MM-DD" in out


def test_ayuda_repite_las_instrucciones(tariff, clock):
    out = run_cli(tariff, clock, [(0, "ayuda")])
    assert out.count("finalizar") >= 2


def test_comando_desconocido(tariff, clock):
    out = run_cli(tariff, clock, [(0, "volar")])
    assert "Comando desconocido" in out


def test_ignora_lineas_vacias_y_mayusculas(tariff, clock):
    out = run_cli(tariff, clock, [(0, ""), (0, "  INICIAR  "), (0, "salir")])
    assert "Carrera iniciada" in out
    assert "Comando desconocido" not in out


def test_estado_sin_carrera(tariff, clock):
    out = run_cli(tariff, clock, [(0, "estado")])
    assert "No hay ninguna carrera en curso" in out


def test_estado_con_carrera_muestra_estado_e_importe(tariff, clock):
    out = run_cli(tariff, clock, [(0, "iniciar"), (10, "estado"), (0, "mover"), (10, "estado")])
    assert "parado" in out and "Importe actual: 0,20 €" in out
    assert "en movimiento" in out and "Importe actual: 0,70 €" in out


# Errores amigables: la CLI no se cae
def test_finalizar_sin_carrera_no_rompe(tariff, clock):
    out = run_cli(tariff, clock, [(0, "finalizar"), (0, "iniciar")])
    assert "No hay ninguna carrera en curso" in out
    assert "Carrera iniciada" in out  # sigue funcionando después del error


def test_iniciar_dos_veces_avisa(tariff, clock):
    out = run_cli(tariff, clock, [(0, "iniciar"), (0, "iniciar")])
    assert "Ya hay una carrera en curso" in out


def test_salir_termina_el_bucle(tariff, clock):
    out = run_cli(tariff, clock, [(0, "salir"), (0, "iniciar")])
    assert "Hasta pronto" in out
    assert "Carrera iniciada" not in out  # no procesó nada tras salir


def test_fin_de_entrada_termina_sin_error(tariff, clock):
    out = run_cli(tariff, clock, [(0, "iniciar")])  # luego EOFError
    assert "Hasta pronto" in out


def test_salir_con_carrera_en_curso_avisa(tariff, clock):
    out = run_cli(tariff, clock, [(0, "iniciar"), (0, "salir")])
    assert "La carrera en curso no se ha cobrado" in out


# TK-04: si falla el guardado en el historial, el taxista ve igualmente el total
def test_si_falla_el_guardado_se_muestra_el_total_y_un_aviso(tariff, clock):
    steps = [(0, "iniciar"), (10, "finalizar")]

    out = run_cli(tariff, clock, steps, repository=BrokenRepository())

    assert "Carrera finalizada. Total: 0,20 €" in out
    assert "Aviso: No se pudo guardar la carrera en el historial: disco lleno" in out
    assert out.index("Total") < out.index("Aviso")  # primero el importe


# TK-04: al arrancar se informa de dónde se guarda el historial
def test_al_arrancar_muestra_las_notas_entre_el_titulo_y_las_instrucciones(tariff, clock):
    out = run_cli(tariff, clock, [], notes=["Historial: /datos/trips.json"])

    assert out.index("Taxímetro digital") < out.index("Historial: /datos/trips.json")
    assert out.index("Historial: /datos/trips.json") < out.index("Comandos disponibles")


def test_sin_notas_no_se_imprime_nada_extra(tariff, clock):
    out = run_cli(tariff, clock, [])

    assert "Historial" not in out


# US-05: histórico de carreras. El reloj de pared de las pruebas marca el 11/11/2026 a las 10:00.
def test_historico_lista_las_carreras_de_hoy_con_hora_importe_y_resumen(tariff, clock):
    repository = InMemoryTripRepository()
    saved_trip(repository, "tarde", (11, 11, 40), (11, 11, 52), "12.30")  # se guarda antes...
    saved_trip(repository, "manana", (11, 9, 5), (11, 9, 12), "7.25")  # ...pero es anterior
    saved_trip(repository, "ayer", (10, 23, 50), (10, 23, 59), "99.99")  # otro día

    out = run_cli(tariff, clock, [(0, "historico")], repository)

    assert "Carreras de hoy:" in out
    assert out.index("1. 09:05 - 09:12  7,25 €") < out.index("2. 11:40 - 11:52  12,30 €")
    assert "Total del día: 2 carreras, 19,55 €" in out
    assert "99,99" not in out


def test_historico_sin_carreras_lo_dice_y_no_muestra_un_resumen(tariff, clock):
    repository = InMemoryTripRepository()
    saved_trip(repository, "ayer", (10, 23, 50), (10, 23, 59), "99.99")  # no es de hoy

    out = run_cli(tariff, clock, [(0, "historico")], repository)

    assert "Hoy no hay carreras finalizadas." in out
    assert "Total del día" not in out
    assert "Carreras de hoy:" not in out


def test_historico_con_una_sola_carrera_usa_el_singular(tariff, clock):
    repository = InMemoryTripRepository()
    saved_trip(repository, "unica", (11, 9, 5), (11, 9, 12), "7.25")

    out = run_cli(tariff, clock, [(0, "historico")], repository)

    assert "Total del día: 1 carrera, 7,25 €" in out
    assert "1 carreras" not in out


def test_historico_con_un_dia_lista_las_carreras_de_ese_dia(tariff, clock):
    repository = InMemoryTripRepository()
    saved_trip(repository, "noche", (10, 23, 50), (10, 23, 59), "99.99")  # se guarda antes...
    saved_trip(repository, "manana", (10, 8, 0), (10, 8, 20), "5.00")  # ...pero es anterior
    saved_trip(repository, "hoy", (11, 9, 5), (11, 9, 12), "7.25")  # otro día

    out = run_cli(tariff, clock, [(0, "historico 2026-11-10")], repository)

    assert "Carreras del 2026-11-10:" in out
    assert out.index("1. 08:00 - 08:20  5,00 €") < out.index("2. 23:50 - 23:59  99,99 €")
    assert "Total del día: 2 carreras, 104,99 €" in out
    assert "7,25" not in out
    assert "Comando desconocido" not in out


def test_historico_de_un_dia_sin_carreras_nombra_ese_dia(tariff, clock):
    repository = InMemoryTripRepository()
    saved_trip(repository, "hoy", (11, 9, 5), (11, 9, 12), "7.25")  # solo hay carreras de hoy

    out = run_cli(tariff, clock, [(0, "historico 2026-11-10")], repository)

    assert "El 2026-11-10 no hubo carreras finalizadas." in out
    assert "Hoy no hay" not in out
    assert "Total del día" not in out


def test_historico_con_el_historial_ilegible_muestra_el_error_y_sigue_funcionando(tariff, clock):
    steps = [(0, "historico"), (0, "iniciar")]

    out = run_cli(tariff, clock, steps, repository=UnreadableHistoryRepository())

    assert "El historial 'trips.json' está dañado: no se puede leer" in out
    assert "Carrera iniciada" in out  # el programa sigue aceptando comandos
    assert "Traceback" not in out


@pytest.mark.parametrize(
    "day_text",
    ["ayer", "2026-13-45", "2026-11", "11/11/2026", "2026-11-10 2026-11-11"],
    ids=["texto", "mes-y-dia-imposibles", "fecha-a-medias", "formato-espanol", "dos-fechas"],
)
def test_historico_con_una_fecha_no_valida_avisa_y_no_cierra_el_programa(tariff, clock, day_text):
    out = run_cli(tariff, clock, [(0, f"historico {day_text}"), (0, "iniciar")])

    assert f"Fecha no válida: '{day_text}'. Usa el formato AAAA-MM-DD." in out
    assert "Carrera iniciada" in out  # el programa sigue aceptando comandos
    assert "Carreras del" not in out
