# Proyecto: py-taximetro
# fuente: tests/conftest.py
from decimal import Decimal

import pytest

from taximetro.core.tariff import Tariff


@pytest.fixture(autouse=True)
def isolated_log_dir(tmp_path, monkeypatch) -> None:
    """Ningún test escribe logs en la carpeta `logs/` del proyecto."""
    monkeypatch.setenv("TAXIMETRO_LOG_DIR", str(tmp_path / "logs-de-prueba"))


@pytest.fixture
def tariff() -> Tariff:
    """Tarifa oficial del enunciado (Zona EMT Madrid, junio 2025)."""
    return Tariff(stopped=Decimal("0.02"), moving=Decimal("0.05"))
