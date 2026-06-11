# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Scatter — standard dots + highlighted outliers + dashed trend line."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from graphs import (
    callout,
    finalize,
    save_chart,
    scatter_highlight,
    scatter_standard,
    set_theme,
    subplots,
    trend_line,
)

set_theme()

rng = np.random.default_rng(42)
n = 60
x = rng.uniform(0, 100, n)
y = 0.6 * x + rng.normal(0, 8, n) + 10

# Plant two outliers
x_out = np.array([18, 82])
y_out = np.array([72, 24])

fig, ax = subplots("wide")

scatter_standard(ax, x, y)
scatter_highlight(ax, x_out, y_out)

# Trend through the bulk of the data
fit = np.polyfit(x, y, 1)
xs = np.linspace(0, 100, 50)
trend_line(ax, xs, np.polyval(fit, xs))

callout(ax, xy=(82, 24), text="Below trend", xytext=(60, 30))
callout(ax, xy=(18, 72), text="Above trend", xytext=(28, 78))

ax.set_xlim(0, 100)
ax.set_ylim(0, 100)

finalize(
    ax,
    title="Two outliers in a noisy field",
    descriptor="Synthetic data, units arbitrary",
    source="Source: Generated",
)

save_chart(__file__)
