# Proyecto: py-taximetro
# fuente: tests/unit/core/test_day_report.py
"""Resumen de las carreras de un día: el cálculo vive en el núcleo, no en la interfaz."""

from datetime import date
from decimal import Decimal

import pytest

from taximetro.core.day_report import DayReport
from taximetro.core.trip_service import TripService
from taximetro.infra.repos.memory import InMemoryTripRepository
from tests.fakes import FakeClock, FakeEventLog, FakeWallClock, saved_trip

DAY = date(2026, 11, 10)


@pytest.fixture
def repository() -> InMemoryTripRepository:
    return InMemoryTripRepository()


@pytest.fixture
def wall_clock() -> FakeWallClock:
    return FakeWallClock()


@pytest.fixture
def report(repository, wall_clock) -> DayReport:
    return DayReport(repository, wall_clock)


def test_un_dia_sin_carreras_tiene_el_total_a_cero(report):
    summary = report.for_day(DAY)

    assert summary.day == DAY
    assert summary.trips == ()
    assert summary.count == 0
    assert summary.total == Decimal("0")


def test_el_total_suma_los_importes_sin_perder_precision(report, repository):
    saved_trip(repository, "a", (10, 8, 0), (10, 8, 5), "0.10")
    saved_trip(repository, "b", (10, 9, 0), (10, 9, 5), "0.20")
    saved_trip(repository, "c", (10, 10, 0), (10, 10, 5), "7.25")

    summary = report.for_day(DAY)

    assert summary.count == 3
    assert summary.total == Decimal("7.55")  # con float, 0.1 + 0.2 no daría 0.30


def test_solo_cuenta_las_carreras_que_terminan_ese_dia_y_en_orden_de_fin(report, repository):
    saved_trip(repository, "tarde", (10, 18, 0), (10, 18, 30), "3.00")
    saved_trip(repository, "manana", (10, 8, 0), (10, 8, 30), "5.00")
    saved_trip(repository, "ayer", (9, 23, 0), (9, 23, 50), "99.99")
    saved_trip(repository, "manana-siguiente", (11, 8, 0), (11, 8, 30), "88.88")

    summary = report.for_day(DAY)

    assert [trip.id for trip in summary.trips] == ["manana", "tarde"]
    assert summary.total == Decimal("8.00")


def test_sin_indicar_el_dia_se_usa_el_de_hoy_segun_el_reloj_de_pared(report, repository):
    saved_trip(repository, "hoy", (11, 9, 0), (11, 9, 30), "1.00")  # el reloj marca el 11/11

    assert report.today() == date(2026, 11, 11)
    summary = report.for_day()

    assert summary.day == date(2026, 11, 11)
    assert [trip.id for trip in summary.trips] == ["hoy"]


def test_las_carreras_que_cobra_el_servicio_aparecen_en_el_dia_en_que_terminan(
    tariff, repository, wall_clock
):
    clock = FakeClock()
    service = TripService(tariff, clock, wall_clock, repository, FakeEventLog())
    report = DayReport(repository, wall_clock)

    def one_trip(seconds):
        trip = service.start()
        clock.advance(seconds)
        wall_clock.advance(seconds)
        service.finish()
        return trip

    first = one_trip(10)
    second = one_trip(5)
    wall_clock.advance(24 * 3600)  # pasa un día
    third = one_trip(3)

    assert [t.id for t in report.for_day(date(2026, 11, 11)).trips] == [first.id, second.id]
    assert [t.id for t in report.for_day(date(2026, 11, 12)).trips] == [third.id]
    assert report.for_day(date(2026, 11, 10)).count == 0
    assert report.for_day().day == date(2026, 11, 12)  # sin día, el de hoy
