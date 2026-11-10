"""Errores del dominio."""


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
