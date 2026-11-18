# Proyecto: py-taximetro
# fuente: tests/unit/test_build_memoria.py
"""Script de la memoria técnica: cómo se prepara cada documento antes de ensamblarlo."""

from scripts.build_memoria import (
    assemble,
    clean_document,
    convert_anchors,
    pandoc_command,
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


def test_pandoc_genera_indice_y_numera_los_apartados():
    command = pandoc_command("a.md", "a.pdf")

    assert "--toc" in command
    assert "--number-sections" in command
