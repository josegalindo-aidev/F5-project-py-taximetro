# Proyecto: py-taximetro
# fuente: src/taximetro/infra/tariff_loader.py
"""Carga de tarifas desde un fichero TOML."""

import tomllib
from decimal import Decimal, InvalidOperation
from pathlib import Path

from taximetro.core.errors import TariffFileError
from taximetro.core.tariff import Tariff


def load_tariff(path: Path) -> Tariff:
    rates = _rates_table(_read_toml(path), path)
    stopped, moving = _required_values(rates, ("stopped", "moving"), path)
    return Tariff(
        stopped=_to_decimal(stopped, "stopped", path),
        moving=_to_decimal(moving, "moving", path),
    )


def _read_toml(path: Path) -> dict:
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except FileNotFoundError as error:
        raise TariffFileError(f"No se encuentra el fichero de tarifas: {path}") from error
    except OSError as error:
        raise TariffFileError(
            f"No se puede leer el fichero de tarifas ({error.strerror or error}): {path}"
        ) from error
    except UnicodeDecodeError as error:
        raise TariffFileError(
            f"El fichero de tarifas debe estar guardado en UTF-8 ({error}): {path}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise TariffFileError(
            f"El fichero de tarifas tiene errores de sintaxis ({error}): {path}"
        ) from error


def _rates_table(data: dict, path: Path) -> dict:
    try:
        rates = data["rates"]
    except KeyError as error:
        raise TariffFileError(f"Falta la sección [rates] en {path}") from error
    if not isinstance(rates, dict):
        raise TariffFileError(f"[rates] debe ser una tabla, no un valor suelto: {path}")
    return rates


def _required_values(rates: dict, keys: tuple[str, ...], path: Path) -> list:
    try:
        return [rates[key] for key in keys]
    except KeyError as error:
        raise TariffFileError(f"Falta la clave {error} en [rates] de {path}") from error


def _to_decimal(value: str, key: str, path: Path) -> Decimal:
    if not isinstance(value, str):
        raise _invalid_value(key, "debe escribirse entre comillas", value, path)
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise _invalid_value(key, "no es un número", value, path) from error
    if not number.is_finite():
        raise _invalid_value(key, "no es un número finito", value, path)
    if number < 0:
        raise _invalid_value(key, "no puede ser negativo", value, path)
    return number


def _invalid_value(key: str, reason: str, value: object, path: Path) -> TariffFileError:
    return TariffFileError(f"El valor de '{key}' {reason}: {value!r} ({path})")
