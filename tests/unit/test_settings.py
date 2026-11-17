# Proyecto: py-taximetro
# fuente: tests/unit/test_settings.py
"""Ajustes del programa: rutas de las tarifas, los datos y los logs."""

from pathlib import Path

import pytest

from taximetro.settings import PROJECT_ROOT, Settings

ENVIRON = {
    "TAXIMETRO_RATES": "/otra/ruta/rates.toml",
    "TAXIMETRO_DATA_DIR": "/montaje/datos",
    "TAXIMETRO_LOG_DIR": "/montaje/logs",
}


def test_las_rutas_salen_de_las_variables_de_entorno():
    settings = Settings.from_environment(ENVIRON)

    assert settings.rates_path == Path("/otra/ruta/rates.toml")
    assert settings.data_dir == Path("/montaje/datos")
    assert settings.log_dir == Path("/montaje/logs")


def test_sin_variables_se_usan_las_rutas_del_proyecto():
    settings = Settings.from_environment({})

    assert settings.rates_path == PROJECT_ROOT / "config" / "rates.toml"
    assert settings.data_dir == PROJECT_ROOT / "data"
    assert settings.log_dir == PROJECT_ROOT / "logs"


@pytest.mark.parametrize("value", ["", "   "], ids=["vacia", "solo-espacios"])
@pytest.mark.parametrize(
    ("variable", "attribute", "default"),
    [
        ("TAXIMETRO_RATES", "rates_path", PROJECT_ROOT / "config" / "rates.toml"),
        ("TAXIMETRO_DATA_DIR", "data_dir", PROJECT_ROOT / "data"),
        ("TAXIMETRO_LOG_DIR", "log_dir", PROJECT_ROOT / "logs"),
    ],
    ids=["tarifas", "datos", "logs"],
)
def test_una_variable_vacia_se_trata_como_no_definida(variable, attribute, default, value):
    settings = Settings.from_environment({variable: value})

    assert getattr(settings, attribute) == default


def test_un_valor_explicito_manda_sobre_el_entorno():
    settings = Settings.from_environment(
        ENVIRON,
        rates_path=Path("explicita/rates.toml"),
        data_dir=Path("explicita/datos"),
        log_dir=Path("explicita/logs"),
    )

    assert settings.rates_path == Path("explicita/rates.toml")
    assert settings.data_dir == Path("explicita/datos")
    assert settings.log_dir == Path("explicita/logs")


def test_solo_se_sustituye_lo_que_se_indica():
    settings = Settings.from_environment(ENVIRON, data_dir=Path("explicita/datos"))

    assert settings.data_dir == Path("explicita/datos")
    assert settings.rates_path == Path("/otra/ruta/rates.toml")  # sigue el entorno


def test_el_historial_es_trips_json_dentro_de_la_carpeta_de_datos():
    settings = Settings.from_environment({"TAXIMETRO_DATA_DIR": "/montaje/datos"})

    assert settings.trips_file == Path("/montaje/datos") / "trips.json"
