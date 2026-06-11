# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Where do most of the plastic bottles
in the ocean come from?" daily chart.

Stacked percentage bars trace the origin of plastic bottles washed up
on Inaccessible Island, a remote speck in the South Atlantic, across
three beach surveys (1989, 2009, 2018). South America's share collapses
while Asia's surges — most of it merchant shipping waste, not river
litter. A circular locator globe (orthographic view of the South
Atlantic, Natural Earth 110m coastlines) sits under the category
legend, matching the original's left column. Shares are read off the
published chart.
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.patches as mpatches
import numpy as np

from graphs import PALETTE, finalize, footnotes, save_chart, set_theme, subplots, top_legend

_LAND_URL = (
    "https://raw.githubusercontent.com/martynafford/natural-earth-geojson"
    "/master/110m/physical/ne_110m_land.json"
)
_LAND_CACHE = Path(__file__).resolve().parent / ".data" / "ne_110m_land.json"


def load_land_rings() -> list[np.ndarray]:
    """Natural Earth 110m land outlines as (n, 2) lon/lat arrays."""
    if not _LAND_CACHE.exists():
        _LAND_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(_LAND_URL) as resp:
            _LAND_CACHE.write_bytes(resp.read())
    collection = json.loads(_LAND_CACHE.read_text())
    return [
        np.asarray(feature["geometry"]["coordinates"][0], dtype=float)
        for feature in collection["features"]
    ]


def orthographic(ring, lon0: float, lat0: float):
    """Project a lon/lat ring onto an orthographic globe (radius 1).

    Far-side vertices are pushed to the horizon circle so coastlines
    that wrap behind the globe stay closed; the caller clips to the
    sea disc. Returns None when the whole ring is on the far side.
    """
    lon = np.radians(ring[:, 0])
    lat = np.radians(ring[:, 1])
    lon0_r, lat0_r = np.radians(lon0), np.radians(lat0)
    cos_c = np.sin(lat0_r) * np.sin(lat) + np.cos(lat0_r) * np.cos(lat) * np.cos(lon - lon0_r)
    if (cos_c <= 0).all():
        return None
    x = np.cos(lat) * np.sin(lon - lon0_r)
    y = np.cos(lat0_r) * np.sin(lat) - np.sin(lat0_r) * np.cos(lat) * np.cos(lon - lon0_r)
    hidden = cos_c < 0
    radius = np.hypot(x[hidden], y[hidden])
    radius[radius == 0] = 1.0
    x[hidden] /= radius
    y[hidden] /= radius
    return np.column_stack([x, y])

set_theme()

C_AFRICA = "#BA95A1"  # lighter tint of the palette purple
C_OTHER_LIGHT = "#BEC7C9"  # pale grey for the "Other regions" bucket
C_SEA = "#E4E9EB"
C_LAND = "#9FB0B8"

YEARS = ["1989", "2009", "2018"]

# (name, colour, % of total per survey year) — read off the published chart.
SERIES = [
    ("South America", PALETTE["blue"], [67, 41, 20]),
    ("Asia", PALETTE["cyan"], [9, 44, 74]),
    ("Europe", PALETTE["purple"], [6, 4, 2]),
    ("Africa", C_AFRICA, [11, 5, 2]),
    ("Other regions", C_OTHER_LIGHT, [7, 6, 2]),
]

fig, ax = subplots("daily", height=4.6)
fig.subplots_adjust(top=0.72, bottom=0.16, left=0.33, right=0.93)

bottom = np.zeros(len(YEARS))
for name, color, shares in SERIES:
    vals = np.array(shares, dtype=float)
    ax.bar(YEARS, vals, 0.72, bottom=bottom, color=color, label=name,
           edgecolor="none", zorder=2)
    # White in-bar labels for the two dominant series, centred per segment.
    if name in ("South America", "Asia"):
        for i, v in enumerate(shares):
            ax.text(i, bottom[i] + v / 2, f"{v}", ha="center", va="center",
                    color="white", fontsize=10.5, fontweight="medium", zorder=3)
    bottom += vals

ax.set_ylim(0, 100)
ax.set_yticks(range(0, 101, 20))
ax.tick_params(axis="x", length=0, labelsize=10)
ax.tick_params(axis="y", labelsize=10)

finalize(
    ax,
    title="Where do most of the plastic bottles in the ocean come from?",
    descriptor="Origin of plastic bottles found on Inaccessible Island\n% of total",
    source="",
    title_x=0.02,
    autoscale_y=False,
    auto_layout=False,
)

# Vertical category key in the left column, flush with the chart top.
handles, labels = ax.get_legend_handles_labels()
top_legend(fig, handles, labels, x=0.02, ncol=1, anchor_to=ax, fontsize=9)

# Circular locator globe: orthographic view of the South Atlantic with
# the island picked out in red (Natural Earth 110m coastlines).
ISLAND_LON, ISLAND_LAT = -12.68, -37.30
VIEW_LON, VIEW_LAT = -14.0, -42.0

ax_map = fig.add_axes((0.015, 0.16, 0.26, 0.26))
ax_map.set_xlim(-1.02, 1.02)
ax_map.set_ylim(-1.02, 1.02)
ax_map.set_aspect("equal")
ax_map.set_xticks([])
ax_map.set_yticks([])
ax_map.axis("off")
sea = mpatches.Circle((0, 0), 1.0, facecolor=C_SEA, edgecolor=C_LAND,
                      linewidth=0.8)
ax_map.add_patch(sea)
for ring in load_land_rings():
    xy = orthographic(ring, VIEW_LON, VIEW_LAT)
    if xy is None:
        continue
    land = mpatches.Polygon(xy, closed=True, facecolor=C_LAND,
                            edgecolor="none")
    land.set_clip_path(sea)
    ax_map.add_patch(land)
# Redraw the rim over the land so horizon-clamped coastlines don't
# leave slivers along the disc edge.
rim = mpatches.Circle((0, 0), 1.0, facecolor="none", edgecolor=C_LAND,
                      linewidth=0.8, zorder=4)
ax_map.add_patch(rim)
island_xy = orthographic(np.array([[ISLAND_LON, ISLAND_LAT]]),
                         VIEW_LON, VIEW_LAT)[0]
# Faint dashed graticule arc around the island, as on the original locator.
graticule = mpatches.Circle(tuple(island_xy), 0.42, facecolor="none",
                            edgecolor=C_LAND, alpha=0.7, linewidth=0.5,
                            linestyle=(0, (2, 2)))
graticule.set_clip_path(sea)
ax_map.add_patch(graticule)
ax_map.plot([island_xy[0]], [island_xy[1]], marker="o", markersize=3.5,
            color=PALETTE["red"], clip_on=False)
ax_map.text(island_xy[0] - 0.02, island_xy[1] - 0.28, "Inaccessible\nIsland",
            ha="center", va="top", color=PALETTE["red"], fontsize=9,
            fontweight="medium", linespacing=1.2)

footnotes(fig, source="Source: [PNAS](https://www.pnas.org/doi/10.1073/pnas.1909816116)")

save_chart(__file__)
