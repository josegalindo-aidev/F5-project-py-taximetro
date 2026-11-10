"""Formato de importes para la consola."""

from decimal import ROUND_HALF_UP, Decimal


def format_euros(amount: Decimal) -> str:
    """Formatea con dos decimales y coma decimal: Decimal('0.7') -> '0,70 €'."""
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}".replace(".", ",") + " €"
