# Proyecto: py-taximetro
# fuente: tests/unit/test_build_memoria.py
"""Script de la memoria técnica: cómo se prepara cada documento antes de ensamblarlo."""

import json
from pathlib import Path

from scripts.build_memoria import (
    CHROME_CONFIG,
    DOCUMENTS,
    EXCLUDED,
    ROOT,
    assemble,
    build,
    clean_document,
    convert_anchors,
    extract_diagrams,
    mermaid_command,
    pandoc_command,
    parse_args,
    pdf_name,
    rewrite_links,
)

HEADER = "<!--\nProyecto: py-taximetro\nfuente: docs/USAGE.md\n-->\n\n"


def test_quita_la_cabecera_de_comentario_del_documento():
    text = HEADER + "# Manual de uso\n\nTexto.\n"

    assert "Proyecto: py-taximetro" not in clean_document(text, "usage")


def test_el_titulo_principal_recibe_un_identificador_para_enlazarlo():
    text = HEADER + "# Manual de uso\n\nTexto.\n"

    assert clean_document(text, "usage").startswith("# Manual de uso {#usage}\n")


def test_conserva_el_resto_del_contenido_sin_tocarlo():
    text = HEADER + "# Manual\n\n## Apartado\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"

    assert clean_document(text, "x").endswith("\n## Apartado\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")


def test_solo_el_primer_titulo_recibe_identificador():
    text = HEADER + "# Uno\n\n```bash\n# comentario de shell\n```\n"

    assert clean_document(text, "x").count("{#x}") == 1


def test_un_documento_sin_cabecera_se_deja_igual_salvo_el_identificador():
    assert clean_document("# Título\n\nTexto.\n", "t") == "# Título {#t}\n\nTexto.\n"


def test_acepta_saltos_de_linea_de_windows():
    text = (HEADER + "# Manual\n\nTexto.\n").replace("\n", "\r\n")

    result = clean_document(text, "usage")

    assert "\r" not in result
    assert result.startswith("# Manual {#usage}\n")


ANCHORS = {"DECISIONS.md": "decisions", "ARCHITECTURE.md": "architecture"}


def test_un_enlace_a_otro_documento_con_ancla_apunta_a_esa_ancla_interna():
    text = "Véase [D25](DECISIONS.md#d25)."

    assert rewrite_links(text, ANCHORS) == "Véase [D25](#d25)."


def test_un_enlace_a_otro_documento_sin_ancla_apunta_a_su_titulo():
    text = "Véase [la arquitectura](ARCHITECTURE.md)."

    assert rewrite_links(text, ANCHORS) == "Véase [la arquitectura](#architecture)."


def test_un_enlace_interno_del_propio_documento_no_cambia():
    assert rewrite_links("[arriba](#cabecera)", ANCHORS) == "[arriba](#cabecera)"


def test_los_enlaces_externos_y_a_ficheros_fuera_de_la_memoria_no_cambian():
    text = "[web](https://example.com/DECISIONS.md) y [readme](../README.md#versionado)"

    assert rewrite_links(text, ANCHORS) == text


def test_reescribe_todos_los_enlaces_de_un_mismo_texto():
    text = "[a](DECISIONS.md#d1), [b](DECISIONS.md#d2) y [c](ARCHITECTURE.md)"

    assert rewrite_links(text, ANCHORS) == "[a](#d1), [b](#d2) y [c](#architecture)"


def test_un_ancla_html_se_convierte_en_ancla_de_pandoc():
    assert convert_anchors('| <a id="d25"></a>D25 | Calidad |') == "| []{#d25}D25 | Calidad |"


def test_convierte_todas_las_anclas_de_un_texto():
    text = '<a id="d1"></a>D1\n<a id="d2"></a>D2\n'

    assert convert_anchors(text) == "[]{#d1}D1\n[]{#d2}D2\n"


def test_el_texto_sin_anclas_no_cambia():
    text = "Texto con [enlace](#d1) y `<a>` en código."

    assert convert_anchors(text) == text


DOCUMENT_NAMES = [
    "ARCHITECTURE.md",
    "DESIGN.md",
    "DECISIONS.md",
    "TESTING.md",
    "USAGE.md",
    "CONTRIBUTING.md",
]


def sample_texts() -> dict[str, str]:
    return {name: f"{HEADER}# Documento {name}\n\nCuerpo.\n" for name in DOCUMENT_NAMES}


