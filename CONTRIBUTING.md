<!--
Proyecto: py-taximetro
fuente: CONTRIBUTING.md
-->

# Guía de trabajo: ramas, PR y releases

Reglas para trabajar en el repositorio. Cada fase del proyecto se desarrolla en una **rama de release** y solo llega a `main` cuando su demo la valida.

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
| `main` | Último estado entregado y demostrado. Solo recibe la rama de release de cada fase (y las correcciones urgentes, ver el apartado 6). |
| `release/X.Y.Z` | Integración de una fase. Se crea desde `main` al empezar la fase y se borra tras promoverla. Vive pocos días. |
| `feat/…`, `fix/…`, `docs/…`, `chore/…`, `test/…` | Una por historia o tarea. Se crea desde la rama de release, se integra en ella con una PR y se borra al fusionar. |
| Etiqueta `vX.Y.Z` | Marca el momento exacto de una release. Se crea sobre `main` tras la promoción, junto con su Release en GitHub. |

**Nombres.** La rama de release no lleva la `v` (`release/X.Y.Z`); la etiqueta sí (`vX.Y.Z`). Las ramas de trabajo siguen el tipo del commit y el identificador del issue: `feat/us-07-tarifas-en-fichero`, `fix/redondeo-total`, `docs/guia-de-trabajo`.

## 2. Ciclo de una funcionalidad

1. Actualizar la rama de release y crear la rama de trabajo desde ella.
2. Desarrollar con **TDD**: test en rojo, código mínimo en verde y refactor.
3. Antes de abrir la PR: `python -m pytest` y `python -m ruff check src tests` sin fallos.
4. Abrir una PR **hacia la rama de release** (no hacia `main`) y enlazar el issue con `Refs #n`.
5. Fusionar con **rebase** para conservar los commits del ciclo TDD y borrar la rama.

## 3. Cierre de issues y tablero

GitHub solo cierra un issue por `Closes #n` cuando la PR llega a la **rama por defecto** (`main`). Por eso:

- En las PR hacia la rama de release se usa `Refs #n`. El issue sigue abierto.
- Durante la fase, la tarjeta del tablero se mueve a mano (*In progress*, *In review*).
- Todos los `Closes #n` de la fase van en la **PR de promoción a `main`**, que los cierra a la vez y deja las tarjetas en *Done*.

## 4. Commits

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

## 5. Cerrar una fase: promoción a `main`

1. La rama de release contiene todas las funcionalidades de la fase y sus pruebas pasan.
2. En un último commit de la rama: subir `version` en `pyproject.toml` y actualizar la tabla de versiones del [README](README.md#versionado).
3. Hacer la **demo** desde la rama de release.
4. Abrir una PR `release/X.Y.Z` → `main` con la plantilla de release (`?template=release.md`), que lista los `Closes #n`.
5. Fusionar con **"Create a merge commit"**, o con un *fast-forward*: así `main` conserva los mismos commits que la rama de release.
6. Crear la etiqueta `vX.Y.Z` sobre `main` y su Release en GitHub.
7. Borrar la rama de release y registrar la demo y la entrega en la hoja *Fases* del backlog.

## 6. Correcciones urgentes

Si aparece un error en lo ya entregado:

1. Rama `fix/…` desde `main` y PR hacia `main`.
2. Etiqueta `vX.Y.Z+1` (el tercer número) con su Release.
3. Traer el cambio a la rama de release activa con un `merge` de `main`, para que no se desincronicen.

## 7. Versiones

El criterio y el estado de las versiones están **solo** en el [README](README.md#versionado), y el número, en `pyproject.toml`. No se repiten en otros ficheros.

## 8. Configuración recomendada del repositorio

En *Settings* de GitHub:

- **Proteger `main`**: exigir PR y prohibir *force push*, para que solo avance por la promoción.
- **Automatically delete head branches**: borra la rama al fusionar su PR.
