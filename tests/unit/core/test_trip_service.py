# Proyecto: py-taximetro
# fuente: tests/unit/core/test_trip_service.py
from datetime import date
from decimal import Decimal

import pytest

from taximetro.core.errors import (
    InvalidTripRecord,
    TripAlreadyStarted,
    TripHistoryError,
    TripNotSaved,
    TripNotStarted,
)
from taximetro.core.trip import State
from taximetro.core.trip_service import TripService
from taximetro.infra.repos.memory import InMemoryTripRepository
from tests.fakes import (
    BrokenRepository,
    FailingEventLog,
    FakeClock,
    FakeEventLog,
    FakeWallClock,
)


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
def event_log() -> FakeEventLog:
    return FakeEventLog()


@pytest.fixture
def service(tariff, clock, wall_clock, repository, event_log) -> TripService:
    return TripService(tariff, clock, wall_clock, repository, event_log)


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
    service = TripService(tariff, clock, wall_clock, BrokenRepository(), FakeEventLog())
    service.start()
    clock.advance(10)

    with pytest.raises(TripNotSaved) as info:
        service.finish()

    assert info.value.total == Decimal("0.20")
    assert isinstance(info.value.__cause__, OSError)
    assert service.active is None  # la carrera queda cerrada: se puede iniciar otra


class DamagedHistoryRepository:
    """Repositorio cuyo historial está dañado: no se puede añadir la carrera."""

    def save(self, trip):
        raise TripHistoryError("El historial 'trips.json' está dañado")

    def list_finished(self, day):
        return []


def test_si_el_historial_esta_danado_la_carrera_se_cobra_y_se_avisa(tariff, clock, wall_clock):
    service = TripService(tariff, clock, wall_clock, DamagedHistoryRepository(), FakeEventLog())
    service.start()
    clock.advance(10)

    with pytest.raises(TripNotSaved) as info:
        service.finish()

    assert info.value.total == Decimal("0.20")
    assert isinstance(info.value.__cause__, TripHistoryError)
    assert "dañado" in str(info.value)  # el aviso incluye el motivo
    assert service.active is None


class BuggyRepository:
    """Repositorio que rechaza la carrera por un error de programación, no del disco."""

    def save(self, trip):
        raise InvalidTripRecord("No se puede guardar una carrera sin fechas.")

    def list_finished(self, day):
        return []


def test_un_error_de_programacion_no_se_disfraza_de_fallo_de_guardado(tariff, clock, wall_clock):
    service = TripService(tariff, clock, wall_clock, BuggyRepository(), FakeEventLog())
    service.start()

    with pytest.raises(InvalidTripRecord):
        service.finish()


# US-05: consultar las carreras terminadas de un día
ONE_DAY = 24 * 3600


def run_one_trip(service, clock, wall_clock, seconds=1):
    """Inicia y finaliza una carrera, avanzando los dos relojes."""
    trip = service.start()
    clock.advance(seconds)
    wall_clock.advance(seconds)
    service.finish()
    return trip


def test_las_carreras_terminadas_de_un_dia_se_listan_por_orden_de_fin(service, clock, wall_clock):
    first = run_one_trip(service, clock, wall_clock, seconds=10)
    second = run_one_trip(service, clock, wall_clock, seconds=5)
    wall_clock.advance(ONE_DAY)
    third = run_one_trip(service, clock, wall_clock, seconds=3)

    assert [t.id for t in service.finished_on(date(2026, 11, 11))] == [first.id, second.id]
    assert [t.id for t in service.finished_on(date(2026, 11, 12))] == [third.id]
    assert service.finished_on(date(2026, 11, 10)) == []


def test_sin_indicar_el_dia_se_usa_el_de_hoy_segun_el_reloj_de_pared(service, clock, wall_clock):
    run_one_trip(service, clock, wall_clock)  # ayer
    wall_clock.advance(ONE_DAY)
    today_trip = run_one_trip(service, clock, wall_clock)

    assert service.today() == date(2026, 11, 12)
    assert [t.id for t in service.finished_on()] == [today_trip.id]


