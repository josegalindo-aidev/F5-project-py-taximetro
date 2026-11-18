<!--
Proyecto: py-taximetro
fuente: docs/TOOLS.md
-->

# Herramientas adicionales del proyecto

Las herramientas que se usan **alrededor** del código del taxímetro: cómo se montaron y cómo se configuran. No forman parte de la memoria técnica en PDF (véase [D33](DECISIONS.md#d33)): son material de trabajo, no del producto.

| Herramienta | Para qué | Dónde está |
|---|---|---|
| Tablero «TTX-247 Taxímetro» | Seguir las historias y las tareas por fase | GitHub Projects |
| Generador de la memoria técnica | Producir el PDF a partir de los documentos de `docs/` | `scripts/build_memoria.py` y `.github/workflows/memoria.yml` |
| `verificar.py` | Lanzar pruebas, cobertura y estilo con una sola orden | `scripts/verificar.py` |

## 1. Tablero «TTX-247 Taxímetro»

Un proyecto de GitHub Projects del usuario del repositorio (el número 1). Es **privado**, así que solo lo ve su propietario. El backlog completo se mantiene además, como copia de trabajo, en `docs/project_backlog.xlsx`.

**Cómo se generó.** Se creó desde GitHub Projects con la plantilla de planificación de equipo, que trae las vistas *Backlog*, *Priority board*, *Team items*, *Roadmap* y *My items*, y se le añadieron los campos y la vista propios del proyecto.

**Campos que usa el proyecto:**

| Campo | Valores | Para qué |
|---|---|---|
| Status | Backlog, Ready, In progress, In review, Done | Estado de la tarjeta; se mueve a mano durante la fase |
| Fase | F1 - MVP CLI, F2 - Observabilidad, F3 - Arquitectura y UI, F4 - Producción, Transversal | Fase de entrega a la que pertenece |
| Tipo | Historia, Tarea técnica | Distingue las US de las TK |
| MoSCoW | Must, Should, Could, Won't | Prioridad de negocio |
| Estimate | Número | Puntos de esfuerzo |

*Priority* y *Size* vienen de la plantilla y no se usan.

**Vistas.** Las cinco de la plantilla más **Por fase**, un tablero agrupado por *Fase* (TK-11) que muestra de un vistazo qué hay en cada fase.

**Alta de trabajo.** Los formularios de `.github/ISSUE_TEMPLATE/` (`historia.yml` y `tarea-tecnica.yml`) crean el issue con su etiqueta (`historia` o `tarea-tecnica`). Las siete automatizaciones integradas de GitHub Projects están activadas (añadir al tablero los issues y sub-issues nuevos, y reaccionar al cierre de un issue o a que una PR se vincule o se fusione). Después se rellenan a mano **Tipo**, **Fase** y **MoSCoW**.

**Cierre.** Las PR hacia la rama de release usan `Refs #n` y los issues se cierran con la promoción a `main`; el detalle está en la [guía de trabajo](CONTRIBUTING.md#4-cierre-de-issues-y-tablero).

## 2. Generador de la memoria técnica

La documentación del proyecto se escribe **a mano, en Markdown, en `docs/`**, y no se extrae del código. Este generador la reúne en un único PDF, sin duplicar nada: el PDF no se escribe, se **ensambla**.

**Cómo se generó.** `scripts/build_memoria.py` solo usa la biblioteca estándar. Une los documentos en un Markdown con portada (quita la cabecera de cada uno, convierte las anclas de las decisiones y reescribe los enlaces entre documentos) y Pandoc lo convierte en PDF con XeLaTeX. Las funciones que deciden se prueban en `tests/unit/test_build_memoria.py`.

**Configuración:**

| Qué | Dónde | Detalle |
|---|---|---|
| Documentos y orden | `DOCUMENTS` en el script | Arquitectura, diseño, decisiones, pruebas, uso y guía de trabajo |
| Documentos excluidos | `EXCLUDED` en el script | `TOOLS.md`. Un test obliga a que cada documento de `docs/` esté en una de las dos listas |
| Versión y nombre | `pyproject.toml` | El PDF se llama `taximetro-memoria-<versión>.pdf` |
| Carpeta de salida | `--salida` | Por defecto `build/memoria`, que Git ignora |
| Motor | Pandoc y XeLaTeX | Se instalan en la CI, no en el entorno de desarrollo |
| Estructura | Clase `report` | Portada, índice y cada documento como capítulo en página nueva; los apartados conservan la numeración escrita en los documentos |
| Fuente de código | DejaVu Sans Mono | Trae los trazos de los árboles de carpetas y de los diagramas; se instala en la CI |

**Uso en local:**

```bash
python scripts/build_memoria.py
```

Escribe `build/memoria/memoria.md`. Si `pandoc` no está instalado, lo avisa y termina sin error: el PDF lo produce la CI.

**En GitHub Actions.** El workflow `.github/workflows/memoria.yml` se ejecuta en las PR que cambian `docs/`, el script o `pyproject.toml`, y a mano desde la pestaña *Actions*. Guarda el PDF como artefacto `memoria-pdf` durante 14 días; se baja desde la página de la ejecución o con `gh run download`. El PDF no se guarda en el repositorio.

**Límites conocidos:** los enlaces al README no funcionan dentro del PDF, los diagramas Mermaid salen como código y las marcas ✅ ⏳ ≥ ↔ y los círculos de colores del texto no se ven, porque su fuente no las trae. Las razones y las alternativas están en [D33](DECISIONS.md#d33).

## 3. `verificar.py`

Una sola orden que sustituye a varias de `pytest`, `coverage` y `ruff`, para que todos comprueben lo mismo y el resultado se lea de un vistazo ([D31](DECISIONS.md#d31)).

**Cómo se generó.** Es `scripts/verificar.py`, solo con la biblioteca estándar. La lógica que decide (la orden de `pytest`, la lectura del resumen y el veredicto) está separada del código que lanza procesos, y se prueba en `tests/unit/test_verificar.py`.

```bash
python scripts/verificar.py --lint
```

**Qué hace.** Ejecuta las pruebas, mide la cobertura de ramas y, con `--lint`, pasa Ruff. Termina con `VERDE` o `ROJO` y el motivo.

**Configuración:**

| Qué | Dónde | Valor |
|---|---|---|
| Mínimo de cobertura del proyecto | `MIN_PROJECT` en el script | 80 % |
| Mínimo de cobertura del núcleo | `MIN_CORE` en el script | 90 % |
| Opciones | Línea de comandos | `--rapido`, `--lint`, `--detalle` y rutas de pruebas |

Las opciones y ejemplos están en la [guía de pruebas](TESTING.md). El hook local de `pre-commit` aplica los mismos mínimos antes de cada commit (se pueden cambiar con `MIN_COVERAGE_TOTAL` y `MIN_COVERAGE_CORE`); Git no lo sube, es de cada equipo.
