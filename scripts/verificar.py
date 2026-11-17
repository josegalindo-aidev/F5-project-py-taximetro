# Proyecto: py-taximetro
# fuente: scripts/verificar.py
"""Lanza las pruebas y la cobertura del proyecto con una sola orden."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

MIN_PROJECT = 80.0
MIN_CORE = 90.0

# Lanza una orden y devuelve (código de salida, salida de texto).
Runner = Callable[[list[str]], tuple[int, str]]


@dataclass(frozen=True)
class Options:
    fast: bool = False
    lint: bool = False
    paths: tuple[str, ...] = ()

    @property
    def partial(self) -> bool:
        """Con rutas concretas solo se ejecuta una parte de las pruebas."""
        return bool(self.paths)


def pytest_command(python: str, options: Options) -> list[str]:
    command = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    if not options.fast:
        command += ["--cov=src/taximetro", "--cov-branch", "--cov-report="]
    return command + list(options.paths)


def parse_total_percent(report: str) -> float:
    """Porcentaje de la línea `TOTAL` de un informe de `coverage report`."""
    for line in reversed(report.splitlines()):
        if line.startswith("TOTAL"):
            return float(line.split()[-1].rstrip("%"))
    raise ValueError("el informe de cobertura no tiene línea TOTAL")


def coverage_failures(
    project: float, core: float, min_project: float = MIN_PROJECT, min_core: float = MIN_CORE
) -> list[str]:
    failures = []
    if project < min_project:
        failures.append(f"la cobertura del proyecto es {project}% y el mínimo es {min_project:g}%")
    if core < min_core:
        failures.append(f"la cobertura del núcleo es {core}% y el mínimo es {min_core:g}%")
    return failures


def parse_args(argv: Sequence[str]) -> Options:
    raise NotImplementedError


def run(
    options: Options,
    python: str,
    runner: Runner,
    output: Callable[[str], None] = print,
) -> int:
    raise NotImplementedError
