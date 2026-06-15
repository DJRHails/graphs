# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica: Economist daily chart on graduate pay vs. college selectivity.

One dot per maths/physics/computer-science programme: earnings one year
after graduation against the college's admissions rate (reversed, so the
most selective schools sit on the right). A solid red trend curve shows
pay climbing steeply once admissions rates drop below ~25%.
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from graphs import C_RED, C_TEXT, finalize, save_chart, scatter_standard, set_theme, subplots

set_theme()

rng = np.random.default_rng(7)


def trend(x):
    """Median earnings ($'000) as a function of admissions rate (%)."""
    return 35 + 0.03 * x + 75 * np.exp(-x / 15)


# Admissions-rate distribution: most colleges admit 40-100%, a thin tail
# of selective schools below 25%.
x = np.concatenate(
    [
        rng.uniform(40, 100, 520),
        rng.uniform(20, 45, 85),
        rng.uniform(1, 25, 65),
    ]
)

# Earnings: a fat band even at open-admission schools (roughly 20-90,
# most mass 30-60), widening as schools get more selective. The slight
# positive mean keeps the bulk of the cloud sitting above the curve, as
# in the original.
spread = 10.5 + 13 * np.exp(-x / 22)
y = trend(x) + rng.normal(0.3, 1, x.size) * spread

# Right-skewed upper fringe: a slice of programmes out-earn the curve at
# every selectivity level, as in the original's loose scatter above 60.
boost = rng.random(x.size) < 0.12
y[boost] += rng.uniform(5, 30, boost.sum())

y = np.clip(y, 17, 132)

# A handful of well-paid programmes at unselective schools, as in the
# original's upper-middle stragglers.
x_hi = np.array([63, 57, 44, 35])
y_hi = np.array([108, 99, 82, 94])
x = np.concatenate([x, x_hi])
y = np.concatenate([y, y_hi])

fig, ax = subplots("daily", height=3.9)

# Firmer dots than the scatter_standard default 50% — the published chart's
# cloud reads more solid — with the trend curve drawn last so it stays on top.
dots = scatter_standard(ax, x, y, color=C_RED, size=76)
dots.set_alpha(0.7)

xs = np.linspace(0, 100, 200)
ax.plot(xs, trend(xs), color=C_RED, linewidth=3.0, zorder=5)

ax.set_xlim(104, -4)
ax.set_xticks([100, 75, 50, 25, 0])
ax.set_ylim(8, 160)
ax.set_yticks([30, 60, 90, 120, 150])
ax.set_xlabel("Admissions rate, %", color=C_TEXT)

# Panel-style series label, sitting just above the topmost (150) gridline
# as in the original.
ax.text(
    103,
    153,
    "Maths/Physics/Computer science",
    fontsize=9.5,
    fontweight="bold",
    color=C_TEXT,
    va="bottom",
    ha="left",
)

with warnings.catch_warnings():
    # The reversed x-axis is deliberate: the original chart runs admissions
    # rate 100 -> 0 so selectivity increases left to right.
    warnings.filterwarnings("ignore", message=".*x-axis runs right-to-left.*")
    finalize(
        ax,
        title="Which degree gives you the best salary after one year in the workforce?",
        descriptor="United States, earnings one year after graduation\n"
        "By major and college selectivity, 2017-18, $'000",
        source="Source: Department of Education",
        autoscale_y=False,
    )

# finalize auto-layouts the right margin from the measured right-hand y-tick
# labels, so they fit on this narrow figure — no manual subplots_adjust needed.

save_chart(__file__)
