<!--
Proyecto: py-taximetro
fuente: docs/USAGE.md
-->

# Manual de uso del taxímetro

Guía para usar y configurar el taxímetro desde la línea de comandos. Para instalarlo y arrancarlo, consulta el [README](../README.md).

## 1. Conceptos básicos

| Concepto | Significado |
|---|---|
| **Carrera** | Un servicio de taxi, desde `iniciar` hasta `finalizar`. |
| **Estado** | Situación del taxi durante la carrera: *parado* o *en movimiento*. |
| **Tramo** | Periodo de tiempo con el mismo estado. Cada cambio de estado cierra un tramo. |
| **Tarifa** | Precio por segundo, que depende del estado. |
| **Historial** | Fichero donde se guardan las carreras finalizadas. Se conserva al cerrar el programa (apartado 8). |

### Tarifas

Las tarifas se leen del fichero `config/rates.toml` al arrancar (ver el apartado 7). Las que se entregan son las de la Zona EMT Madrid (junio 2025):

| Estado | Precio |
|---|---|
| Parado | 0,02 € por segundo |
| En movimiento | 0,05 € por segundo |

### Cómo se calcula el importe

El importe es la suma, por tramos, del tiempo en cada estado multiplicado por su tarifa. Ejemplo: 10 s parado, 10 s en movimiento y 10 s parado.

```
10 × 0,02  +  10 × 0,05  +  10 × 0,02  =  0,20 + 0,50 + 0,20  =  0,90 €
```

El total se redondea al céntimo **solo al final** (por ejemplo, 0,5 s parado son 0,01 €).

## 2. Comandos

Escribe un comando y pulsa Intro. No distingue mayúsculas de minúsculas ni espacios sobrantes, y las líneas vacías se ignoran.

| Comando | Qué hace | Respuesta |
|---|---|---|
| `iniciar` | Inicia una carrera; el taxi empieza **parado** | `Carrera iniciada (taxi parado).` |
| `parar` | Cambia al estado parado | `Estado: parado.` |
| `mover` | Cambia al estado en movimiento | `Estado: en movimiento.` |
| `estado` | Muestra el estado y el importe acumulado, sin cerrar la carrera | `Estado: en movimiento - Importe actual: 0,70 €` |
| `finalizar` | Termina la carrera y muestra el total | `Carrera finalizada. Total: 0,70 €` |
| `historico` | Muestra las carreras finalizadas de hoy; con una fecha, las de ese día (`historico AAAA-MM-DD`) | `Total del día: 2 carreras, 19,55 €` |
| `ayuda` | Repite la lista de comandos | La lista de comandos |
| `salir` | Cierra el programa | `Hasta pronto.` |

### El histórico del día

`historico` lista las carreras **finalizadas** de hoy, de la más antigua a la más reciente, con su hora de inicio y de fin y su importe, y suma el total del día:

```
> historico
Carreras de hoy:
  1. 09:05 - 09:12  7,25 €
  2. 11:40 - 11:52  12,30 €
Total del día: 2 carreras, 19,55 €
```

Con una fecha en formato `AAAA-MM-DD` muestra otro día:

```
> historico 2026-11-10
Carreras del 2026-11-10:
  1. 08:00 - 08:20  5,00 €
Total del día: 1 carrera, 5,00 €
```

Una carrera cuenta en el día en que **termina** (una que empieza a las 23:50 y acaba a las 00:20 figura en el día siguiente). Una carrera sin finalizar no aparece. El histórico persiste entre sesiones porque sale del historial en disco (apartado 8).

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `Hoy no hay carreras finalizadas.` | Todavía no has finalizado ninguna carrera hoy | Nada: es informativo |
| `El 2026-11-10 no hubo carreras finalizadas.` | Ese día no hay carreras en el historial | Comprueba la fecha |
| `Fecha no válida: 'ayer'. Usa el formato AAAA-MM-DD.` | La fecha no existe o no está en ese formato (por ejemplo, `11/11/2026` o `2026-13-45`) | Escríbela con año, mes y día separados por guiones |
| `El historial '<ruta>' está dañado: …` | El fichero del historial no se puede interpretar (apartado 8) | Revisa el fichero; el mensaje explica cómo |

Si el historial no se puede leer, el mensaje es el mismo que al arrancar (apartado 8) y el programa **sigue funcionando**: puedes seguir cobrando carreras.

## 3. Una carrera paso a paso

Ejemplo de sesión. Las líneas que empiezan por `>` son lo que escribes tú; los importes dependen del tiempo real que dejes pasar entre comandos.

