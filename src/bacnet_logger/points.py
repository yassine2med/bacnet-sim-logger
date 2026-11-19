"""Point definitions loaded from a JSON file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

OBJECT_TYPES = {"analogInput", "analogOutput", "analogValue", "binaryInput", "binaryOutput", "binaryValue"}


@dataclass(frozen=True)
class Point:
    """One BACnet object to log. base, amplitude and noise only drive the simulator."""

    name: str
    object_type: str
    instance: int
    units: str = ""
    base: float = 0.0
    amplitude: float = 0.0
    noise: float = 0.0

    @property
    def is_binary(self) -> bool:
        """True for binary object types."""
        return self.object_type.startswith("binary")


def load_points(path: str | Path) -> list[Point]:
    """Load points from a JSON list. Raises ValueError on a bad entry."""
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, list) or not raw:
        raise ValueError("points file must hold a non-empty JSON list")
    points = []
    for entry in raw:
        try:
            point = Point(**entry)
        except TypeError as err:
            raise ValueError(f"bad point entry {entry!r}: {err}") from err
        if point.object_type not in OBJECT_TYPES:
            raise ValueError(f"{point.name}: unknown object type '{point.object_type}'")
        points.append(point)
    names = [p.name for p in points]
    if len(set(names)) != len(names):
        raise ValueError("point names must be unique")
    return points
