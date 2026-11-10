from decimal import Decimal

import pytest

from taximetro.core.errors import (
    InvalidTimestamp,
    TripAlreadyFinished,
    TripAlreadyStarted,
    TripNotStarted,
)
from taximetro.core.trip import State, Trip


@pytest.fixture
def trip(tariff) -> Trip:
    return Trip(tariff)


# US-01 / US-03: iniciar y finalizar con total en euros
def test_parado_10s_cobra_020(trip):
    trip.start(at=0)
    assert trip.finish(at=10) == Decimal("0.20")


def test_carrera_instantanea_cuesta_cero(trip):
    trip.start(at=5)
    assert trip.finish(at=5) == Decimal("0.00")


# US-02: cambiar entre parado y en movimiento
def test_cambio_de_estado_cierra_el_tramo(trip):
    trip.start(at=0)                       # parado
    trip.change_state(State.MOVING, at=10)  # 10 * 0.02 = 0.20
    assert trip.finish(at=20) == Decimal("0.70")  # + 10 * 0.05 = 0.50


def test_varios_cambios_acumulan(trip):
    trip.start(at=0)
    trip.change_state(State.MOVING, at=10)   # tramo parado: 10 * 0.02 = 0.20
    trip.change_state(State.STOPPED, at=20)  # tramo en movimiento: 10 * 0.05 = 0.50
    assert trip.finish(at=30) == Decimal("0.90")  # último tramo parado: 0.20


def test_total_se_redondea_a_dos_decimales(trip):
    trip.start(at=0)
    assert trip.finish(at=0.5) == Decimal("0.01")  # 0.5 * 0.02 = 0.01


# Importe provisional (para mostrar el importe acumulado sin cerrar la carrera)
def test_importe_provisional_no_cierra_la_carrera(trip):
    trip.start(at=0)
    trip.change_state(State.MOVING, at=10)
    assert trip.amount_at(20) == Decimal("0.70")
    assert trip.amount_at(20) == Decimal("0.70")  # idempotente
    assert trip.finish(at=30) == Decimal("1.20")


def test_importe_provisional_sin_iniciar_falla(trip):
    with pytest.raises(TripNotStarted):
        trip.amount_at(1)


def test_estado_actual(trip):
    assert trip.state is None
    trip.start(at=0)
    assert trip.state is State.STOPPED
    trip.change_state(State.MOVING, at=1)
    assert trip.state is State.MOVING


# Casos límite
def test_finalizar_sin_iniciar_falla(trip):
    with pytest.raises(TripNotStarted):
        trip.finish(at=1)


def test_cambiar_estado_sin_iniciar_falla(trip):
    with pytest.raises(TripNotStarted):
        trip.change_state(State.MOVING, at=1)


def test_no_se_puede_iniciar_dos_veces(trip):
    trip.start(at=0)
    with pytest.raises(TripAlreadyStarted):
        trip.start(at=1)


def test_no_se_puede_operar_tras_finalizar(trip):
    trip.start(at=0)
    trip.finish(at=1)
    with pytest.raises(TripAlreadyFinished):
        trip.change_state(State.MOVING, at=2)


def test_una_carrera_finalizada_no_se_reinicia(trip):
    trip.start(at=0)
    assert not trip.is_finished
    trip.finish(at=1)
    assert trip.is_finished
    with pytest.raises(TripAlreadyFinished):
        trip.start(at=2)


def test_instante_anterior_al_ultimo_es_invalido(trip):
    trip.start(at=10)
    with pytest.raises(InvalidTimestamp):
        trip.change_state(State.MOVING, at=5)