```
Taxímetro digital TTX-247
Historial: /ruta/a/data/trips.json
Logs: /ruta/a/logs
Comandos disponibles:
  iniciar    Inicia una carrera (el taxi empieza parado)
  parar      El taxi está parado
  mover      El taxi está en movimiento
  estado     Muestra el estado y el importe actual
  finalizar  Termina la carrera y muestra el total
  historico  Muestra las carreras de hoy, o de un día: historico AAAA-MM-DD
  ayuda      Muestra esta ayuda
  salir      Cierra el programa
> iniciar
Carrera iniciada (taxi parado).
> mover                     (pasan unos segundos)
Estado: en movimiento.
> estado
Estado: en movimiento - Importe actual: 0,16 €
> finalizar
Carrera finalizada. Total: 0,16 €
> salir
Hasta pronto.
```

En este ejemplo, 3 s parado (0,06 €) más 2 s en movimiento (0,10 €) dan 0,16 €.

## 4. Encadenar carreras

Tras `finalizar` no hace falta cerrar el programa: puedes escribir `iniciar` para la siguiente carrera. **El tiempo entre carreras no se cobra**: el contador solo corre mientras hay una carrera en curso.

## 5. Mensajes y qué hacer

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `No hay ninguna carrera en curso. Usa 'iniciar'.` | Has usado `parar`, `mover`, `estado` o `finalizar` sin carrera activa | Escribe `iniciar` |
| `Ya hay una carrera en curso. Usa 'finalizar' antes de iniciar otra.` | Has escrito `iniciar` con una carrera ya iniciada | Escribe `finalizar` y después `iniciar` |
| `Comando desconocido: 'xxx'. Escribe 'ayuda'.` | El comando no existe | Escribe `ayuda` para ver la lista |
| `Aviso: La carrera en curso no se ha cobrado.` | Has salido del programa sin finalizar la carrera | Vuelve a abrirlo; esa carrera no se recupera |
| `Aviso: No se pudo guardar la carrera en el historial: …` | Tras `finalizar`, el total se ha mostrado, pero no se pudo guardar (disco lleno, fichero bloqueado, historial dañado) | Anota el total. Revisa el motivo que indica el aviso; el programa sigue funcionando y puedes iniciar otra carrera |

Los errores **no cierran el programa**: puedes seguir escribiendo comandos. Los errores del fichero de tarifas y del historial son distintos: ocurren al arrancar y se explican en los apartados 7 y 8.

## 6. Cerrar el programa

- Escribe `salir`.
- También se cierra con **Ctrl+C**, o al terminar la entrada (Ctrl+D en Linux y macOS; Ctrl+Z y Intro en Windows).

Si hay una carrera sin finalizar, el programa te avisa de que no se ha cobrado.

## 7. Configurar las tarifas

Las tarifas están en un fichero de texto y se leen **una sola vez, al arrancar**. Para cambiarlas, edita el fichero y vuelve a abrir el programa.

### El fichero

Por defecto es `config/rates.toml`, en la raíz del proyecto:

```toml
[rates]
stopped = "0.02"   # parado, en euros por segundo
moving = "0.05"    # en movimiento, en euros por segundo
```

| Regla | Correcto | Incorrecto |
|---|---|---|
| Los valores van **entre comillas** | `"0.02"` | `0.02` |
| Punto decimal, no coma | `"0.05"` | `"0,05"` |
| Número finito y no negativo (el cero se admite) | `"0.02"`, `"0"` | `"-0.02"`, `"NaN"`, `"Infinity"` |
| Las dos claves y la tabla `[rates]` son obligatorias | `[rates]` con `stopped` y `moving` | falta alguna |
| El fichero se guarda en UTF-8 | | |

Las comillas son necesarias porque un número sin comillas se lee como decimal binario y arrastra un pequeño error de redondeo; como texto, el valor es exacto.

### Usar otro fichero

La variable de entorno `TAXIMETRO_RATES` indica otra ruta. En Git Bash:

```bash
TAXIMETRO_RATES=otras_tarifas.toml python -m taximetro
```

En PowerShell:

```powershell
$env:TAXIMETRO_RATES = "otras_tarifas.toml"; python -m taximetro
```

Una ruta relativa se interpreta desde la carpeta en la que ejecutas el programa. Si la variable está vacía, se ignora y se usa el fichero por defecto.

### Si el fichero tiene errores

