# Proyecto: py-taximetro
# fuente: scripts/build_memoria.py
"""Ensambla la memoria técnica en un único Markdown a partir de los documentos de docs/."""

from __future__ import annotations

import re

_HEADER_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.DOTALL)
_FIRST_TITLE = re.compile(r"^# (.+?)[ \t]*$", re.MULTILINE)


def clean_document(text: str, anchor: str) -> str:
    """Quita la cabecera de comentario y da un identificador al título principal."""
    text = text.replace("\r\n", "\n")
    text = _HEADER_COMMENT.sub("", text, count=1)
    return _FIRST_TITLE.sub(rf"# \1 {{#{anchor}}}", text, count=1)
