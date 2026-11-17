# Proyecto: py-taximetro
# fuente: scripts/verificar.py
"""Lanza las pruebas y la cobertura del proyecto con una sola orden."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    parser = argparse.ArgumentParser(
        prog="verificar",
        description="Lanza las pruebas y la cobertura del proyecto y da un veredicto.",
    )
    parser.add_argument("paths", nargs="*", help="pruebas a ejecutar (por defecto, todas)")
    parser.add_argument("--rapido", action="store_true", help="solo las pruebas, sin cobertura")
    parser.add_argument("--lint", action="store_true", help="comprueba también el estilo (Ruff)")
    args = parser.parse_args(argv)
    return Options(fast=args.rapido, lint=args.lint, paths=tuple(args.paths))


def run(
    options: Options,
    python: str,
    runner: Runner,
    output: Callable[[str], None] = print,
) -> int:
    reasons = []

    tests_code, tests_output = runner(pytest_command(python, options))
    output(tests_output.rstrip())
    if tests_code != 0:
        reasons.append("hay pruebas en rojo")

    if not options.fast:
        project = _coverage(runner, python, output, "Cobertura del proyecto")
        core = _coverage(
            runner, python, output, "Cobertura del núcleo", "--include=src/taximetro/core/*"
        )
        if options.partial:
            output("AVISO: ejecución parcial, la cobertura no es representativa y no se juzga.")
        else:
            failures = coverage_failures(project, core)
            for failure in failures:
                output(f"FALLO: {failure}")
            reasons += failures

    if options.lint:
        lint_code, lint_output = runner([python, "-m", "ruff", "check", "."])
        output(lint_output.rstrip())
        if lint_code != 0:
            reasons.append("el estilo tiene errores")

    if reasons:
        output("ROJO: " + "; ".join(reasons))
        return 1
    output("VERDE: todo en orden")
    return 0


def _coverage(
    runner: Runner, python: str, output: Callable[[str], None], title: str, *extra: str
) -> float:
    _, report = runner(
        [python, "-m", "coverage", "report", "--precision=2", "--fail-under=0", *extra]
    )
    output(f"{title}:")
    output(report.rstrip())
    return parse_total_percent(report)


def launch(command: list[str]) -> tuple[int, str]:
    """Lanza una orden en la raíz del proyecto y devuelve su código y su salida."""
    result = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout + result.stderr


def main(argv: Sequence[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return run(parse_args(sys.argv[1:] if argv is None else argv), sys.executable, launch)


if __name__ == "__main__":
    raise SystemExit(main())
