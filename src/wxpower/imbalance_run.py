"""v0.3: what the forecast errors cost at German imbalance prices (reBAP), and a cost-aware bid.

Usage: python -m wxpower.imbalance_run   (after python -m wxpower.run has written data/forecasts.parquet,
and with NTP_CLIENT_ID / NTP_CLIENT_SECRET set for the first download of reBAP and ID-AEP)
Writes results/tables/imbalance.md and results/figures/fig5_*.png, fig6_*.png.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import capacity, imbalance, metrics, netztransparenz, smard  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
TECHS = ("onshore", "offshore", "solar")
FCS = {"tso": "TSO day-ahead forecast", "nwp2_ensemble": "ICON + ECMWF ensemble", "meta": "Combination with TSO"}


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    F = pd.read_parquet(ROOT / "data" / "forecasts.parquet")
    start, end = f"{F.index.min():%Y-%m-%d}", f"{F.index.max():%Y-%m-%d}"
    px = netztransparenz.hourly(start, end, RAW / "netztransparenz")
    px["da"] = smard.load_series("price", start, end, RAW / "smard")
    px = px.reindex(F.index)
    keep = px[["da", "short", "long"]].notna().all(axis=1) & (px["quarters"] == 4)
    # Wind + solar total: errors of different technologies partly net out within one balance group.
    for k in ("actual", *FCS):
        F[("total", k)] = sum(F[(t, k)] for t in TECHS)
    return F[keep], px[keep]


def cost_table(F, px, techs, fcs) -> pd.DataFrame:
    rows = {}
    for tech in techs:
        for k in fcs:
            rows[(tech, FCS.get(k, k))] = imbalance.decompose(F[(tech, "actual")], F[(tech, k)], px.da, px.short, px.long)
    return pd.DataFrame(rows).T


def daily_cost_test(F, px, tech, k1, k2, b1=None, b2=None) -> tuple[float, float]:
    """Mean daily cost difference (k1 - k2) in EUR per MWh and its HAC t-statistic."""
    a = F[(tech, "actual")]
    c1 = imbalance.hourly_cost(a, F[(tech, k1)] if b1 is None else b1, px.da, px.short, px.long)
    c2 = imbalance.hourly_cost(a, F[(tech, k2)] if b2 is None else b2, px.da, px.short, px.long)
    df = pd.concat({"d": c1 - c2, "a": a}, axis=1).dropna().resample("D").sum()
    d = (df["d"] / df["a"].mean()).values
    return float(d.mean()), float(d.mean() / np.sqrt(metrics.newey_west_var(d, 7) / len(d)))


def main() -> None:
    F, px = load()
    TABLES.mkdir(parents=True, exist_ok=True)
    lines = [f"Sample: {F.index.min():%d %b %Y} to {F.index.max():%d %b %Y}, {len(F):,} hours with day-ahead price "
             "and all four quarter-hourly reBAP values. Price-taker portfolio with the profile of the national fleet; "
             "forecast sold day-ahead, whole error settled at reBAP (no intraday trading).\n"]

    lines.append("\n### Prices (EUR/MWh)\n")
    s = pd.DataFrame({"day-ahead": px.da, "reBAP short": px.short, "reBAP long": px.long, "ID-AEP": px.idaep})
    lines.append(s.describe(percentiles=[0.01, 0.5, 0.99]).T.round(1).to_markdown())

    techs = (*TECHS, "total")
    t = cost_table(F, px, techs, FCS)
    lines.append("\n### Imbalance cost of the forecast error, EUR per MWh generated\n")
    lines.append("Spreads are volume-weighted: day-ahead minus reBAP when long, reBAP minus day-ahead when short.\n")
    lines.append(t.round(2).to_markdown())

    by_year = {}
    for tech in techs:
        for k in FCS:
            c = imbalance.hourly_cost(F[(tech, "actual")], F[(tech, k)], px.da, px.short, px.long)
            g = pd.concat({"c": c, "a": F[(tech, "actual")]}, axis=1).groupby(c.index.year).sum()
            by_year[(tech, FCS[k])] = g["c"] / g["a"]
    lines.append("\n### Imbalance cost by year, EUR/MWh (2024 = December only)\n")
    lines.append(pd.DataFrame(by_year).T.round(2).to_markdown())

    # Value of the cheaper forecast, scaled to a 1 GW portfolio of each technology.
    cap = capacity.hourly(capacity.load_monthly(RAW / "capacity_energy_charts.json"), F.index)
    rows = {}
    for tech in TECHS:
        mwh_per_gw_year = 8760 * 1000 * (F[(tech, "actual")] / cap[tech]).mean()
        for k in ("nwp2_ensemble", "meta"):
            d, tstat = daily_cost_test(F, px, tech, "tso", k)
            rows[(tech, FCS[k])] = {"saving vs TSO forecast, EUR/MWh": d, "HAC t": tstat,
                                    "capacity factor": mwh_per_gw_year / 8.76e6, "kEUR per GW and year": d * mwh_per_gw_year / 1000}
    v = pd.DataFrame(rows).T
    lines.append("\n### Saving against the TSO forecast, per MWh and for a 1 GW portfolio\n")
    lines.append(v.round({"saving vs TSO forecast, EUR/MWh": 3, "HAC t": 2, "capacity factor": 3, "kEUR per GW and year": 0}).to_markdown())

    # System link: when the fleet is long, the system tends to be long and reBAP falls below day-ahead.
    err = F[("total", "tso")] - F[("total", "actual")]
    bins = pd.cut(-err / 1000, [-np.inf, -4, -2, -1, 0, 1, 2, 4, np.inf])
    link = pd.DataFrame({"reBAP long - day-ahead": (px.long - px.da).groupby(bins, observed=True).mean(),
                         "ID-AEP - day-ahead": (px.idaep - px.da).groupby(bins, observed=True).mean(),
                         "hours": err.groupby(bins, observed=True).size()})
    link.index = link.index.astype(str)
    link.index.name = "wind + solar actual - TSO forecast, GW"
    lines.append("\n### Prices against the national forecast error (TSO forecast), EUR/MWh\n")
    lines.append(link.round(1).to_markdown())

    # Hypothetical: the same error closed in the intraday market at ID-AEP instead of settled at reBAP.
    rows = {}
    for tech in techs:
        a, f = F[(tech, "actual")], F[(tech, "meta")]
        ok = px.idaep.notna()
        rows[tech] = {"at reBAP": imbalance.unit_cost(a[ok], f[ok], px.da[ok], px.short[ok], px.long[ok]),
                      "at ID-AEP": imbalance.unit_cost(a[ok], f[ok], px.da[ok], px.idaep[ok], px.idaep[ok])}
    lines.append("\n### Combined forecast: error settled at reBAP or the same error closed at the "
                 "intraday index ID-AEP (hypothetical: assumes the error is known before intraday trading), EUR/MWh\n")
    lines.append(pd.DataFrame(rows).T.round(2).to_markdown())

    # Why a less accurate forecast can be cheaper: the cost is a covariance with the system imbalance plus a bias term.
    rows = {}
    for tech in techs:
        for k in FCS:
            rows[(tech, FCS[k])] = imbalance.covariance_split(F[(tech, "actual")], F[(tech, k)], px.da, px.long)
    lines.append("\n### Cost split: covariance with the imbalance spread (reBAP - day-ahead) and bias, EUR/MWh\n")
    lines.append(f"reBAP short and long are equal in all {len(px):,} hours, so the split is exact. "
                 "A negative correlation means the portfolio tends to be long when reBAP is below day-ahead.\n")
    lines.append(pd.DataFrame(rows).T.round(3).to_markdown())

    # Own forecast vs TSO forecast, with and without the most extreme spreads.
    s_ = px.long - px.da
    lo, hi = s_.quantile([0.01, 0.99])
    clipped = px.assign(long=px.da + s_.clip(lo, hi), short=px.da + s_.clip(lo, hi))
    rows = {}
    for tech in techs:
        d, t = daily_cost_test(F, px, tech, "tso", "nwp2_ensemble")
        d2, t2 = daily_cost_test(F, clipped, tech, "tso", "nwp2_ensemble")
        mae = {k: (F[(tech, k)] - F[(tech, "actual")]).abs().mean() for k in ("tso", "nwp2_ensemble")}
        rows[tech] = {"MAE TSO, MW": mae["tso"], "MAE own, MW": mae["nwp2_ensemble"], "saving, EUR/MWh": d,
                      "HAC t": t, f"saving, spread clipped to [{lo:.0f}, {hi:.0f}]": d2, "HAC t (clipped)": t2}
    lines.append("\n### ICON + ECMWF ensemble against the TSO forecast: accuracy and imbalance cost\n")
    lines.append(pd.DataFrame(rows).T.round(3).to_markdown())

    (TABLES / "imbalance.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    figures(F, px, link)


def figures(F, px, link) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8), sharey=True)
    for ax, tech in zip(axes, (*TECHS, "total")):
        for k, color in (("tso", "#555555"), ("nwp2_ensemble", "#1f77b4"), ("meta", "#d62728")):
            c = imbalance.hourly_cost(F[(tech, "actual")], F[(tech, k)], px.da, px.short, px.long)
            g = pd.concat({"c": c, "a": F[(tech, "actual")]}, axis=1).resample("MS").sum()
            ax.plot(g["c"] / g["a"], label=FCS[k], color=color, lw=1.6)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title("wind + solar" if tech == "total" else tech)
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("imbalance cost, EUR per MWh generated")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_imbalance_cost_monthly.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(link))
    ax.bar(x - 0.2, link["reBAP long - day-ahead"], 0.4, label="reBAP - day-ahead", color="#1f77b4")
    ax.bar(x + 0.2, link["ID-AEP - day-ahead"], 0.4, label="ID-AEP - day-ahead", color="#ff7f0e")
    ax.set_xticks(x, link.index, rotation=30, fontsize=8)
    ax.set_xlabel(link.index.name)
    ax.set_ylabel("EUR/MWh")
    ax.axhline(0, color="k", lw=0.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(FIGS / "fig6_prices_vs_forecast_error.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
