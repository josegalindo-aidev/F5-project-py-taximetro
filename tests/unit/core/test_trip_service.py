# Proyecto: py-taximetro
# fuente: tests/unit/core/test_trip_service.py
from decimal import Decimal

import pytest

from taximetro.core.errors import (
    InvalidTripRecord,
    TripAlreadyStarted,
    TripNotSaved,
    TripNotStarted,
)
from taximetro.core.trip import State
from taximetro.core.trip_service import TripService
from taximetro.infra.repos.memory import InMemoryTripRepository
from tests.fakes import BrokenRepository, FakeClock, FakeWallClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def wall_clock() -> FakeWallClock:
    return FakeWallClock()


@pytest.fixture
def repository() -> InMemoryTripRepository:
    return InMemoryTripRepository()


@pytest.fixture
def service(tariff, clock, wall_clock, repository) -> TripService:
    return TripService(tariff, clock, wall_clock, repository)


def test_sin_carrera_al_arrancar(service):
    assert service.active is None


def test_iniciar_y_finalizar_cobra_el_tiempo_parado(service, clock):
    service.start()
    clock.advance(10)
    assert service.finish() == Decimal("0.20")


def test_cambiar_estado_aplica_la_tarifa_de_cada_tramo(service, clock):
    service.start()
    clock.advance(10)
    service.set_state(State.MOVING)
    clock.advance(10)
    assert service.finish() == Decimal("0.70")


def test_importe_actual_no_cierra_la_carrera(service, clock):
    service.start()
    clock.advance(10)
    assert service.current_amount() == Decimal("0.20")
    assert service.active is not None
    clock.advance(10)
    assert service.finish() == Decimal("0.40")


# US-04: encadenar carreras sin reiniciar
def test_tras_finalizar_se_puede_iniciar_otra_carrera(service, clock):
    service.start()
    clock.advance(10)
    assert service.finish() == Decimal("0.20")
    assert service.active is None

    service.start()
    clock.advance(4)
    service.set_state(State.MOVING)
    clock.advance(10)
    assert service.finish() == Decimal("0.58")  # 4*0.02 + 10*0.05


def test_cada_carrera_tiene_identificador_distinto(service):
    first = service.start()
    service.finish()
    second = service.start()
    assert first.id and second.id and first.id != second.id


# Casos límite
def test_no_se_puede_iniciar_con_otra_en_curso(service):
    service.start()
    with pytest.raises(TripAlreadyStarted):
        service.start()


def test_cambiar_estado_sin_carrera_falla(service):
    with pytest.raises(TripNotStarted):
        service.set_state(State.MOVING)


def test_finalizar_sin_carrera_falla(service):
    with pytest.raises(TripNotStarted):
        service.finish()


def test_importe_actual_sin_carrera_falla(service):
    with pytest.raises(TripNotStarted):
        service.current_amount()


# TK-04: el servicio estampa la carrera con la fecha y hora del reloj de pared
def test_al_iniciar_la_carrera_guarda_la_fecha_de_inicio(service, wall_clock):
    trip = service.start()

    assert trip.started_at == wall_clock.now


def test_al_finalizar_guarda_la_carrera_en_el_repositorio(service, clock, wall_clock, repository):
    service.start()
    clock.advance(10)
    wall_clock.advance(10)
    service.finish()

    saved = repository.list_finished(wall_clock.now.date())
    assert len(saved) == 1
    trip = saved[0]
    assert trip.total == Decimal("0.20")
    assert trip.stopped_seconds == Decimal("10")
    assert trip.finished_at == wall_clock.now


def test_si_falla_el_guardado_la_carrera_se_cobra_y_el_error_lleva_el_total(
    tariff, clock, wall_clock
):
    service = TripService(tariff, clock, wall_clock, BrokenRepository())
    service.start()
    clock.advance(10)

    with pytest.raises(TripNotSaved) as info:
        service.finish()

    assert info.value.total == Decimal("0.20")
    assert isinstance(info.value.__cause__, OSError)
    assert service.active is None  # la carrera queda cerrada: se puede iniciar otra


class BuggyRepository:
    """Repositorio que rechaza la carrera por un error de programación, no del disco."""

    def save(self, trip):
        raise InvalidTripRecord("No se puede guardar una carrera sin fechas.")

    def list_finished(self, day):
        return []


def test_un_error_de_programacion_no_se_disfraza_de_fallo_de_guardado(tariff, clock, wall_clock):
    service = TripService(tariff, clock, wall_clock, BuggyRepository())
    service.start()

    with pytest.raises(InvalidTripRecord):
        service.finish()
