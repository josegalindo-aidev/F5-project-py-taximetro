"""Dobles de test compartidos."""


class FakeClock:
    """Reloj controlable: cumple el puerto `Clock`."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds
