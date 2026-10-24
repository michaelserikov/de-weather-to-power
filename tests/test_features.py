import numpy as np
import pandas as pd

from wxpower import capacity, features, openmeteo
from wxpower.sites import all_sites, onshore_grid


def test_power_curve_shape():
    v = np.array([0, 2.9, 3.0, 7.0, 11.5, 20.0, 25.0, 30.0])
    cf = features.power_curve(v)
    assert cf[0] == 0 and cf[1] == 0 and cf[2] == 0
    assert 0 < cf[3] < 1
    assert cf[4] == 1 and cf[5] == 1
    assert cf[6] == 0 and cf[7] == 0  # cut-out
    assert np.all(np.diff(features.power_curve(np.linspace(3, 11.5, 50))) > 0)


def test_hub_wind_uses_local_shear():
    idx = pd.date_range("2025-01-01", periods=3, freq="h", tz="UTC")
    ws100 = pd.DataFrame({"a": [10.0, 10.0, 10.0]}, index=idx)
    ws10 = pd.DataFrame({"a": [10 / 10**0.2, 10.0, 0.0]}, index=idx)  # alpha 0.2, then 0 -> clipped, then undefined
    v = features.hub_wind(ws100, ws10, 135.0)["a"].values
    assert np.isclose(v[0], 10 * 1.35**0.2)
    assert np.isclose(v[1], 10 * 1.35**0.05)
    assert np.isfinite(v[2])


def test_pv_output_temperature_derating():
    ghi = pd.DataFrame({"a": [1000.0, 1000.0]})
    t = pd.DataFrame({"a": [-5.0, 25.0]})
    pv = features.pv_output(ghi, t)["a"].values
    assert pv[0] > pv[1]                       # cold panels are more efficient
    assert np.isclose(pv[1], 1 - 0.004 * 30)   # 25 C air + 30 K -> 55 C cell


def test_interval_alignment():
    idx = pd.date_range("2025-06-01", periods=3, freq="h", tz="UTC")
    df = pd.DataFrame({"shortwave_radiation": [0.0, 100.0, 300.0], "wind_speed_100m": [4.0, 6.0, 8.0]}, index=idx)
    out = openmeteo.to_interval_means(df)
    # hour starting 00:00 gets the radiation mean labelled 01:00, and the mean of 00:00 and 01:00 wind
    assert out["shortwave_radiation"].iloc[0] == 100.0
    assert out["wind_speed_100m"].iloc[0] == 5.0
    assert np.isnan(out["shortwave_radiation"].iloc[-1])


def test_capacity_interpolation_between_month_ends():
    monthly = pd.DataFrame({"solar": [100.0, 131.0]},
                           index=pd.to_datetime(["2025-01-01", "2025-02-01"]).tz_localize("UTC"))
    idx = pd.date_range("2025-01-31 23:00", "2025-02-28 23:00", freq="h", tz="UTC")
    h = capacity.hourly(monthly, idx)["solar"]
    assert np.isclose(h.iloc[0], 100.0) and np.isclose(h.iloc[-1], 131.0)
    assert 100 < h.iloc[len(h) // 2] < 131


def test_sites_inside_germany():
    g = onshore_grid()
    assert 40 <= len(g) <= 60
    assert g.lat.between(47.2, 55.1).all() and g.lon.between(5.8, 15.1).all()
    assert (all_sites().kind == "offshore").sum() == 6


def test_build_shapes():
    idx = pd.date_range("2025-01-01", periods=48, freq="h", tz="UTC")
    rng = np.random.default_rng(0)
    pts = ["p1", "p2"]
    w = {v: pd.DataFrame(rng.uniform(1, 10, (48, 2)), index=idx, columns=pts) for v in openmeteo.VARIABLES}
    phys, full = features.build(w, "onshore", pts, [])
    assert list(phys.columns) == ["pc_p1", "pc_p2"] and phys.values.max() <= 1
    assert full.shape[1] == 2 + 2 + 3 + 5
    phys, full = features.build(w, "solar", pts, [])
    assert list(phys.columns) == ["pv_p1", "pv_p2"]


def test_day_type():
    idx = pd.to_datetime(["2026-04-03 10:00", "2026-04-04 10:00", "2026-04-05 10:00", "2026-04-07 10:00",
                          "2026-04-05 22:30"]).tz_localize("UTC")
    # Good Friday, Saturday, Easter Sunday, Tuesday; 22:30 UTC on Sunday is already Monday 00:30 (Easter Monday)
    assert features.day_type(idx).tolist() == [2, 1, 2, 0, 2]


def test_aifs_is_a_day_ahead_source_like_ifs():
    url, extra, suffix = openmeteo.ENDPOINTS["aifs"]
    assert extra == {"models": "ecmwf_aifs025_single"}
    assert suffix == openmeteo.ENDPOINTS["ecmwf"][2] == "_previous_day1"
    assert url == openmeteo.ENDPOINTS["ecmwf"][0]
