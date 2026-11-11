# Proyecto: py-taximetro
# fuente: tests/integration/test_json_trip_repository.py
"""Comportamiento propio del repositorio JSON: lo que el contrato común no puede cubrir."""

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

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


def finished_trip(trip_id: str = "nueva") -> Trip:
    return Trip.restore(
        trip_id,
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


# Primer arranque: la carpeta del historial todavía no existe.
def test_guardar_crea_las_carpetas_que_falten_y_el_historial_perdura(tmp_path):
    path = tmp_path / "data" / "2026" / "historial.json"

    JsonTripRepository(path).save(finished_trip())

    reopened = JsonTripRepository(path)  # como al reiniciar el programa
    assert [trip.id for trip in reopened.list_finished(DAY)] == ["nueva"]


def test_sin_fichero_el_historial_esta_vacio_y_listar_no_lo_crea(tmp_path):
    path = tmp_path / "data" / "historial.json"

    assert JsonTripRepository(path).list_finished(DAY) == []
    assert not path.parent.exists()


# Escritura atómica: un fallo a mitad de escritura no puede destruir el historial anterior.
def test_si_falla_la_escritura_a_medias_el_historial_anterior_sigue_intacto(path, monkeypatch):
    repository = JsonTripRepository(path)
    repository.save(finished_trip("primera"))
    antes = path.read_text(encoding="utf-8")

    escribir = Path.write_text

    def escribe_la_mitad_y_falla(self, text, *args, **kwargs):
        escribir(self, text[: len(text) // 2], *args, **kwargs)
        raise OSError("disco lleno")

    monkeypatch.setattr(Path, "write_text", escribe_la_mitad_y_falla)

    with pytest.raises(OSError, match="disco lleno"):
        repository.save(finished_trip("segunda"))

    monkeypatch.undo()
    assert path.read_text(encoding="utf-8") == antes  # el fichero no se tocó
    assert [t.id for t in repository.list_finished(DAY)] == ["primera"]
    assert list(path.parent.iterdir()) == [path]  # sin ficheros temporales sueltos


# Historial que existe pero no se puede leer (aquí, una carpeta en lugar de un fichero).
@pytest.mark.parametrize("operacion", ["listar", "guardar"])
def test_un_historial_ilegible_da_un_error_que_nombra_el_fichero_y_el_motivo(path, operacion):
    path.mkdir()
    repository = JsonTripRepository(path)

    with pytest.raises(TripHistoryError) as info:
        if operacion == "listar":
            repository.list_finished(DAY)
        else:
            repository.save(finished_trip())

    assert "No se pudo leer el historial" in str(info.value)
    assert "historial.json" in str(info.value)
