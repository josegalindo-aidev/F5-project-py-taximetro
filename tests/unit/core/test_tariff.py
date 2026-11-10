from decimal import Decimal

import pytest

from taximetro.core.errors import InvalidTariff
from taximetro.core.tariff import Tariff
from taximetro.core.trip import State


def test_parado_cuesta_002_por_segundo(tariff):
    assert tariff.rate_for(State.STOPPED) == Decimal("0.02")


def test_en_movimiento_cuesta_005_por_segundo(tariff):
    assert tariff.rate_for(State.MOVING) == Decimal("0.05")


@pytest.mark.parametrize(
    ("stopped", "moving"),
    [(Decimal("-0.01"), Decimal("0.05")), (Decimal("0.02"), Decimal("-1"))],
)
def test_tarifa_negativa_es_invalida(stopped, moving):
    with pytest.raises(InvalidTariff):
        Tariff(stopped=stopped, moving=moving)
