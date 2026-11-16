# Proyecto: py-taximetro
# fuente: tests/test_architecture.py
"""Regla de dependencias (TK-05): el dominio no conoce a nadie y la UI no conoce la persistencia.

Dominio, servicio, persistencia y UI viven en capas distintas y solo se pueden conocer en un
sentido: `infra/` y `ui/` dependen de `core/`, y `core/` no depende de nadie. Los ficheros de la
raíz de `taximetro` (el arranque) son los únicos que conectan todas las capas.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "taximetro"

# Capas de `taximetro` que puede importar cada capa (además de la suya).
ALLOWED: dict[str, set[str]] = {
    "core": set(),
    "infra": {"core"},
    "ui": {"core"},
}


def layers_imported(source: str) -> set[str]:
    """Capas de `taximetro` que importa un código: `core`, `infra`, `ui`..."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        elif isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        else:
            continue
        for module in modules:
            parts = module.split(".")
            if parts[0] == "taximetro" and len(parts) > 1:
                found.add(parts[1])
    return found


def python_files(layer: str) -> list[Path]:
    return sorted(
        path
        for path in (SRC / layer).rglob("*.py")
        if "__pycache__" not in path.parts and path.read_text(encoding="utf-8").strip()
    )


# --- el detector de importaciones ------------------------------------------------------------
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("from taximetro.infra.folders import file_in_the_way", {"infra"}),
        ("import taximetro.ui.cli.app", {"ui"}),
        ("from taximetro.core.trip import Trip\nimport taximetro.ui.cli.format", {"core", "ui"}),
        ("import json\nfrom pathlib import Path\nfrom decimal import Decimal", set()),
        ("from taximetro import __main__", set()),
    ],
    ids=["from-import", "import-de-submodulo", "dos-capas", "solo-libreria-estandar", "raiz"],
)
def test_el_detector_encuentra_las_capas_importadas(source, expected):
    assert layers_imported(source) == expected


# --- la regla sobre el código real -----------------------------------------------------------
@pytest.mark.parametrize("layer", sorted(ALLOWED))
def test_cada_capa_tiene_codigo_que_comprobar(layer):
    assert python_files(layer), f"no hay ficheros en {layer}/: la regla pasaría en vacío"


@pytest.mark.parametrize(
    ("layer", "path"),
    [(layer, path) for layer in sorted(ALLOWED) for path in python_files(layer)],
    ids=lambda value: value.name if isinstance(value, Path) else value,
)
def test_una_capa_solo_importa_de_las_capas_que_le_estan_permitidas(layer, path):
    forbidden = layers_imported(path.read_text(encoding="utf-8")) - {layer} - ALLOWED[layer]

    assert not forbidden, (
        f"{path.relative_to(SRC)} ({layer}/) importa de {sorted(forbidden)}; "
        f"solo puede importar de {sorted(ALLOWED[layer]) or 'ninguna otra capa'}"
    )
