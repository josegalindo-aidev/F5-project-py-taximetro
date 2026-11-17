# Proyecto: py-taximetro
# fuente: scripts/verificar.py
"""Lanza las pruebas y la cobertura del proyecto con una sola orden."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "[Verifica]"  # marca las líneas del script y las separa de la salida de pytest
MIN_PROJECT = 80.0
MIN_CORE = 90.0

# Lanza una orden y devuelve (código de salida, salida de texto).
Runner = Callable[[list[str]], tuple[int, str]]


@dataclass(frozen=True)
class Options:
    fast: bool = False
    lint: bool = False
    paths: tuple[str, ...] = ()
    detail: bool = False

    @property
    def partial(self) -> bool:
        """Con rutas concretas solo se ejecuta una parte de las pruebas."""
        return bool(self.paths)


def pytest_command(python: str, options: Options) -> list[str]:
    verbosity = "-v" if options.detail else "-q"
    command = [python, "-m", "pytest", verbosity, "-p", "no:cacheprovider"]
    if not options.fast:
        command += ["--cov=src/taximetro", "--cov-branch", "--cov-report="]
    return command + list(options.paths)


@dataclass(frozen=True)
class PytestSummary:
    passed: int
    failed: int
    errors: int
    skipped: int
    seconds: float


_SUMMARY_LINE = re.compile(r"((?:\d+ [a-z]+(?:, )?)+) in (\d+(?:\.\d+)?)s")


def parse_test_summary(output: str) -> PytestSummary | None:
    """Cuenta de pruebas de la última línea de resumen de pytest, si la hay."""
    for line in reversed(output.splitlines()):
        found = _SUMMARY_LINE.search(line)
        if found:
            counts = {word: int(number) for number, word in re.findall(r"(\d+) ([a-z]+)", found[1])}
            return PytestSummary(
                passed=counts.get("passed", 0),
                failed=counts.get("failed", 0),
                errors=counts.get("error", 0) + counts.get("errors", 0),
                skipped=counts.get("skipped", 0),
                seconds=float(found[2]),
            )
    return None


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
    parser.add_argument("--detalle", action="store_true", help="muestra el nombre de cada prueba")
    args = parser.parse_args(argv)
    return Options(fast=args.rapido, lint=args.lint, paths=tuple(args.paths), detail=args.detalle)


def run(
    options: Options,
    python: str,
    runner: Runner,
    output: Callable[[str], None] = print,
) -> int:
    reasons = []
    steps = (
        ["pruebas"] + ([] if options.fast else ["cobertura"]) + (["estilo"] if options.lint else [])
    )

    def say(text: str) -> None:
        output(f"{TAG} {text}")

    def announce(name: str) -> None:
        say(f"Paso {steps.index(name) + 1} de {len(steps)}: {name}")

    def coverage_report(label: str, minimum: float, *extra: str) -> float:
        command = [python, "-m", "coverage", "report", "--precision=2", "--fail-under=0", *extra]
        _, report = runner(command)
        say(f"Cobertura del {label}:")
        output(report.rstrip())
        value = parse_total_percent(report)
        note = "no se juzga: ejecución parcial" if options.partial else f"mínimo {minimum:g}%"
        say(f"Resultado del {label}: {value:.2f}% ({note})")
        return value

    announce("pruebas")
    if options.detail:
        say("Leyenda: cada línea es una prueba y su resultado.")
    else:
        say("Leyenda: . superada · F fallida · E error · s omitida · [nn%] avance de la ejecución")
    tests_code, tests_output = runner(pytest_command(python, options))
    output(tests_output.rstrip())
    summary = parse_test_summary(tests_output)
    if summary is None:
        say("Pruebas: no se pudo leer el resumen de pytest")
    else:
        say(
            f"Pruebas: {summary.passed} superadas, {summary.failed} fallidas, "
            f"{summary.errors} con error, {summary.skipped} omitidas, en {summary.seconds:g} s"
        )
    if tests_code != 0:
        reasons.append("hay pruebas en rojo")

    if not options.fast:
        announce("cobertura")
        say(
            "Columnas: Stmts = líneas ejecutables, Miss = sin cubrir, Branch = ramas, "
            "BrPart = ramas a medias, Cover = % cubierto, Missing = líneas sin cubrir"
        )
        project = coverage_report("proyecto", MIN_PROJECT)
        core = coverage_report("núcleo", MIN_CORE, "--include=src/taximetro/core/*")
        if options.partial:
            say("AVISO: ejecución parcial, la cobertura no es representativa y no se juzga.")
        else:
            failures = coverage_failures(project, core)
            for failure in failures:
                say(f"FALLO: {failure}")
            reasons += failures

    if options.lint:
        announce("estilo")
        lint_code, lint_output = runner([python, "-m", "ruff", "check", "."])
        output(lint_output.rstrip())
        say("Estilo: sin errores" if lint_code == 0 else "Estilo: hay errores")
        if lint_code != 0:
            reasons.append("el estilo tiene errores")

    if reasons:
        say("ROJO: " + "; ".join(reasons))
        return 1
    say("VERDE: todo en orden")
    return 0


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
