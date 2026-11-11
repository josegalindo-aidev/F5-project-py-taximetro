<!--
Proyecto: py-taximetro
fuente: docs/usage.md
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
| `ayuda` | Repite la lista de comandos | La lista de comandos |
| `salir` | Cierra el programa | `Hasta pronto.` |

## 3. Una carrera paso a paso

Ejemplo de sesión. Las líneas que empiezan por `>` son lo que escribes tú; los importes dependen del tiempo real que dejes pasar entre comandos.

```
Taxímetro digital TTX-247
Historial: /ruta/a/data/trips.json
Comandos disponibles:
  iniciar    Inicia una carrera (el taxi empieza parado)
  parar      El taxi está parado
  mover      El taxi está en movimiento
  estado     Muestra el estado y el importe actual
  finalizar  Termina la carrera y muestra el total
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

Cada vez que finalizas una carrera, se añade a un fichero `trips.json` dentro de la **carpeta de datos**. Al arrancar, el programa muestra la ruta completa en la línea `Historial: …`.

| Qué | Dónde | Cómo cambiarlo |
|---|---|---|
| Historial de carreras | `trips.json` dentro de la carpeta de datos. Por defecto, `data/` en la raíz del proyecto | Variable de entorno `TAXIMETRO_DATA_DIR`, que indica **una carpeta**, no un fichero |
| Logs de ejecución | Carpeta propia, separada de los datos | `TAXIMETRO_LOG_DIR`. **Reservada**: se usará cuando se añadan los logs (US-06) y todavía no tiene efecto |
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

### Si el historial tiene problemas

Al arrancar, el programa lee el historial una vez. Si no puede, **no arranca** y no toca el fichero, para que puedas recuperarlo. Muestra un mensaje que empieza por `Error:` y termina con **código de salida 1**.

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `El historial '<ruta>' está dañado: …` | El fichero no es JSON válido, no es una lista de carreras o alguna carrera no se puede interpretar | Guarda una copia, corrige el fichero o quítalo para empezar un historial nuevo |
| `No se pudo leer el historial '<ruta>': …` | El fichero existe pero no se puede leer: falta el permiso o la ruta es una carpeta | Revisa los permisos y que `trips.json` sea un fichero |

Si el fallo ocurre **después** de arrancar, al finalizar una carrera, el total se muestra igualmente seguido de un `Aviso:` (apartado 5): un problema del historial nunca esconde el importe.

## 9. Limitaciones actuales

| Limitación | Detalle |
|---|---|
| Historial sin consulta | Las carreras finalizadas se guardan, pero todavía no hay un comando para consultarlas (histórico del día, US-05). |
| Una carrera sin finalizar no se guarda | Solo se guardan las carreras finalizadas; si sales con una en curso, no se recupera. |
| Un solo programa por carpeta de datos | Si dos instancias escriben a la vez en la misma carpeta, pueden perderse carreras. |
| Tarifas leídas al arrancar | Si editas el fichero con el programa abierto, el cambio no se aplica hasta volver a abrirlo. |
| Estado indicado a mano | El taxi solo puede estar parado o en movimiento, y el estado lo indicas tú con `parar` y `mover`. El programa no mide la velocidad, así que no aplica por sí mismo la regla de «menos de 20 km/h». |
| Una carrera a la vez | Solo hay una carrera activa en cada momento. |

## 10. Qué llegará en las siguientes fases

Las tarifas configurables y el historial en disco, previstos para la Fase 2, ya están disponibles (apartados 7 y 8).

| Fase | Novedades para el usuario |
|---|---|
| 2 | Consulta del histórico del día y registro de operaciones (logs) |
| 3 | Acceso con contraseña e interfaz gráfica con botones grandes para tablet |
| 4 | API REST, panel web para el responsable de flota y despliegue con un único comando |

Detalles técnicos y diseño: [docs/architecture.md](architecture.md).
