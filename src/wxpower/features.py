"""Physical features from point weather: wind at hub height through a generic power curve, PV output.

All functions take wide frames (one column per point) and return frames of the same shape,
so the models can learn a weight per point.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HUB_ONSHORE = 135.0   # m, typical hub height of the turbines added in the 2020s
HUB_OFFSHORE = 110.0  # m


def shear_exponent(ws100: pd.DataFrame, ws10: pd.DataFrame) -> pd.DataFrame:
    """Power-law shear exponent from 10 m and 100 m wind, clipped to a plausible range."""
    with np.errstate(divide="ignore", invalid="ignore"):
        a = np.log(ws100 / ws10) / np.log(10.0)
    return a.where(np.isfinite(a), 1 / 7).clip(0.05, 0.45)


def hub_wind(ws100: pd.DataFrame, ws10: pd.DataFrame, hub: float) -> pd.DataFrame:
    """Wind speed at hub height from the 100 m wind and the local shear."""
    return ws100 * (hub / 100.0) ** shear_exponent(ws100, ws10)


def power_curve(v, cut_in: float = 3.0, rated: float = 11.5, cut_out: float = 25.0):
    """Generic turbine power curve as a capacity factor (0-1): cubic between cut-in and rated speed."""
    v = np.asarray(v, dtype=float)
    cf = (v**3 - cut_in**3) / (rated**3 - cut_in**3)
    cf = np.where(v < cut_in, 0.0, np.where(v >= rated, 1.0, cf))
    return np.where(v >= cut_out, 0.0, cf)


def pv_output(ghi: pd.DataFrame, t2m: pd.DataFrame, gamma: float = -0.004, k: float = 0.03) -> pd.DataFrame:
    """Relative PV output: irradiance times a cell-temperature efficiency factor.

    Cell temperature is approximated as T2m + k * GHI (about +30 K at 1000 W/m2); efficiency
    changes by gamma per kelvin above 25 C.
    """
    t_cell = t2m + k * ghi
    return (ghi / 1000.0) * (1.0 + gamma * (t_cell - 25.0))


# Nationwide public holidays in Germany (low demand; with sun and wind, prices turn negative and
# plants are curtailed).
HOLIDAYS = pd.to_datetime([
    "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-01", "2024-05-09", "2024-05-20", "2024-10-03", "2024-12-25", "2024-12-26",
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-29", "2025-06-09", "2025-10-03", "2025-12-25", "2025-12-26",
    "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-10-03", "2026-12-25", "2026-12-26",
]).date


def day_type(index: pd.DatetimeIndex) -> pd.Series:
    """0 working day, 1 Saturday, 2 Sunday or public holiday (local date in Germany)."""
    local = index.tz_convert("Europe/Berlin")
    t = np.where(local.dayofweek == 5, 1, 0)
    t = np.where((local.dayofweek == 6) | np.isin(local.date, HOLIDAYS), 2, t)
    return pd.Series(t, index=index, name="day_type")


def calendar(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Hour of day and day of year as cyclic terms (UTC), and the day type."""
    h = index.hour + index.minute / 60.0
    d = index.day_of_year
    return pd.DataFrame(
        {"hour_sin": np.sin(2 * np.pi * h / 24), "hour_cos": np.cos(2 * np.pi * h / 24),
         "doy_sin": np.sin(2 * np.pi * d / 365.25), "doy_cos": np.cos(2 * np.pi * d / 365.25),
         "day_type": day_type(index).values},
        index=index,
    )


def build(weather: dict[str, pd.DataFrame], tech: str, onshore: list[str], offshore: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Feature matrices for one technology.

    weather: variable name -> wide frame (index hour, column point), already aligned to SMARD hours.
    Returns (physical, full): `physical` holds one physically transformed column per point
    (power-curve capacity factor or PV output), used by the linear model; `full` adds the hub
    wind or irradiance itself, national means and calendar terms, used by the nonlinear models.
    """
    if tech in ("onshore", "offshore"):
        pts = onshore if tech == "onshore" else offshore
        hub = HUB_ONSHORE if tech == "onshore" else HUB_OFFSHORE
        v = hub_wind(weather["wind_speed_100m"][pts], weather["wind_speed_10m"][pts], hub)
        phys = pd.DataFrame(power_curve(v), index=v.index, columns=[f"pc_{c}" for c in pts])
        extra = v.add_prefix("v_")
        extra["v_mean"] = v.mean(axis=1)
        extra["v_std"] = v.std(axis=1)
        # Expected solar: with day type and hour, lets the model learn curtailment in sunny, low-demand hours.
        extra["pv_mean"] = pv_output(weather["shortwave_radiation"][onshore], weather["temperature_2m"][onshore]).mean(axis=1)
    elif tech == "solar":
        pts = onshore
        ghi = weather["shortwave_radiation"][pts]
        phys = pv_output(ghi, weather["temperature_2m"][pts]).add_prefix("pv_")
        direct = weather["direct_radiation"][pts]
        extra = pd.DataFrame(index=ghi.index)
        extra["ghi_mean"] = ghi.mean(axis=1)
        extra["direct_frac"] = (direct.sum(axis=1) / ghi.sum(axis=1).replace(0, np.nan)).fillna(0.0)
        extra["t2m_mean"] = weather["temperature_2m"][pts].mean(axis=1)
        # Expected onshore wind output: high wind and sun together drive prices negative.
        v_on = hub_wind(weather["wind_speed_100m"][pts], weather["wind_speed_10m"][pts], HUB_ONSHORE)
        extra["wind_cf_mean"] = power_curve(v_on).mean(axis=1)
    else:
        raise ValueError(tech)
    full = pd.concat([phys, extra, calendar(phys.index)], axis=1)
    return phys, full
