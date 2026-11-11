# Proyecto: py-taximetro
# fuente: src/taximetro/core/errors.py
"""Errores del dominio."""

from decimal import Decimal


class TaximetroError(Exception):
    """Base de todos los errores del taxímetro."""


class InvalidTariff(TaximetroError):
    """La tarifa no es válida (valores negativos o no numéricos)."""


class TripNotStarted(TaximetroError):
    """Se intentó operar sobre una carrera que no ha comenzado."""


class TripAlreadyStarted(TaximetroError):
    """Se intentó iniciar una carrera ya iniciada."""


class TripAlreadyFinished(TaximetroError):
    """Se intentó operar sobre una carrera ya finalizada."""


class InvalidTimestamp(TaximetroError):
    """El instante recibido es anterior al último registrado."""


class TariffFileError(TaximetroError):
    """No se pudieron cargar las tarifas desde su fichero de configuración."""


class InvalidTripRecord(TaximetroError):
    """La carrera no se puede guardar en el historial (sin terminar o sin fechas)."""


class TripNotSaved(TaximetroError):
    """La carrera se cobró, pero no se pudo guardar en el historial."""

    def __init__(self, total: Decimal, reason: str = "") -> None:
        super().__init__(f"No se pudo guardar la carrera en el historial: {reason}")
        self.total = total
