# Proyecto: py-taximetro
# fuente: scripts/build_memoria.py
"""Ensambla la memoria técnica en un único Markdown a partir de los documentos de docs/."""

from __future__ import annotations

import re

# Documentos de docs/ que forman la memoria, en el orden en que aparecen.
DOCUMENTS = (
    "ARCHITECTURE.md",
    "DESIGN.md",
    "DECISIONS.md",
    "TESTING.md",
    "USAGE.md",
    "CONTRIBUTING.md",
)
TITLE = "Memoria técnica del taxímetro digital (TTX-247)"

_HEADER_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.DOTALL)
_FIRST_TITLE = re.compile(r"^# (.+?)[ \t]*$", re.MULTILINE)
_HTML_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
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


def convert_anchors(text: str) -> str:
    """Convierte las anclas HTML en anclas de Pandoc, que el PDF sí conserva."""
    return _HTML_ANCHOR.sub(r"[]{#\1}", text)


def assemble(texts: dict[str, str], version: str) -> str:
    """Une los documentos de la memoria, en orden y con portada, en un solo Markdown."""
    anchors = {name: name.removesuffix(".md").lower() for name in DOCUMENTS}
    cover = f'---\ntitle: "{TITLE}"\nsubtitle: "Versión {version}"\nlang: es\n---\n'
    chapters = [
        rewrite_links(convert_anchors(clean_document(texts[name], anchors[name])), anchors)
        for name in DOCUMENTS
    ]
    return "\n".join([cover, *chapters])
