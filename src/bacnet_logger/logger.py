"""Sample points on a fixed step and write the readings to CSV."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from .points import Point
from .sources import Source

COLUMNS = ["timestamp", "point", "value", "units"]


def log_points(
    source: Source,
    points: list[Point],
    out_path: str | Path,
    start: datetime,
    samples: int,
    interval_s: int,
    sleep: Callable[[float], None] | None = None,
) -> int:
    """Write `samples` rounds of readings to `out_path` and return the number of rows.

    Timestamps advance by `interval_s` from `start`. Pass `sleep=time.sleep` to wait
    the interval between rounds, as a live logger would. A point that raises while
    being read is logged with an empty value and the run continues.
    """
    if samples < 1 or interval_s < 1:
        raise ValueError("samples and interval must be at least 1")
    rows = 0
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for step in range(samples):
            when = start + timedelta(seconds=step * interval_s)
            for point in points:
                try:
                    value = source.read(point, when)
                except Exception:  # a failed read must not stop the run
                    value = ""
                writer.writerow([when.isoformat(), point.name, value, point.units])
                rows += 1
            if sleep and step < samples - 1:
                sleep(interval_s)
    return rows

