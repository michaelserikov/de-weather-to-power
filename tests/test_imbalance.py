import numpy as np
import pandas as pd

from wxpower import imbalance, netztransparenz

REBAP_CSV = """Datum;Zeitzone;von;bis;Datenkategorie;Datentyp;Einheit;reBAP unterdeckt;reBAP ueberdeckt
10.06.2023;UTC;13:00;13:15;reBAP;Qualitätsgesichert;EUR/MWh;103,97;103,97
10.06.2023;UTC;13:15;13:30;reBAP;Qualitätsgesichert;EUR/MWh;1.104,06;-5,50
10.06.2023;UTC;13:30;13:45;reBAP;Qualitätsgesichert;EUR/MWh;104,57;104,57
10.06.2023;UTC;13:45;14:00;reBAP;Qualitätsgesichert;EUR/MWh;100,00;100,00
"""
IDAEP_CSV = """Datum von;(Uhrzeit) von;Zeitzone;(Uhrzeit) bis;Zeitzone;ID AEP in €/MWh
2023-07-01;00:00;UTC;00:15;UTC;90,30
2023-07-01;00:15;UTC;00:30;UTC;46,35
"""


def test_parse_rebap_german_numbers_and_sides():
    df = netztransparenz.parse_rebap(REBAP_CSV)
    assert df.index[0] == pd.Timestamp("2023-06-10 13:00", tz="UTC")
    assert df.loc["2023-06-10 13:15", "short"].item() == 1104.06
    assert df.loc["2023-06-10 13:15", "long"].item() == -5.5


def test_parse_idaep():
    s = netztransparenz.parse_idaep(IDAEP_CSV)
    assert list(s.values) == [90.30, 46.35]
    assert s.index[1] == pd.Timestamp("2023-07-01 00:15", tz="UTC")


def test_cost_signs():
    idx = pd.date_range("2025-01-01", periods=4, freq="h", tz="UTC")
    a = pd.Series([100.0, 100.0, 100.0, 100.0], idx)
    f = pd.Series([100.0, 90.0, 110.0, 110.0], idx)
    da = pd.Series(50.0, idx)
    short = pd.Series([0.0, 0.0, 80.0, 20.0], idx)
    long = pd.Series([0.0, 30.0, 0.0, 0.0], idx)
    c = imbalance.hourly_cost(a, f, da, short, long)
    assert c.iloc[0] == 0                   # perfect forecast
    assert c.iloc[1] == (50 - 30) * 10      # long, surplus paid below day-ahead
    assert c.iloc[2] == (80 - 50) * 10      # short, buys back above day-ahead
    assert c.iloc[3] == (20 - 50) * 10      # short, but reBAP below day-ahead: a gain
    assert imbalance.unit_cost(a, a, da, short, long) == 0


def test_covariance_split_is_exact_and_rewards_independent_errors():
    """Two forecasts with the same accuracy: the one whose error moves against the spread costs more."""
    rng = np.random.default_rng(1)
    idx = pd.date_range("2025-01-01", periods=5000, freq="h", tz="UTC")
    a = pd.Series(rng.uniform(50, 150, len(idx)), idx)
    da = pd.Series(80.0, idx)
    noise = rng.normal(0, 10, len(idx))
    rebap = da - 3 * noise                       # system long (low reBAP) when this error is positive
    herd = a - pd.Series(noise, idx)             # error A - F = noise: long exactly when reBAP is low
    own = a - pd.Series(rng.permutation(noise), idx)
    s_herd = imbalance.covariance_split(a, herd, da, rebap)
    s_own = imbalance.covariance_split(a, own, da, rebap)
    assert abs(s_herd["EUR/MWh"] - imbalance.unit_cost(a, herd, da, rebap, rebap)) < 1e-9
    assert abs(s_herd["EUR/MWh"] - s_herd["covariance term"] - s_herd["bias term"]) < 1e-9
    assert s_herd["EUR/MWh"] > 1 > abs(s_own["EUR/MWh"])
