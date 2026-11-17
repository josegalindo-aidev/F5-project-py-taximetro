<!--
Proyecto: py-taximetro
fuente: docs/TESTING.md
-->

# Guía de pruebas

Cómo se prueba el taxímetro y cómo se escribe una prueba nueva. El proyecto se desarrolla con **TDD**: primero el test, después el código.

## 1. Cómo se trabaja: TDD

El ciclo es **rojo, verde, refactor**, con **un solo test cada vez**:

| Fase | Qué se hace |
|---|---|
| 🔴 Rojo | Se escribe un test que expresa un comportamiento nuevo y se ejecuta: **debe fallar** |
| 🟢 Verde | Se escribe el código **mínimo** para que pase |
| 🔵 Refactor | Con todo en verde, se mejora el código en pasos pequeños, ejecutando las pruebas entre cada uno |

### Reglas prácticas

1. **El rojo debe ser por la razón correcta.** Se lee el mensaje del fallo: tiene que decir que falta el comportamiento, no que hay un error de importación. Para eso se crea antes un *esqueleto* mínimo (por ejemplo, una función que lanza `NotImplementedError`) que haga compilar el test.
2. **El verde es lo mínimo.** No se escribe código que ningún test pida todavía. Cada grieta que deja el código mínimo es el siguiente test.
3. **El refactor solo con todo en verde**, y en pasos pequeños. Si algo se rompe, se sabe qué fue.
4. **Un test que pasa a la primera cuando debía fallar es una alarma.** O el código ya hacía lo pedido, o el test no mide lo que se cree. Se investiga antes de seguir.
5. **Un test en verde no demuestra que el código sea correcto**, solo que no encontró el fallo. Para comprobarlo se usan las [pruebas de mutación](#6-pruebas-de-mutación-manuales).
6. **Los datos de prueba deben distinguir.** Casos asimétricos (13 y 15, no 15 y 15), valores en los bordes (una carrera a las 23:55 y otra a las 00:05) y ids que no coincidan con el orden esperado.
7. **Además de los tests, se ejecuta el programa real** y se contrasta lo que dice la documentación con lo que imprime.

## 2. Niveles de prueba

| Nivel | Carpeta | Qué prueba |
|---|---|---|
| Unitarias del núcleo | `tests/unit/core/` | `Tariff`, `Trip`, `TripService` y `DayReport`, aislados y sin entrada/salida, con repositorios simulados |
| Unitarias de la CLI | `tests/unit/ui/` | `Cli` y `format_euros`, con una consola simulada |
| Unitarias de los ajustes y del script | `tests/unit/test_settings.py` y `tests/unit/test_verificar.py` | `Settings` (valor explícito, variable de entorno y valor por defecto) y la lógica de `scripts/verificar.py` |
| Integración | `tests/integration/` | La infraestructura y el arranque, con ficheros temporales: cargador de tarifas, registro de eventos (`test_logging.py`), comportamiento propio del repositorio JSON (fichero dañado, escritura atómica), el montaje de la aplicación (`test_bootstrap.py`) y `main` |
| **Aceptación** | `tests/acceptance/` | Cada historia de usuario **de principio a fin** por la consola, con el nombre `test_usNN_…`. Las de la Fase 2 arrancan `main` entero sobre una carpeta de datos temporal (`test_fase2_historial.py`, `test_us05_historico.py`, `test_us06_logs.py`), con las utilidades comunes en `tests/acceptance/helpers.py`. `test_arranque_real.py` lanza `python -m taximetro` **en un proceso aparte**, como lo haría una persona, con datos y logs en una carpeta temporal |
| Contrato | `tests/contract/` | Reglas que debe cumplir **cualquier implementación** de un puerto: el repositorio en memoria y el JSON pasan la misma batería (apartado 5) |
| Arquitectura | `tests/test_architecture.py` | La regla de dependencias entre capas: lee los imports de cada fichero y falla si `core/` importa de otra capa o si `ui/` e `infra/` importan algo que no sea `core/` |
| Convenciones | `tests/test_conventions.py` | Reglas del repositorio, como la cabecera de los `.py` |
| Calidad | `tests/test_quality_gates.py` | Umbrales de calidad: la cobertura mínima del núcleo, configurada en `pyproject.toml` |

Las pruebas de aceptación son las más valiosas al cambiar el comportamiento visible: si una historia deja de cumplirse, fallan.

## 3. Cómo ejecutarlas

Comandos en Git Bash, desde la raíz del proyecto y con el entorno virtual activado.

Todas las pruebas:

```bash
python -m pytest
```

Con el nombre de cada test:

```bash
python -m pytest -v
```

Un nivel (por ejemplo, las de aceptación):

```bash
python -m pytest tests/acceptance -v
```

Un fichero:

```bash
python -m pytest tests/unit/core/test_trip.py
```

Los tests cuyo nombre contenga un texto (por ejemplo, la historia US-02):

```bash
python -m pytest tests/acceptance -k "us02"
```

Un test concreto:

```bash
python -m pytest "tests/acceptance/test_fase1_mvp.py::test_us01_iniciar_carrera_con_un_comando"
```

Ver en qué orden se preparan los *fixtures* de un test:

```bash
python -m pytest tests/unit/core/test_trip_service.py --setup-show -q
```

Cobertura del **núcleo** (`core/`). Falla, con código de salida 1, si baja del 90 % (TK-03):

```bash
python -m pytest --cov
```

Cobertura de todo el proyecto y estilo:

```bash
python -m pytest --cov=src/taximetro --cov-report=term-missing
```

La cobertura se configura en `[tool.coverage]` de `pyproject.toml`: se mide `src/taximetro/core`, se cuentan también las **ramas** (un `if` cuyo camino «no» nunca se ejecuta cuenta como sin cubrir) y el mínimo es `fail_under = 90`. También se activa la cobertura de **subprocesos** (`patch = ["subprocess"]`), para que cuente la prueba que arranca `python -m taximetro` en un proceso aparte. `tests/test_quality_gates.py` falla si alguien baja el umbral, quita las ramas o los subprocesos, o cambia lo que se mide.

Ejecutar `--cov` con **un solo fichero de tests** dará una cobertura baja y fallará: es lo esperado, porque el umbral se refiere a la suite completa.

```bash
python -m ruff check src tests
```

### Todo de una vez: el script de verificación

Para no escribir las órdenes una a una, `scripts/verificar.py` lanza las pruebas, la cobertura y, si se pide, el estilo, y termina con un veredicto. Solo usa la biblioteca estándar y el Python con el que se ejecuta, así que sirve con el entorno virtual activado desde cualquier terminal.

```bash
python scripts/verificar.py
```

| Orden | Qué hace |
|---|---|
| `python scripts/verificar.py` | Toda la suite con cobertura de ramas, informe del proyecto y del núcleo con las líneas sin cubrir, y veredicto |
| `python scripts/verificar.py --rapido` | Solo las pruebas, sin cobertura |
| `python scripts/verificar.py --lint` | Lo anterior y además Ruff |
| `python scripts/verificar.py tests/unit/core` | Solo esas pruebas (ejecución **parcial**) |
| `python scripts/verificar.py --detalle` | Muestra el nombre de cada prueba y su resultado (una línea por prueba) |

Las opciones se combinan: `python scripts/verificar.py --rapido --lint tests/unit`.

Las líneas que escribe el script llevan la marca `[Verifica]`, para distinguirlas de la salida de pytest y de Ruff, que se muestra tal cual. El script avanza por **pasos numerados** (`Paso 1 de 3: pruebas`, `Paso 2 de 3: cobertura`, `Paso 3 de 3: estilo`; el total depende de las opciones) y explica lo que va a mostrar:

| Línea | Qué cuenta |
|---|---|
| `Leyenda: . superada · F fallida · E error · s omitida · [nn%] avance` | Cómo leer la salida de pytest: cada `.` es una prueba superada y el porcentaje del final de cada línea es el avance de la ejecución. Con `--detalle` dice que cada línea es una prueba |
| `Pruebas: 323 superadas, 0 fallidas, 0 con error, 0 omitidas, en 2.21 s` | Resumen propio de las pruebas. Si no puede leer el resumen de pytest, lo dice |
| `Columnas: Stmts, Miss, Branch, BrPart, Cover, Missing` | Qué significa cada columna de las tablas de cobertura: líneas ejecutables, sin cubrir, ramas, ramas a medias, porcentaje y números de las líneas sin cubrir |
| `Resultado del proyecto: 99.64% (mínimo 80%)` | Cobertura de cada tabla frente a su mínimo. En una ejecución parcial dice `no se juzga: ejecución parcial` |
| `Estilo: sin errores` | Resultado de Ruff (solo con `--lint`) |

La última línea es el veredicto:

- `[Verifica] VERDE: todo en orden`, con código de salida 0.
- `[Verifica] ROJO: ...`, con código de salida 1 y los motivos: pruebas en rojo, cobertura por debajo del mínimo o errores de estilo.

Los mínimos son el 80 % para el proyecto y el 90 % para el núcleo, los mismos que comprueba el hook de pre-commit. En una ejecución **parcial** el script avisa de que la cobertura no es representativa y no la juzga: solo cuentan las pruebas (y el estilo, si se pidió).

### No se ejecutan con `python -m <fichero>`

Un fichero de tests solo **define** funciones; quien las llama es `pytest`. Ejecutarlo como un programa termina **en silencio y con código de salida 0**, aunque alguna prueba fallara:

| Comando | Resultado con un test que falla a propósito |
|---|---|
| `python -m test_roto` | Silencio y código 0: parece que todo va bien |
| `python -m pytest` | `1 failed`, con el detalle del fallo |

## 4. Dobles de prueba y fixtures

El código recibe sus dependencias (reloj, teclado, pantalla) en lugar de crearlas, y los tests le pasan versiones controlables. Así no hay esperas ni teclado real.

| Pieza | Dónde | Para qué |
|---|---|---|
| `FakeClock` | `tests/fakes.py` | Reloj que avanza a mano con `advance(segundos)`: simula el paso del tiempo sin esperar |
| `FakeWallClock` | `tests/fakes.py` | Reloj de pared (fecha y hora con zona) controlable: simula *cuándo* ocurre algo, sin depender del día real |
| `BrokenRepository` | `tests/fakes.py` | Repositorio cuyo guardado siempre falla (`OSError`): prueba que el total se muestra aunque no se pueda guardar |
| `FakeEventLog` | `tests/fakes.py` | Registro de eventos en memoria: permite comprobar qué eventos, con qué hora y datos, anota el servicio |
| `FailingEventLog` | `tests/fakes.py` | Registro cuya escritura siempre falla (`OSError`): prueba que un fallo del log nunca impide cobrar ni esconde el total |
| `UnreadableHistoryRepository` | `tests/fakes.py` | Repositorio cuya consulta siempre falla (`TripHistoryError`): prueba que `historico` muestra el error y el programa sigue |
| `ScriptedInput` | `tests/fakes.py` | Consola que devuelve comandos y avanza el reloj entre ellos |
| `tariff` | `tests/conftest.py` | La tarifa oficial (0,02 y 0,05 €/s), disponible en cualquier test |
| `tmp_path` | `pytest` | Carpeta temporal para los ficheros de prueba: nunca se toca `config/` ni `data/` |
| `monkeypatch` | `pytest` | Cambia una variable de entorno o una función solo durante un test y la restaura al terminar |
| `isolated_log_dir` | `tests/conftest.py` | Fixture automático: apunta `TAXIMETRO_LOG_DIR` a una carpeta temporal, para que ningún test escriba logs en `logs/` del proyecto |
| `capsys` | `pytest` | Captura lo que el programa imprime por `stdout` y `stderr` |

Los datos de las pruebas se eligen para que solo una implementación correcta pueda explicarlos. Por ejemplo, el test del arranque usa tarifas de 0,10 y 0,20 €/s, no las oficiales: con las oficiales pasaría igualmente aunque no se leyera el fichero.

## 5. Pruebas de contrato

Un puerto (por ejemplo `TripRepository`) tiene varias implementaciones. Los tests del **contrato** describen lo que cualquiera de ellas debe cumplir y se escriben **una sola vez**: la fixture `repository` de `tests/contract/test_trip_repository.py` está parametrizada y cada test se ejecuta contra todas.

```python
@pytest.fixture(params=["memory", "json"])
def repository(request, tmp_path):
    ...
```

Añadir una implementación nueva (por ejemplo, SQL) es añadir un valor a `params` y su construcción: si se comporta distinto del resto, algún test del contrato falla. Lo que es propio de una implementación y el contrato no puede expresar (un fichero dañado, la escritura atómica) va en su propio fichero de `tests/integration/`.

### Simular fallos que no se pueden provocar de verdad

| Fallo | Cómo se simula |
|---|---|
| El disco se llena o el equipo se corta **a mitad de escritura** | `monkeypatch` sustituye `Path.write_text` por una versión que escribe la mitad del texto y lanza `OSError`; después se comprueba que el fichero anterior está intacto y que no quedan temporales |
| Un fichero que existe pero **no se puede leer** | Crear una **carpeta** con el nombre del fichero: da error de lectura en cualquier sistema operativo |
| Un historial **dañado** | Escribir texto que no es JSON, o un JSON con la forma equivocada, y comprobar también que el fichero no se modifica |
| Un guardado que falla en un test de la CLI o del servicio | `BrokenRepository`, que siempre lanza `OSError` |

## 6. Pruebas de mutación manuales

Para saber si los tests protegen de verdad, se **rompe el código a propósito**, de una forma cada vez, y se comprueba que algún test falla:

1. Se guarda una copia del fichero.
2. Se introduce una rotura (quitar una validación, cambiar `+=` por `=`, alterar un mensaje, invertir un orden…).
3. Se ejecutan las pruebas: **tienen que fallar**. Si pasan, el mutante «sobrevive» y falta un test.
4. Se restaura el original y se verifica que es idéntico, byte a byte.

Lecciones aprendidas con esta técnica:

| Mutante vivo | Causa | Solución |
|---|---|---|
| Un mensaje cambiado no hacía fallar el test | `pytest` crea la carpeta temporal con el nombre del test, y esa ruta aparecía en el mensaje, así que el `match` se cumplía por casualidad | Comprobar una frase que la ruta no pueda contener |
| Ordenar por nombre en vez de por fecha | Los ids estaban en orden alfabético *y* cronológico a la vez | Ids que no sigan ningún orden esperado |
| `=` en vez de `+=` en un acumulador | Los tests tenían un único tramo por estado | Varios tramos del mismo estado |
| Un test de «no repite la ruta» pasaba cuando debía fallar | Windows muestra las barras duplicadas en el error del sistema | Contar el nombre de la carpeta, no la ruta completa |
| Un mensaje de error del historial cumplía el test por casualidad | El nombre del fichero buscado coincidía con parte de la ruta temporal del test | Dar al fichero de prueba un nombre que la ruta no pueda contener (`historial.json`) |
| Un mensaje que nombraba la ruta equivocada pasaba los tests | El test solo buscaba un fragmento (el nombre del fichero), que también forma parte de la ruta completa | Comparar el **texto completo** del mensaje |

Cuidado al automatizarlo con scripts: los ficheros del proyecto pueden tener saltos de línea de Windows, y un patrón de varias líneas escrito con `\n` no coincidiría. Se mutan líneas sueltas y se leen y escriben los **bytes**, sin transformarlos.

Un script de mutación fiable cumple estas reglas:

1. **Cada patrón debe aparecer exactamente una vez** en el fichero. Si no, se avisa en lugar de mutar a ciegas.
2. **La restauración se comprueba** con un hash del fichero antes y después de cada mutante, y el script se detiene si no coincide. Al final, `git status` tiene que estar vacío.
3. **El resultado se cuenta, no se estima**: el propio script imprime «N de M detectados» y los supervivientes.
4. **Se ejecuta con `-x`** (parar en el primer fallo): basta un test en rojo para dar el mutante por detectado.

Al cerrar TK-04 se probaron 26 mutantes sobre el repositorio JSON, el arranque, `TripService`, la CLI y la validación común, y los 26 fueron detectados. Es una comprobación de las decisiones que más importan, no una cobertura exhaustiva. Después, con el histórico del día y los logs de operación, se repitió con 41 mutantes más: 39 se detectaron a la primera, y los dos supervivientes llevaron a eliminar código muerto y a cubrir un hueco de pruebas (la escritura dentro de la carpeta de logs). Con los mensajes de error claros se repitió con 14 mutantes más: 13 se detectaron y el superviviente enseñó la lección de la tabla anterior sobre comparar el texto exacto. Al cerrar TK-05 se repitió sobre las piezas nuevas (`Settings`, `DayReport`, `TripStatus`, `check()`, `bootstrap` y `main`): 35 mutantes y los 35 se detectaron.

## 7. Convenciones de los tests

| Convención | Detalle |
|---|---|
| Cabecera | Dos líneas al principio de cada `.py`, comprobadas por `tests/test_conventions.py` |
| Nombres | En español y descriptivos: `test_<comportamiento esperado>` |
| Estructura | Preparar, actuar y comprobar, separados por una línea en blanco |
| Un test, una razón para fallar | Si hay que probar varias entradas, `@pytest.mark.parametrize` con `ids` legibles |
| Errores | `pytest.raises(Tipo, match="…")` con un texto que no pueda coincidir por casualidad |
| Aceptación | Un test `test_usNN_…` por historia de usuario |
| Sin tiempo real ni teclado | Siempre `FakeClock` y `ScriptedInput` |
| Estilo | Líneas de hasta 100 caracteres, comprobado por `ruff` |
