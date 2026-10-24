"""Imbalance prices (reBAP) and the intraday price index ID-AEP from the TSOs' netztransparenz.de WebAPI, cached on disk.

  token:  https://identity.netztransparenz.de/users/connect/token   (OAuth 2.0, grant type client_credentials)
  reBAP:  https://ds.netztransparenz.de/api/v1/data/NrvSaldo/reBAP/Qualitaetsgesichert/{from}/{to}
  ID-AEP: https://ds.netztransparenz.de/api/v1/data/IdAep/{from}/{to}
Free credentials from the WebAPI portal (https://api-portal.netztransparenz.de), read from the environment
variables NTP_CLIENT_ID and NTP_CLIENT_SECRET. Values are quarter-hourly in EUR/MWh, times requested in UTC.

reBAP is the uniform German imbalance price. Since 2022 it is published as two prices: "unterdeckt" applies
to a balance group that is short (it pays), "ueberdeckt" to one that is long (it is paid); they differ only
when a surcharge applies. ID-AEP is the volume-weighted price of intraday trades in each quarter hour.
"""

from __future__ import annotations

import io
import os
import time
from pathlib import Path

import pandas as pd
import requests

TOKEN_URL = "https://identity.netztransparenz.de/users/connect/token"
BASE = "https://ds.netztransparenz.de/api/v1/data"
PATHS = {"rebap": "NrvSaldo/reBAP/Qualitaetsgesichert", "idaep": "IdAep"}

_session = requests.Session()
_session.headers["User-Agent"] = "de-weather-to-power (research; github.com/michaelserikov/de-weather-to-power)"
_token: dict = {}


def _bearer() -> str:
    if _token.get("expires", 0) < time.time() + 60:
        cid, secret = os.environ.get("NTP_CLIENT_ID"), os.environ.get("NTP_CLIENT_SECRET")
        if not cid or not secret:
            raise RuntimeError("set NTP_CLIENT_ID and NTP_CLIENT_SECRET (free WebAPI client from api-portal.netztransparenz.de)")
        r = _session.post(TOKEN_URL, data={"grant_type": "client_credentials", "client_id": cid, "client_secret": secret},
                          timeout=30)
        r.raise_for_status()
        doc = r.json()
        _token.update(value=doc["access_token"], expires=time.time() + doc.get("expires_in", 3600))
    return _token["value"]


def _get_csv(url: str, retries: int = 4) -> str:
    for attempt in range(retries):
        r = _session.get(url, headers={"Authorization": f"Bearer {_bearer()}"}, timeout=120)
        if r.status_code == 200:
            return r.content.decode("utf-8-sig")
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(2 ** attempt * 5)
            continue
        raise RuntimeError(f"{r.status_code} {url} {r.text[:200]}")
    raise RuntimeError(f"failed: {url}")


def _number(s: pd.Series) -> pd.Series:
    """German number format: '1.234,56' -> 1234.56; empty -> NaN."""
    return pd.to_numeric(s.astype(str).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                         errors="coerce")


def parse_rebap(text: str) -> pd.DataFrame:
    """Format 9: Datum;Zeitzone;von;bis;...;reBAP unterdeckt;reBAP ueberdeckt -> columns short, long by quarter start (UTC)."""
    df = pd.read_csv(io.StringIO(text), sep=";", dtype=str)
    if df.empty:
        return pd.DataFrame(columns=["short", "long"], index=pd.DatetimeIndex([], tz="UTC"))
    assert (df["Zeitzone"].str.upper() == "UTC").all(), "request the data in UTC"
    idx = pd.to_datetime(df["Datum"] + " " + df["von"], format="%d.%m.%Y %H:%M", utc=True)
    short = [c for c in df.columns if "unterdeckt" in c.lower()][0]
    long_ = [c for c in df.columns if "berdeckt" in c.lower() and c != short][0]
    out = pd.DataFrame({"short": _number(df[short]).values, "long": _number(df[long_]).values}, index=idx)
    return out[~out.index.duplicated()].sort_index()


def parse_idaep(text: str) -> pd.Series:
    """Format 13: Datum von;(Uhrzeit) von;Zeitzone;(Uhrzeit) bis;Zeitzone;ID AEP in EUR/MWh -> series by quarter start (UTC)."""
    df = pd.read_csv(io.StringIO(text), sep=";", dtype=str)
    if df.empty:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"), name="idaep")
    cols = list(df.columns)
    idx = pd.to_datetime(df[cols[0]] + " " + df[cols[1]], format="%Y-%m-%d %H:%M", utc=True)
    s = pd.Series(_number(df[cols[-1]]).values, index=idx, name="idaep")
    return s[~s.index.duplicated()].sort_index()


def load(name: str, start: str, end: str, cache_dir: Path) -> list[str]:
    """Raw CSV text for every month between start and end, one cached file per month (past months only)."""
    folder = cache_dir / name
    folder.mkdir(parents=True, exist_ok=True)
    parts = []
    for m0 in pd.date_range(pd.Timestamp(start).replace(day=1), end, freq="MS"):
        m1 = m0 + pd.offsets.MonthBegin(1)
        path = folder / f"{m0:%Y-%m}.csv"
        if path.exists():
            text = path.read_text(encoding="utf-8")
        else:
            text = _get_csv(f"{BASE}/{PATHS[name]}/{m0:%Y-%m-%dT%H:%M:%S}/{m1:%Y-%m-%dT%H:%M:%S}")
            if m1 < pd.Timestamp.now():
                path.write_text(text, encoding="utf-8")
            time.sleep(1)
        parts.append(text)
    return parts


def hourly(start: str, end: str, cache_dir: Path) -> pd.DataFrame:
    """Hourly means of reBAP (short, long) and ID-AEP, indexed by hour start (UTC) like SMARD."""
    rebap = pd.concat([parse_rebap(t) for t in load("rebap", start, end, cache_dir)])
    idaep = pd.concat([parse_idaep(t) for t in load("idaep", start, end, cache_dir)])
    q = pd.concat([rebap[~rebap.index.duplicated()], idaep[~idaep.index.duplicated()]], axis=1)
    h = q.resample("h").mean()
    h["quarters"] = q["short"].resample("h").count()
    return h
