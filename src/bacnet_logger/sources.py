"""Value sources: a deterministic simulator and a thin BAC0 adapter."""

from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Any, Protocol

from .points import Point


class Source(Protocol):
    """Anything that can return the present value of a point at a time."""

    def read(self, point: Point, when: datetime) -> float | bool: ...


class SimulatedSource:
    """Daily sine cycle plus Gaussian noise. Binary points are on from 07:00 to 18:00."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def read(self, point: Point, when: datetime) -> float | bool:
        """Return a simulated present value."""
        hour = when.hour + when.minute / 60
        if point.is_binary:
            return 7 <= hour < 18
        cycle = math.sin(2 * math.pi * (hour - 9) / 24)
        return round(point.base + point.amplitude * cycle + self._rng.gauss(0, point.noise), 2)


class BAC0Source:
    """Reads present values through an already connected BAC0 object.

    Pass the object returned by BAC0.lite() and the device address, for example
    "192.168.1.50". Each read issues "<address> <objectType> <instance> presentValue".
    This adapter is covered by tests that use a stand-in object, not a live device.
    """

    def __init__(self, bacnet: Any, address: str) -> None:
        self._bacnet = bacnet
        self._address = address

    def read(self, point: Point, when: datetime) -> float | bool:
        """Read one present value from the device."""
        value = self._bacnet.read(
            f"{self._address} {point.object_type} {point.instance} presentValue"
        )
        if point.is_binary:
            return str(value).lower() in {"active", "true", "1"}
        return float(value)
