"""Weather points: a regular onshore grid over Germany and points at the offshore wind clusters.

The model learns how much each point matters, so the grid only has to cover the country
evenly; no plant register is needed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.path import Path as PolyPath

# Rough outline of Germany (lon, lat), about 20 km accuracy; enough to drop sea and foreign points.
GERMANY = [
    (6.0, 51.9), (6.8, 52.1), (7.0, 52.6), (6.7, 53.5), (7.2, 53.7), (8.5, 53.6), (8.9, 54.0),
    (8.6, 54.9), (9.9, 54.8), (11.0, 54.4), (12.4, 54.5), (14.2, 53.9), (14.4, 53.2), (14.6, 52.6),
    (14.7, 51.6), (15.0, 51.1), (14.3, 50.9), (12.5, 50.4), (12.1, 50.3), (13.8, 48.8), (13.0, 47.5),
    (10.5, 47.5), (9.6, 47.5), (7.6, 47.6), (7.5, 48.1), (8.2, 49.0), (6.4, 49.5), (6.1, 50.2),
    (6.0, 50.8), (5.9, 51.0),
]

# Offshore wind clusters in the German EEZ (approximate centres).
OFFSHORE = {
    "off_borkum": (53.95, 6.45),     # Borkum Riffgrund, Trianel Borkum, Gode Wind area
    "off_nordsee_ost": (54.45, 7.70),  # Nordsee Ost, Meerwind, Amrumbank West
    "off_dolwin": (54.20, 6.60),     # DolWin cluster, BARD, Veja Mate, Deutsche Bucht
    "off_sylt": (54.95, 7.10),       # Butendiek, DanTysk, Sandbank
    "off_baltic_w": (54.65, 12.65),  # Baltic 1 and 2
    "off_baltic_e": (54.80, 14.05),  # Wikinger, Arkona, Baltic Eagle
}


def onshore_grid(step: float = 1.0) -> pd.DataFrame:
    """Grid points inside the Germany outline, named on_<lat>_<lon>."""
    poly = PolyPath(GERMANY)
    lats = np.arange(47.5, 55.0 + 1e-9, step)
    lons = np.arange(6.0, 15.0 + 1e-9, step)
    pts = [(la, lo) for la in lats for lo in lons if poly.contains_point((lo, la))]
    return pd.DataFrame(
        {"name": [f"on_{la:.2f}_{lo:.2f}" for la, lo in pts], "lat": [p[0] for p in pts],
         "lon": [p[1] for p in pts], "kind": "onshore"}
    )


def all_sites(step: float = 1.0) -> pd.DataFrame:
    off = pd.DataFrame(
        {"name": list(OFFSHORE), "lat": [v[0] for v in OFFSHORE.values()],
         "lon": [v[1] for v in OFFSHORE.values()], "kind": "offshore"}
    )
    return pd.concat([onshore_grid(step), off], ignore_index=True)
