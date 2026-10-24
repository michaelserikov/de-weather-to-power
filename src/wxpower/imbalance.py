"""What a forecast error costs a renewable portfolio that sells its day-ahead forecast and settles the rest at reBAP.

The portfolio sells forecast F (MWh) in the day-ahead auction at price p. Actual output A differs; the
imbalance A - F is settled at the imbalance price: a long position (A > F) is paid the "long" reBAP, a short
one (A < F) pays the "short" reBAP. Against a perfect forecast (selling A at p) the cost of the error is

    cost = (p - reBAP_long) * (A - F)+  +  (reBAP_short - p) * (F - A)+

which is negative in hours where the imbalance price happens to favour the position. The portfolio is a
price-taker with the profile of the national fleet: its errors move with the system imbalance but it is too
small to move reBAP itself. No intraday trading: the whole forecast error goes to imbalance settlement.
"""

from __future__ import annotations

import pandas as pd


def hourly_cost(actual: pd.Series, forecast: pd.Series, da: pd.Series, short: pd.Series, long: pd.Series) -> pd.Series:
    """Cost of the forecast error in EUR per hour (MW for one hour = MWh)."""
    d = actual - forecast
    return (da - long) * d.clip(lower=0) + (short - da) * (-d).clip(lower=0)


def unit_cost(actual: pd.Series, forecast: pd.Series, da: pd.Series, short: pd.Series, long: pd.Series) -> float:
    """Imbalance cost in EUR per MWh generated."""
    c = hourly_cost(actual, forecast, da, short, long)
    ok = c.notna()
    return float(c[ok].sum() / actual[ok].sum())


def decompose(actual, forecast, da, short, long) -> dict:
    """Unit cost split into the long and short sides and the volume-weighted spreads behind them."""
    d = actual - forecast
    lo, sh = d.clip(lower=0), (-d).clip(lower=0)
    gen = actual.sum()
    return {
        "EUR/MWh": unit_cost(actual, forecast, da, short, long),
        "long side": float(((da - long) * lo).sum() / gen),
        "short side": float(((short - da) * sh).sum() / gen),
        "long, % of output": 100 * float(lo.sum() / gen),
        "short, % of output": 100 * float(sh.sum() / gen),
        "spread when long": float(((da - long) * lo).sum() / lo.sum()),
        "spread when short": float(((short - da) * sh).sum() / sh.sum()),
    }


def covariance_split(actual, forecast, da, rebap) -> dict:
    """With one imbalance price for both sides, cost per hour is -(reBAP - p) * (A - F), so the unit cost splits
    exactly into a covariance term (errors that move with the system imbalance) and a bias term
    (a systematic long or short position times the mean spread)."""
    df = pd.concat({"a": actual, "f": forecast, "p": da, "r": rebap}, axis=1).dropna()
    spread, err = df.r - df.p, df.a - df.f
    gen = df.a.mean()
    cov = float(((spread - spread.mean()) * (err - err.mean())).mean())
    return {"EUR/MWh": float(-(spread * err).mean() / gen), "covariance term": -cov / gen,
            "bias term": float(-spread.mean() * err.mean() / gen), "corr(spread, error)": float(spread.corr(err))}
