<!--
Proyecto: py-taximetro
fuente: README.md
-->

# py-taximetro · Taxímetro digital (TTX-247)

Prototipo de taxímetro 100 % software para **TaxiTech Solutions S.L.**, que sustituye a los taxímetros físicos Hale T200 (sin soporte desde 2023). Calcula el importe de cada carrera por segundo según el estado del taxi y lo muestra en euros.

Proyecto del bootcamp de Factoría F5, desarrollado con **TDD** y una arquitectura modular.

**Fuente del ejercicio:** [Factoria-F5-madrid/project-py-taximetro](https://github.com/Factoria-F5-madrid/project-py-taximetro), con el enunciado, las fases de entrega y los requisitos.

## Estado del proyecto

| Fase | Contenido | Estado |
|---|---|---|
| **1 · MVP CLI** | Iniciar, cambiar de estado y finalizar carreras desde la consola; encadenar carreras | ✅ Implementada |
| 2 · Observabilidad y persistencia | Logs, historial en disco, histórico del día y tarifas en fichero (ya hecho) | En desarrollo |
| 3 · Arquitectura y UI | Acceso con contraseña e interfaz gráfica para tablet | ⏳ Planificada |
| 4 · Producción | Base de datos, API REST, panel web y despliegue con un comando | ⏳ Planificada |

## Requisitos

- Python **3.11 o superior**.
- Git.

## Instalación y arranque

Desde la raíz del repositorio. En **Git Bash** (Windows):

```bash
python -m venv .venv
```

```bash
source .venv/Scripts/activate
```

```bash
pip install -e ".[dev]"
```

En PowerShell se activa con `.\.venv\Scripts\Activate.ps1`; en Linux o macOS, con `source .venv/bin/activate`.

Arranque del taxímetro:

```bash
python -m taximetro
```

(Tras la instalación también está disponible el comando `taximetro`.)

## Uso en un minuto

El programa muestra las instrucciones al arrancar y espera comandos:

| Comando | Qué hace |
|---|---|
| `iniciar` | Inicia una carrera (el taxi empieza parado) |
| `parar` | El taxi está parado |
| `mover` | El taxi está en movimiento |
| `estado` | Muestra el estado y el importe actual |
| `finalizar` | Termina la carrera y muestra el total |
| `ayuda` | Repite las instrucciones |
| `salir` | Cierra el programa |

Tarifas (Zona EMT Madrid, junio 2025): **0,02 €/s** parado (o a menos de 20 km/h) y **0,05 €/s** en movimiento. El estado lo indicas tú con `parar` y `mover`. Las tarifas se leen de `config/rates.toml` al arrancar, así que se pueden cambiar sin tocar el código.

Cada carrera finalizada se guarda en un historial en disco, que se conserva al cerrar el programa. Al arrancar, el programa indica la ruta (`Historial: …`). La carpeta de datos se elige con la variable `TAXIMETRO_DATA_DIR` y, por defecto, es `data/` en la raíz del proyecto.

Manual completo, con ejemplos, cómo configurar las tarifas y dónde se guardan los datos, y mensajes de error: [docs/usage.md](docs/usage.md).

## Pruebas y calidad

Todas las pruebas:

```bash
python -m pytest
```

Solo las **pruebas de aceptación** (US-01 a US-04 y el historial en disco, de principio a fin):

```bash
python -m pytest tests/acceptance -v
```

Cobertura y calidad del código:

```bash
python -m pytest --cov=src/taximetro --cov-report=term-missing
```

```bash
python -m ruff check src tests
```

Las pruebas se ejecutan siempre con `pytest`. Un fichero de tests no es un programa: `python -m` sobre él no ejecuta ninguna prueba, termina en silencio y con código 0, aunque alguna fallara. Más ejemplos (un fichero, un test por nombre) y cómo se escriben las pruebas: [docs/TESTING.md](docs/TESTING.md).

## Estructura

```
src/taximetro/
├── core/      Reglas de negocio puras: Tariff, Trip, TripService, errores y puertos
├── ui/cli/    Interfaz de línea de comandos
├── infra/     Adaptadores externos: carga de tarifas y repositorios de carreras (memoria y JSON)
└── __main__.py  Punto de arranque
tests/         Pruebas unitarias, de integración, de aceptación y de convenciones
docs/          Documentación y backlog
config/        Tarifas (rates.toml)
data/          Historial de carreras (trips.json); se crea al guardar la primera y Git lo ignora
```

## Documentación

| Documento | Contenido |
|---|---|
| [docs/usage.md](docs/usage.md) | Manual de uso del taxímetro |
| [docs/architecture.md](docs/architecture.md) | Arquitectura, módulos y decisiones de diseño |
| [docs/TESTING.md](docs/TESTING.md) | Cómo se prueba el proyecto: TDD, niveles de prueba, ejecución y mutaciones |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Flujo de trabajo: ramas, PR, commits y releases |
| [docs/project_backlog.xlsx](docs/project_backlog.xlsx) | Backlog con historias de usuario, fases y avance |

## Dependencias y justificación

El programa **no tiene dependencias externas en ejecución**: usa solo la biblioteca estándar de Python. Las herramientas de desarrollo son:

| Herramienta | Para qué |
|---|---|
| `pytest` y `pytest-cov` | Ejecutar las pruebas (TDD) y medir la cobertura |
| `ruff` | Comprobar el estilo y los errores comunes del código |
| `hatchling` | Construir e instalar el paquete (`pyproject.toml`) |

Las fases siguientes incorporarán `sqlalchemy` (base de datos) y `fastapi` con `uvicorn` (API), declaradas como extras opcionales (`[sql]` y `[api]`). Esta sección se ampliará con su justificación cuando se usen.

## Versionado

Se sigue el [versionado semántico](https://semver.org/lang/es/) (`MAJOR.MINOR.PATCH`). La versión vive **solo** en `pyproject.toml`, y el estado de las versiones publicadas, **solo** en esta sección: no se repite en ningún otro fichero.

| Número | Significado | Cuándo sube |
|---|---|---|
| `MAJOR` | Cambios incompatibles. Con `0` el proyecto está en desarrollo inicial y la interfaz puede cambiar. | Al llegar a producción (`1.0.0`) |
| `MINOR` | Funcionalidad nueva compatible | Al cerrar cada fase |
| `PATCH` | Corrección de errores | Cuando haga falta, sin esperar a una fase |

| Fase | Versión | Estado |
|---|---|---|
| 1 · MVP CLI | `0.1.0` | ✅ [Publicada](https://github.com/josegalindo-aidev/F5-project-py-taximetro/releases/tag/v0.1.0) |
| 2 · Observabilidad y persistencia | `0.2.0` | ⏳ Planificada |
| 3 · Arquitectura y UI | `0.3.0` | ⏳ Planificada |
| 4 · Producción | `1.0.0` | ⏳ Planificada |

Al cerrar una fase se sube `version` en `pyproject.toml` dentro de su PR y se crea la etiqueta `vX.Y.Z` con su release en GitHub.

## Flujo de trabajo

Cada fase se desarrolla en una rama `release/X.Y.Z`, con una rama por funcionalidad que se integra en ella. `main` solo avanza cuando la demo de la fase la valida. **Todo cambio entra por PR**: no hay `push` directo a `main` ni a las ramas de release. Ramas, PR, cierre de issues, promoción de releases y limitaciones: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Metodología

- **TDD**: primero el test en rojo, luego el código mínimo y después el refactor ([guía de pruebas](docs/TESTING.md)).
- **Commits** en formato [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/), con referencia al issue.
- **Seguimiento** en el tablero GitHub Projects «TTX-247 Taxímetro» (una vista por fase) y en los issues del repositorio.
