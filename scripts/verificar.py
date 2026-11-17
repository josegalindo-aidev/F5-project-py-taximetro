# Proyecto: py-taximetro
# fuente: scripts/verificar.py
"""Lanza las pruebas y la cobertura del proyecto con una sola orden."""

from __future__ import annotations

from dataclasses import dataclass

MIN_PROJECT = 80.0
MIN_CORE = 90.0


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
    raise NotImplementedError


def parse_total_percent(report: str) -> float:
    raise NotImplementedError


def coverage_failures(
    project: float, core: float, min_project: float = MIN_PROJECT, min_core: float = MIN_CORE
) -> list[str]:
    raise NotImplementedError
