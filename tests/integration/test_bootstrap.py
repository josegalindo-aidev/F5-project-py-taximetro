# Proyecto: py-taximetro
# fuente: tests/integration/test_bootstrap.py
"""Montaje de la aplicación (TK-05): ajustes de entrada, piezas reales conectadas de salida."""

import json
from decimal import Decimal

import pytest

from taximetro.bootstrap import Application, build_application
from taximetro.core.errors import EventLogError, TariffFileError, TripHistoryError
from taximetro.settings import Settings
from tests.fakes import FakeClock, FakeWallClock

RATES = '[rates]\nstopped = "0.10"\nmoving = "0.20"\n'


def settings_in(tmp_path, rates_text: str | None = RATES) -> Settings:
    rates = tmp_path / "rates.toml"
    if rates_text is not None:
        rates.write_text(rates_text, encoding="utf-8")
    return Settings(rates_path=rates, data_dir=tmp_path / "datos", log_dir=tmp_path / "logs")


def build(settings: Settings, clock=None, wall_clock=None) -> Application:
    return build_application(settings, clock or FakeClock(), wall_clock or FakeWallClock())


def one_trip(app: Application, clock: FakeClock) -> Decimal:
    """Una carrera de 10 s parado, de principio a fin."""
    app.service.start()
    clock.advance(10)
    return app.service.finish()


def test_la_aplicacion_cobra_con_las_tarifas_del_fichero_de_los_ajustes(tmp_path):
    clock = FakeClock()
    app = build(settings_in(tmp_path), clock)

    assert one_trip(app, clock) == Decimal("1.00")  # 10 s parado a 0,10 EUR/s


def test_la_carrera_terminada_se_guarda_en_el_historial_de_los_ajustes(tmp_path):
    settings = settings_in(tmp_path)
    clock = FakeClock()
    app = build(settings, clock)

    one_trip(app, clock)

    saved = json.loads(settings.trips_file.read_text(encoding="utf-8"))
    assert [record["total"] for record in saved] == ["1.00"]


def test_el_informe_del_dia_lee_ese_historial_y_usa_el_reloj_de_pared_recibido(tmp_path):
    clock, wall_clock = FakeClock(), FakeWallClock()
    app = build(settings_in(tmp_path), clock, wall_clock)

    one_trip(app, clock)

    summary = app.report.for_day()
    assert summary.day == wall_clock().date()
    assert (summary.count, summary.total) == (1, Decimal("1.00"))


def test_los_eventos_de_la_carrera_se_registran_en_la_carpeta_de_logs_de_los_ajustes(tmp_path):
    settings = settings_in(tmp_path)
    clock = FakeClock()
    app = build(settings, clock)

    one_trip(app, clock)

    assert len(list(settings.log_dir.glob("taximetro-*.jsonl"))) == 1


def test_las_notas_dicen_donde_se_guardan_el_historial_y_los_logs(tmp_path):
    settings = settings_in(tmp_path)

    app = build(settings)

    assert app.notes == (f"Historial: {settings.trips_file}", f"Logs: {settings.log_dir}")


def test_sin_fichero_de_tarifas_no_se_puede_montar(tmp_path):
    with pytest.raises(TariffFileError, match="No se encuentra el fichero de tarifas"):
        build(settings_in(tmp_path, rates_text=None))


def test_con_un_historial_danado_no_se_puede_montar_y_no_se_toca(tmp_path):
    settings = settings_in(tmp_path)
    settings.data_dir.mkdir()
    settings.trips_file.write_text("{esto no es json", encoding="utf-8")

    with pytest.raises(TripHistoryError, match="trips.json"):
        build(settings)

    assert settings.trips_file.read_text(encoding="utf-8") == "{esto no es json"


def test_con_una_carpeta_de_logs_que_es_un_fichero_no_se_puede_montar(tmp_path):
    settings = settings_in(tmp_path)
    settings.log_dir.write_text("esto es un fichero", encoding="utf-8")

    with pytest.raises(EventLogError, match="carpeta de logs"):
        build(settings)
