# Proyecto: py-taximetro
# fuente: tests/contract/test_trip_repository.py
"""Contrato de TripRepository: todas las implementaciones deben cumplir estos tests."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from taximetro.core.errors import InvalidTripRecord
from taximetro.core.trip import Trip
from taximetro.infra.repos.memory import InMemoryTripRepository


@pytest.fixture(params=["memory"])
def repository(request):
    if request.param == "memory":
        return InMemoryTripRepository()
    raise AssertionError(request.param)


def finished_trip(
    trip_id: str,
    finished_at: datetime,
    total: str = "1.00",
    started_at: datetime | None = None,
) -> Trip:
    started_at = started_at or finished_at.replace(minute=0)
    return Trip.restore(
        trip_id, started_at, finished_at, Decimal("30"), Decimal("20"), Decimal(total)
    )


def summary(trip: Trip) -> tuple:
    """Los datos que identifican una carrera, para compararlas sin depender de la identidad."""
    return (
        trip.id,
        trip.started_at,
        trip.finished_at,
        trip.stopped_seconds,
        trip.moving_seconds,
        trip.total,
    )


def test_guarda_y_lista_una_carrera_terminada(repository):
    trip = finished_trip("a", datetime(2026, 11, 11, 10, 5, tzinfo=UTC), total="7.25")

    repository.save(trip)

    listed = repository.list_finished(date(2026, 11, 11))
    assert [summary(t) for t in listed] == [summary(trip)]


def test_solo_lista_las_carreras_terminadas_en_el_dia_pedido(repository):
    repository.save(finished_trip("hoy", datetime(2026, 11, 11, 10, 5, tzinfo=UTC)))
    repository.save(finished_trip("ayer", datetime(2026, 11, 10, 23, 55, tzinfo=UTC)))
    repository.save(finished_trip("manana", datetime(2026, 11, 12, 0, 5, tzinfo=UTC)))

    listed = repository.list_finished(date(2026, 11, 11))

    assert [t.id for t in listed] == ["hoy"]


def test_lista_las_carreras_de_la_mas_antigua_a_la_mas_reciente(repository):
    # Los ids no siguen el orden cronológico, ni el de guardado, ni el alfabético.
    repository.save(finished_trip("a", datetime(2026, 11, 11, 18, 30, tzinfo=UTC)))  # tarde
    repository.save(finished_trip("b", datetime(2026, 11, 11, 8, 15, tzinfo=UTC)))  # mañana
    repository.save(finished_trip("c", datetime(2026, 11, 11, 12, 0, tzinfo=UTC)))  # mediodía

    listed = repository.list_finished(date(2026, 11, 11))

    assert [t.id for t in listed] == ["b", "c", "a"]


def test_una_carrera_que_cruza_la_medianoche_cuenta_en_el_dia_en_que_termina(repository):
    inicio = datetime(2026, 11, 10, 23, 50, tzinfo=UTC)
    fin = datetime(2026, 11, 11, 0, 20, tzinfo=UTC)
    repository.save(finished_trip("noche", fin, started_at=inicio))

    assert [t.id for t in repository.list_finished(date(2026, 11, 11))] == ["noche"]
    assert repository.list_finished(date(2026, 11, 10)) == []


def test_ordena_por_la_hora_de_fin_y_no_por_la_de_inicio(repository):
    # "larga" empieza antes pero termina después que "corta".
    larga = finished_trip(
        "larga",
        datetime(2026, 11, 11, 19, 0, tzinfo=UTC),
        started_at=datetime(2026, 11, 11, 8, 0, tzinfo=UTC),
    )
    corta = finished_trip(
        "corta",
        datetime(2026, 11, 11, 11, 0, tzinfo=UTC),
        started_at=datetime(2026, 11, 11, 10, 0, tzinfo=UTC),
    )
    repository.save(larga)
    repository.save(corta)

    assert [t.id for t in repository.list_finished(date(2026, 11, 11))] == ["corta", "larga"]


def test_no_se_guarda_una_carrera_sin_terminar(repository, tariff):
    en_curso = Trip(tariff, "en-curso")
    en_curso.start(at=0, when=datetime(2026, 11, 11, 10, 0, tzinfo=UTC))

    with pytest.raises(InvalidTripRecord, match="sin terminar"):
        repository.save(en_curso)


MOMENT = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("started_at", "finished_at"),
    [(None, None), (MOMENT, None), (None, MOMENT)],
    ids=["ninguna", "falta-el-fin", "falta-el-inicio"],
)
def test_no_se_guarda_una_carrera_sin_fechas(repository, tariff, started_at, finished_at):
    trip = Trip(tariff, "sin-fechas")
    trip.start(at=0, when=started_at)
    trip.finish(at=5, when=finished_at)

    with pytest.raises(InvalidTripRecord, match="sin fechas"):
        repository.save(trip)
