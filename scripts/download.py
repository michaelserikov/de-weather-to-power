"""Download and cache all inputs: SMARD series, installed capacity, ERA5 and ICON day-1 weather at every point."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wxpower import capacity, openmeteo, smard  # noqa: E402
from wxpower.sites import all_sites  # noqa: E402

START, END = "2024-02-20", "2026-09-30"   # ICON day-1 forecasts with 100 m wind start on 20 Feb 2024
RAW = ROOT / "data" / "raw"


def main() -> None:
    df = smard.load_all(START, END, RAW / "smard")
    print("smard", df.shape, df.index.min(), df.index.max(), df.isna().sum().to_dict(), flush=True)
    cap = capacity.load_monthly(RAW / "capacity_energy_charts.json")
    print("capacity", cap.index.min().date(), cap.index.max().date(), flush=True)
    sites = all_sites()
    for source in ("icon", "era5", "ecmwf"):
        for i, s in enumerate(sites.itertuples()):
            cached = (RAW / "weather" / source / f"{s.name}.csv").exists()
            w = openmeteo.load_point(source, s.name, s.lat, s.lon, START, END, RAW / "weather")
            print(source, i + 1, len(sites), s.name, w.shape, int(w.isna().sum().sum()), flush=True)
            if not cached:
                time.sleep(8)  # stay well inside the free API's per-minute limit


if __name__ == "__main__":
    main()