El programa **no arranca**: no usa ninguna tarifa por defecto, porque cobrar con una tarifa equivocada es peor que no cobrar. Muestra un mensaje que empieza por `Error:` y termina con **código de salida 1**.

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `No se encuentra el fichero de tarifas: <ruta>` | La ruta es incorrecta o el fichero no existe | Revisa la ruta o la variable `TAXIMETRO_RATES` |
| `No se puede leer el fichero de tarifas (…): <ruta>` | La ruta es una carpeta, o no hay permiso de lectura | Indica un fichero y revisa sus permisos |
| `El fichero de tarifas debe estar guardado en UTF-8 (…)` | Otra codificación, por ejemplo ANSI | Guárdalo como UTF-8 |
| `El fichero de tarifas tiene errores de sintaxis (…)` | Falta un corchete o una comilla | Corrige la línea y la columna que indica el mensaje |
| `Falta la sección [rates] en <ruta>` | No existe la tabla `[rates]` | Añade `[rates]` |
| `[rates] debe ser una tabla, no un valor suelto` | Se escribió `rates = 5` | Usa la sección `[rates]` |
| `Falta la clave 'moving' en [rates] de <ruta>` | Falta `stopped` o `moving` | Añade la clave que falta |
| `El valor de 'stopped' debe escribirse entre comillas: 0.02 (<ruta>)` | Número sin comillas | Escríbelo entre comillas |
| `El valor de 'stopped' no es un número: 'abc' (<ruta>)` | Texto, o coma decimal | Usa un número con punto decimal |
| `El valor de 'stopped' no es un número finito: 'NaN' (<ruta>)` | `NaN` o `Infinity` | Usa un número normal |
| `El valor de 'stopped' no puede ser negativo: '-0.02' (<ruta>)` | Valor negativo | Usa un valor mayor o igual que cero |

## 8. Dónde se guardan los datos

Cada vez que finalizas una carrera, se añade a un fichero `trips.json` dentro de la **carpeta de datos**. Al arrancar, el programa muestra las rutas completas en las líneas `Historial: …` y `Logs: …`.

| Qué | Dónde | Cómo cambiarlo |
|---|---|---|
| Historial de carreras | `trips.json` dentro de la carpeta de datos. Por defecto, `data/` en la raíz del proyecto | Variable de entorno `TAXIMETRO_DATA_DIR`, que indica **una carpeta**, no un fichero |
| Logs de operación | Un fichero por día, `taximetro-AAAA-MM-DD.jsonl`, dentro de la **carpeta de logs**, separada de los datos. Por defecto, `logs/` en la raíz del proyecto | Variable de entorno `TAXIMETRO_LOG_DIR`, que indica **una carpeta**, no un fichero |
| Tarifas | `config/rates.toml` | `TAXIMETRO_RATES` (apartado 7) |

La carpeta de datos y la de logs son independientes a propósito: en una instalación de producción se pueden montar en ubicaciones distintas (por ejemplo, volúmenes diferentes). Se configuran como **carpetas** y no como ficheros porque, para no perder el historial si algo falla a mitad de escritura, el programa escribe primero un fichero temporal junto a `trips.json` y después lo intercambia por el original. Eso exige poder crear ficheros en esa carpeta.

En Git Bash:

```bash
TAXIMETRO_DATA_DIR=/ruta/a/mis/datos python -m taximetro
```

En PowerShell:

```powershell
$env:TAXIMETRO_DATA_DIR = "C:\ruta\a\mis\datos"; python -m taximetro
```

Si la carpeta no existe, el programa la crea al guardar la primera carrera. Una variable vacía se ignora y se usa la carpeta por defecto.

### Los logs de operación

El responsable puede auditar el uso del taxímetro con los logs. Cada evento es **una línea JSON** que se añade al fichero del día, sin borrar nunca lo anterior:

```
{"ts": "2026-11-16T10:05:00.123456+01:00", "evento": "carrera_iniciada", "carrera": "a1b2c3d4"}
{"ts": "2026-11-16T10:05:30.456789+01:00", "evento": "estado_cambiado", "carrera": "a1b2c3d4", "estado": "moving"}
{"ts": "2026-11-16T10:12:00.789012+01:00", "evento": "carrera_finalizada", "carrera": "a1b2c3d4", "total": "7.25"}
```

| Evento | Cuándo se registra | Datos |
|---|---|---|
| `carrera_iniciada` | Al escribir `iniciar` | `carrera` |
| `estado_cambiado` | En cada `parar` o `mover` | `carrera` y `estado` (`stopped` o `moving`) |
| `carrera_finalizada` | Al escribir `finalizar` | `carrera` y `total` en euros, con punto decimal |
| `carrera_no_guardada` | Si tras finalizar no se pudo guardar en el historial | `carrera` y `motivo` |

- `ts` es la fecha y hora local, con la zona horaria. El identificador `carrera` es el mismo en todos los eventos de una carrera, así que se pueden seguir de principio a fin.
- Una carrera que se inicia y no se finaliza deja solo su `carrera_iniciada`: así se ve que empezó y no se cobró.
- Cada día tiene su fichero (`taximetro-2026-11-16.jsonl`). Los ficheros no se borran ni se rotan solos: archivarlos es cosa del responsable.
- Los acentos y la `ñ` se escriben tal cual, sin secuencias de escape.

