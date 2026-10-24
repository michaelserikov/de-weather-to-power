"""Hourly weather from Open-Meteo, cached per point on disk.

Three sources for the same variables:
  era5:  ERA5 reanalysis (archive API), the best estimate of the weather that actually happened
  icon:  DWD ICON forecasts issued about one day before the valid hour (previous-runs API,
         suffix _previous_day1), i.e. the information a day-ahead forecaster had
  ecmwf: ECMWF IFS (0.25 degree) forecasts issued one day before, same API (archive from mid-March 2024)
  aifs:  ECMWF AIFS Single (0.25 degree), ECMWF's machine-learning forecast model, issued one day before,
         same API (archive from 18 February 2025; native output every 6 hours, interpolated to hours by Open-Meteo)
Data: Open-Meteo.com, CC BY 4.0 (ERA5: Copernicus Climate Change Service; ICON: Deutscher Wetterdienst; IFS, AIFS: ECMWF).
Times are UTC. Wind in m/s. Radiation is the mean over the preceding hour; wind and temperature
are instantaneous values at the full hour.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

VARIABLES = ["wind_speed_100m", "wind_speed_10m", "shortwave_radiation", "direct_radiation", "temperature_2m"]

ENDPOINTS = {
    "era5": ("https://archive-api.open-meteo.com/v1/archive", {"models": "era5"}, ""),
    "icon": ("https://previous-runs-api.open-meteo.com/v1/forecast", {"models": "icon_seamless"}, "_previous_day1"),
    "ecmwf": ("https://previous-runs-api.open-meteo.com/v1/forecast", {"models": "ecmwf_ifs025"}, "_previous_day1"),
    "aifs": ("https://previous-runs-api.open-meteo.com/v1/forecast", {"models": "ecmwf_aifs025_single"}, "_previous_day1"),
}

_session = requests.Session()
_session.headers["User-Agent"] = "de-weather-to-power (research; github.com/michaelserikov/de-weather-to-power)"


def _get(url: str, params: dict, retries: int = 6) -> dict:
    for attempt in range(retries):
        try:
            r = _session.get(url, params=params, timeout=120)
            if r.status_code == 200:
                return r.json()
        except (requests.ConnectionError, requests.Timeout, ValueError):  # dropped connection or non-JSON body
            time.sleep(30)
            continue
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(min(60 * (attempt + 1), 300) if r.status_code == 429 else 2 ** attempt)
            continue
        raise RuntimeError(f"{r.status_code} {r.text[:200]}")
    raise RuntimeError(f"failed: {url}")


def parse(doc: dict, suffix: str) -> pd.DataFrame:
    """API document to a frame indexed by UTC time with the plain variable names."""
    h = doc["hourly"]
    df = pd.DataFrame({v: h.get(v + suffix) for v in VARIABLES})
    df.index = pd.to_datetime(h["time"], utc=True)
    df.index.name = "ts_utc"
    return df.astype(float)


def load_point(source: str, name: str, lat: float, lon: float, start: str, end: str, cache_dir: Path) -> pd.DataFrame:
    """Hourly weather at one point; downloaded once, then read from cache_dir/<source>/<name>.csv."""
    path = cache_dir / source / f"{name}.csv"
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
    url, extra, suffix = ENDPOINTS[source]
    params = {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "hourly": ",".join(v + suffix for v in VARIABLES), "timezone": "UTC", "wind_speed_unit": "ms", **extra,
    }
    df = parse(_get(url, params), suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def to_interval_means(df: pd.DataFrame) -> pd.DataFrame:
    """Align weather with SMARD hours, which are labelled by their start (hour [t, t+1)).

    Radiation labelled t+1 is already the mean over [t, t+1); instantaneous variables are
    averaged over the two ends of the hour.
    """
    out = pd.DataFrame(index=df.index)
    for c in df.columns:
        if "radiation" in c:
            out[c] = df[c].shift(-1)
        else:
            out[c] = 0.5 * (df[c] + df[c].shift(-1))
    return out
