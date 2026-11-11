# Proyecto: py-taximetro
# fuente: src/taximetro/ui/cli/app.py
"""Interfaz de línea de comandos del taxímetro (Fase 1 - MVP)."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from taximetro.core.errors import (
    InvalidTimestamp,
    TaximetroError,
    TripAlreadyFinished,
    TripAlreadyStarted,
    TripNotSaved,
    TripNotStarted,
)
from taximetro.core.state import State
from taximetro.core.trip_service import TripService
from taximetro.ui.cli.format import format_euros

HELP = """Comandos disponibles:
  iniciar    Inicia una carrera (el taxi empieza parado)
  parar      El taxi está parado
  mover      El taxi está en movimiento
  estado     Muestra el estado y el importe actual
  finalizar  Termina la carrera y muestra el total
  ayuda      Muestra esta ayuda
  salir      Cierra el programa"""

ERRORS: dict[type[TaximetroError], str] = {
    TripNotStarted: "No hay ninguna carrera en curso. Usa 'iniciar'.",
    TripAlreadyStarted: "Ya hay una carrera en curso. Usa 'finalizar' antes de iniciar otra.",
    TripAlreadyFinished: "La carrera ya está finalizada.",
    InvalidTimestamp: "El reloj retrocedió; no se puede continuar la carrera.",
}

STATE_LABEL = {State.STOPPED: "parado", State.MOVING: "en movimiento"}


class Cli:
    def __init__(
        self,
        service: TripService,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        notes: Sequence[str] = (),
    ) -> None:
        self._service = service
        self._input = input_fn
        self._print = output_fn
        self._notes = notes
        self._commands: dict[str, Callable[[], None]] = {
            "iniciar": self._start,
            "parar": lambda: self._set_state(State.STOPPED),
            "mover": lambda: self._set_state(State.MOVING),
            "estado": self._status,
            "finalizar": self._finish,
            "ayuda": lambda: self._print(HELP),
        }

    def run(self) -> None:
        self._print("Taxímetro digital TTX-247")
        for note in self._notes:
            self._print(note)
        self._print(HELP)
        while True:
            try:
                line = self._input("> ")
            except (EOFError, KeyboardInterrupt):
                break
            command = line.strip().lower()
            if not command:
                continue
            if command == "salir":
                break
            self._dispatch(command)
        self._goodbye()

    def _dispatch(self, command: str) -> None:
        handler = self._commands.get(command)
        if handler is None:
            self._print(f"Comando desconocido: '{command}'. Escribe 'ayuda'.")
            return
        try:
            handler()
        except TaximetroError as error:
            self._print(ERRORS.get(type(error), str(error) or "Operación no válida."))

    def _start(self) -> None:
        self._service.start()
        self._print("Carrera iniciada (taxi parado).")

    def _set_state(self, state: State) -> None:
        self._service.set_state(state)
        self._print(f"Estado: {STATE_LABEL[state]}.")

    def _status(self) -> None:
        trip = self._service.active
        if trip is None or trip.state is None:
            self._print(ERRORS[TripNotStarted])
            return
        amount = format_euros(self._service.current_amount())
        self._print(f"Estado: {STATE_LABEL[trip.state]} - Importe actual: {amount}")

    def _finish(self) -> None:
        try:
            total = self._service.finish()
        except TripNotSaved as error:
            self._print(f"Carrera finalizada. Total: {format_euros(error.total)}")
            self._print(f"Aviso: {error}")
            return
        self._print(f"Carrera finalizada. Total: {format_euros(total)}")

    def _goodbye(self) -> None:
        if self._service.active is not None:
            self._print("Aviso: La carrera en curso no se ha cobrado.")
        self._print("Hasta pronto.")
