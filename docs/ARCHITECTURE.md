<!--
Proyecto: py-taximetro
fuente: docs/ARCHITECTURE.md
-->

# Arquitectura del taxímetro digital (TTX-247)

| | |
|---|---|
| **Proyecto** | py-taximetro (prototipo de TaxiTech Solutions S.L.) |
| **Alcance que refleja** | Fase 1 (MVP CLI): US-01 a US-04 y TK-02, más de la Fase 2: US-07 (tarifas en fichero de configuración), TK-04 (historial de carreras en disco), US-05 (histórico del día) y US-06 (logs de operación) y TK-03 (umbral de cobertura del núcleo) |
| **Fuente de verdad** | El código en `src/taximetro/`. Si algo de este documento y el código difieren, manda el código. |

> **Convención de estado.** Cada elemento lleva una marca: ✅ implementado y probado, 🟡 existe pero aún no se usa, ⏳ planificado (no existe todavía).

---

## 1. Propósito y alcance

TaxiTech Solutions necesita sustituir sus taxímetros físicos por una solución 100 % software. Este repositorio es el **prototipo** que valida el concepto antes de contratar a un proveedor.

El taxímetro funciona por línea de comandos (Fase 1, más US-07 y TK-04 de la Fase 2) y:

- cobra por segundo según el estado del taxi (parado o en movimiento),
- muestra el importe acumulado y el total final en euros,
- permite encadenar carreras sin cerrar el programa,
- lee sus tarifas de un fichero de configuración, de modo que cambiar el cobro no exige tocar el código (US-07),
- guarda cada carrera finalizada en un historial en disco que se conserva al cerrar el programa, sin que un fallo del historial esconda nunca el importe (TK-04),
- permite consultar las carreras de hoy o de otro día, con su hora, su importe y el total (US-05),
- registra el inicio, los cambios de estado y el fin de cada carrera en un log de operación para auditar el uso, sin que un fallo del log impida cobrar (US-06).

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
| `infra/` | Adaptadores a recursos externos (carga de configuración, repositorios de datos, logging). | ✅ carga de tarifas, repositorios (memoria y JSON) y registro de eventos · ⏳ repositorio SQL |
| `__main__.py` | Punto de arranque: crea las piezas reales y las conecta. | ✅ |

**Regla de dependencias (solo hacia dentro):**

```
__main__  →  ui     →  core
          →  infra  →  core
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
        PORTS["ports<br/>Clock · WallClock · TripRepository · EventLog"]
    end

    subgraph INFRA["infra (adaptadores)"]
        LOADER["tariff_loader<br/>load_tariff"]
        REPOS["repos<br/>memoria · JSON<br/>SQL planificado"]
        EVLOG["event_log<br/>FileEventLog"]
    end

    MAIN --> CLI
    MAIN --> LOADER
    MAIN --> REPOS
    MAIN --> EVLOG
    LOADER --> TAR
    CLI --> SVC
    SVC --> TRIP
    TRIP --> TAR
    TRIP --> ST
    TAR --> ST
    SVC -. usa .-> PORTS
    REPOS -. implementa .-> PORTS
    EVLOG -. implementa .-> PORTS
    GUI -.-> SVC
    API -.-> SVC
```

Los bloques marcados como `planificado` (GUI, API y el repositorio SQL) aún no existen en el código. Las líneas discontinuas indican «usa» o «implementa» un contrato.

---

## 3. Módulos codificados

### 3.1 Núcleo — `src/taximetro/core/`

| Módulo | Responsabilidad | Depende de | Estado |
|---|---|---|---|
| `state.py` | Enumeración `State` con los estados del taxi: `STOPPED` y `MOVING`. Vive en su propio módulo para evitar una importación circular entre `Tariff` y `Trip`. | — | ✅ |
| `errors.py` | Jerarquía de errores del dominio, con `TaximetroError` como base. Incluye `TariffFileError` (fallos al cargar las tarifas) y, para el historial: `InvalidTripRecord` (carrera que no se puede guardar: sin terminar o sin fechas), `TripHistoryError` (fichero dañado o ilegible) `TripNotSaved` (la carrera se cobró pero no se guardó; lleva el total) y `EventLogError` (la carpeta del registro de eventos no se puede usar). | — | ✅ |
| `tariff.py` | `Tariff`: precio por segundo parado y en movimiento. Es inmutable (`frozen`), rechaza valores negativos y expone `rate_for(state)`. Los valores reales los aporta el cargador de tarifas (`infra/`). | `state`, `errors` | ✅ |
| `trip.py` | `Trip`: una carrera. Acumula el importe por tramos, cierra un tramo en cada cambio de estado y redondea el total a céntimos. **No conoce ningún reloj**: recibe el instante (`at`) en cada operación y, opcionalmente, la fecha y hora de pared (`when`). Acumula también los segundos parado y en movimiento, y expone `started_at` y `finished_at`. `Trip.restore(...)` reconstruye una carrera ya terminada a partir de los datos guardados. | `state`, `tariff`, `errors` | ✅ |
| `trip_service.py` | `TripService`: caso de uso. Mantiene la carrera activa, lee los dos relojes y delega el cálculo en `Trip`. Al finalizar guarda la carrera en el repositorio y libera la carrera activa para encadenar la siguiente, **incluso si el guardado falla** (en ese caso lanza `TripNotSaved` con el total). Anota en el registro de eventos el inicio, los cambios de estado, el fin y las carreras no guardadas; si el registro falla, lo ignora (`_log`). | `trip`, `tariff`, `ports`, `errors` | ✅ |
| `ports.py` | Contratos (`Protocol`): `Clock` (segundos monotónicos, para medir duraciones), `WallClock` (fecha y hora con zona horaria, para saber *cuándo*), `TripRepository` (`save` y `list_finished`) y `EventLog` (`record`: anota un evento con su hora). | `trip` | ✅ |

