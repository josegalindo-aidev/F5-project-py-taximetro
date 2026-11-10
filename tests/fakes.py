"""Dobles de test compartidos."""


class FakeClock:
    """Reloj controlable: cumple el puerto `Clock`."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


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
