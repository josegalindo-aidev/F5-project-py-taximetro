# Proyecto: py-taximetro
# fuente: tests/unit/core/test_trip_service.py
from decimal import Decimal

import pytest

from taximetro.core.errors import TripAlreadyStarted, TripNotStarted
from taximetro.core.trip import State
from taximetro.core.trip_service import TripService
from tests.fakes import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def service(tariff, clock) -> TripService:
    return TripService(tariff, clock)


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
