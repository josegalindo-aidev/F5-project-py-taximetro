# Proyecto: py-taximetro
# fuente: tests/fakes.py
"""Dobles de test compartidos."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from taximetro.core.errors import TripHistoryError
from taximetro.core.trip import Trip


class FakeWallClock:
    """Reloj de pared controlable: cumple el puerto `WallClock`."""

    def __init__(self, now: datetime | None = None) -> None:
        self.now = now or datetime(2026, 11, 11, 10, 0, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class FakeClock:
    """Reloj controlable: cumple el puerto `Clock`."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class BrokenRepository:
    """Repositorio cuyo guardado siempre falla (disco lleno, fichero bloqueado...)."""

    def save(self, trip):
        raise OSError("disco lleno")

    def list_finished(self, day):
        return []


class UnreadableHistoryRepository:
    """Repositorio cuyo historial no se puede leer: consultarlo siempre falla."""

    def save(self, trip):
        pass

    def list_finished(self, day):
        raise TripHistoryError("El historial 'trips.json' está dañado: no se puede leer")


class FakeEventLog:
    """Registro de eventos en memoria: cumple el puerto `EventLog`."""

    def __init__(self) -> None:
        self.events: list[tuple[datetime, str, dict]] = []

    def record(self, at: datetime, event: str, **data: str) -> None:
        self.events.append((at, event, data))


class FailingEventLog:
    """Registro de eventos cuya escritura siempre falla (disco lleno, fichero bloqueado...)."""

    def record(self, at: datetime, event: str, **data: str) -> None:
        raise OSError("disco del registro lleno")


class ScriptedInput:
    """Consola simulada: cada paso (segundos, comando) avanza el reloj y devuelve el comando."""

    def __init__(self, clock: FakeClock, steps: list[tuple[float, str]]) -> None:
        self.clock = clock
        self.steps = list(steps)

    def __call__(self, prompt: str = "") -> str:
        if not self.steps:
            raise EOFError
        seconds, command = self.steps.pop(0)
        self.clock.advance(seconds)
        return command


def saved_trip(repository, trip_id, start, end, total) -> None:
    """Guarda en el repositorio una carrera ya terminada en noviembre de 2026.

    `start` y `end` son tuplas (día, hora, minuto). El reloj de pared de las pruebas marca el
    11/11/2026 a las 10:00.
    """
    started = datetime(2026, 11, *start, tzinfo=UTC)
    finished = datetime(2026, 11, *end, tzinfo=UTC)
    trip = Trip.restore(trip_id, started, finished, Decimal("30"), Decimal("20"), Decimal(total))
    repository.save(trip)
