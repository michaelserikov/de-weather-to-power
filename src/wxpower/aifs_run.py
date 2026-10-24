"""v0.3: ECMWF's machine-learning forecast model AIFS against the physics-based IFS and ICON as input to the
day-ahead wind and solar forecasts.

AIFS day-1 forecasts are archived from 18 February 2025, so all inputs are compared on a common, shorter
period with a 180-day training window: test months September 2025 to September 2026. With so little training
data, stacking the features of several weather models overfits, so combinations are equal-weight averages of
the single-model forecasts.

AIFS output is 6-hourly (interpolated to hours by Open-Meteo). To separate temporal resolution from model
skill, IFS is also degraded to 6-hourly wind and temperature ("IFS, 6-hourly") and run through the same models.

Usage: python -m wxpower.aifs_run   (after scripts/download.py has fetched the aifs weather)
Writes results/tables/aifs.md and results/figures/fig7_aifs_*.png.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import capacity, features, imbalance, metrics, models, netztransparenz, openmeteo, smard  # noqa: E402
from .run import END as RUN_END, START as RUN_START, load_weather  # noqa: E402
from .sites import all_sites  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
START, END = "2025-02-20", "2026-09-30"
TEST_START = "2025-09-01"
WINDOW = 180
TECHS = ("onshore", "offshore", "solar")
SOURCES = {"icon": "icon", "ifs": "ecmwf", "aifs": "aifs", "ifs6": "ecmwf6"}
COMBOS = {"ifs+icon": ("ifs", "icon"), "aifs+icon": ("aifs", "icon"), "aifs+ifs": ("aifs", "ifs"),
          "all three": ("aifs", "ifs", "icon")}
LABELS = {"icon": "ICON", "ifs": "ECMWF IFS", "aifs": "ECMWF AIFS", "ifs6": "ECMWF IFS, 6-hourly",
          "ifs+icon": "mean of IFS and ICON", "aifs+icon": "mean of AIFS and ICON", "aifs+ifs": "mean of AIFS and IFS",
          "all three": "mean of AIFS, IFS and ICON"}
# Pairs tested with Diebold-Mariano (first minus second; negative = first more accurate).
PAIRS = [("aifs", "ifs"), ("aifs", "ifs6"), ("aifs", "icon"), ("aifs+icon", "ifs+icon"), ("all three", "ifs+icon")]


def six_hourly(sites) -> dict[str, pd.DataFrame]:
    """IFS weather with wind and temperature kept only at 00, 06, 12 and 18 UTC and linearly interpolated
    in between, like AIFS; radiation is left hourly (used for wind models only)."""
    per_point = {}
    for s in sites.itertuples():
        df = openmeteo.load_point("ecmwf", s.name, s.lat, s.lon, RUN_START, RUN_END, RAW / "weather")
        df.index = pd.to_datetime(df.index, utc=True)
        for c in df.columns:
            if "radiation" not in c:
                df[c] = df[c].where(df.index.hour % 6 == 0).interpolate(method="time", limit_area="inside")
        per_point[s.name] = openmeteo.to_interval_means(df)
    return {v: pd.DataFrame({n: d[v] for n, d in per_point.items()}) for v in openmeteo.VARIABLES}


def forecasts() -> tuple[pd.DataFrame, pd.DataFrame]:
    sites = all_sites()
    on = sites.loc[sites.kind == "onshore", "name"].tolist()
    off = sites.loc[sites.kind == "offshore", "name"].tolist()
    obs = smard.load_all(START, END, RAW / "smard")
    obs = obs[obs.index >= pd.Timestamp(START, tz="UTC")]
    cap = capacity.hourly(capacity.load_monthly(RAW / "capacity_energy_charts.json"), obs.index)
    wx = {src: load_weather(src, sites) for src in ("icon", "ecmwf", "aifs")}
    wx["ecmwf6"] = six_hourly(sites)
    fc = {}
    for tech in TECHS:
        y_cf = obs[tech] / cap[tech]
        for name, src in SOURCES.items():
            if name == "ifs6" and tech == "solar":
                continue
            phys, full = features.build({v: f.reindex(obs.index) for v, f in wx[src].items()}, tech, on, off)
            pred = models.rolling_forecast(phys, full, y_cf, TEST_START, solar=(tech == "solar"), window_days=WINDOW)
            fc[(tech, name)] = models.rolling_scale(pred["ensemble"] * cap[tech].reindex(pred.index), obs[tech])
            print(tech, name, "done", flush=True)
        for name, parts in COMBOS.items():
            fc[(tech, name)] = sum(fc[(tech, k)] for k in parts) / len(parts)
        fc[(tech, "tso")] = obs[f"{tech}_tso"]
        fc[(tech, "actual")] = obs[tech]
    F = pd.DataFrame(fc)
    F.columns = pd.MultiIndex.from_tuples(F.columns)
    F = F[F.index >= pd.Timestamp(TEST_START, tz="UTC")].dropna()
    return F, cap.reindex(F.index)


def main() -> None:
    F, cap = forecasts()
    F.to_parquet(ROOT / "data" / "forecasts_aifs.parquet")
    TABLES.mkdir(parents=True, exist_ok=True)
    lines = [f"Evaluation sample: {F.index.min():%d %b %Y} to {F.index.max():%d %b %Y}, {len(F):,} hours. "
             f"Every input uses the same models (ensemble of linear, gradient boosting and neural network), monthly "
             f"refits on the previous {WINDOW} days and the 30-day drift correction.\n"]
    for tech in TECHS:
        keys = [k for k in ("tso", *SOURCES, *COMBOS) if (tech, k) in F]
        rows = {LABELS.get(k, "TSO day-ahead forecast"): metrics.summary(F[(tech, "actual")], F[(tech, k)], cap[tech])
                for k in keys}
        t = pd.DataFrame(rows).T[["MAE", "RMSE", "bias", "nMAE_%"]]
        t["skill_vs_TSO_%"] = 100 * (1 - t["MAE"] / t.loc["TSO day-ahead forecast", "MAE"])
        lines.append(f"\n### {tech} (MW; mean capacity {cap[tech].mean():,.0f} MW)\n")
        lines.append(t.round({"MAE": 0, "RMSE": 0, "bias": 0, "nMAE_%": 2, "skill_vs_TSO_%": 1}).to_markdown())
        dm = {}
        for a, b in PAIRS:
            if (tech, b) not in F:
                continue
            s, p = metrics.diebold_mariano(F[(tech, "actual")], F[(tech, a)], F[(tech, b)])
            mae_a = (F[(tech, a)] - F[(tech, "actual")]).abs().mean()
            mae_b = (F[(tech, b)] - F[(tech, "actual")]).abs().mean()
            dm[f"{LABELS[a]} vs {LABELS[b]}"] = {"MAE change %": 100 * (mae_a / mae_b - 1), "DM stat": s, "p-value": p}
        lines.append("\nDiebold-Mariano (daily mean absolute error; negative = first more accurate)\n")
        lines.append(pd.DataFrame(dm).T.round(3).to_markdown())

    # Do AIFS and IFS make the same mistakes? Correlation of the errors of the single-input forecasts.
    rows = {}
    for tech in TECHS:
        e = pd.DataFrame({k: F[(tech, k)] - F[(tech, "actual")] for k in ("icon", "ifs", "aifs", "tso")})
        c = e.corr()
        rows[tech] = {"AIFS-IFS": c.loc["aifs", "ifs"], "AIFS-ICON": c.loc["aifs", "icon"],
                      "IFS-ICON": c.loc["ifs", "icon"], "AIFS-TSO": c.loc["aifs", "tso"], "IFS-TSO": c.loc["ifs", "tso"]}
    lines.append("\n### Correlation of hourly forecast errors\n")
    lines.append(pd.DataFrame(rows).T.round(2).to_markdown())

    # Solar by hour of day: AIFS radiation is 6-hourly, so the diurnal cycle is interpolated.
    hourly = {}
    for k in ("tso", "icon", "ifs", "aifs"):
        e = (F[("solar", k)] - F[("solar", "actual")]).abs()
        hourly[LABELS.get(k, "TSO")] = e.groupby(e.index.hour).mean()
    hourly = pd.DataFrame(hourly)
    lines.append("\n### Solar MAE by hour of day (UTC), MW, daylight hours\n")
    lines.append(hourly.loc[5:18].round(0).to_markdown())

    # Imbalance cost of the single-input forecasts (as in v0.2), where reBAP is cached.
    try:
        px = netztransparenz.hourly(f"{F.index.min():%Y-%m-%d}", f"{F.index.max():%Y-%m-%d}", RAW / "netztransparenz")
        px["da"] = smard.load_series("price", f"{F.index.min():%Y-%m-%d}", f"{F.index.max():%Y-%m-%d}", RAW / "smard")
        px = px.reindex(F.index)
        ok = px[["da", "short", "long"]].notna().all(axis=1) & (px["quarters"] == 4)
        rows = {}
        for tech in TECHS:
            rows[tech] = {LABELS.get(k, "TSO"): imbalance.unit_cost(F.loc[ok, (tech, "actual")], F.loc[ok, (tech, k)],
                                                                   px.da[ok], px.short[ok], px.long[ok])
                          for k in ("tso", "icon", "ifs", "aifs", "ifs+icon", "all three")}
        lines.append(f"\n### Imbalance cost at reBAP, EUR per MWh generated ({int(ok.sum()):,} hours)\n")
        lines.append(pd.DataFrame(rows).T.round(2).to_markdown())
    except RuntimeError as err:   # no netztransparenz credentials and no cache
        lines.append(f"\n(imbalance cost skipped: {err})\n")

    (TABLES / "aifs.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    figure(F, cap, hourly)


def figure(F, cap, hourly) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    colors = {"tso": "#555555", "icon": "#9ecae1", "ifs": "#1f77b4", "aifs": "#ff7f0e", "all three": "#d62728"}
    fig, axes = plt.subplots(1, 4, figsize=(17, 3.8))
    x = np.arange(len(TECHS))
    keys = ("tso", "icon", "ifs", "aifs", "all three")
    for i, k in enumerate(keys):
        v = [100 * ((F[(t, k)] - F[(t, "actual")]).abs() / cap[t]).mean() for t in TECHS]
        axes[0].bar(x + (i - 2) * 0.16, v, 0.16, label=LABELS.get(k, "TSO day-ahead forecast"), color=colors[k])
    axes[0].set_xticks(x, TECHS)
    axes[0].set_ylabel("MAE, % of installed capacity")
    axes[0].set_ylim(0, 11)
    axes[0].legend(fontsize=7, loc="upper left")
    axes[0].grid(alpha=0.3, axis="y")
    for ax, tech in zip(axes[1:3], ("onshore", "offshore")):
        for k in ("tso", "ifs", "ifs6", "aifs"):
            e = (F[(tech, k)] - F[(tech, "actual")]).abs() / cap[tech] * 100
            ax.plot(e.resample("MS").mean(), label=LABELS.get(k, "TSO"), color=colors["ifs" if k == "ifs6" else k],
                    lw=1.6, ls="--" if k == "ifs6" else "-")
        ax.set_title(f"{tech}, monthly MAE (% of capacity)")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
    ax = axes[3]
    for k, col in (("TSO", "tso"), ("ECMWF IFS", "ifs"), ("ECMWF AIFS", "aifs")):
        ax.plot(hourly.index, hourly[k] / 1000, marker="o", ms=3, label=k, color=colors[col])
    ax.set_title("solar, MAE by hour of day (GW)")
    ax.set_xlabel("hour (UTC)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGS / "fig7_aifs_vs_ifs.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
