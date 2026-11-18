<!--
Proyecto: py-taximetro
fuente: docs/AUTOEVALUACION.md
-->

# Autoevaluación frente a la rúbrica

Índice que contrasta el proyecto con los criterios de la rúbrica del ejercicio (Fullstack, nivel Inicial). **No contiene evidencia propia**: cada fila da el veredicto y enlaza al apartado de los documentos donde la evidencia está trazada.

**Última revisión:** 18/11/2026, con la Fase 3 en desarrollo.

**Cómo comprobarlo.** La calidad del código se reproduce con una orden: `python scripts/verificar.py --lint` lanza las pruebas, la cobertura y el estilo, y termina con un veredicto `VERDE` o `ROJO` ([TESTING.md](TESTING.md#todo-de-una-vez-el-script-de-verificación)).

## 1. Configurar y automatizar el entorno de trabajo digital

| Criterio | Veredicto | Dónde está la evidencia |
|---|---|---|
| **Organiza directorios de proyecto** | Cumple | [README: estructura](../README.md#estructura) y [ARCHITECTURE: módulos](ARCHITECTURE.md#3-módulos-codificados). La regla de capas la comprueba [`tests/test_architecture.py`](../tests/test_architecture.py) |
| **Busca información técnica** | Cumple | [DECISIONS.md](DECISIONS.md) (el motivo de cada decisión), [README: dependencias y justificación](../README.md#dependencias-y-justificación) y los apartados de referencias: [DESIGN](DESIGN.md#11-referencias), [ARCHITECTURE](ARCHITECTURE.md#11-referencias), [TESTING](TESTING.md#8-referencias) y [CONTRIBUTING](CONTRIBUTING.md#12-referencias) |
| **Consulta documentación en inglés** | Cumple | Documentación oficial y estándares en inglés, cada uno con lo que se aplicó: [DESIGN](DESIGN.md#11-referencias) (Python), [ARCHITECTURE](ARCHITECTURE.md#11-referencias) (Python), [TESTING](TESTING.md#8-referencias) (pytest, coverage.py, Ruff y PEP 8) y [CONTRIBUTING](CONTRIBUTING.md#12-referencias) (GitHub, Conventional Commits, SemVer y PEP 440) |
| **Instala aplicaciones y extensiones** | Cumple | [README: instalación y arranque](../README.md#instalación-y-arranque), [CONTRIBUTING: entorno de desarrollo](CONTRIBUTING.md#11-entorno-de-desarrollo) (editor y extensiones) las herramientas declaradas en [`pyproject.toml`](../pyproject.toml) y [TOOLS.md](TOOLS.md) (herramientas adicionales: tablero, generador de la memoria técnica y `verificar.py`) |

## 2. Aplicar fundamentos, paradigmas y buenas prácticas de programación

| Criterio | Veredicto | Dónde está la evidencia |
|---|---|---|
| **Organización y legibilidad básica** | Cumple | [DESIGN: recursos de Python](DESIGN.md#10-recursos-de-python-que-usa-el-código) (legibilidad), [TESTING: convenciones](TESTING.md#7-convenciones-de-los-tests) y [ARCHITECTURE: convenciones del repositorio](ARCHITECTURE.md#7-convenciones-del-repositorio) |
| **Declara y utiliza variables y tipos de datos** | Cumple | [DESIGN: recursos de Python](DESIGN.md#10-recursos-de-python-que-usa-el-código) y [DESIGN: `Tariff` y `Trip`](DESIGN.md#32-state-y-tariff-lo-más-pequeño-del-dominio) |
| **Implementa estructuras de control de flujo** | Cumple | [DESIGN: recursos de Python](DESIGN.md#10-recursos-de-python-que-usa-el-código) y [DESIGN: `TripService`](DESIGN.md#34-tripservice-el-caso-de-uso-que-opera) |
| **Utiliza colecciones y genéricos** | Cumple | [DESIGN: recursos de Python](DESIGN.md#10-recursos-de-python-que-usa-el-código), con la tabla de comandos de `Cli` y los contratos de `core/ports.py`. No se definen genéricos propios, lo que a este nivel no se exige |
| **Descompone problemas en pasos lógicos** | Cumple | [DESIGN: del enunciado a las clases](DESIGN.md#2-del-enunciado-a-las-clases), [DESIGN: una carrera completa](DESIGN.md#flujo-de-una-carrera) y [TESTING: cómo se trabaja con TDD](TESTING.md#1-cómo-se-trabaja-tdd) |

## 3. Cómo se mantiene

- Se revisa al cerrar cada fase y se actualiza la fecha de la última revisión.
- La evidencia vive en los documentos que se enlazan: si cambia, se actualiza allí y aquí solo cambia el veredicto, con el motivo en la propia fila.
- Las cifras que caducan (número de pruebas, de clases o de líneas) no se escriben en ningún documento: se obtienen ejecutando `python scripts/verificar.py --lint`.
- Las herramientas y las fuentes de los documentos solo incluyen lo que se ha usado y consultado de verdad.