Al arrancar, el programa comprueba la carpeta de logs: la crea si no existe y prueba a escribir en ella. Como los logs sirven para auditar, si no se puede usar el programa **no arranca**: muestra un mensaje que empieza por `Error:` y termina con **código de salida 1**.

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `La carpeta de logs '<ruta>' no es una carpeta: es un fichero.` | `TAXIMETRO_LOG_DIR` apunta a un fichero, o una carpeta por encima de la ruta lo es | Indica una carpeta, existente o que todavía no exista |
| `No se puede usar la carpeta de logs '<ruta>': <motivo>` | La carpeta no se puede crear o no hay permiso para escribir en ella; el motivo lo da el sistema operativo | Indica una carpeta en la que puedas escribir |

Si el log falla **después** de arrancar (por ejemplo, el disco se llena), el programa lo ignora y sigue: la carrera se cobra con normalidad y el taxista nunca ve un error por culpa del registro.

### Si el historial tiene problemas

Al arrancar, el programa lee el historial una vez. Si no puede, **no arranca** y no toca el fichero, para que puedas recuperarlo. Muestra un mensaje que empieza por `Error:` y termina con **código de salida 1**.

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `El historial '<ruta>' está dañado: no es un JSON válido (línea 3, columna 1)` | El fichero no es JSON válido; la línea y la columna dicen dónde falla | Abre el fichero en esa posición y corrígelo, o guarda una copia y quítalo para empezar un historial nuevo |
| `El historial '<ruta>' está dañado: la carrera n.º 2 tiene un dato que falta o no es válido` | Una carrera, la segunda en este ejemplo, no tiene todos sus datos, tiene un importe que no es un número o una fecha mal escrita | Corrige o quita esa carrera |
| `El historial '<ruta>' está dañado: no está guardado en UTF-8` | El fichero se guardó con otra codificación | Guárdalo como UTF-8 |
| `El historial '<ruta>' está dañado: se esperaba una lista de carreras` | Es un JSON válido, pero no una lista de carreras | Corrige el fichero o quítalo para empezar un historial nuevo |
| `No se pudo leer el historial '<ruta>': …` | El fichero existe pero no se puede leer: falta el permiso o la ruta es una carpeta | Revisa los permisos y que `trips.json` sea un fichero |
| `La carpeta de datos '<ruta>' no es una carpeta: es un fichero.` | `TAXIMETRO_DATA_DIR` apunta a un fichero, o una carpeta por encima de la ruta lo es | Indica una carpeta, existente o que todavía no exista |

Si el fallo ocurre **después** de arrancar, al finalizar una carrera, el total se muestra igualmente seguido de un `Aviso:` (apartado 5): un problema del historial nunca esconde el importe.

## 9. Limitaciones actuales

| Limitación | Detalle |
|---|---|
| El histórico muestra un día cada vez | No hay resúmenes por semana o por mes: se consulta un día con `historico AAAA-MM-DD`. |
| Una carrera sin finalizar no se guarda | Solo se guardan las carreras finalizadas; si sales con una en curso, no se recupera. |
| Un solo programa por carpeta de datos | Si dos instancias escriben a la vez en la misma carpeta, pueden perderse carreras. |
| Los logs no se rotan | Hay un fichero por día y se acumulan; archivarlos o borrarlos es cosa del responsable. |
| Un fallo del log durante la jornada no se avisa | Si el log deja de escribirse a mitad de la jornada, el programa sigue cobrando y no lo comunica: faltarían eventos. |
| Tarifas leídas al arrancar | Si editas el fichero con el programa abierto, el cambio no se aplica hasta volver a abrirlo. |
| Estado indicado a mano | El taxi solo puede estar parado o en movimiento, y el estado lo indicas tú con `parar` y `mover`. El programa no mide la velocidad, así que no aplica por sí mismo la regla de «menos de 20 km/h». |
| Una carrera a la vez | Solo hay una carrera activa en cada momento. |

## 10. Qué llegará en las siguientes fases

Las tarifas configurables, el historial en disco, la consulta del histórico del día y el registro de operaciones, previstos para la Fase 2, ya están disponibles (apartados 2, 7 y 8).

| Fase | Novedades para el usuario |
|---|---|
| 3 | Acceso con contraseña e interfaz gráfica con botones grandes para tablet |
| 4 | API REST, panel web para el responsable de flota y despliegue con un único comando |

Detalles técnicos y diseño: [docs/ARCHITECTURE.md](ARCHITECTURE.md).
