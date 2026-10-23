"""Figures for the README."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .sites import GERMANY  # noqa: E402

TECHS = ("onshore", "offshore", "solar")
COLORS = {"tso": "#555555", "icon_ensemble": "#9ecae1", "nwp2_ensemble": "#1f77b4", "meta": "#d62728", "era5_ensemble": "#2ca02c"}


def monthly_nmae(F, cap, out: Path, labels) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8), sharey=False)
    for ax, tech in zip(axes, TECHS):
        for k in ("tso", "nwp2_ensemble", "meta", "era5_ensemble"):
            e = (F[(tech, k)] - F[(tech, "actual")]).abs() / cap[tech] * 100
            ax.plot(e.resample("MS").mean(), label=labels[k], color=COLORS[k], lw=1.6 if k != "era5_ensemble" else 1.0,
                    ls="--" if k == "era5_ensemble" else "-")
        ax.set_title(tech)
        ax.set_ylabel("MAE, % of installed capacity")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def hourly_mae(F, out: Path, labels) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
    for ax, tech in zip(axes, TECHS):
        for k in ("tso", "nwp2_ensemble", "meta"):
            e = (F[(tech, k)] - F[(tech, "actual")]).abs()
            ax.plot(e.groupby(e.index.hour).mean() / 1000, label=labels[k], color=COLORS[k], marker="o", ms=3)
        ax.set_title(tech)
        ax.set_xlabel("hour (UTC)")
        ax.set_ylabel("MAE, GW")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def weight_map(weights: dict, sites: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 5.2))
    border = list(GERMANY) + [GERMANY[0]]
    for ax, tech in zip(axes, TECHS):
        w = weights[tech]
        names = [c.split("_", 1)[1] for c in w.index]
        s = sites.set_index("name").loc[names]
        ax.plot([p[0] for p in border], [p[1] for p in border], color="k", lw=0.8)
        share = w.values / w.values.sum() if w.values.sum() > 0 else w.values
        ax.scatter(sites.lon, sites.lat, s=4, color="#bbbbbb")
        ax.scatter(s.lon, s.lat, s=2000 * share + 1, color="#1f77b4", alpha=0.7)
        ax.set_title(f"{tech}: learnt point weights")
        ax.set_aspect(1.6)
        ax.set_xlim(5.5, 15.2)
        ax.set_ylim(47.2, 55.3)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def worst_week(F, out: Path, labels, tech: str = "onshore") -> None:
    e = (F[(tech, "tso")] - F[(tech, "actual")]).abs().resample("D").mean()
    d0 = e.idxmax() - pd.Timedelta(days=3)
    sl = F.loc[d0:d0 + pd.Timedelta(days=7)]
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.plot(sl[(tech, "actual")] / 1000, color="k", lw=2, label="actual")
    for k in ("tso", "nwp2_ensemble", "meta"):
        ax.plot(sl[(tech, k)] / 1000, color=COLORS[k], lw=1.3, label=labels[k])
    ax.set_ylabel("GW")
    ax.set_title(f"Wind {tech}: week around the largest daily TSO error ({e.idxmax():%d %b %Y})")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def all_figures(F, cap, weights, sites, figs: Path, labels) -> None:
    monthly_nmae(F, cap, figs / "fig1_monthly_nmae.png", labels)
    hourly_mae(F, figs / "fig2_mae_by_hour.png", labels)
    weight_map(weights, sites, figs / "fig3_point_weights.png")
    worst_week(F, figs / "fig4_worst_week_onshore.png", labels)
