# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: 2019 was Australia's hottest year on record (The Economist, 2020).

Vertical diverging bar chart of Australia's annual mean surface-air
temperature anomaly relative to the 1961-90 average. Positive anomalies
in red, negative in blue-grey. Values were digitised bar-by-bar from the
original chart (Bureau of Meteorology ACORN-SAT series).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import C_RED, C_SPINE, bar_v, finalize, inset_tick_labels, set_theme

set_theme()

C_NEG = "#6C9EB3"  # blue-grey for below-average years (sampled from original)

YEARS = list(range(1950, 2020))
# Annual mean temperature anomaly vs 1961-90 average, deg C — digitised
# from the original chart's bar heights.
ANOMALY = [
    -0.60, -0.41, -0.42, -0.44, -0.35, -0.32, -0.91, 0.03, 0.13, 0.23,    # 1950s
    -0.65, 0.04, -0.10, -0.12, -0.21, 0.24, -0.50, -0.21, -0.38, -0.01,   # 1960s
    -0.09, -0.21, 0.14, 0.52, -0.70, -0.21, -0.74, -0.04, -0.30, 0.36,    # 1970s
    0.72, 0.26, -0.02, 0.32, -0.38, 0.21, 0.21, 0.16, 0.72, -0.02,        # 1980s
    0.46, 0.58, 0.12, 0.29, 0.17, 0.15, 0.58, 0.29, 0.95, 0.30,           # 1990s
    -0.04, 0.03, 0.70, 0.68, 0.52, 1.14, 0.49, 0.74, 0.45, 0.91,          # 2000s
    0.32, 0.00, 0.24, 1.32, 1.03, 0.94, 0.99, 1.09, 1.13, 1.50,           # 2010s
]

fig, ax = plt.subplots(figsize=(5.0, 5.1))

bar_v(
    ax,
    YEARS,
    ANOMALY,
    bar_colors=[C_RED if v >= 0 else C_NEG for v in ANOMALY],
    highlight_max=False,
    width=0.78,
)

ax.axhline(0, color=C_SPINE, linewidth=0.8, zorder=3)
ax.set_ylim(-1.0, 1.55)
ax.set_yticks([-1.0, -0.5, 0, 0.5, 1.0, 1.5])
ax.set_yticklabels(["-1.0", "-0.5", "0", "0.5", "1.0", "1.5"])

ax.set_xlim(1949.2, 2019.8)
ax.set_xticks([1950, 1960, 1970, 1980, 1990, 2000, 2010, 2019])
ax.set_xticklabels(["1950", "60", "70", "80", "90", "2000", "10", "19"])
inset_tick_labels(ax)

finalize(
    ax,
    title="2019 was Australia’s hottest year on record",
    marker="rule",
    descriptor="Australia, average surface-air temperature\nDeviation from 1961-90 average, °C",
    source="Source: Australian Bureau of Meteorology",
    autoscale_y=False,
)

out = Path(__file__).resolve().parent / "australia_heat.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Australia heat chart")
