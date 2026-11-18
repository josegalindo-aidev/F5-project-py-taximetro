<!--
Proyecto: py-taximetro
fuente: docs/AUTOEVALUACION.md
-->

# Autoevaluación frente a la rúbrica

Índice que contrasta el proyecto con los criterios de la rúbrica del ejercicio (Fullstack, nivel Inicial). **No contiene evidencia propia**: cada fila da el veredicto y enlaza al apartado de los documentos donde la evidencia está trazada.

**Última revisión:** 18/11/2026, sobre la Fase 2 entregada.

**Cómo comprobarlo.** La calidad del código se reproduce con las órdenes del [README](../README.md#pruebas-y-calidad): `python -m pytest --cov=src/taximetro --cov-branch --cov-report=term-missing` para las pruebas y la cobertura, y `python -m ruff check src tests` para el estilo.

## 1. Configurar y automatizar el entorno de trabajo digital

| Criterio | Veredicto | Dónde está la evidencia |
|---|---|---|
| **Organiza directorios de proyecto** | Cumple | [README: estructura](../README.md#estructura) y [ARCHITECTURE: módulos](ARCHITECTURE.md#3-módulos-codificados) |
| **Busca información técnica** | Cumple | [ARCHITECTURE: decisiones de diseño](ARCHITECTURE.md#5-decisiones-de-diseño) (el motivo de cada una), [README: dependencias y justificación](../README.md#dependencias-y-justificación) y los apartados de referencias: [ARCHITECTURE](ARCHITECTURE.md#12-referencias), [TESTING](TESTING.md#8-referencias) y [CONTRIBUTING](CONTRIBUTING.md#12-referencias) |
| **Consulta documentación en inglés** | Cumple | Documentación oficial y estándares en inglés, cada uno con lo que se aplicó: [ARCHITECTURE](ARCHITECTURE.md#12-referencias) (Python), [TESTING](TESTING.md#8-referencias) (pytest, coverage.py, Ruff y PEP 8) y [CONTRIBUTING](CONTRIBUTING.md#12-referencias) (GitHub, Conventional Commits y SemVer) |
| **Instala aplicaciones y extensiones** | Cumple | [README: instalación y arranque](../README.md#instalación-y-arranque), [CONTRIBUTING: entorno de desarrollo](CONTRIBUTING.md#11-entorno-de-desarrollo) (editor y extensiones) y las herramientas declaradas en [`pyproject.toml`](../pyproject.toml) |

## 2. Aplicar fundamentos, paradigmas y buenas prácticas de programación

| Criterio | Veredicto | Dónde está la evidencia |
|---|---|---|
| **Organización y legibilidad básica** | Cumple | [ARCHITECTURE: recursos de Python](ARCHITECTURE.md#11-recursos-de-python-que-usa-el-código) (legibilidad), [TESTING: convenciones](TESTING.md#7-convenciones-de-los-tests) y [ARCHITECTURE: convenciones del repositorio](ARCHITECTURE.md#7-convenciones-del-repositorio) |
| **Declara y utiliza variables y tipos de datos** | Cumple | [ARCHITECTURE: recursos de Python](ARCHITECTURE.md#11-recursos-de-python-que-usa-el-código) y [ARCHITECTURE: módulos del núcleo](ARCHITECTURE.md#3-módulos-codificados) |
| **Implementa estructuras de control de flujo** | Cumple | [ARCHITECTURE: recursos de Python](ARCHITECTURE.md#11-recursos-de-python-que-usa-el-código) y [ARCHITECTURE: reglas de negocio](ARCHITECTURE.md#41-modelo-de-cálculo) |
| **Utiliza colecciones y genéricos** | Cumple | [ARCHITECTURE: recursos de Python](ARCHITECTURE.md#11-recursos-de-python-que-usa-el-código), con la tabla de comandos de `Cli` y los contratos de `core/ports.py`. No se definen genéricos propios, lo que a este nivel no se exige |
| **Descompone problemas en pasos lógicos** | Cumple | [ARCHITECTURE: modelo de cálculo y reglas](ARCHITECTURE.md#41-modelo-de-cálculo), [ARCHITECTURE: flujo de una carrera](ARCHITECTURE.md#44-flujo-de-una-carrera-completa) y [TESTING: cómo se trabaja con TDD](TESTING.md#1-cómo-se-trabaja-tdd) |

## 3. Cómo se mantiene

- Se revisa al cerrar cada fase y se actualiza la fecha de la última revisión.
- La evidencia vive en los documentos que se enlazan: si cambia, se actualiza allí y aquí solo cambia el veredicto, con el motivo en la propia fila.
- Las herramientas y las fuentes de los documentos solo incluyen lo que se ha usado y consultado de verdad.
