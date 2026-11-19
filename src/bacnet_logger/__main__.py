"""Command line entry: python -m bacnet_logger --points FILE.json --out FILE.csv"""

import argparse
import sys
import time
from datetime import datetime

from .logger import log_points
from .points import load_points
from .sources import SimulatedSource


def main(argv: list[str] | None = None) -> int:
    """Run the simulator source and write a CSV. Returns 0 on success, 2 on bad input."""
    parser = argparse.ArgumentParser(prog="bacnet_logger", description="Log simulated BACnet points to CSV.")
    parser.add_argument("--points", required=True, help="JSON file of point definitions")
    parser.add_argument("--out", required=True, help="CSV file to write")
    parser.add_argument("--samples", type=int, default=6, help="number of rounds")
    parser.add_argument("--interval", type=int, default=600, help="seconds between rounds")
    parser.add_argument("--start", default="2026-07-01T06:00", help="first timestamp (ISO)")
    parser.add_argument("--seed", type=int, default=1, help="simulator seed")
    parser.add_argument("--live", action="store_true", help="really wait between rounds")
    args = parser.parse_args(argv)
    try:
        points = load_points(args.points)
        rows = log_points(
            SimulatedSource(args.seed), points, args.out, datetime.fromisoformat(args.start),
            args.samples, args.interval, time.sleep if args.live else None,
        )
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"wrote {rows} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
