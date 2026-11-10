# Proyecto: py-taximetro
# fuente: tests/integration/test_tariff_loader.py
"""Cargador de tarifas desde un fichero TOML (US-07)."""

import re
import tomllib
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest

from taximetro.core.errors import TariffFileError
from taximetro.core.tariff import Tariff
from taximetro.infra.tariff_loader import load_tariff

VALID = {"stopped": "0.02", "moving": "0.05"}

INVALID_VALUES = [
    pytest.param("abc", "no es un número:", id="texto"),
    pytest.param("1,5", "no es un número:", id="coma-decimal"),
    pytest.param("-0.02", "no puede ser negativo", id="negativo"),
    pytest.param("NaN", "no es un número finito", id="nan"),
    pytest.param("Infinity", "no es un número finito", id="infinito"),
]


# (cómo se crea el fichero problemático, excepción original que debe quedar como causa)
CAUSES = [
    pytest.param(lambda p: p / "no_existe.toml", FileNotFoundError, id="inexistente"),
    pytest.param(lambda p: p, OSError, id="directorio"),
    pytest.param(
        lambda p: write_raw(p, b'[rates]\nstopped = "\xff"\n'),
        UnicodeDecodeError,
        id="utf8",
    ),
    pytest.param(lambda p: write_rates(p, "[rates\n"), tomllib.TOMLDecodeError, id="sintaxis"),
    pytest.param(lambda p: write_rates(p, 'otra = "cosa"\n'), KeyError, id="tabla-ausente"),
    pytest.param(lambda p: write_rates(p, rates_toml(stopped="1")), KeyError, id="clave-ausente"),
    pytest.param(
        lambda p: write_rates(p, rates_toml(stopped="abc", moving="1")),
        InvalidOperation,
        id="no-numerico",
    ),
]


def rates_toml(**values: str) -> str:
    """Contenido de un rates.toml con solo las claves indicadas."""
    lines = [f'{key} = "{value}"' for key, value in values.items()]
    return "[rates]\n" + "\n".join(lines) + "\n"


def write_rates(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "rates.toml"
    path.write_text(content, encoding="utf-8")
    return path


def write_raw(tmp_path: Path, data: bytes) -> Path:
    path = tmp_path / "rates.toml"
    path.write_bytes(data)
    return path


def test_carga_las_tarifas_de_un_fichero_toml(tmp_path):
    path = write_rates(tmp_path, rates_toml(**VALID))

    tariff = load_tariff(path)

    assert tariff == Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))


@pytest.mark.parametrize("missing", ["stopped", "moving"])
def test_falta_una_clave_de_tarifa_y_el_error_la_nombra(tmp_path, missing):
    present = {key: value for key, value in VALID.items() if key != missing}
    path = write_rates(tmp_path, rates_toml(**present))

    with pytest.raises(TariffFileError, match=missing):
        load_tariff(path)


def test_falta_la_tabla_rates_y_el_error_la_nombra(tmp_path):
    path = write_rates(tmp_path, 'otra = "cosa"\n')

    with pytest.raises(TariffFileError, match=r"\[rates\]"):
        load_tariff(path)


@pytest.mark.parametrize("key", ["stopped", "moving"])
@pytest.mark.parametrize(("value", "reason"), INVALID_VALUES)
def test_un_valor_invalido_lanza_un_error_con_la_clave_y_el_motivo(tmp_path, key, value, reason):
    path = write_rates(tmp_path, rates_toml(**{**VALID, key: value}))

    with pytest.raises(TariffFileError, match=rf"'{key}' {re.escape(reason)}"):
        load_tariff(path)


@pytest.mark.parametrize("content", ["rates = 5\n", 'rates = "hola"\n'], ids=["entero", "texto"])
def test_rates_que_no_es_una_tabla_lanza_un_error_claro(tmp_path, content):
    path = write_rates(tmp_path, content)

    with pytest.raises(TariffFileError, match=r"\[rates\] debe ser una tabla"):
        load_tariff(path)


@pytest.mark.parametrize("key", ["stopped", "moving"])
def test_un_numero_sin_comillas_lanza_un_error_que_pide_las_comillas(tmp_path, key):
    # En TOML 0.02 (sin comillas) es un float binario: arrastraría un error de redondeo.
    raw = {"stopped": '"0.02"', "moving": '"0.05"', key: "0.02"}
    content = "[rates]\n" + "\n".join(f"{name} = {value}" for name, value in raw.items()) + "\n"
    path = write_rates(tmp_path, content)

    with pytest.raises(TariffFileError, match=rf"'{key}' debe escribirse entre comillas"):
        load_tariff(path)


def test_un_toml_con_sintaxis_rota_lanza_un_error_claro(tmp_path):
    path = write_rates(tmp_path, '[rates\nstopped = "0.02"\n')  # falta el "]"

    with pytest.raises(TariffFileError, match="errores de sintaxis"):
        load_tariff(path)


def test_un_fichero_inexistente_lanza_un_error_claro(tmp_path):
    missing = tmp_path / "no_existe.toml"

    with pytest.raises(TariffFileError, match="no_existe.toml"):
        load_tariff(missing)


def test_una_ruta_que_no_es_un_fichero_lanza_un_error_claro(tmp_path):
    # tmp_path es un directorio: existe, pero no se puede leer como fichero.
    with pytest.raises(TariffFileError, match="No se puede leer"):
        load_tariff(tmp_path)


def test_un_fichero_que_no_es_utf8_lanza_un_error_que_menciona_la_codificacion(tmp_path):
    path = tmp_path / "rates.toml"
    # \xff\xfe no son una secuencia válida en UTF-8
    path.write_bytes(b'[rates]\nstopped = "\xff\xfe"\nmoving = "0.05"\n')

    with pytest.raises(TariffFileError, match="UTF-8"):
        load_tariff(path)


def test_el_mensaje_de_ruta_ilegible_no_repite_la_ruta(tmp_path):
    with pytest.raises(TariffFileError) as info:
        load_tariff(tmp_path)  # un directorio

    # Se cuenta el nombre de la carpeta: el error del sistema duplica las barras de la ruta.
    assert str(info.value).count(tmp_path.name) == 1


@pytest.mark.parametrize(("make_path", "cause"), CAUSES)
def test_el_error_conserva_la_causa_original(tmp_path, make_path, cause):
    path = make_path(tmp_path)

    with pytest.raises(TariffFileError) as info:
        load_tariff(path)

    assert isinstance(info.value.__cause__, cause)
