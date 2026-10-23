"""Installed wind and solar capacity in Germany, monthly, from Energy-Charts (Fraunhofer ISE).

API: https://api.energy-charts.info/installed_power?country=de&time_step=monthly (GW, CC BY 4.0).
The models predict capacity factors (generation / installed capacity), so the fleet growth over
the sample (solar +40%) does not have to be learnt from the weather.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

URL = "https://api.energy-charts.info/installed_power"
NAMES = {"onshore": "Wind onshore", "offshore": "Wind offshore", "solar": "Solar AC"}


def load_monthly(cache: Path) -> pd.DataFrame:
    """Monthly capacity in MW, indexed by the first day of the month (UTC)."""
    if cache.exists():
        doc = json.loads(cache.read_text(encoding="utf-8"))
    else:
        r = requests.get(URL, params={"country": "de", "time_step": "monthly", "installation_decommission": "false"}, timeout=60)
        r.raise_for_status()
        doc = r.json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(doc), encoding="utf-8")
    idx = pd.to_datetime(doc["time"], format="%m.%Y").tz_localize("UTC")
    by_name = {p["name"]: p["data"] for p in doc["production_types"]}
    return pd.DataFrame({k: pd.Series(by_name[v], index=idx, dtype=float) * 1000.0 for k, v in NAMES.items()})


def hourly(monthly: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Capacity on each hour of `index`: the month-end value, linearly interpolated between month ends.

    A monthly figure is taken to hold at the end of its month (the stock after that month's additions).
    """
    m = monthly.copy()
    m.index = m.index + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23)
    grid = m.reindex(m.index.union(index)).interpolate(method="time").ffill().bfill()
    return grid.reindex(index)