def test_la_memoria_empieza_por_una_portada_con_la_version():
    memoria = assemble(sample_texts(), "1.2.3")

    assert memoria.startswith("---\n")
    assert 'title: "Memoria técnica del taxímetro digital (TTX-247)"' in memoria
    assert 'subtitle: "Versión 1.2.3"' in memoria
    assert "lang: es" in memoria


def test_incluye_los_documentos_en_el_orden_de_la_memoria():
    memoria = assemble(sample_texts(), "1.2.3")

    positions = [memoria.index(f"# Documento {name}") for name in DOCUMENT_NAMES]
    assert positions == sorted(positions)


def test_cada_documento_se_limpia_y_recibe_su_ancla():
    memoria = assemble(sample_texts(), "1.2.3")

    assert "Proyecto: py-taximetro" not in memoria
    assert "# Documento DECISIONS.md {#decisions}" in memoria


def test_convierte_los_enlaces_y_las_anclas_de_los_documentos():
    texts = sample_texts()
    texts["USAGE.md"] += '\nVéase [D1](DECISIONS.md#d1).\n'
    texts["DECISIONS.md"] += '\n| <a id="d1"></a>D1 | Dominio |\n'

    memoria = assemble(texts, "1.2.3")

    assert "Véase [D1](#d1)." in memoria
    assert "| []{#d1}D1 | Dominio |" in memoria


def test_ignora_los_documentos_que_no_forman_parte_de_la_memoria():
    texts = sample_texts() | {"OTRO.md": "# No debe salir\n"}

    assert "No debe salir" not in assemble(texts, "1.2.3")


def test_el_pdf_se_llama_como_el_proyecto_la_memoria_y_la_version():
    assert pdf_name("0.3.0a2.dev0") == "taximetro-memoria-0.3.0a2.dev0.pdf"


def test_pandoc_convierte_el_markdown_ensamblado_en_el_pdf_indicado():
    command = pandoc_command("memoria.md", "salida/memoria.pdf")

    assert command[:2] == ["pandoc", "memoria.md"]
    assert command[command.index("-o") + 1] == "salida/memoria.pdf"


def test_pandoc_usa_xelatex_para_los_acentos_y_los_simbolos():
    assert "--pdf-engine=xelatex" in pandoc_command("a.md", "a.pdf")


def test_pandoc_genera_indice():
    assert "--toc" in pandoc_command("a.md", "a.pdf")


def test_pandoc_no_numera_los_apartados_porque_los_documentos_ya_van_numerados():
    assert "--number-sections" not in pandoc_command("a.md", "a.pdf")


def test_cada_documento_es_un_capitulo_en_pagina_nueva_con_portada_propia():
    command = pandoc_command("a.md", "a.pdf")

    assert "--top-level-division=chapter" in command
    assert "--variable=documentclass:report" in command


def make_project(root):
    (root / "docs").mkdir()
    (root / "pyproject.toml").write_text('[project]\nversion = "9.8.7"\n', encoding="utf-8")
    for name, text in sample_texts().items():
        (root / "docs" / name).write_text(text, encoding="utf-8")


class FakeRunner:
    def __init__(self, code=0):
        self.code = code
        self.commands = []

    def __call__(self, command):
        self.commands.append(command)
        return self.code


def test_escribe_el_markdown_ensamblado_con_la_version_del_proyecto(tmp_path):
    make_project(tmp_path)

    build(tmp_path, tmp_path / "out", FakeRunner(), pandoc="pandoc", output=lambda _: None)

    memoria = (tmp_path / "out" / "memoria.md").read_text(encoding="utf-8")
    assert 'subtitle: "Versión 9.8.7"' in memoria
    assert "# Documento DESIGN.md {#design}" in memoria


def test_con_pandoc_lo_lanza_para_obtener_el_pdf_con_el_nombre_de_la_version(tmp_path):
    make_project(tmp_path)
    runner = FakeRunner()

    code = build(tmp_path, tmp_path / "out", runner, pandoc="pandoc", output=lambda _: None)

    assert code == 0
    (command,) = runner.commands
    assert command[1].endswith("memoria.md")
    assert command[command.index("-o") + 1].endswith("taximetro-memoria-9.8.7.pdf")


