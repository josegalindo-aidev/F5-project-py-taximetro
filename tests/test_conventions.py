# Proyecto: py-taximetro
# fuente: tests/test_conventions.py
"""Convención de cabecera de los ficheros .py.

Cada fichero .py no vacío de `src/` y `tests/` empieza por dos líneas:

    # Proyecto: py-taximetro
    # fuente: <ruta del fichero desde la raíz del proyecto>

La versión NO va en los ficheros: la única fuente es `pyproject.toml`.
Los ficheros vacíos (por ejemplo, `__init__.py`) no llevan cabecera.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "py-taximetro"
FOLDERS = ("src", "tests")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def python_files() -> list[Path]:
    """Ficheros .py no vacíos de src/ y tests/ (los vacíos están exentos)."""
    found = []
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            if path.read_text(encoding="utf-8").strip():
                found.append(path)
    return found


def header_of(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()[:5]


FILES = python_files()
IDS = [relative(p) for p in FILES]


def test_se_encuentran_ficheros_python():
    # Evita que el resto de pruebas "pasen" en vacío si la ruta base estuviera mal.
    assert FILES, "No se encontró ningún fichero .py en src/ ni tests/"


@pytest.mark.parametrize("path", FILES, ids=IDS)
def test_cabecera_con_proyecto_y_fuente(path):
    header = header_of(path)
    assert header[:1] == [f"# Proyecto: {PROJECT}"], (
        f"falta '# Proyecto: {PROJECT}' en la línea 1"
    )
    assert header[1:2] == [f"# fuente: {relative(path)}"], (
        f"falta '# fuente: {relative(path)}' en la línea 2"
    )


@pytest.mark.parametrize("path", FILES, ids=IDS)
def test_la_cabecera_no_lleva_version(path):
    versiones = [line for line in header_of(path) if line.lower().startswith("# version")]
    assert not versiones, "la versión vive solo en pyproject.toml; quita: " + versiones[0]
