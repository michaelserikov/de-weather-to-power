"""Full pipeline: data, rolling forecasts for wind onshore, offshore and solar, comparison with the TSO forecast.

Usage: python -m wxpower.run   (after scripts/download.py has filled data/raw)
Writes results/tables/*.md, results/figures/*.png and data/forecasts.parquet.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import capacity, features, metrics, models, openmeteo, plots, smard
from .sites import all_sites

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
START, END = "2024-02-20", "2026-09-30"
TEST_START = "2024-09-01"
META_START = "2024-12-01"   # the TSO/own combination needs three months of out-of-sample forecasts first
WINDOW = 365                # training window in days: the last year covers every season but forgets old fleet behaviour
# Weather inputs per model family: day-ahead NWP (one or two models) and reanalysis (weather known).
INPUTS = {"icon": ["icon"], "nwp2": ["icon", "ecmwf"], "era5": ["era5"]}
TECHS = ("onshore", "offshore", "solar")


def load_weather(source: str, sites: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Variable -> wide frame (hour x point), aligned to SMARD hours."""
    per_point = {s.name: openmeteo.to_interval_means(
        openmeteo.load_point(source, s.name, s.lat, s.lon, START, END, RAW / "weather")) for s in sites.itertuples()}
    return {v: pd.DataFrame({n: df[v] for n, df in per_point.items()}) for v in openmeteo.VARIABLES}


def fmt(df: pd.DataFrame, digits: int = 0) -> str:
    return df.round(digits).to_markdown()


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    sites = all_sites()
    on = sites.loc[sites.kind == "onshore", "name"].tolist()
    off = sites.loc[sites.kind == "offshore", "name"].tolist()

    obs = smard.load_all(START, END, RAW / "smard")
    obs = obs[(obs.index >= pd.Timestamp(START, tz="UTC"))]
    cap = capacity.hourly(capacity.load_monthly(RAW / "capacity_energy_charts.json"), obs.index)
    wx = {src: load_weather(src, sites) for src in ("icon", "ecmwf", "era5")}

    fc = {}
    weights = {}
    for tech in TECHS:
        y_cf = obs[tech] / cap[tech]
        for name, srcs in INPUTS.items():
            parts = [features.build({v: f.reindex(obs.index) for v, f in wx[src].items()}, tech, on, off) for src in srcs]
            phys = pd.concat([p.add_prefix(f"{src}_") for (p, _), src in zip(parts, srcs)], axis=1)
            full = pd.concat([f.add_prefix(f"{src}_") for (_, f), src in zip(parts, srcs)], axis=1)
            pred = models.rolling_forecast(phys, full, y_cf, TEST_START, solar=(tech == "solar"), window_days=WINDOW)
            for col in pred:
                raw = pred[col] * cap[tech].reindex(pred.index)
                fc[(tech, f"{name}_{col}")] = models.rolling_scale(raw, obs[tech])
                if col == "ensemble":
                    fc[(tech, f"{name}_ensemble_raw")] = raw
            if name == "icon":
                weights[tech] = models.linear_weights(parts[0][0], y_cf)
            print(tech, name, "done", flush=True)
        own = fc[(tech, "nwp2_ensemble")]
        meta_cf = models.meta_forecast(own / cap[tech], obs[f"{tech}_tso"] / cap[tech], y_cf, META_START)
        fc[(tech, "meta")] = (meta_cf.clip(lower=0) * cap[tech].reindex(meta_cf.index))
        fc[(tech, "tso")] = obs[f"{tech}_tso"]
        fc[(tech, "actual")] = obs[tech]
    F = pd.DataFrame(fc)
    F.columns = pd.MultiIndex.from_tuples(F.columns)
    # Common evaluation sample: hours where every forecast of every technology exists.
    F = F[F.index >= pd.Timestamp(META_START, tz="UTC")].dropna()
    F.to_parquet(ROOT / "data" / "forecasts.parquet")
    report(F, cap.reindex(F.index), obs["price"].reindex(F.index), weights, sites)


LABELS = {
    "tso": "TSO day-ahead forecast",
    "icon_linear": "ICON, linear (point weights)",
    "icon_gbm": "ICON, gradient boosting",
    "icon_mlp": "ICON, neural network",
    "icon_ensemble": "ICON, ensemble",
    "nwp2_ensemble_raw": "ICON + ECMWF, ensemble without drift correction",
    "nwp2_ensemble": "ICON + ECMWF, ensemble",
    "meta": "Meta (ICON + ECMWF ensemble and TSO)",
    "era5_ensemble": "ERA5 ensemble (weather known)",
}


def report(F: pd.DataFrame, cap: pd.DataFrame, price: pd.Series, weights: dict, sites: pd.DataFrame) -> None:
    lines = [f"Evaluation sample: {F.index.min():%d %b %Y} to {F.index.max():%d %b %Y}, {len(F):,} hours, "
             "all forecasts out of sample (monthly refits on earlier hours only).\n"]
    for tech in TECHS:
        rows = {LABELS[k]: metrics.summary(F[(tech, "actual")], F[(tech, k)], cap[tech]) for k in LABELS}
        t = pd.DataFrame(rows).T[["MAE", "RMSE", "bias", "nMAE_%"]]
        t["skill_vs_TSO_%"] = 100 * (1 - t["MAE"] / t.loc[LABELS["tso"], "MAE"])
        lines.append(f"\n### {tech} (MW; mean capacity {cap[tech].mean():,.0f} MW)\n")
        lines.append(t.round({"MAE": 0, "RMSE": 0, "bias": 0, "nMAE_%": 2, "skill_vs_TSO_%": 1}).to_markdown())
        dm = {}
        for k in ("icon_ensemble", "nwp2_ensemble", "meta", "era5_ensemble"):
            s, p = metrics.diebold_mariano(F[(tech, "actual")], F[(tech, k)], F[(tech, "tso")])
            dm[LABELS[k]] = {"DM stat vs TSO": s, "p-value": p}
        lines.append("\nDiebold-Mariano (daily mean absolute error; negative = more accurate than TSO)\n")
        lines.append(pd.DataFrame(dm).T.round(3).to_markdown())
    # Total wind + solar: what matters for residual load and the price.
    tot = {k: sum(F[(t, k)] for t in TECHS) for k in ("actual", "tso", "icon_ensemble", "nwp2_ensemble", "meta")}
    yearly = {}
    for k in ("tso", "icon_ensemble", "nwp2_ensemble", "meta"):
        e = (tot[k] - tot["actual"]).abs()
        yearly[LABELS[k]] = e.groupby(e.index.year).mean() / 1000
        yearly[LABELS[k]]["all"] = e.mean() / 1000
    lines.append("\n### Wind + solar total, MAE in GW by year\n")
    lines.append(pd.DataFrame(yearly).T.round(2).to_markdown())
    # Negative-price hours: plants are curtailed, which the weather alone cannot show.
    neg = price < 0
    rows = {}
    for tech in TECHS:
        for k in ("tso", "nwp2_ensemble", "meta"):
            e = F[(tech, k)] - F[(tech, "actual")]
            rows[(tech, LABELS[k])] = {"MAE price<0": e[neg].abs().mean(), "bias price<0": e[neg].mean(),
                                       "MAE price>=0": e[~neg].abs().mean()}
    lines.append(f"\n### Negative-price hours ({int(neg.sum())} of {len(F)} hours), MW\n")
    lines.append(pd.DataFrame(rows).T.round(0).to_markdown())
    (TABLES / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    plots.all_figures(F, cap, weights, sites, FIGS, LABELS)


if __name__ == "__main__":
    main()