def test_sin_pandoc_deja_el_markdown_avisa_y_no_falla(tmp_path):
    make_project(tmp_path)
    runner = FakeRunner()
    lines = []

    code = build(tmp_path, tmp_path / "out", runner, pandoc=None, output=lines.append)

    assert code == 0
    assert runner.commands == []
    assert (tmp_path / "out" / "memoria.md").exists()
    assert any("pandoc" in line.lower() for line in lines)


def test_si_pandoc_falla_devuelve_su_codigo_de_salida(tmp_path):
    make_project(tmp_path)

    code = build(tmp_path, tmp_path / "out", FakeRunner(code=3), pandoc="pandoc", output=print)

    assert code == 3


def test_por_defecto_la_salida_va_a_build_memoria():
    assert parse_args([]) == Path("build/memoria")


def test_la_carpeta_de_salida_se_puede_elegir():
    assert parse_args(["--salida", "otra/carpeta"]) == Path("otra/carpeta")


def test_tools_no_forma_parte_de_la_memoria():
    assert "TOOLS.md" in EXCLUDED
    assert "TOOLS.md" not in DOCUMENTS


def test_cada_documento_de_docs_se_incluye_o_se_excluye_a_proposito():
    docs = {path.name for path in (ROOT / "docs").glob("*.md")}

    assert docs <= set(DOCUMENTS) | set(EXCLUDED), "documento sin decidir si va en la memoria"
    assert set(DOCUMENTS) <= docs, "la memoria incluye un documento que no existe"


def test_el_codigo_usa_una_fuente_con_los_trazos_de_los_arboles_de_carpetas():
    assert "--variable=monofont:DejaVu Sans Mono" in pandoc_command("a.md", "a.pdf")


def test_los_identificadores_de_los_titulos_son_los_de_github_para_que_los_enlaces_funcionen():
    assert "--from=markdown+gfm_auto_identifiers" in pandoc_command("a.md", "a.pdf")


FENCE = "`" * 3


def mermaid_block(source: str) -> str:
    return f"{FENCE}mermaid\n{source}\n{FENCE}\n"


def test_un_bloque_mermaid_se_sustituye_por_una_imagen_numerada():
    text = "Antes.\n\n" + mermaid_block("flowchart LR\n    A --> B") + "\nDespués.\n"

    result, _ = extract_diagrams(text)

    assert result == "Antes.\n\n![Diagrama 1](diagramas/diagrama-1.pdf)\n\nDespués.\n"


def test_devuelve_el_texto_de_cada_diagrama_sin_las_vallas():
    first = mermaid_block("flowchart LR\n    A --> B")
    second = mermaid_block("classDiagram\n    class X")
    text = first + "\n" + second

    _, sources = extract_diagrams(text)

    assert sources == ["flowchart LR\n    A --> B", "classDiagram\n    class X"]


def test_numera_los_diagramas_en_el_orden_en_que_aparecen():
    text = mermaid_block("a") + "\n" + mermaid_block("b") + "\n" + mermaid_block("c")

    result, _ = extract_diagrams(text)

    positions = [result.index(f"diagrama-{n}.pdf") for n in (1, 2, 3)]
    assert positions == sorted(positions)


def test_no_toca_los_demas_bloques_de_codigo():
    text = f"{FENCE}bash\npython scripts/verificar.py\n{FENCE}\n"

    assert extract_diagrams(text) == (text, [])


def test_un_texto_sin_diagramas_no_cambia():
    assert extract_diagrams("# Título\n\nTexto.\n") == ("# Título\n\nTexto.\n", [])


def test_mmdc_convierte_el_diagrama_en_el_pdf_indicado():
    command = mermaid_command("d.mmd", "d.pdf", "chrome.json")

    assert command[0] == "mmdc"
    assert command[command.index("-i") + 1] == "d.mmd"
    assert command[command.index("-o") + 1] == "d.pdf"


def test_mmdc_recibe_la_configuracion_de_chrome():
    command = mermaid_command("d.mmd", "d.pdf", "chrome.json")

    assert command[command.index("-p") + 1] == "chrome.json"


def test_mmdc_no_imprime_su_registro():
    assert "--quiet" in mermaid_command("d.mmd", "d.pdf", "chrome.json")


def test_la_configuracion_de_chrome_desactiva_el_sandbox_que_la_ci_no_permite():
    assert "--no-sandbox" in json.loads(CHROME_CONFIG)["args"]
