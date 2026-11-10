<!--
Proyecto: py-taximetro
fuente: docs/architecture.md
-->

# Arquitectura del taxímetro digital (TTX-247)

| | |
|---|---|
| **Proyecto** | py-taximetro (prototipo de TaxiTech Solutions S.L.) |
| **Alcance que refleja** | Fase 1 (MVP CLI): US-01 a US-04 y TK-02 |
| **Fuente de verdad** | El código en `src/taximetro/`. Si algo de este documento y el código difieren, manda el código. |

> **Convención de estado.** Cada elemento lleva una marca: ✅ implementado y probado, 🟡 existe pero aún no se usa, ⏳ planificado (no existe todavía).

---

## 1. Propósito y alcance

TaxiTech Solutions necesita sustituir sus taxímetros físicos por una solución 100 % software. Este repositorio es el **prototipo** que valida el concepto antes de contratar a un proveedor.

La Fase 1 entrega un taxímetro funcional por línea de comandos que:

- cobra por segundo según el estado del taxi (parado o en movimiento),
- muestra el importe acumulado y el total final en euros,
- permite encadenar carreras sin cerrar el programa.

Este documento describe **cómo está construido** (módulos), **qué hace** (arquitectura funcional) y **por qué** se diseñó así (decisiones). Las fases 2 a 4 se recogen como evolución prevista en la sección 9.

---

## 2. Visión general

### 2.1 Estilo arquitectónico

**Núcleo puro con puertos y adaptadores (versión ligera).** El cálculo del negocio vive en un núcleo sin entrada/salida ni librerías externas. Todo lo que toca el mundo exterior (teclado, pantalla, reloj, disco) se queda en los bordes y se conecta al núcleo mediante contratos pequeños.

Tres paquetes, un punto de arranque:

| Paquete | Rol | Estado |
|---|---|---|
| `core/` | Reglas de negocio y casos de uso. No importa nada de `ui/` ni de `infra/`. | ✅ |
| `ui/` | Puertas de entrada del usuario: CLI hoy; GUI y API después. | ✅ CLI · ⏳ GUI, API |
| `infra/` | Adaptadores a recursos externos (repositorios de datos, carga de configuración, logging). | ⏳ vacío |
| `__main__.py` | Punto de arranque: crea las piezas reales y las conecta. | ✅ |

**Regla de dependencias (solo hacia dentro):**

```
__main__  →  ui  →  core
              infra  →  core
```

El núcleo no conoce a nadie. Esa regla es la que permite probarlo sin teclado, sin pantalla y sin esperar tiempo real.

### 2.2 Diagrama de componentes

```mermaid
flowchart LR
    MAIN["__main__<br/>arranque"]

    subgraph UI["ui (entradas)"]
        CLI["ui/cli<br/>Cli · format_euros"]
        GUI["ui/gui<br/>planificado"]
        API["ui/api<br/>planificado"]
    end

    subgraph CORE["core (núcleo puro)"]
        SVC["TripService"]
        TRIP["Trip"]
        TAR["Tariff"]
        ST["State"]
        ERR["errors"]
        PORTS["ports<br/>Clock · TripRepository"]
    end

    subgraph INFRA["infra (adaptadores)"]
        REPOS["repos<br/>memoria · JSON · SQL<br/>planificado"]
    end

    MAIN --> CLI
    CLI --> SVC
    SVC --> TRIP
    TRIP --> TAR
    TRIP --> ST
    TAR --> ST
    SVC -. usa .-> PORTS
    REPOS -. implementa .-> PORTS
    GUI -.-> SVC
    API -.-> SVC
```

Las líneas discontinuas con `planificado` aún no existen en el código.

---

## 3. Módulos codificados

### 3.1 Núcleo — `src/taximetro/core/`

