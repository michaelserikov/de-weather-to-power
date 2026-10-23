import numpy as np
import pandas as pd

from wxpower import metrics, models


def synthetic(days: int = 260, seed: int = 0):
    """Two points; the true capacity factor is 0.7 * point 1 + 0.3 * point 2 plus noise."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=days * 24, freq="h", tz="UTC")
    phys = pd.DataFrame(rng.uniform(0, 1, (len(idx), 2)), index=idx, columns=["pc_a", "pc_b"])
    y = (0.7 * phys["pc_a"] + 0.3 * phys["pc_b"] + rng.normal(0, 0.02, len(idx))).clip(0, 1)
    full = phys.copy()
    full["hour"] = idx.hour
    return phys, full, y


def test_linear_weights_recover_truth():
    phys, _, y = synthetic()
    w = models.linear_weights(phys, y)
    assert np.allclose(w.values, [0.7, 0.3], atol=0.02)


def test_rolling_forecast_is_out_of_sample_and_accurate():
    phys, full, y = synthetic()
    pred = models.rolling_forecast(phys, full, y, "2024-07-01", min_train_days=100)
    assert pred.index.min() >= pd.Timestamp("2024-07-01", tz="UTC")
    assert set(pred.columns) == {"linear", "gbm", "mlp", "ensemble"}
    assert pred.values.min() >= 0 and pred.values.max() <= 1
    mae = (pred["linear"] - y.reindex(pred.index)).abs().mean()
    assert mae < 0.03


def test_rolling_forecast_does_not_see_the_future():
    phys, full, y = synthetic()
    pred1 = models.rolling_forecast(phys, full, y, "2024-07-01", min_train_days=100)
    y2 = y.copy()
    y2[y2.index >= pd.Timestamp("2024-08-01", tz="UTC")] = 0.0  # change the future only
    pred2 = models.rolling_forecast(phys, full, y2, "2024-07-01", min_train_days=100)
    july = pred1.index < pd.Timestamp("2024-08-01", tz="UTC")
    assert np.allclose(pred1.loc[july, "linear"], pred2.loc[july, "linear"])


def test_meta_forecast_weights_better_input():
    phys, _, y = synthetic(days=200)
    rng = np.random.default_rng(1)
    good = y + rng.normal(0, 0.02, len(y))
    bad = y + rng.normal(0, 0.2, len(y))
    meta = models.meta_forecast(good, bad, y, "2024-05-01")
    e_meta = (meta - y.reindex(meta.index)).abs().mean()
    e_good = (good.reindex(meta.index) - y.reindex(meta.index)).abs().mean()
    assert e_meta <= e_good * 1.05


def test_diebold_mariano_sign():
    idx = pd.date_range("2025-01-01", periods=24 * 120, freq="h", tz="UTC")
    rng = np.random.default_rng(2)
    y = pd.Series(rng.normal(size=len(idx)), index=idx)
    f1 = y + rng.normal(0, 0.1, len(idx))
    f2 = y + rng.normal(0, 1.0, len(idx))
    stat, p = metrics.diebold_mariano(y, f1, f2)
    assert stat < 0 and p < 0.001
    s = metrics.summary(y, f1, pd.Series(10.0, index=idx))
    assert np.isclose(s["nMAE_%"], 10 * s["MAE"])


def test_rolling_scale_removes_drift_without_lookahead():
    idx = pd.date_range("2025-01-01", periods=24 * 120, freq="h", tz="UTC")
    pred = pd.Series(100.0, index=idx)
    actual = pd.Series(np.where(idx < pd.Timestamp("2025-03-01", tz="UTC"), 100.0, 80.0), index=idx)
    out = models.rolling_scale(pred, actual, window_days=30, lag_days=2)
    # before the drift: unchanged; first two days of the drift: still the old factor (lag)
    assert np.isclose(out[pd.Timestamp("2025-02-20", tz="UTC")], 100.0)
    assert np.isclose(out[pd.Timestamp("2025-03-02 12:00", tz="UTC")], 100.0)
    # a month later the factor has adapted
    assert np.isclose(out[pd.Timestamp("2025-04-15", tz="UTC")], 80.0)