# US-06: registro de eventos de operación
def test_al_iniciar_la_carrera_se_registra_el_evento_con_su_hora_e_identificador(
    service, event_log, wall_clock
):
    trip = service.start()

    assert event_log.events == [(wall_clock.now, "carrera_iniciada", {"carrera": trip.id})]


def test_cada_cambio_de_estado_se_registra_con_el_estado_nuevo(
    service, clock, wall_clock, event_log
):
    trip = service.start()
    clock.advance(5)
    wall_clock.advance(5)
    service.set_state(State.MOVING)
    moving_at = wall_clock.now
    clock.advance(3)
    wall_clock.advance(3)
    service.set_state(State.STOPPED)

    assert event_log.events[1:] == [
        (moving_at, "estado_cambiado", {"carrera": trip.id, "estado": "moving"}),
        (wall_clock.now, "estado_cambiado", {"carrera": trip.id, "estado": "stopped"}),
    ]


def test_al_finalizar_la_carrera_se_registra_el_total_con_la_hora_de_fin(
    service, clock, wall_clock, event_log
):
    trip = service.start()
    clock.advance(10)
    wall_clock.advance(10)
    service.set_state(State.MOVING)
    clock.advance(10)
    wall_clock.advance(10)
    total = service.finish()

    assert total == Decimal("0.70")
    assert [name for _, name, _ in event_log.events] == [
        "carrera_iniciada",
        "estado_cambiado",
        "carrera_finalizada",
    ]
    assert event_log.events[-1] == (
        wall_clock.now,
        "carrera_finalizada",
        {"carrera": trip.id, "total": "0.70"},
    )


@pytest.mark.parametrize(
    ("repository", "reason"),
    [
        (BrokenRepository(), "disco lleno"),
        (DamagedHistoryRepository(), "El historial 'trips.json' está dañado"),
    ],
    ids=["fallo-de-disco", "historial-danado"],
)
def test_si_no_se_puede_guardar_la_carrera_se_registra_el_motivo(
    tariff, clock, wall_clock, event_log, repository, reason
):
    service = TripService(tariff, clock, wall_clock, repository, event_log)
    trip = service.start()
    clock.advance(10)
    wall_clock.advance(10)

    with pytest.raises(TripNotSaved):
        service.finish()

    assert [name for _, name, _ in event_log.events] == [
        "carrera_iniciada",
        "carrera_finalizada",
        "carrera_no_guardada",
    ]
    assert event_log.events[-1] == (
        wall_clock.now,
        "carrera_no_guardada",
        {"carrera": trip.id, "motivo": reason},
    )


# Un fallo del registro de eventos nunca impide cobrar ni esconde el total
def test_si_falla_el_registro_se_puede_iniciar_cambiar_de_estado_y_cobrar(
    tariff, clock, wall_clock, repository
):
    service = TripService(tariff, clock, wall_clock, repository, FailingEventLog())

    service.start()
    clock.advance(10)
    service.set_state(State.MOVING)
    clock.advance(10)
    total = service.finish()

    assert total == Decimal("0.70")
    assert service.active is None
    assert [t.total for t in repository.list_finished(wall_clock.now.date())] == [Decimal("0.70")]


def test_si_fallan_el_registro_y_el_historial_el_total_llega_en_trip_not_saved(
    tariff, clock, wall_clock
):
    service = TripService(tariff, clock, wall_clock, BrokenRepository(), FailingEventLog())
    service.start()
    clock.advance(10)

    with pytest.raises(TripNotSaved) as info:
        service.finish()

    assert info.value.total == Decimal("0.20")
    assert "disco lleno" in str(info.value)  # el motivo es el del historial, no el del registro
    assert service.active is None
