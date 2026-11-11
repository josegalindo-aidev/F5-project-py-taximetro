# Proyecto: py-taximetro
# fuente: tests/integration/test_json_trip_repository.py
"""Comportamiento propio del repositorio JSON: lo que el contrato común no puede cubrir."""

import json
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from taximetro.core.errors import TripHistoryError
from taximetro.core.trip import Trip
from taximetro.infra.repos.json_file import JsonTripRepository

DAY = date(2026, 11, 11)


def record(**changes) -> dict:
    """Un registro válido del historial; `changes` lo estropea."""
    base = {
        "id": "a",
        "started_at": "2026-11-11T10:00:00+00:00",
        "finished_at": "2026-11-11T10:05:00+00:00",
        "stopped_seconds": "30",
        "moving_seconds": "20",
        "total": "1.00",
    }
    return {**base, **changes}


def without(field: str) -> dict:
    return {k: v for k, v in record().items() if k != field}


def finished_trip() -> Trip:
    return Trip.restore(
        "nueva",
        datetime(2026, 11, 11, 11, 0, tzinfo=UTC),
        datetime(2026, 11, 11, 11, 5, tzinfo=UTC),
        Decimal("30"),
        Decimal("20"),
        Decimal("1.00"),
    )


@pytest.fixture
def path(tmp_path):
    return tmp_path / "historial.json"


# Fichero dañado en su conjunto: no es JSON, está vacío o no es una lista.
FILE_LEVEL_DAMAGE = [
    pytest.param("", id="vacio"),
    pytest.param("{esto no es json", id="no-es-json"),
    pytest.param(json.dumps({"id": "a"}), id="no-es-una-lista"),
]

# Fichero con forma de lista pero con un registro que no se puede interpretar.
RECORD_LEVEL_DAMAGE = [
    pytest.param(json.dumps(["a"]), id="registro-que-no-es-objeto"),
    pytest.param(json.dumps([without("total")]), id="falta-un-campo"),
    pytest.param(json.dumps([record(total="abc")]), id="importe-no-numerico"),
    pytest.param(json.dumps([record(started_at="ayer")]), id="fecha-invalida"),
]


@pytest.mark.parametrize("content", FILE_LEVEL_DAMAGE + RECORD_LEVEL_DAMAGE)
def test_listar_un_historial_danado_da_un_error_que_nombra_el_fichero(path, content):
    path.write_text(content, encoding="utf-8")

    with pytest.raises(TripHistoryError) as info:
        JsonTripRepository(path).list_finished(DAY)

    assert "historial.json" in str(info.value)


@pytest.mark.parametrize("content", FILE_LEVEL_DAMAGE)
def test_guardar_sobre_un_historial_danado_falla_y_no_lo_sobrescribe(path, content):
    path.write_text(content, encoding="utf-8")

    with pytest.raises(TripHistoryError):
        JsonTripRepository(path).save(finished_trip())

    assert path.read_text(encoding="utf-8") == content  # no se pierde lo que hubiera