| Módulo | Responsabilidad | Depende de | Estado |
|---|---|---|---|
| `state.py` | Enumeración `State` con los estados del taxi: `STOPPED` y `MOVING`. Vive en su propio módulo para evitar una importación circular entre `Tariff` y `Trip`. | — | ✅ |
| `errors.py` | Jerarquía de errores del dominio, con `TaximetroError` como base. | — | ✅ |
| `tariff.py` | `Tariff`: precio por segundo parado y en movimiento. Es inmutable (`frozen`), rechaza valores negativos y expone `rate_for(state)`. Incluye `DEFAULT_TARIFF` (Zona EMT Madrid, junio 2025). | `state`, `errors` | ✅ |
| `trip.py` | `Trip`: una carrera. Acumula el importe por tramos, cierra un tramo en cada cambio de estado y redondea el total a céntimos. **No conoce ningún reloj**: recibe el instante (`at`) en cada operación. | `state`, `tariff`, `errors` | ✅ |
| `trip_service.py` | `TripService`: caso de uso. Mantiene la carrera activa, lee el reloj y delega el cálculo en `Trip`. Al finalizar libera la carrera activa para poder encadenar la siguiente. | `trip`, `tariff`, `ports`, `errors` | ✅ |
| `ports.py` | Contratos (`Protocol`): `Clock` (función que devuelve segundos) y `TripRepository` (`save`, `get`, `list_finished`). | `trip` | `Clock` ✅ · `TripRepository` 🟡 |

**API pública de `Trip`:**

| Elemento | Función |
|---|---|
| `start(at)` | Inicia la carrera en estado parado. |
| `change_state(state, at)` | Cierra el tramo actual y cambia de estado. |
| `amount_at(at)` | Importe acumulado hasta `at`, sin cerrar la carrera. |
| `finish(at)` | Cierra el último tramo y devuelve el total en `Decimal` redondeado a 2 decimales. |
| `state` · `is_finished` | Consulta del estado actual y de si la carrera terminó. |

**API pública de `TripService`:**

| Elemento | Función |
|---|---|
| `start()` | Crea y arranca una carrera nueva con identificador único. |
| `set_state(state)` | Cambia el estado de la carrera activa. |
| `current_amount()` | Importe actual de la carrera activa. |
| `finish()` | Finaliza, devuelve el total y deja el servicio libre. |
| `active` | La carrera activa, o `None`. |

### 3.2 Interfaz de línea de comandos — `src/taximetro/ui/cli/`

| Módulo | Responsabilidad | Estado |
|---|---|---|
| `app.py` | `Cli`: bucle de lectura de comandos. Traduce cada comando a una llamada a `TripService` y los errores de dominio a mensajes legibles. Recibe `input_fn` y `output_fn`, por lo que se puede probar sin teclado ni pantalla. Contiene el texto de ayuda (`HELP`) y la tabla de mensajes de error (`ERRORS`). | ✅ |
| `format.py` | `format_euros`: función pura que formatea un importe como `0,70 €` (coma decimal, dos decimales, redondeo medio hacia arriba). | ✅ |

**Comandos disponibles:**

| Comando | Acción |
|---|---|
| `iniciar` | Inicia una carrera (el taxi empieza parado). |
| `parar` | Pasa al estado parado. |
| `mover` | Pasa al estado en movimiento. |
| `estado` | Muestra el estado y el importe actual. |
| `finalizar` | Termina la carrera y muestra el total. |
| `ayuda` | Repite las instrucciones. |
| `salir` | Cierra el programa (avisa si hay una carrera sin cobrar). |

La entrada no distingue mayúsculas ni espacios sobrantes, e ignora las líneas vacías.

### 3.3 Arranque — `src/taximetro/__main__.py` ✅

Es el único módulo que conoce todas las piezas. Crea `TripService` con `DEFAULT_TARIFF` y `time.monotonic`, y lanza la CLI. Se ejecuta con `python -m taximetro` o con el comando `taximetro` (definido en `pyproject.toml`).

### 3.4 Elementos que existen pero aún no se usan

| Elemento | Situación |
|---|---|
| `infra/`, `infra/repos/`, `ui/gui/`, `ui/api/` | Paquetes vacíos que reservan el sitio de las fases 2 a 4. |
| `config/rates.toml` | Contiene las tarifas oficiales, pero **el código todavía no lo lee**: usa `DEFAULT_TARIFF`. Se conectará con US-07 (Fase 2). |
| `core/ports.py::TripRepository` | Contrato definido; ninguna clase lo implementa ni lo usa todavía. Entra con US-05 y TK-04. |

---

## 4. Arquitectura funcional

### 4.1 Modelo de cálculo

El importe de una carrera es la suma, por tramos, del tiempo transcurrido multiplicado por la tarifa del estado vigente:

