# Proyecto: py-taximetro
# fuente: scripts/build_memoria.py
"""Ensambla la memoria técnica en un único Markdown a partir de los documentos de docs/."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Documentos de docs/ que forman la memoria, en el orden en que aparecen.
DOCUMENTS = (
    "ARCHITECTURE.md",
    "DESIGN.md",
    "DECISIONS.md",
    "TESTING.md",
    "USAGE.md",
    "CONTRIBUTING.md",
)
# Documentos de docs/ que se dejan fuera de la memoria a propósito.
EXCLUDED = ("TOOLS.md", "AUTOEVALUACION.md")
TITLE = "Memoria técnica del taxímetro digital (TTX-247)"

_HEADER_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.DOTALL)
_FIRST_TITLE = re.compile(r"^# (.+?)[ \t]*$", re.MULTILINE)
_HTML_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
_LINK = re.compile(r"\]\(([^)#\s]+)(#[^)\s]*)?\)")
_MERMAID_BLOCK = re.compile(r"^```mermaid\n(.*?)\n```[ \t]*$", re.MULTILINE | re.DOTALL)
DIAGRAMS_DIR = "diagramas"


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


def extract_diagrams(text: str) -> tuple[str, list[str]]:
    """Sustituye cada bloque Mermaid por una imagen numerada y devuelve sus textos."""
    sources: list[str] = []

    def replace(found: re.Match[str]) -> str:
        sources.append(found[1])
        number = len(sources)
        return f"![Diagrama {number}]({DIAGRAMS_DIR}/diagrama-{number}.pdf)"

    return _MERMAID_BLOCK.sub(replace, text), sources


# Opciones de Chrome para mmdc: la CI no permite el sandbox, y el texto son documentos propios.
CHROME_CONFIG = '{"args": ["--no-sandbox"]}'


def mermaid_command(source: str, target: str, chrome_config: str) -> list[str]:
    """Orden de mmdc que convierte un diagrama Mermaid en un PDF."""
    return ["mmdc", "-i", source, "-o", target, "-p", chrome_config, "--quiet"]


def assemble(texts: dict[str, str], version: str) -> str:
    """Une los documentos de la memoria, en orden y con portada, en un solo Markdown."""
    anchors = {name: name.removesuffix(".md").lower() for name in DOCUMENTS}
    cover = f'---\ntitle: "{TITLE}"\nsubtitle: "Versión {version}"\nlang: es\n---\n'
    chapters = [
        rewrite_links(convert_anchors(clean_document(texts[name], anchors[name])), anchors)
        for name in DOCUMENTS
    ]
    return "\n".join([cover, *chapters])


def pdf_name(version: str) -> str:
    """Nombre del PDF de la memoria para una versión del paquete."""
    return f"taximetro-memoria-{version}.pdf"


def pandoc_command(source: str, target: str) -> list[str]:
    """Orden de Pandoc que convierte el Markdown ensamblado en el PDF."""
    return [
        "pandoc",
        source,
        "--from=markdown+gfm_auto_identifiers",
        "--pdf-engine=xelatex",
        "--toc",
        "--toc-depth=3",
        "--top-level-division=chapter",
        "--variable=documentclass:report",
        "--variable=colorlinks:true",
        "--variable=monofont:DejaVu Sans Mono",
        "--variable=geometry:margin=2.5cm",
        "-o",
        target,
    ]


# Lanza una orden y devuelve su código de salida.
Runner = Callable[[list[str]], int]


def build(
    root: Path,
    out_dir: Path,
    runner: Runner,
    pandoc: str | None,
    output: Callable[[str], None] = print,
) -> int:
    """Escribe el Markdown ensamblado y, si hay Pandoc, lo convierte en PDF."""
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    texts = {name: (root / "docs" / name).read_text(encoding="utf-8") for name in DOCUMENTS}
    out_dir.mkdir(parents=True, exist_ok=True)
    source = out_dir / "memoria.md"
    source.write_text(assemble(texts, version), encoding="utf-8")
    output(f"[Memoria] Markdown ensamblado: {source}")

    if pandoc is None:
        output("[Memoria] AVISO: pandoc no está instalado, no se genera el PDF (lo hace la CI).")
        return 0
    target = out_dir / pdf_name(version)
    code = runner(pandoc_command(str(source), str(target)))
    if code == 0:
        output(f"[Memoria] PDF generado: {target}")
    else:
        output(f"[Memoria] FALLO: pandoc terminó con el código {code}")
    return code


def parse_args(argv: Sequence[str]) -> Path:
    parser = argparse.ArgumentParser(
        prog="build_memoria",
        description="Ensambla la memoria técnica y, si hay Pandoc, genera el PDF.",
    )
    parser.add_argument(
        "--salida", default="build/memoria", help="carpeta de salida (por defecto build/memoria)"
    )
    return Path(parser.parse_args(argv).salida)


def launch(command: list[str]) -> int:
    """Lanza una orden en la raíz del proyecto y devuelve su código de salida."""
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def main(argv: Sequence[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out_dir = parse_args(sys.argv[1:] if argv is None else argv)
    return build(ROOT, ROOT / out_dir, launch, shutil.which("pandoc"))


if __name__ == "__main__":
    raise SystemExit(main())
