import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from bacnet_logger import BAC0Source, Point, SimulatedSource, load_points, log_points
from bacnet_logger.__main__ import main

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "points.json"
START = datetime(2026, 7, 1, 6, 0)
SAT = Point("A.SAT", "analogInput", 1, "degF", base=60, amplitude=3, noise=0.5)
FAN = Point("A.FAN", "binaryInput", 1)


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_simulator_is_deterministic_for_a_seed():
    a, b = SimulatedSource(7), SimulatedSource(7)
    assert [a.read(SAT, START) for _ in range(5)] == [b.read(SAT, START) for _ in range(5)]


def test_simulator_seeds_differ():
    assert SimulatedSource(1).read(SAT, START) != SimulatedSource(2).read(SAT, START)


def test_analog_value_stays_near_base():
    source = SimulatedSource(3)
    values = [source.read(SAT, datetime(2026, 7, 1, h)) for h in range(24)]
    assert all(55 < v < 65 for v in values)


def test_binary_follows_occupied_hours():
    source = SimulatedSource()
    assert source.read(FAN, datetime(2026, 7, 1, 6, 59)) is False
    assert source.read(FAN, datetime(2026, 7, 1, 7, 0)) is True
    assert source.read(FAN, datetime(2026, 7, 1, 18, 0)) is False


def test_log_points_writes_header_and_rows(tmp_path):
    out = tmp_path / "log.csv"
    count = log_points(SimulatedSource(1), [SAT, FAN], out, START, 3, 600)
    rows = read_rows(out)
    assert count == 6 == len(rows)
    assert list(rows[0]) == ["timestamp", "point", "value", "units"]
    assert rows[2]["timestamp"] == "2026-07-01T06:10:00"


def test_log_points_sleeps_between_rounds_only(tmp_path):
    waits: list[float] = []
    log_points(SimulatedSource(), [SAT], tmp_path / "l.csv", START, 3, 30, waits.append)
    assert waits == [30, 30]


def test_log_points_rejects_bad_counts(tmp_path):
    with pytest.raises(ValueError):
        log_points(SimulatedSource(), [SAT], tmp_path / "l.csv", START, 0, 60)
    with pytest.raises(ValueError):
        log_points(SimulatedSource(), [SAT], tmp_path / "l.csv", START, 1, 0)


def test_failed_read_is_logged_as_empty(tmp_path):
    class Broken:
        def read(self, point, when):
            raise TimeoutError("no reply")

    out = tmp_path / "l.csv"
    assert log_points(Broken(), [SAT], out, START, 2, 60) == 2
    assert [r["value"] for r in read_rows(out)] == ["", ""]


def test_bac0_adapter_builds_read_string_and_converts():
    calls = []

    class FakeBacnet:
        def read(self, request):
            calls.append(request)
            return "active" if "binaryInput" in request else "61.5"

    source = BAC0Source(FakeBacnet(), "10.0.0.5")
    assert source.read(SAT, START) == 61.5
    assert source.read(FAN, START) is True
    assert calls[0] == "10.0.0.5 analogInput 1 presentValue"


def test_load_points_example():
    points = load_points(EXAMPLE)
    assert len(points) == 4 and points[3].is_binary


@pytest.mark.parametrize(
    "content",
    ["[]", "{}", '[{"name": "x"}]', '[{"name": "x", "object_type": "foo", "instance": 1}]',
     '[{"name": "x", "object_type": "analogInput", "instance": 1},'
     ' {"name": "x", "object_type": "analogInput", "instance": 2}]'],
)
def test_load_points_rejects_bad_files(tmp_path, content):
    path = tmp_path / "p.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_points(path)


def test_cli_success_and_failure(tmp_path, capsys):
    out = tmp_path / "o.csv"
    assert main(["--points", str(EXAMPLE), "--out", str(out), "--samples", "2"]) == 0
    assert len(read_rows(out)) == 8
    assert "wrote 8 rows" in capsys.readouterr().out
    assert main(["--points", str(tmp_path / "none.json"), "--out", str(out)]) == 2


def test_points_file_is_valid_json():
    assert isinstance(json.loads(EXAMPLE.read_text(encoding="utf-8")), list)
