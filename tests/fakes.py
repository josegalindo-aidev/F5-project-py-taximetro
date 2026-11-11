# Proyecto: py-taximetro
# fuente: tests/fakes.py
"""Dobles de test compartidos."""

from datetime import UTC, datetime, timedelta


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
