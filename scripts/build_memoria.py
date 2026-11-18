# Proyecto: py-taximetro
# fuente: scripts/build_memoria.py
"""Ensambla la memoria técnica en un único Markdown a partir de los documentos de docs/."""

from __future__ import annotations

import re

_HEADER_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.DOTALL)
_FIRST_TITLE = re.compile(r"^# (.+?)[ \t]*$", re.MULTILINE)
_LINK = re.compile(r"\]\(([^)#\s]+)(#[^)\s]*)?\)")


def clean_document(text: str, anchor: str) -> str:
    """Quita la cabecera de comentario y da un identificador al título principal."""
    text = text.replace("\r\n", "\n")
    text = _HEADER_COMMENT.sub("", text, count=1)
    return _FIRST_TITLE.sub(rf"# \1 {{#{anchor}}}", text, count=1)


def rewrite_links(text: str, anchors: dict[str, str]) -> str:
    """Convierte los enlaces a otros documentos de la memoria en enlaces internos."""

    def replace(found: re.Match[str]) -> str:
        document, fragment = found[1], found[2]
        if document not in anchors:
            return found[0]
        return f"]({fragment or '#' + anchors[document]})"

    return _LINK.sub(replace, text)
