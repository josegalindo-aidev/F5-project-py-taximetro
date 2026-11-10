# Proyecto: py-taximetro
# fuente: src/taximetro/core/state.py
"""Estados posibles del taxi durante una carrera."""

from enum import Enum


class State(Enum):
    STOPPED = "stopped"
    MOVING = "moving"