```
importe = Σ  (duración del tramo en segundos × precio por segundo del estado)

parado:         0,02 €/s
en movimiento:  0,05 €/s
```

Un tramo termina en cada cambio de estado o al finalizar. Ejemplo (10 s parado, 10 s en movimiento, 10 s parado):

```
10 × 0,02 + 10 × 0,05 + 10 × 0,02  =  0,20 + 0,50 + 0,20  =  0,90 €
```

**Reglas de negocio implementadas:**

1. Toda carrera comienza en estado parado.
2. El cambio de estado cierra el tramo anterior con la tarifa que tenía.
3. El total se redondea a céntimos con redondeo medio hacia arriba (`ROUND_HALF_UP`) **solo al final**.
4. Las tarifas no pueden ser negativas.
5. El tiempo entre carreras no se cobra.
6. Solo hay una carrera activa a la vez.
7. El instante de una operación no puede ser anterior al de la última.

### 4.2 Trazabilidad: historia de usuario → módulos → pruebas

| Historia | Qué cubre | Módulos que intervienen | Prueba de aceptación |
|---|---|---|---|
| **US-01** (#2) | Iniciar una carrera con un comando | `Cli._start`, `TripService.start`, `Trip.start` | `test_us01_iniciar_carrera_con_un_comando` |
| **US-02** (#3) | Cambiar entre parado y en movimiento | `Cli._set_state`, `TripService.set_state`, `Trip.change_state`, `Tariff.rate_for` | `test_us02_cambiar_entre_parado_y_en_movimiento` |
| **US-03** (#4) | Finalizar y ver el total en euros | `Cli._finish`, `TripService.finish`, `Trip.finish`, `format_euros` | `test_us03_finalizar_muestra_el_total_con_dos_decimales` |
| **US-04** (#5) | Encadenar carreras sin cerrar el programa | `TripService.finish` (libera la carrera activa), bucle de `Cli.run` | `test_us04_encadenar_carreras_sin_cerrar_el_programa` |
| **TK-02** (#12) | Instrucciones de uso al arrancar | `HELP` y `Cli.run` | `test_muestra_instrucciones_al_arrancar` |
| — | Consulta del importe en curso (`estado`) | `Cli._status`, `TripService.current_amount`, `Trip.amount_at` | `test_estado_con_carrera_muestra_estado_e_importe` |

### 4.3 Ciclo de vida de una carrera

```mermaid
stateDiagram-v2
    [*] --> SinIniciar
    SinIniciar --> Parado: start
    Parado --> EnMovimiento: change_state MOVING
    EnMovimiento --> Parado: change_state STOPPED
    Parado --> Finalizada: finish
    EnMovimiento --> Finalizada: finish
    Finalizada --> [*]
```

Una carrera finalizada no admite más operaciones. Para iniciar otra, `TripService` crea una `Trip` nueva.

### 4.4 Flujo de una carrera completa

```mermaid
sequenceDiagram
    actor U as Taxista
    participant C as Cli
    participant S as TripService
    participant K as Clock
    participant T as Trip

    U->>C: iniciar
    C->>S: start
    S->>K: lee el reloj
    K-->>S: t0
    S->>T: crea Trip y start en t0
    C-->>U: Carrera iniciada

    U->>C: mover
    C->>S: set_state MOVING
    S->>K: lee el reloj
    K-->>S: t1
    S->>T: change_state MOVING en t1
    Note over T: cierra el tramo parado<br/>(t1 - t0) x tarifa parado

    U->>C: finalizar
    C->>S: finish
    S->>K: lee el reloj
    K-->>S: t2
    S->>T: finish en t2
    T-->>S: total Decimal
    S-->>C: total
    C-->>U: Carrera finalizada. Total: 0,70 €
```

### 4.5 Manejo de errores

Los errores de negocio son excepciones del dominio. `Cli._dispatch` las captura y muestra un mensaje; el programa **no se cierra**.

| Excepción | Cuándo se lanza | Mensaje en la CLI |
|---|---|---|
| `TripNotStarted` | Cambiar estado, consultar o finalizar sin carrera activa | "No hay ninguna carrera en curso. Usa 'iniciar'." |
| `TripAlreadyStarted` | Iniciar con otra carrera ya en curso | "Ya hay una carrera en curso. Usa 'finalizar' antes de iniciar otra." |
| `TripAlreadyFinished` | Operar sobre una `Trip` ya finalizada | "La carrera ya está finalizada." |
| `InvalidTimestamp` | Instante anterior al último registrado | "El reloj retrocedió; no se puede continuar la carrera." |
| `InvalidTariff` | Construir una `Tariff` con valores negativos | No llega a la CLI: se produce al crear la tarifa |

Con `time.monotonic` el reloj no retrocede, y `TripService` descarta la carrera al finalizar, por lo que `InvalidTimestamp` y `TripAlreadyFinished` solo aparecen al usar `Trip` directamente o con un reloj de pruebas.

---

## 5. Decisiones de diseño

| # | Decisión | Motivo |
|---|---|---|
| D1 | **`Trip` no tiene reloj**: recibe `at` en cada operación y es el servicio quien lee el `Clock`. | El cálculo es determinista y se prueba sin esperas ni `sleep`. |
| D2 | **Reloj inyectado** como dependencia (`Clock`): `time.monotonic` en producción y `FakeClock` en pruebas. | Permite simular el paso del tiempo a voluntad. `monotonic` no se ve afectado por cambios en la hora del sistema. |
| D3 | **`Decimal` para el dinero**, nunca `float`. Los segundos se restan a partir de su representación textual. | Evita errores de redondeo binario. El redondeo solo se aplica al final. |
| D4 | **Entrada y salida inyectadas en `Cli`** (`input_fn`, `output_fn`). | La CLI se prueba entera con una consola simulada. |
| D5 | **La carrera activa vive en memoria** dentro de `TripService`. El repositorio se pospone. | En la Fase 1 no hay persistencia (YAGNI). El contrato `TripRepository` queda definido para la Fase 2. |
| D6 | **`State` en su propio módulo.** | Rompe la dependencia circular `Tariff` ↔ `Trip`. `Trip` lo reexporta para no romper importaciones. |
| D7 | **Tarifa por defecto en código** (`DEFAULT_TARIFF`). | Basta para el MVP. Pasa a fichero de configuración en US-07. |
| D8 | **Un único punto de arranque** (`__main__`). | Una interfaz futura (GUI o API) solo necesita su propio arranque y reutiliza el mismo núcleo. |
| D9 | **Sin dependencias externas en ejecución** (`dependencies = []`). Solo la biblioteca estándar. | Mínima superficie; las extras `sql` y `api` se instalan cuando haga falta. |
| D10 | **Solo existen puertos con más de una implementación real** (`Clock`, `TripRepository`). | Evita abstracciones sin uso. Se añade un puerto cuando aparece una segunda implementación. |

---

## 6. Estrategia de pruebas

El proyecto se desarrolla con **TDD**: primero el test en rojo, luego el código mínimo en verde y después el refactor.

| Nivel | Carpeta | Qué prueba | Pruebas |
|---|---|---|---|
| Unitarias del núcleo | `tests/unit/core/` | `Tariff`, `Trip` y `TripService` aislados | 28 |
| Unitarias de la CLI | `tests/unit/ui/` | `Cli` y `format_euros` con consola simulada | 15 |
| Aceptación | `tests/acceptance/` | US-01 a US-04 de principio a fin | 4 |
| Convenciones | `tests/test_conventions.py` | Cabecera de cada `.py` (crece con cada fichero nuevo) | 35 |
| Contrato · integración | `tests/contract/`, `tests/integration/` | ⏳ vacías hasta las fases 2 y 4 | 0 |
| | | **Total** | **82** |

**Dobles de prueba** (`tests/fakes.py`): `FakeClock` (reloj que avanza a mano) y `ScriptedInput` (consola que devuelve comandos y avanza el reloj entre ellos). Los fixtures compartidos están en `tests/conftest.py`.

**Cobertura:** aproximadamente el 94 % al cerrar la Fase 1. El núcleo y la CLI están prácticamente al 100 %; `__main__.py` no tiene prueba automática (se verificó a mano).

---

## 7. Convenciones del repositorio

| Aspecto | Convención |
|---|---|
| Cabecera de cada fichero `.py` | Dos líneas al principio: `# Proyecto: py-taximetro` y `# fuente: <ruta desde la raíz>` (por ejemplo, `src/taximetro/core/trip.py`). Los ficheros vacíos, como los `__init__.py`, no la llevan. La regla se comprueba en `tests/test_conventions.py`. |
| Versión | La versión vive solo en `pyproject.toml`. El criterio de versionado y el estado de las versiones publicadas se documentan únicamente en el [README](../README.md#versionado); no se repiten en ningún otro fichero. |
| Documentación | `README.md` (entrada del repositorio: instalación, arranque y enlaces), `docs/usage.md` (manual de uso) y `docs/architecture.md` (este documento). El README resume y enlaza; el detalle vive en `docs/`. |
| Commits | Conventional Commits (`feat`, `fix`, `test`, `refactor`, `docs`, `chore`) con referencia al issue (`Refs #n`) |
| Ramas y PR | Una rama por funcionalidad; la PR cierra los issues con `Closes #n` |
| Seguimiento | Tablero GitHub Projects «TTX-247 Taxímetro» (campos Fase, Tipo, MoSCoW, Estimate y Status) y backlog en `docs/project_backlog.xlsx` |
| Estilo | `ruff` (líneas de hasta 100 caracteres) |

---

## 8. Ejecución y verificación

Comandos en Git Bash, desde la raíz del proyecto y con el entorno virtual activado:

```bash
python -m taximetro
```

```bash
python -m pytest -v
```

```bash
python -m pytest --cov=src/taximetro --cov-report=term-missing
```

```bash
python -m ruff check src tests
```

---

## 9. Evolución prevista (planificado, aún no codificado)

| Fase | Módulos nuevos o cambios | Issues |
|---|---|---|
| **Fase 2** — Observabilidad y persistencia | `infra/repos/` (memoria y JSON) implementando `TripRepository`; cargador de tarifas desde `config/rates.toml`; logging estructurado; comando de histórico del día | US-05 (#6), US-06 (#7), US-07 (#8), TK-03 (#13), TK-04 (#14) |
| **Fase 3** — Arquitectura y UI | Refuerzo de la POO y de las responsabilidades; acceso con contraseña (hash, sin texto plano); `ui/gui/` en tkinter sin bloquear la ventana | US-08 (#9), US-09 (#10), TK-05 (#15) |
| **Fase 4** — Producción | Repositorio SQL; `ui/api/` (API REST: iniciar, cambiar, finalizar, consultar); panel web para el responsable de flota; despliegue con un único comando (Docker) | TK-06 (#16), TK-07 (#17), TK-08 (#18), TK-09 (#19) |
| **Transversal** | README con instrucciones y justificación de librerías; tablero y Conventional Commits | TK-10 (#20), TK-11 (#21) |

**Impacto previsto en la arquitectura:** la API (Fase 4) no tiene estado entre peticiones, así que la carrera activa deberá guardarse en el repositorio con `save` (D5 se revisará entonces). El diseño actual ya lo permite porque `TripRepository.save` está pensado para carreras en curso y terminadas.

---

## 10. Limitaciones conocidas y deuda técnica

| # | Limitación | Plan |
|---|---|---|
| L1 | **Regla de 20 km/h.** El enunciado cobra la tarifa baja por debajo de 20 km/h, pero el modelo solo distingue parado y en movimiento, sin velocidad. | Valorar un estado derivado de la velocidad si el enunciado lo exige. |
| L2 | Las tarifas están en código; `config/rates.toml` no se lee. | US-07 (Fase 2). |
| L3 | **No hay persistencia**: al cerrar el programa se pierde todo y una carrera sin finalizar no se cobra. | US-05, TK-04 (Fase 2). |
| L4 | Una sola carrera activa a la vez: un taxi, un taxímetro. No hay soporte multi-taxi. | Fuera del alcance del prototipo. |
| L5 | `__main__.py` no tiene prueba automática. | Test de humo o de integración en la Fase 2. |
| L6 | `TripRepository` está definido pero sin implementar ni usar. | Fase 2. |
| L7 | El módulo `taximetro.core.ports` importa `Trip`, lo que acopla el contrato al modelo. Es aceptable mientras `Trip` sea el único agregado. | Revisar si el modelo crece. |

