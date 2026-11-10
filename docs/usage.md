<!--
Proyecto: py-taximetro
fuente: docs/usage.md
-->

# Manual de uso del taxímetro

Guía para usar el taxímetro desde la línea de comandos (Fase 1 · MVP). Para instalarlo y arrancarlo, consulta el [README](../README.md).

## 1. Conceptos básicos

| Concepto | Significado |
|---|---|
| **Carrera** | Un servicio de taxi, desde `iniciar` hasta `finalizar`. |
| **Estado** | Situación del taxi durante la carrera: *parado* o *en movimiento*. |
| **Tramo** | Periodo de tiempo con el mismo estado. Cada cambio de estado cierra un tramo. |
| **Tarifa** | Precio por segundo, que depende del estado. |

### Tarifas

Zona EMT Madrid (junio 2025):

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

Los errores **no cierran el programa**: puedes seguir escribiendo comandos.

## 6. Cerrar el programa

- Escribe `salir`.
- También se cierra con **Ctrl+C**, o al terminar la entrada (Ctrl+D en Linux y macOS; Ctrl+Z y Intro en Windows).

Si hay una carrera sin finalizar, el programa te avisa de que no se ha cobrado.

## 7. Limitaciones actuales

| Limitación | Detalle |
|---|---|
| Sin historial | Al cerrar el programa se pierde todo; no hay histórico del día todavía (Fase 2). |
| Tarifas fijas | Los precios están en el código; en la Fase 2 se leerán de `config/rates.toml`. |
| Estado indicado a mano | El taxi solo puede estar parado o en movimiento, y el estado lo indicas tú con `parar` y `mover`. El programa no mide la velocidad, así que no aplica por sí mismo la regla de «menos de 20 km/h». |
| Una carrera a la vez | Solo hay una carrera activa en cada momento. |

## 8. Qué llegará en las siguientes fases

| Fase | Novedades para el usuario |
|---|---|
| 2 | Histórico del día, registro de operaciones y tarifas configurables |
| 3 | Acceso con contraseña e interfaz gráfica con botones grandes para tablet |
| 4 | API REST, panel web para el responsable de flota y despliegue con un único comando |

Detalles técnicos y diseño: [docs/architecture.md](architecture.md).
