# Proyecto: py-taximetro
# fuente: tests/unit/test_build_memoria.py
"""Script de la memoria técnica: cómo se prepara cada documento antes de ensamblarlo."""

from scripts.build_memoria import clean_document, rewrite_links

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
