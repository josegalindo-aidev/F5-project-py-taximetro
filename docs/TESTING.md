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
| Unitarias del núcleo | `tests/unit/core/` | `Tariff`, `Trip` y `TripService`, aislados y sin entrada/salida, con repositorios simulados |
| Unitarias de la CLI | `tests/unit/ui/` | `Cli` y `format_euros`, con una consola simulada |
| Integración | `tests/integration/` | La infraestructura y el arranque, con ficheros temporales: cargador de tarifas, comportamiento propio del repositorio JSON (fichero dañado, escritura atómica) y `main` |
| **Aceptación** | `tests/acceptance/` | Cada historia de usuario **de principio a fin** por la consola, con el nombre `test_usNN_…`. Las de la Fase 2 arrancan `main` entero sobre una carpeta de datos temporal (`test_fase2_historial.py`) |
| Contrato | `tests/contract/` | Reglas que debe cumplir **cualquier implementación** de un puerto: el repositorio en memoria y el JSON pasan la misma batería (apartado 5) |
| Convenciones | `tests/test_conventions.py` | Reglas del repositorio, como la cabecera de los `.py` |

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

Cobertura y estilo:

```bash
python -m pytest --cov=src/taximetro --cov-report=term-missing
```

```bash
python -m ruff check src tests
```

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
| `ScriptedInput` | `tests/fakes.py` | Consola que devuelve comandos y avanza el reloj entre ellos |
| `tariff` | `tests/conftest.py` | La tarifa oficial (0,02 y 0,05 €/s), disponible en cualquier test |
| `tmp_path` | `pytest` | Carpeta temporal para los ficheros de prueba: nunca se toca `config/` ni `data/` |
| `monkeypatch` | `pytest` | Cambia una variable de entorno o una función solo durante un test y la restaura al terminar |
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

Cuidado al automatizarlo con scripts: los ficheros del proyecto pueden tener saltos de línea de Windows, y un patrón de varias líneas escrito con `\n` no coincidiría. Se mutan líneas sueltas y se leen y escriben los **bytes**, sin transformarlos.

Un script de mutación fiable cumple estas reglas:

1. **Cada patrón debe aparecer exactamente una vez** en el fichero. Si no, se avisa en lugar de mutar a ciegas.
2. **La restauración se comprueba** con un hash del fichero antes y después de cada mutante, y el script se detiene si no coincide. Al final, `git status` tiene que estar vacío.
3. **El resultado se cuenta, no se estima**: el propio script imprime «N de M detectados» y los supervivientes.
4. **Se ejecuta con `-x`** (parar en el primer fallo): basta un test en rojo para dar el mutante por detectado.

Al cerrar TK-04 se probaron 26 mutantes sobre el repositorio JSON, el arranque, `TripService`, la CLI y la validación común, y los 26 fueron detectados. Es una comprobación de las decisiones que más importan, no una cobertura exhaustiva.

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
