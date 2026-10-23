"""Weather-to-power models with monthly rolling-origin evaluation.

Every model predicts the national capacity factor of one technology. For each test month the
models are refitted on all earlier hours (expanding window), so every forecast uses only
information available before that month.

  linear:   non-negative least squares on the physical point features (one weight per point:
            the model learns where the capacity is)
  gbm:      histogram gradient boosting on hub wind or irradiance per point, national means and calendar
  mlp:      small feed-forward neural network (two hidden layers) on the same inputs, standardised
  ensemble: mean of the three
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MODELS = ("linear", "gbm", "mlp")


def make(name: str, seed: int = 0):
    if name == "linear":
        return LinearRegression(positive=True)
    if name == "gbm":
        return HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                             min_samples_leaf=40, l2_regularization=1.0, random_state=seed)
    if name == "mlp":
        return make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3,
                                                            learning_rate_init=1e-3, max_iter=500,
                                                            early_stopping=True, n_iter_no_change=15,
                                                            random_state=seed))
    raise ValueError(name)


def rolling_forecast(phys: pd.DataFrame, full: pd.DataFrame, y: pd.Series, test_start: str,
                     min_train_days: int = 150, seed: int = 0, solar: bool = False,
                     window_days: int | None = None) -> pd.DataFrame:
    """Out-of-sample capacity-factor forecasts, refitted at the start of every month from test_start.

    window_days: train on the last window_days only (rolling window); None uses all earlier hours.

    For solar, night hours (no irradiance anywhere) are set to zero and left out of training.
    Returns a frame with one column per model plus `ensemble`, on the test hours.
    """
    ok = phys.notna().all(axis=1) & full.notna().all(axis=1) & y.notna()
    phys, full, y = phys[ok], full[ok], y[ok]
    day = (phys.sum(axis=1) > 0) if solar else pd.Series(True, index=phys.index)
    months = pd.date_range(pd.Timestamp(test_start, tz="UTC"), phys.index.max(), freq="MS")
    out = []
    for m0 in months:
        m1 = m0 + pd.offsets.MonthBegin(1)
        train = (phys.index < m0) & day.values
        if window_days is not None:
            train &= phys.index >= m0 - pd.Timedelta(days=window_days)
        test = (phys.index >= m0) & (phys.index < m1)
        if train.sum() < min_train_days * 24 * (0.5 if solar else 1.0) or test.sum() == 0:
            continue
        pred = pd.DataFrame(index=phys.index[test])
        for name in MODELS:
            X_tr, X_te = (phys, phys) if name == "linear" else (full, full)
            model = make(name, seed).fit(X_tr[train].values, y[train].values)
            pred[name] = np.clip(model.predict(X_te[test].values), 0.0, 1.0)
        if solar:
            pred.loc[~day[test].values, :] = 0.0
        out.append(pred)
    res = pd.concat(out)
    res["ensemble"] = res[list(MODELS)].mean(axis=1)
    return res


def rolling_scale(pred: pd.Series, actual: pd.Series, window_days: int = 30, lag_days: int = 2) -> pd.Series:
    """Multiply a forecast by the ratio of actual to forecast energy over a trailing window.

    The ratio for day d uses days d-lag_days-window_days+1 .. d-lag_days, i.e. only observations
    that are published by the time the day-ahead forecast for d is made. It removes slow drifts
    the weather cannot explain (self-consumption, feed-in limits, outages, wrong capacity data).
    """
    df = pd.concat({"p": pred, "a": actual}, axis=1).dropna()
    daily = df.resample("D").sum()
    roll = daily.rolling(window_days, min_periods=window_days // 2).sum().shift(lag_days)
    ratio = (roll["a"] / roll["p"]).clip(0.5, 1.5)
    factor = ratio.reindex(pred.index.floor("D")).to_numpy()
    out = pred * np.where(np.isfinite(factor), factor, 1.0)
    return out.rename(pred.name)


def linear_weights(phys: pd.DataFrame, y: pd.Series) -> pd.Series:
    """Point weights of the non-negative linear model fitted on all hours (for the map of learnt capacity)."""
    ok = phys.notna().all(axis=1) & y.notna()
    m = LinearRegression(positive=True).fit(phys[ok].values, y[ok].values)
    return pd.Series(m.coef_, index=phys.columns)


def meta_forecast(own: pd.Series, tso: pd.Series, y: pd.Series, test_start: str, min_train_days: int = 90) -> pd.Series:
    """Combine own and TSO forecasts: linear regression of the actual on both, refitted monthly on past hours.

    Weights are re-estimated each month on all earlier test hours, so the combination is out of sample too.
    """
    df = pd.concat({"own": own, "tso": tso, "y": y}, axis=1).dropna()
    months = pd.date_range(pd.Timestamp(test_start, tz="UTC"), df.index.max(), freq="MS")
    out = []
    for m0 in months:
        m1 = m0 + pd.offsets.MonthBegin(1)
        tr, te = df[df.index < m0], df[(df.index >= m0) & (df.index < m1)]
        if len(tr) < min_train_days * 24 or te.empty:
            continue
        lr = LinearRegression().fit(tr[["own", "tso"]].values, tr["y"].values)
        out.append(pd.Series(lr.predict(te[["own", "tso"]].values), index=te.index))
    return pd.concat(out).rename("meta")
