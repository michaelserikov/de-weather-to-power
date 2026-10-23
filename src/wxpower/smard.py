"""Hourly generation, TSO day-ahead forecasts and prices from SMARD (Bundesnetzagentur), cached on disk.

  index:  https://www.smard.de/app/chart_data/{filter}/{region}/index_hour.json
  chunk:  https://www.smard.de/app/chart_data/{filter}/{region}/{filter}_{region}_hour_{ts}.json
Timestamps are ms since the epoch (UTC) and label the start of the hour; generation in MWh per hour.
Data licence: CC BY 4.0, Bundesnetzagentur | SMARD.de.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.smard.de/app/chart_data"
REGION = "DE-LU"

SERIES = {
    "onshore": 4067,      # actual generation, wind onshore
    "offshore": 1225,     # actual generation, wind offshore
    "solar": 4068,        # actual generation, photovoltaics
    "onshore_tso": 123,   # TSO day-ahead forecast, wind onshore
    "offshore_tso": 3791, # TSO day-ahead forecast, wind offshore
    "solar_tso": 125,     # TSO day-ahead forecast, photovoltaics
    "price": 4169,        # day-ahead price DE-LU, EUR/MWh
}

_session = requests.Session()
_session.headers["User-Agent"] = "de-weather-to-power (research; github.com/michaelserikov/de-weather-to-power)"


def _get_json(url: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        r = _session.get(url, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
    raise RuntimeError(f"failed: {url}")


def parse_chunk(doc: dict) -> pd.DataFrame:
    rows = [(t, v) for t, v in doc.get("series", []) if v is not None]
    df = pd.DataFrame(rows, columns=["ts_ms", "value"])
    df["ts_utc"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)
    return df[["ts_utc", "value"]]


def load_series(name: str, start: str, end: str, cache_dir: Path) -> pd.Series:
    """Hourly series between start and end (inclusive dates, UTC); full past weeks are cached."""
    fid = SERIES[name]
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    week = pd.Timedelta(days=7)
    folder = cache_dir / f"{fid}_{REGION}"
    folder.mkdir(parents=True, exist_ok=True)
    frames = []
    for ts in _get_json(f"{BASE}/{fid}/{REGION}/index_hour.json")["timestamps"]:
        t0 = pd.Timestamp(ts, unit="ms", tz="UTC")
        if t0 + week <= start_ts or t0 >= end_ts:
            continue
        path = folder / f"{ts}.json"
        if path.exists():
            doc = json.loads(path.read_text(encoding="utf-8"))
        else:
            doc = _get_json(f"{BASE}/{fid}/{REGION}/{fid}_{REGION}_hour_{ts}.json")
            if t0 + week < pd.Timestamp.now(tz="UTC"):
                path.write_text(json.dumps(doc), encoding="utf-8")
            time.sleep(0.2)
        frames.append(parse_chunk(doc))
    df = pd.concat(frames, ignore_index=True).drop_duplicates("ts_utc")
    df = df[(df["ts_utc"] >= start_ts) & (df["ts_utc"] < end_ts)]
    return df.set_index("ts_utc")["value"].sort_index().rename(name)


def load_all(start: str, end: str, cache_dir: Path) -> pd.DataFrame:
    return pd.concat([load_series(n, start, end, cache_dir) for n in SERIES], axis=1)
