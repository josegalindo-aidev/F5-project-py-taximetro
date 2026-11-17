# Proyecto: py-taximetro
# fuente: tests/unit/test_verificar.py
"""Script de verificación: la orden que lanza y el veredicto sobre la cobertura."""

import pytest

from scripts.verificar import (
    Options,
    coverage_failures,
    parse_args,
    parse_total_percent,
    pytest_command,
    run,
)

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


class FakeRunner:
    """Lanzador de órdenes de mentira: anota lo que se le pide y contesta con lo programado."""

    def __init__(self, tests=(0, "291 passed in 1.2s\n"), project=95.0, core=98.0, lint=(0, "")):
        self.tests, self.project, self.core, self.lint = tests, project, core, lint
        self.commands: list[list[str]] = []

    def __call__(self, command):
        self.commands.append(command)
        if "pytest" in command:
            return self.tests
        if "coverage" in command:
            only_core = any(part.startswith("--include") for part in command)
            return 0, f"TOTAL   10   0   2   0   {self.core if only_core else self.project:.2f}%\n"
        if "ruff" in command:
            return self.lint
        raise AssertionError(command)

    def launched(self, name: str) -> list[list[str]]:
        return [command for command in self.commands if name in command]


def verify(options=None, runner=None):
    runner = runner or FakeRunner()
    out: list[str] = []
    code = run(options or Options(), PY, runner, out.append)
    return code, "\n".join(out), out, runner


def test_sin_opciones_lanza_pytest_y_los_informes_de_proyecto_y_nucleo():
    _, _, _, runner = verify()

    assert runner.commands[0] == pytest_command(PY, Options())
    assert len(runner.launched("coverage")) == 2
    assert any(
        "--include=src/taximetro/core/*" in command for command in runner.launched("coverage")
    )


def test_todo_en_orden_termina_en_verde_con_codigo_0():
    code, _, out, _ = verify()

    assert code == 0
    assert out[-1].startswith("VERDE")


def test_muestra_la_salida_de_las_pruebas_y_los_informes():
    _, text, _, _ = verify()

    assert "291 passed in 1.2s" in text
    assert "95.00%" in text
    assert "98.00%" in text


def test_con_pruebas_en_rojo_termina_en_rojo_con_codigo_1():
    code, _, out, _ = verify(runner=FakeRunner(tests=(1, "2 failed, 289 passed\n")))

    assert code == 1
    assert out[-1].startswith("ROJO")
    assert "pruebas" in out[-1]


def test_con_cobertura_baja_termina_en_rojo_y_dice_cual():
    code, text, out, _ = verify(runner=FakeRunner(core=85.0))

    assert code == 1
    assert out[-1].startswith("ROJO")
    assert "núcleo" in text


def test_en_modo_rapido_solo_lanza_las_pruebas():
    code, _, out, runner = verify(Options(fast=True))

    assert code == 0
    assert runner.commands == [pytest_command(PY, Options(fast=True))]
    assert out[-1].startswith("VERDE")


def test_una_ejecucion_parcial_avisa_y_no_juzga_la_cobertura():
    code, text, out, _ = verify(Options(paths=("tests/unit",)), FakeRunner(project=11.0, core=40.0))

    assert code == 0
    assert "parcial" in text
    assert out[-1].startswith("VERDE")


def test_una_ejecucion_parcial_con_pruebas_en_rojo_sigue_siendo_rojo():
    code, _, out, _ = verify(Options(paths=("tests/unit",)), FakeRunner(tests=(1, "1 failed\n")))

    assert code == 1
    assert out[-1].startswith("ROJO")


def test_con_lint_lanza_ruff_y_si_falla_es_rojo():
    runner = FakeRunner(lint=(1, "E501 Line too long\n"))

    code, text, out, _ = verify(Options(lint=True), runner)

    assert runner.launched("ruff") == [[PY, "-m", "ruff", "check", "."]]
    assert code == 1
    assert "E501" in text
    assert "estilo" in out[-1]


def test_sin_lint_no_lanza_ruff():
    _, _, _, runner = verify()

    assert runner.launched("ruff") == []


def test_los_argumentos_vacios_dan_las_opciones_por_defecto():
    assert parse_args([]) == Options()


def test_los_argumentos_se_convierten_en_opciones():
    options = parse_args(["--rapido", "--lint", "tests/unit", "tests/contract"])

    assert options == Options(fast=True, lint=True, paths=("tests/unit", "tests/contract"))
