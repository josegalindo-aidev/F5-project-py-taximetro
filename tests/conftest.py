# Proyecto: py-taximetro
# fuente: tests/conftest.py
from decimal import Decimal

import pytest

from taximetro.core.tariff import Tariff


@pytest.fixture
def tariff() -> Tariff:
    """Tarifa oficial del enunciado (Zona EMT Madrid, junio 2025)."""
    return Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))