**API pública de `Trip`:**

| Elemento | Función |
|---|---|
| `start(at, when=None)` | Inicia la carrera en estado parado. `when` es la fecha y hora de pared de inicio. |
| `change_state(state, at)` | Cierra el tramo actual y cambia de estado. |
| `amount_at(at)` | Importe acumulado hasta `at`, sin cerrar la carrera. |
| `finish(at, when=None)` | Cierra el último tramo y devuelve el total en `Decimal` redondeado a 2 decimales. `when` es la fecha y hora de pared de fin. |
| `state` · `is_finished` | Consulta del estado actual y de si la carrera terminó. |
| `stopped_seconds` · `moving_seconds` | Segundos acumulados en cada estado. |
| `started_at` · `finished_at` | Fecha y hora de pared de inicio y fin, o `None` si no se indicaron. |
| `Trip.restore(...)` | Reconstruye una carrera terminada a partir de datos guardados (sin tarifa: ya no se recalcula). |

**API pública de `TripService`:**

| Elemento | Función |
|---|---|
| `start()` | Crea y arranca una carrera nueva con identificador único. |
| `set_state(state)` | Cambia el estado de la carrera activa. |
| `current_amount()` | Importe actual de la carrera activa. |
| `finish()` | Finaliza, guarda la carrera en el historial, devuelve el total y deja el servicio libre. Si el guardado falla, lanza `TripNotSaved` con el total. |
| `today()` | El día actual según el reloj de pared. |
| `finished_on(day=None)` | Las carreras terminadas ese día, de la más antigua a la más reciente; sin día, las de hoy. Delega en `TripRepository.list_finished`. |
| `active` | La carrera activa, o `None`. |

### 3.2 Interfaz de línea de comandos — `src/taximetro/ui/cli/`

| Módulo | Responsabilidad | Estado |
|---|---|---|
| `app.py` | `Cli`: bucle de lectura de comandos. Traduce cada comando a una llamada a `TripService` y los errores de dominio a mensajes legibles. Recibe `input_fn` y `output_fn`, por lo que se puede probar sin teclado ni pantalla. Contiene el texto de ayuda (`HELP`) y la tabla de mensajes de error (`ERRORS`). Al arrancar imprime las **notas** que recibe (por ejemplo, la ruta del historial) entre el título y la ayuda, sin saber de dónde vienen; y si el guardado falla al finalizar, muestra el total seguido de un `Aviso:`. | ✅ |
| `format.py` | `format_euros`: función pura que formatea un importe como `0,70 €` (coma decimal, dos decimales, redondeo medio hacia arriba). | ✅ |

**Comandos disponibles:**

| Comando | Acción |
|---|---|
| `iniciar` | Inicia una carrera (el taxi empieza parado). |
| `parar` | Pasa al estado parado. |
| `mover` | Pasa al estado en movimiento. |
| `estado` | Muestra el estado y el importe actual. |
| `finalizar` | Termina la carrera y muestra el total. |
| `historico [AAAA-MM-DD]` | Lista las carreras finalizadas de hoy o del día indicado, con su hora, su importe y el total. |
| `ayuda` | Repite las instrucciones. |
| `salir` | Cierra el programa (avisa si hay una carrera sin cobrar). |

La entrada no distingue mayúsculas ni espacios sobrantes, e ignora las líneas vacías. `historico` es el único comando con argumento: `Cli._dispatch` separa la línea en nombre y argumento solo para él, y los demás siguen buscándose por línea completa (`iniciar hola` es un comando desconocido). Una fecha que no es `AAAA-MM-DD` muestra `Fecha no válida…` y el programa sigue.

### 3.3 Infraestructura — `src/taximetro/infra/`

| Módulo | Responsabilidad | Estado |
|---|---|---|
| `tariff_loader.py` | `load_tariff(path)`: lee un fichero TOML y devuelve un `Tariff`. Convierte **todos** los fallos posibles en un único `TariffFileError`, con la clave o el fichero implicado, y conserva el error original como causa. | ✅ |
| `repos/memory.py` | `InMemoryTripRepository`: guarda las carreras en una lista; se pierden al cerrar el programa. Lo usan las pruebas. | ✅ |
| `repos/json_file.py` | `JsonTripRepository(path)`: guarda las carreras terminadas en un fichero JSON. Escritura atómica, errores claros y creación de carpetas (ver abajo). | ✅ |
| `repos/validation.py` | `ensure_can_be_saved`: reglas comunes a todo repositorio (la carrera debe estar terminada y tener fechas). | ✅ |
| `folders.py` | `file_in_the_way(carpeta)`: devuelve el fichero que impide usar una ruta como carpeta (la propia ruta o la primera que exista por encima), o `None`. La comparten el repositorio JSON y el registro de eventos; cada uno pone su propio mensaje. | ✅ |
| `repos/` (SQL) | Repositorio relacional (Fase 4). | ⏳ |
| `event_log.py` | `FileEventLog(carpeta)`: escribe cada evento como una línea JSON en el fichero del día. `check()` crea la carpeta, prueba que se puede escribir y convierte los fallos en `EventLogError` (ver abajo). | ✅ |

El cargador se organiza en una función pública y cuatro privadas, cada una con una sola responsabilidad:

| Función | Responsabilidad |
|---|---|
| `load_tariff` | Orquesta: leer, localizar la tabla, extraer las claves y convertir |
| `_read_toml` | Abrir y decodificar el fichero (ausente, ilegible, codificación, sintaxis) |
| `_rates_table` | Localizar la tabla `[rates]` y comprobar que lo es |
| `_required_values` | Extraer las claves `stopped` y `moving` |
| `_to_decimal` | Validar y convertir un valor: texto, número, finito y no negativo |

