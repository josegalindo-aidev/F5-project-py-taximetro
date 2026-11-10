<!--
Proyecto: py-taximetro
fuente: CONTRIBUTING.md
-->

# Guía de trabajo: ramas, PR y releases

Reglas para trabajar en el repositorio. Cada fase del proyecto se desarrolla en una **rama de release** y solo llega a `main` cuando su demo la valida. **Todo cambio entra por una pull request (PR)**: no hay `push` directo a `main` ni a las ramas de release.

## 1. Modelo de ramas

```
main            ●─────────────────────────────●   último estado entregado y demostrado  → etiqueta vX.Y.Z
                 \                           /
release/X.Y.Z     ●───●────●────●───────────●     integración de la fase
                       \  /      \  /
feat/us-NN-…            ●         ●               una rama por historia o tarea
```

| Rama | Regla |
|---|---|
| `main` | Último estado entregado y demostrado. Solo recibe la rama de release de cada fase y las correcciones urgentes (apartado 6). |
| `release/X.Y.Z` | Integración de una fase. Se crea desde `main` al empezar la fase y se borra al promoverla. Vive pocos días. |
| `feat/…`, `fix/…`, `docs/…`, `chore/…`, `test/…` | Una por historia o tarea. Se crea desde la rama de release, se integra en ella con una PR y se borra al fusionar. |
| Etiqueta `vX.Y.Z` | Marca el momento exacto de una release. Se crea sobre `main` tras la promoción, junto con su Release en GitHub. |

**Nombres.** La rama de release no lleva la `v` (`release/X.Y.Z`); la etiqueta sí (`vX.Y.Z`). Las ramas de trabajo siguen el tipo del commit y el identificador del issue: `feat/us-07-tarifas-en-fichero`, `fix/redondeo-total`, `docs/guia-de-trabajo`.

## 2. Lo que imponen los rulesets de GitHub

El repositorio tiene tres rulesets activos. Sin lista de bypass, **se aplican también a la persona propietaria**.

