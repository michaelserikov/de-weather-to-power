"""Forecast error metrics and the Diebold-Mariano test on daily mean absolute errors."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def summary(actual: pd.Series, forecast: pd.Series, capacity: pd.Series | None = None) -> dict:
    """MAE, RMSE and bias in MW; nMAE in % of installed capacity when capacity is given."""
    e = (forecast - actual).dropna()
    out = {"MAE": e.abs().mean(), "RMSE": float(np.sqrt((e**2).mean())), "bias": e.mean(), "hours": len(e)}
    if capacity is not None:
        out["nMAE_%"] = 100 * (e.abs() / capacity.reindex(e.index)).mean()
    return out


def newey_west_var(d: np.ndarray, lags: int) -> float:
    """Long-run variance of a series (Bartlett kernel)."""
    d = d - d.mean()
    n = len(d)
    v = d @ d / n
    for k in range(1, lags + 1):
        v += 2 * (1 - k / (lags + 1)) * (d[k:] @ d[:-k]) / n
    return v


def diebold_mariano(actual: pd.Series, f1: pd.Series, f2: pd.Series, lags: int = 7) -> tuple[float, float]:
    """DM statistic and two-sided p-value for equal absolute error, on daily means (HAC variance).

    Negative statistic: forecast 1 is more accurate.
    """
    df = pd.concat({"y": actual, "a": f1, "b": f2}, axis=1).dropna()
    d = ((df["a"] - df["y"]).abs() - (df["b"] - df["y"]).abs()).resample("D").mean().dropna().values
    stat = d.mean() / np.sqrt(newey_west_var(d, lags) / len(d))
    return float(stat), float(2 * (1 - stats.norm.cdf(abs(stat))))