El formato del fichero y los mensajes de error están en el [manual de uso](USAGE.md#7-configurar-las-tarifas).

#### Repositorio JSON

El fichero es una lista de registros, uno por carrera terminada:

```json
[
  {
    "id": "…",
    "started_at": "2026-11-11T10:00:00+01:00",
    "finished_at": "2026-11-11T10:05:00+01:00",
    "stopped_seconds": "30",
    "moving_seconds": "20",
    "total": "1.00"
  }
]
```

Las fechas se guardan en ISO 8601 con zona horaria y los importes y segundos **como texto**, para que `Decimal` no pase por `float` y no pierda precisión.

| Comportamiento | Cómo |
|---|---|
| **Escritura atómica** | `save` escribe en un fichero temporal en la misma carpeta y lo intercambia con `os.replace`. Un corte a mitad de escritura deja el historial anterior intacto; si algo falla, se borra el temporal |
| **Historial dañado** | Un fichero vacío, que no es JSON, que no es una lista o con un registro ilegible lanza `TripHistoryError` con la ruta y un motivo legible: la línea y la columna donde falla el JSON, que no está en UTF-8 o el número de la carrera ilegible, sin textos técnicos del intérprete. `save` valida **antes** de escribir, así que un fichero dañado nunca se sobrescribe |
| **Historial ilegible** | Un fichero que existe pero no se puede leer (permisos, es una carpeta) también lanza `TripHistoryError` |
| **Carpeta de datos inválida** | Si la carpeta de datos, o la primera que exista por encima, es un fichero, lanza `TripHistoryError` nombrándola. Un primer arranque, con las carpetas aún sin crear, sigue siendo válido |
| **Primer arranque** | Si el fichero no existe, el historial está vacío. Listar nunca crea nada; guardar crea las carpetas que falten |
| **Qué carreras lista** | `list_finished(día)` devuelve las que **terminan** ese día, de la más antigua a la más reciente por hora de fin |

El repositorio en memoria y el JSON pasan la misma batería de tests de contrato (`tests/contract/`).
#### Registro de eventos

`TripService` anota los eventos de operación en un `EventLog`. La implementación real, `FileEventLog`, escribe **JSON Lines**: una línea por evento, en un fichero por día (`taximetro-AAAA-MM-DD.jsonl`) dentro de la carpeta de logs.

```json
{"ts": "2026-11-16T10:05:00.123456+01:00", "evento": "carrera_iniciada", "carrera": "a1b2c3d4"}
```

| Evento | Quién lo registra | Datos |
|---|---|---|
| `carrera_iniciada` | `TripService.start` | `carrera` |
| `estado_cambiado` | `TripService.set_state` | `carrera`, `estado` (valor interno: `stopped` o `moving`) |
| `carrera_finalizada` | `TripService.finish`, antes de guardar | `carrera`, `total` (texto) |
| `carrera_no_guardada` | `TripService.finish`, si falla el historial | `carrera`, `motivo` |

| Comportamiento | Cómo |
|---|---|
| **Hora determinista** | La marca de tiempo es la del reloj de pared inyectado, no la del sistema. `start` y `finish` leen el reloj **una sola vez**, así que el log y el historial coinciden |
| **Un fichero por día** | El nombre sale de la fecha del evento, y cada evento se añade abriendo el fichero en modo *append*: una caída no deja eventos sin volcar y nada se pisa |
| **Acentos legibles** | `ensure_ascii=False`: la `ñ` y las tildes se escriben tal cual |
| **Comprobación al arrancar** | `check()` crea la carpeta, prueba a escribir con un fichero temporal dentro de ella y lanza `EventLogError` con la ruta y el motivo. Como el log sirve para auditar, `main` **aborta** (código 1) si falla |
| **Fallo durante la jornada** | `TripService._log` ignora los `OSError` del registro: cobrar es lo primero, y el taxista nunca ve un error por culpa del log |

### 3.4 Arranque — `src/taximetro/__main__.py` ✅

Es el único módulo que conoce todas las piezas (*composition root*). Se ejecuta con `python -m taximetro` o con el comando `taximetro` (definido en `pyproject.toml`).

| Elemento | Función |
|---|---|
| `default_rates_path(environ)` | Decide de dónde se leen las tarifas: la variable `TAXIMETRO_RATES` (una variable vacía se ignora) o, si no existe, `config/rates.toml` en la raíz del proyecto. |
| `default_data_dir(environ)` | Decide la carpeta de datos: la variable `TAXIMETRO_DATA_DIR` (vacía se ignora) o, si no existe, `data/` en la raíz del proyecto. El historial es `trips.json` dentro de esa carpeta. |
| `default_log_dir(environ)` | Decide la carpeta de logs: la variable `TAXIMETRO_LOG_DIR` (vacía se ignora) o, si no existe, `logs/` en la raíz del proyecto. Es independiente de la carpeta de datos. |
| `build_service(rates_path, repository, event_log, clock, wall_clock)` | Carga las tarifas y crea el `TripService` con el repositorio y el registro de eventos que se le dan. Es donde se unen la infraestructura y el núcleo. |
| `main(rates_path, data_dir, clock, input_fn, output_fn)` | Elige las rutas, crea el repositorio JSON, construye el servicio, **lee el historial una vez** para detectar un fichero dañado, **comprueba la carpeta de logs** y lanza la CLI con las notas `Historial: <ruta>` y `Logs: <ruta>`. Devuelve el **código de salida**: `0` si todo va bien y `1` si el fichero de tarifas o el historial son inválidos, con el mensaje `Error: …` en `stderr`. Captura `TariffFileError`, `TripHistoryError` y `EventLogError`. |

Reloj, entrada y salida se inyectan, por lo que el arranque completo se prueba sin teclado ni esperas.

#### Ubicaciones de datos

| Qué | Variable | Por defecto | Estado |
|---|---|---|---|
| Tarifas (un fichero, solo lectura) | `TAXIMETRO_RATES` | `config/rates.toml` | ✅ |
| Historial (`trips.json`) | `TAXIMETRO_DATA_DIR` | `data/` | ✅ |
| Logs de operación | `TAXIMETRO_LOG_DIR` | `logs/` | ✅ |

Los datos y los logs son **dos carpetas independientes** para poder montarlas en ubicaciones distintas en producción. Se configuran como carpetas y no como ficheros porque la escritura atómica necesita crear un temporal junto al fichero final, y montar un único fichero lo impediría (decisión D18).

### 3.5 Elementos que existen pero aún no se usan

| Elemento | Situación |
|---|---|
| `ui/gui/`, `ui/api/` | Paquetes vacíos que reservan el sitio de las fases 3 y 4. |

---

## 4. Arquitectura funcional

### 4.1 Modelo de cálculo

El importe de una carrera es la suma, por tramos, del tiempo transcurrido multiplicado por la tarifa del estado vigente:

```
importe = Σ  (duración del tramo en segundos × precio por segundo del estado)

parado:         0,02 €/s     (valores de config/rates.toml)
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
4. Las tarifas son números finitos y no negativos.
5. El tiempo entre carreras no se cobra.
6. Solo hay una carrera activa a la vez.
7. El instante de una operación no puede ser anterior al de la última.
8. Las tarifas se leen del fichero de configuración al arrancar y no cambian durante la ejecución.
9. Cada carrera finalizada se guarda en el historial con su fecha de inicio y fin, los segundos en cada estado y el total.
10. **Un fallo del historial nunca esconde el importe**: si no se puede guardar, el total se muestra igualmente con un aviso y la carrera queda cerrada.
11. Un historial dañado o ilegible impide arrancar y **no se sobrescribe**.

### 4.2 Trazabilidad: historia de usuario → módulos → pruebas

| Historia | Qué cubre | Módulos que intervienen | Prueba de aceptación |
|---|---|---|---|
| **US-01** (#2) | Iniciar una carrera con un comando | `Cli._start`, `TripService.start`, `Trip.start` | `test_us01_iniciar_carrera_con_un_comando` |
| **US-02** (#3) | Cambiar entre parado y en movimiento | `Cli._set_state`, `TripService.set_state`, `Trip.change_state`, `Tariff.rate_for` | `test_us02_cambiar_entre_parado_y_en_movimiento` |
| **US-03** (#4) | Finalizar y ver el total en euros | `Cli._finish`, `TripService.finish`, `Trip.finish`, `format_euros` | `test_us03_finalizar_muestra_el_total_con_dos_decimales` |
| **US-04** (#5) | Encadenar carreras sin cerrar el programa | `TripService.finish` (libera la carrera activa), bucle de `Cli.run` | `test_us04_encadenar_carreras_sin_cerrar_el_programa` |
| **TK-02** (#12) | Instrucciones de uso al arrancar | `HELP` y `Cli.run` | `test_muestra_instrucciones_al_arrancar` |
| **US-07** (#8) | Tarifas en fichero de configuración | `load_tariff`, `default_rates_path`, `build_service`, `main` | `test_el_servicio_cobra_con_las_tarifas_del_fichero` y `test_con_un_fichero_valido_lanza_la_cli_con_esas_tarifas_y_devuelve_0` |
| **TK-04** (#14) | Historial guardado en disco | `JsonTripRepository`, `ensure_can_be_saved`, `TripService.finish`, `Trip.restore`, `default_data_dir`, `main` | `test_las_carreras_terminadas_se_conservan_al_reiniciar_el_programa` y el resto de `test_fase2_historial.py` |
| **US-05** (#6) | Ver el histórico del día (o de otro día) | `Cli._history`, `Cli._dispatch`, `TripService.finished_on` y `today`, `TripRepository.list_finished` | `test_us05_el_historico_del_dia_conserva_las_carreras_al_reiniciar` y el resto de `test_us05_historico.py` |
| **US-06** (#7) | Logs de operación | `EventLog`, `FileEventLog`, `TripService._log`, `default_log_dir`, `main` | `test_us06_una_carrera_deja_inicio_cambio_de_estado_y_fin_con_marca_de_tiempo` y el resto de `test_us06_logs.py` |
| **TK-03** (#13) | Tests automatizados de la lógica de cálculo (cobertura ≥ 90 % en `core/`) | `[tool.coverage]` de `pyproject.toml` | `tests/test_quality_gates.py` y `python -m pytest --cov` |
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
    participant R as TripRepository
    participant E as EventLog

    U->>C: iniciar
    C->>S: start
    S->>K: lee el reloj
    K-->>S: t0
    S->>T: crea Trip y start en t0
    S->>E: carrera_iniciada
    C-->>U: Carrera iniciada

    U->>C: mover
    C->>S: set_state MOVING
    S->>K: lee el reloj
    K-->>S: t1
    S->>T: change_state MOVING en t1
    S->>E: estado_cambiado
    Note over T: cierra el tramo parado<br/>(t1 - t0) x tarifa parado

    U->>C: finalizar
    C->>S: finish
    S->>K: lee el reloj
    K-->>S: t2
    S->>T: finish en t2
    T-->>S: total Decimal
    S->>E: carrera_finalizada
    S->>R: save de la carrera
    S-->>C: total
    C-->>U: Carrera finalizada. Total: 0,70 €
```

### 4.5 Arranque: tarifas, historial y logs

```mermaid
flowchart TD
    A["main"] --> B["default_rates_path<br/>TAXIMETRO_RATES o config/rates.toml"]
    A --> G["default_data_dir<br/>TAXIMETRO_DATA_DIR o data/"]
    G --> H["JsonTripRepository<br/>trips.json"]
    B --> C["build_service"]
    H --> C
    A --> L["default_log_dir<br/>TAXIMETRO_LOG_DIR o logs/"]
    L --> M["FileEventLog"]
    M --> C
    C --> D["load_tariff<br/>leer y validar el TOML"]
    D -->|válido| I["leer el historial una vez"]
    I -->|legible| J["comprobar la carpeta de logs"]
    J -->|usable| E["Tariff, TripService y Cli<br/>con las notas Historial y Logs"]
    J -->|EventLogError| F
    D -->|TariffFileError| F["Error por stderr<br/>código de salida 1"]
    I -->|TripHistoryError| F
```

Si el fichero de tarifas, el historial o la carpeta de logs son inválidos el programa **no arranca**: no existe ninguna tarifa por defecto (decisión D11), un historial dañado no se sobrescribe (decisión D17) y sin logs no hay auditoría (decisión D22).

### 4.6 Manejo de errores

Los errores de negocio son excepciones del dominio. `Cli._dispatch` las captura y muestra un mensaje; el programa **no se cierra**.

| Excepción | Cuándo se lanza | Mensaje en la CLI |
|---|---|---|
| `TripNotStarted` | Cambiar estado, consultar o finalizar sin carrera activa | "No hay ninguna carrera en curso. Usa 'iniciar'." |
| `TripAlreadyStarted` | Iniciar con otra carrera ya en curso | "Ya hay una carrera en curso. Usa 'finalizar' antes de iniciar otra." |
| `TripAlreadyFinished` | Operar sobre una `Trip` ya finalizada | "La carrera ya está finalizada." |
| `InvalidTimestamp` | Instante anterior al último registrado | "El reloj retrocedió; no se puede continuar la carrera." |
| `InvalidTariff` | Construir una `Tariff` con valores negativos | No llega a la CLI: el cargador valida antes los valores del fichero |
| `TariffFileError` | El fichero de tarifas falta, no se puede leer, está mal formado o tiene valores inválidos | No llega a la CLI: al arrancar se imprime `Error: …` por `stderr` y el código de salida es 1 |
| `TripHistoryError` | El historial está dañado (no es JSON, no es una lista, un registro ilegible), existe pero no se puede leer, o la carpeta de datos es en realidad un fichero | **Al arrancar**: `Error: …` por `stderr` y código de salida 1. **Al finalizar una carrera**: `TripService` lo convierte en `TripNotSaved` |
| `TripNotSaved` | La carrera se cobró, pero no se pudo guardar (`OSError` o `TripHistoryError`) | La CLI muestra `Carrera finalizada. Total: …` y después `Aviso: No se pudo guardar la carrera en el historial: …` |
| `EventLogError` | La carpeta de logs no se puede crear o no se puede escribir en ella | **Al arrancar**: `Error: …` por `stderr` y código de salida 1. **Durante la jornada**, un fallo de escritura del registro se ignora (`TripService._log`) y no llega a la CLI |
| `InvalidTripRecord` | Intentar guardar una carrera sin terminar o sin fechas: un error de programación | **No** se convierte en `TripNotSaved`, para no disfrazarlo de problema del disco |

Con `time.monotonic` el reloj no retrocede, y `TripService` descarta la carrera al finalizar, por lo que `InvalidTimestamp` y `TripAlreadyFinished` solo aparecen al usar `Trip` directamente o con un reloj de pruebas.

---

## 5. Decisiones de diseño

| # | Decisión | Motivo |
|---|---|---|
| D1 | **`Trip` no tiene reloj**: recibe `at` en cada operación y es el servicio quien lee el `Clock`. | El cálculo es determinista y se prueba sin esperas ni `sleep`. |
| D2 | **Reloj inyectado** como dependencia (`Clock`): `time.monotonic` en producción y `FakeClock` en pruebas. | Permite simular el paso del tiempo a voluntad. `monotonic` no se ve afectado por cambios en la hora del sistema. |
| D3 | **`Decimal` para el dinero**, nunca `float`. Los segundos se restan a partir de su representación textual. | Evita errores de redondeo binario. El redondeo solo se aplica al final. |
| D4 | **Entrada y salida inyectadas en `Cli`** (`input_fn`, `output_fn`). | La CLI se prueba entera con una consola simulada. |
| D5 | **La carrera activa vive en memoria** dentro de `TripService`; solo se guarda al terminar. | Una carrera en curso no tiene total ni fecha de fin. Guardar la carrera en curso se revisará con la API de la Fase 4. |
| D6 | **`State` en su propio módulo.** | Rompe la dependencia circular `Tariff` ↔ `Trip`. `Trip` lo reexporta para no romper importaciones. |
| D7 | **Las tarifas viven en `config/rates.toml`**, con los valores como **texto** (`"0.02"`). | Cambiar el cobro no exige tocar el código. Como texto, el valor es un `Decimal` exacto; un número sin comillas es un `float` binario con error de redondeo, y se rechaza. |
| D8 | **Un único punto de arranque** (`__main__`). | Una interfaz futura (GUI o API) solo necesita su propio arranque y reutiliza el mismo núcleo. |
| D9 | **Sin dependencias externas en ejecución** (`dependencies = []`). Solo la biblioteca estándar. | Mínima superficie; las extras `sql` y `api` se instalan cuando haga falta. |
| D10 | **Solo existen puertos con más de una implementación real** (`Clock`, `TripRepository`). | Evita abstracciones sin uso. Se añade un puerto cuando aparece una segunda implementación. |
| D11 | **Un fichero de tarifas inválido impide arrancar**; no hay tarifa por defecto. | Cobrar con una tarifa equivocada es peor que no cobrar. El error sale por `stderr` y el código de salida es 1. |
| D12 | **`main` devuelve el código de salida** y recibe ruta, reloj y consola inyectables. | El arranque completo se prueba sin teclado ni esperas; el bloque `if __name__ == "__main__"` lo traduce en `SystemExit`. |
| D13 | **El cargador convierte todo fallo en `TariffFileError`** y conserva el error original (`from error`). | Quien lo llama gestiona un solo tipo de error y no pierde la información técnica. Se comprobó con una batería de entradas anómalas. |
| D14 | **Dos relojes**: `Clock` (monotónico, mide duraciones y se usa para cobrar) y `WallClock` (fecha y hora con zona, dice *cuándo*). `Trip` no lee ninguno. | El cobro no se altera si cambia la hora del sistema, y el historial puede decir cuándo ocurrió cada carrera. |
| D15 | **Historial en JSON** con fechas ISO 8601 con zona e importes como texto. | Legible y editable a mano, sin dependencias externas, sin perder precisión de `Decimal`. |
| D16 | **Escritura atómica**: temporal junto al fichero y `os.replace`. | Un corte a mitad de escritura no destruye el historial anterior. |
| D17 | **Un historial dañado o ilegible impide arrancar y nunca se sobrescribe**; un fallo al guardar nunca esconde el total (`TripNotSaved`). | Perder datos es peor que no arrancar, y el taxista debe poder cobrar siempre. |
| D18 | **Datos y logs en carpetas independientes**, configuradas como **directorios** (`TAXIMETRO_DATA_DIR`, `TAXIMETRO_LOG_DIR`), no como ficheros. | Se pueden montar en ubicaciones distintas en producción, y la escritura atómica necesita crear un temporal junto al fichero final. |
| D19 | **Contrato común** para los repositorios y la validación de guardado en un único sitio (`ensure_can_be_saved`). | Una implementación nueva solo se añade a la fixture parametrizada; las reglas no se duplican. |
| D20 | **El registro de eventos es un puerto propio (`EventLog`)**, con la hora del reloj de pared inyectado, y no el módulo `logging` de Python. | La marca de tiempo es determinista en las pruebas, no hay configuración global compartida y se prueba con el mismo estilo que el resto (doble de pruebas, mutación). |
| D21 | **Formato JSON Lines, un fichero por día**; nombres de evento en español y estado con el valor interno (`stopped`, `moving`). | Una línea por evento se lee y se filtra con herramientas, no se corrompe si el programa se corta, y el formato de datos no depende del idioma de la consola. |
| D22 | **Un fallo del registro nunca impide cobrar, pero una carpeta de logs inservible impide arrancar.** | Cobrar es lo primero durante la jornada; pero los logs existen para auditar, y arrancar sin poder auditar vaciaría su propósito. |
| D23 | **La cobertura del núcleo tiene un umbral del 90 %**, con ramas, configurado en `pyproject.toml`, y un test impide relajarlo. | El criterio de TK-03 se cumple hoy con un 100 %, pero solo un umbral que falla evita que baje sin que nadie lo note, y el núcleo es donde está el negocio. |
| D24 | **Los mensajes de error se redactan para quien no conoce Python**: nombran la ruta y dicen dónde mirar (línea y columna, número de carrera, qué fichero estorba), sin el texto de la excepción. | Los errores salen por pantalla al arrancar, donde los lee un responsable y no un programador; para depurar queda el error original encadenado (`from error`). |

---

## 6. Estrategia de pruebas

El proyecto se desarrolla con **TDD**: primero el test en rojo, luego el código mínimo en verde y después el refactor. La guía práctica (cómo ejecutarlas, dobles de prueba, contratos y mutaciones) está en [TESTING.md](TESTING.md).

| Nivel | Carpeta | Qué prueba | Pruebas |
|---|---|---|---|
| Unitarias del núcleo | `tests/unit/core/` | `Tariff`, `Trip` y `TripService` aislados | 51 |
| Unitarias de la CLI | `tests/unit/ui/` | `Cli` y `format_euros` con consola simulada | 30 |
| Aceptación | `tests/acceptance/` | US-01 a US-04 (4), el historial en disco, TK-04 (3), el histórico del día, US-05 (4), y los logs, US-06 (4), de principio a fin | 15 |
| Convenciones | `tests/test_conventions.py` | Cabecera de cada `.py` (crece con cada fichero nuevo) | 67 |
| Calidad | `tests/test_quality_gates.py` | Umbral de cobertura del núcleo en `pyproject.toml` (TK-03) | 3 |
| Integración | `tests/integration/` | Cargador de tarifas (30), repositorio JSON (28), registro de eventos (9) y arranque (25), con ficheros temporales | 92 |
| Contrato | `tests/contract/` | La misma batería de 9 tests para el repositorio en memoria y el JSON | 18 |
| | | **Total** | **276** |

**Dobles de prueba** (`tests/fakes.py`): `FakeClock` (reloj que avanza a mano), `FakeWallClock` (reloj de pared controlable), `FakeEventLog` (registro de eventos en memoria), `FailingEventLog` (registro cuya escritura siempre falla), `BrokenRepository` (guardado que siempre falla), `UnreadableHistoryRepository` (consultar el historial siempre falla) y `ScriptedInput` (consola que devuelve comandos y avanza el reloj entre ellos). Los fixtures compartidos están en `tests/conftest.py`.

**Cobertura:** 99 % al cerrar US-06. Todos los módulos están al 100 % salvo `__main__.py`, cuya única línea sin cubrir es la llamada `raise SystemExit(main())` del bloque `if __name__ == "__main__"`. El **núcleo** (`core/`) está al **100 %** en líneas y ramas, y `pyproject.toml` exige un mínimo del **90 %**: `python -m pytest --cov` falla si baja (decisión D23).

**Pruebas de mutación manuales:** el cargador y el arranque se comprobaron rompiendo el código a propósito (quitar una validación, cambiar un mensaje, alterar el orden de los `except`…). Los tests detectaron todas las roturas deliberadas que se probaron al cerrar US-07. Al cerrar TK-04 se repitió sobre el repositorio JSON, el arranque, `TripService`, la CLI y la validación común: 26 mutantes, 26 detectados. Al cerrar US-05 y US-06 se repitió con el histórico y el registro de eventos: de 41 mutantes, 39 se detectaron a la primera y los dos supervivientes llevaron a eliminar código muerto y a cubrir un hueco de pruebas. Con los mensajes de error claros se probaron 14 mutantes más: 13 se detectaron y el superviviente, un mensaje con la ruta equivocada, llevó a comparar el texto exacto.

---

## 7. Convenciones del repositorio

| Aspecto | Convención |
|---|---|
| Cabecera de cada fichero `.py` | Dos líneas al principio: `# Proyecto: py-taximetro` y `# fuente: <ruta desde la raíz>` (por ejemplo, `src/taximetro/core/trip.py`). Los ficheros vacíos, como los `__init__.py`, no la llevan. La regla se comprueba en `tests/test_conventions.py`. |
| Versión | La versión vive solo en `pyproject.toml`. El criterio de versionado y el estado de las versiones publicadas se documentan únicamente en el [README](../README.md#versionado); no se repiten en ningún otro fichero. |
| Documentación | `README.md` (entrada del repositorio: instalación, arranque y enlaces), `docs/USAGE.md` (manual de uso), `docs/ARCHITECTURE.md` (este documento), `docs/TESTING.md` (cómo se prueba) y `docs/AUTOEVALUACION.md` (autoevaluación frente a la rúbrica) y `docs/CONTRIBUTING.md` (flujo de trabajo). El README resume y enlaza; el detalle vive en `docs/`, y el README es el único documento de la raíz. Los documentos `.md` llevan el **nombre en mayúsculas** (`USAGE.md`, `ARCHITECTURE.md`…) para distinguirlos del código y de los tests, que van en minúsculas. |
| Commits | Conventional Commits (`feat`, `fix`, `test`, `refactor`, `docs`, `chore`) con referencia al issue (`Refs #n`) |
| Ramas y PR | Una rama de release por fase y una rama por funcionalidad; `main` solo avanza tras la demo. Reglas completas en [CONTRIBUTING.md](CONTRIBUTING.md). |
| Seguimiento | Tablero GitHub Projects «TTX-247 Taxímetro» (campos Fase, Tipo, MoSCoW, Estimate y Status) y backlog en `docs/project_backlog.xlsx` |
| Estilo | `ruff` (líneas de hasta 100 caracteres) |

---

## 8. Ejecución y verificación

Comandos en Git Bash, desde la raíz del proyecto y con el entorno virtual activado:

```bash
python -m taximetro
```

Con otro fichero de tarifas:

```bash
TAXIMETRO_RATES=otras_tarifas.toml python -m taximetro
```

Con otra carpeta de datos:

```bash
TAXIMETRO_DATA_DIR=mis_datos python -m taximetro
```

```bash
python -m pytest -v
```

```bash
python -m pytest --cov
```

```bash
python -m pytest --cov=src/taximetro --cov-report=term-missing
```

```bash
python -m ruff check src tests
```

---

## 9. Evolución prevista (planificado, salvo lo indicado)

| Fase | Módulos nuevos o cambios | Issues |
|---|---|---|
| **Fase 2** — Observabilidad y persistencia | `infra/repos/` (memoria y JSON) implementando `TripRepository` y `event_log.py` implementando `EventLog`. **Ya hecho:** cargador de tarifas desde `config/rates.toml` (US-07), repositorio JSON del historial con la carpeta de datos (TK-04), comando `historico` con el día como argumento (US-05) y registro de eventos de operación en la carpeta `TAXIMETRO_LOG_DIR` (US-06) y umbral de cobertura del 90 % para el núcleo (TK-03). **Pendiente:** la promoción a `main` | US-05 (#6), US-06 (#7), US-07 (#8), TK-03 (#13), TK-04 (#14) |
| **Fase 3** — Arquitectura y UI | Refuerzo de la POO y de las responsabilidades; acceso con contraseña (hash, sin texto plano); `ui/gui/` en tkinter sin bloquear la ventana | US-08 (#9), US-09 (#10), TK-05 (#15) |
| **Fase 4** — Producción | Repositorio SQL; `ui/api/` (API REST: iniciar, cambiar, finalizar, consultar); panel web para el responsable de flota; despliegue con un único comando (Docker) | TK-06 (#16), TK-07 (#17), TK-08 (#18), TK-09 (#19) |
| **Transversal** | README con instrucciones y justificación de librerías; tablero y Conventional Commits | TK-10 (#20), TK-11 (#21) |

**Impacto previsto en la arquitectura:** la API (Fase 4) no tiene estado entre peticiones, así que la carrera activa deberá guardarse en el repositorio con `save` (D5 se revisará entonces). El diseño actual ya lo permite porque `TripRepository.save` está pensado para carreras en curso y terminadas.

---

## 10. Limitaciones conocidas y deuda técnica

| # | Limitación | Plan |
|---|---|---|
| L1 | **Regla de 20 km/h.** El enunciado cobra la tarifa baja por debajo de 20 km/h, pero el modelo solo distingue parado y en movimiento, sin velocidad. | Valorar un estado derivado de la velocidad si el enunciado lo exige. |
| L2 | **Las tarifas se leen una sola vez, al arrancar**: cambiar el fichero exige reiniciar el programa. | Aceptable; la recarga en caliente queda fuera del alcance. |
| L3 | **Solo se guardan las carreras finalizadas**: una carrera en curso al cerrar el programa no se cobra ni se recupera. | Revisar con la API de la Fase 4 (D5). |
| L4 | Una sola carrera activa a la vez: un taxi, un taxímetro. No hay soporte multi-taxi. | Fuera del alcance del prototipo. |
| L5 | **El historial JSON se reescribe entero en cada guardado** y no admite dos programas escribiendo a la vez en la misma carpeta (leer-modificar-escribir): podrían perderse carreras. | Suficiente para un taxi; el repositorio SQL de la Fase 4 lo resuelve. |
| L6 | El módulo `taximetro.core.ports` importa `Trip`, lo que acopla el contrato al modelo. Es aceptable mientras `Trip` sea el único agregado. | Revisar si el modelo crece. |
| L7 | **La validación se repite**: el cargador comprueba que los valores no sean negativos (para poder nombrar la clave y el fichero) y `Tariff` también lo comprueba. | Duplicación asumida: `Tariff` debe protegerse aunque se construya por otro camino, como la API de la Fase 4. |
| L8 | **Las rutas por defecto dependen de la instalación en modo desarrollo**: se calculan desde la ubicación del código (`parents[2]`), y en una instalación normal no apuntarían a `config/` ni a `data/`. | Usar `TAXIMETRO_RATES` y `TAXIMETRO_DATA_DIR`; en la Fase 4 (Docker) se fijarán explícitamente. |
| L9 | **Un fallo al escribir el log durante la jornada se ignora en silencio**: el taxista cobra, pero el responsable no se entera de que faltan eventos. | Valorar un aviso único por sesión. |
| L10 | **Los logs no rotan**: hay un fichero por día y se acumulan; archivarlos o borrarlos es tarea del responsable. | Suficiente para el prototipo; con volumen real, rotación o retención. |

## 11. Recursos de Python que usa el código

Una guía para leer el código: qué recursos del lenguaje aparecen y dónde verlos.

| Recurso | Dónde se ve | Para qué |
|---|---|---|
| **Tipos de datos**: `Decimal`, `datetime` con zona horaria, `Enum` y `dataclass(frozen=True)` | [`core/tariff.py`](../src/taximetro/core/tariff.py), [`core/trip.py`](../src/taximetro/core/trip.py), [`core/state.py`](../src/taximetro/core/state.py) | Dinero exacto, fechas sin ambigüedad, estados cerrados y una tarifa inmutable |
| **Colecciones tipadas**: diccionarios, listas y tuplas | La tabla de comandos `dict[str, Callable[[], None]]` y `dict[type[TaximetroError], str]` en [`ui/cli/app.py`](../src/taximetro/ui/cli/app.py); `list[Trip]` en los repositorios; `tuple[str, ...]` en [`infra/tariff_loader.py`](../src/taximetro/infra/tariff_loader.py) | Elegir la acción por nombre sin una cadena de `if`, traducir errores a mensajes y devolver resultados |
| **Genéricos de la biblioteca estándar**: `Callable`, `Sequence` y `Protocol` | [`core/ports.py`](../src/taximetro/core/ports.py) y las firmas de `Cli` | Describir qué se recibe sin atarlo a una clase concreta. No se definen genéricos propios con `TypeVar`, que no hacen falta en este proyecto |
| **Bucles** | El `while` con `break` y `continue` de `Cli.run`, y el `for` con `enumerate` del histórico | Mantener la consola esperando comandos hasta `salir` y numerar las carreras |
| **Condicionales** | Las cláusulas de guarda de `Trip._close_segment`: carrera terminada, sin iniciar o con el tiempo retrocedido | Proteger los invariantes de la entidad antes de calcular |
| **Excepciones** | `try/except` en `TripService.finish` y `_log`; `raise … from error` en el cargador y los repositorios | Que un fallo del disco o del registro nunca esconda el importe |
| **Comprensiones y generadores** | `[trip for trip in trips if …]` en `JsonTripRepository.list_finished` y `[rates[key] for key in keys]` en el cargador de tarifas | Filtrar y extraer valores sin variables auxiliares |
| **Legibilidad** | Anotaciones de tipo en las funciones, docstrings, nombres descriptivos en `snake_case`, funciones cortas y cabecera de dos líneas en cada fichero | Que el código se lea solo. Lo comprueban Ruff y [`tests/test_conventions.py`](../tests/test_conventions.py) ([TESTING.md](TESTING.md#7-convenciones-de-los-tests)) |

La descomposición del problema en pasos está en el [modelo de cálculo y las reglas de negocio](#41-modelo-de-cálculo) y en el [flujo de una carrera completa](#44-flujo-de-una-carrera-completa).

## 12. Referencias

Documentación oficial de Python, en inglés, en la que se apoya el código.

| Fuente | Qué se aplicó |
|---|---|
| [Python: `decimal`](https://docs.python.org/3/library/decimal.html) | Importes en `Decimal` y redondeo medio hacia arriba al final, sin errores de coma flotante (decisión D3) |
| [Python: `dataclasses`](https://docs.python.org/3/library/dataclasses.html) | La tarifa como objeto valor inmutable con `frozen=True` (`Tariff`) |
| [Python: `typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol) | Los contratos de `core/ports.py`, sin herencia (decisión D10) |
| [Python: `pathlib`](https://docs.python.org/3/library/pathlib.html) | Rutas de tarifas, datos y logs, y escritura atómica del historial (decisión D16) |
| [Python: `tomllib`](https://docs.python.org/3/library/tomllib.html) | Lectura de `config/rates.toml` en el cargador de tarifas (decisión D7) |