| Ruleset | Se aplica a | Reglas |
|---|---|---|
| Proteger main | `main` | No se puede borrar ni forzar (*force push*). Exige PR (0 aprobaciones). Solo permite el método **Merge**. |
| proteger releases/** | `release/**` | No se puede forzar. Exige PR (0 aprobaciones). Permite **Merge** y **Rebase**. |
| Proteger etiquetas de release | `v*` | No se pueden borrar, mover ni forzar. Crear etiquetas sí está permitido. |

Además, el repositorio **borra automáticamente la rama de origen** al fusionar su PR.

## 3. Flujo de subida: todo por PR

Este es el recorrido de cualquier cambio, también de los pequeños (una línea de documentación incluida).

1. **Actualizar la rama de release y crear la rama de trabajo desde ella.**

   ```bash
   git switch release/X.Y.Z
   git pull
   git switch -c feat/us-NN-descripcion
   ```

2. **Desarrollar con TDD**: test en rojo, código mínimo en verde y refactor. Un commit por paso con sentido, en formato Conventional Commits (apartado 7).
3. **Comprobar en local antes de subir** (no hay CI todavía): `python -m pytest` y `python -m ruff check src tests`, sin fallos.
4. **Subir la rama y abrir la PR hacia la rama de release**, no hacia `main`. Enlazar el issue con `Refs #n`.

   ```bash
   git push -u origin feat/us-NN-descripcion
   ```

5. **Fusionar con "Rebase and merge"**, que conserva los commits del ciclo TDD. La rama remota se borra sola.
6. **Limpiar en local.**

   ```bash
   git switch release/X.Y.Z
   git pull
   git fetch --prune
   git branch -D feat/us-NN-descripcion
   ```

   Se usa `-D` y no `-d` porque el *rebase* reescribe los commits al fusionar: Git no reconoce la rama como fusionada aunque su contenido ya esté en la release. Comprueba antes que la PR figura como fusionada.

## 4. Cierre de issues y tablero

GitHub solo cierra un issue por `Closes #n` cuando la PR llega a la **rama por defecto** (`main`). Por eso:

- En las PR hacia la rama de release se usa `Refs #n`. El issue sigue abierto.
- Durante la fase, la tarjeta del tablero se mueve a mano (*In progress*, *In review*).
- Todos los `Closes #n` de la fase van en la **PR de promoción a `main`**, que los cierra a la vez y deja las tarjetas en *Done*.

## 5. Cerrar una fase: promoción a `main`

1. La rama de release contiene todas las funcionalidades de la fase y sus pruebas pasan.
2. **Subir la versión por PR**: una rama `chore/…` desde la release que cambie `version` en `pyproject.toml` y la tabla de versiones del [README](README.md#versionado), integrada con el flujo del apartado 3.
3. Hacer la **demo** desde la rama de release.
4. **Registrar la demo y la entrega** en la hoja *Fases* del backlog, también por PR hacia la rama de release. Debe hacerse antes de promover: después solo se admiten PR a `main` con el método *Merge*.
5. Abrir la PR de promoción `release/X.Y.Z` → `main`, con la plantilla de release. Desde la web, añadir `?template=release.md` a la URL de comparación. La plantilla lista los `Closes #n` de la fase.
6. Fusionar con **"Create a merge commit"**. Es el único método que admite `main`, y así conserva los mismos commits que la rama de release. La rama de release se borra sola.
7. Crear la etiqueta `vX.Y.Z` sobre `main` y su Release en GitHub.

## 6. Correcciones urgentes

Si aparece un error en lo ya entregado:

1. Rama `fix/…` desde `main` y PR hacia `main`, fusionada con **"Create a merge commit"** (es lo único que admite `main`).
2. Etiqueta `vX.Y.Z+1` (el tercer número) con su Release.
3. Traer el cambio a la rama de release activa con una PR de `main` hacia `release/X.Y.Z`, con el método *Merge*, para que no se desincronicen.

## 7. Commits

[Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/): `tipo(ámbito): descripción en imperativo`, con la referencia al issue en el cuerpo (`Refs #n`).

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de un error |
| `test` | Añadir o cambiar pruebas |
| `refactor` | Cambio interno sin alterar el comportamiento |
| `docs` | Documentación |
| `chore` | Mantenimiento (configuración, dependencias) |
| `ci` / `build` | Integración continua y empaquetado |

## 8. Limitaciones y cómo actuar

| Limitación | Qué implica | Qué hacer |
|---|---|---|
| No hay `push` directo a `main` ni a `release/**` | Ni la persona propietaria puede saltarse la PR | Todo cambio, por pequeño que sea, va en una rama con su PR |
| `main` solo admite *Merge* | Las PR hacia `main` no pueden usar *Rebase* ni *Squash* | Usar "Create a merge commit" en promociones y correcciones urgentes |
| `release/**` solo admite *Merge* y *Rebase* | No se puede aplastar (*Squash*) | Usar *Rebase* en las funcionalidades |
| Sin aprobaciones obligatorias | Es un proyecto de una sola persona; la PR da trazabilidad, no revisión | Revisar el diff de la PR antes de fusionar |
| `Closes #n` solo actúa en `main` | Los issues no se cierran al integrar en la release | Usar `Refs #n` y poner los `Closes` en la promoción |
| Sin integración continua | GitHub no ejecuta los tests | Ejecutar pytest y ruff en local y marcarlo en el checklist de la PR |
| Las etiquetas `v*` son inmutables | No se pueden mover ni borrar | Corregir con una versión nueva. Solo en un caso excepcional: desactivar el ruleset un momento y reactivarlo después |
| El *rebase* reescribe los commits al fusionar | La rama local no aparece como fusionada y no debe reutilizarse | Borrarla con `-D` y crear una nueva para el siguiente trabajo |
| Rama de release de vida corta | Si dura semanas, se aleja de `main` | Mantenerla breve y sincronizarla tras cada corrección urgente |
| El backlog es un `.xlsx` binario | Dos ramas que lo editan no se pueden fusionar | Editarlo en una sola PR cada vez y limpiar el autor de sus metadatos antes del commit |

## 9. Versiones

El criterio y el estado de las versiones están **solo** en el [README](README.md#versionado), y el número, en `pyproject.toml`. No se repiten en otros ficheros.

## 10. Cambiar las reglas del repositorio

Los rulesets se editan en *Settings → Rules → Rulesets*. Si se cambian, hay que actualizar el apartado 2 de esta guía en la misma PR.
