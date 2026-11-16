# Proyecto: py-taximetro
# fuente: src/taximetro/infra/folders.py
"""Comprobaciones comunes sobre las carpetas donde el programa guarda sus datos."""

from __future__ import annotations

from pathlib import Path


def file_in_the_way(folder: Path) -> Path | None:
    """Devuelve el fichero que impide usar `folder` como carpeta, o `None` si no hay ninguno.

    Se mira `folder` y, si no existe, la primera carpeta que exista por encima. Una carpeta que
    todavía no se ha creado es válida: se creará al escribir.
    """
    existing = next((path for path in (folder, *folder.parents) if path.exists()), None)
    return existing if existing is not None and not existing.is_dir() else None
