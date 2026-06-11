# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: The Economist daily chart on Europe's populist vote.

Aggregated populist vote share across 33 European countries, 1980-2019,
stacked into right-wing (red, bottom) and left-wing (pale blue, top)
parties. The story is in the mix: the populist total doubles while its
composition flips from left- to right-wing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import (
    C_RED,
    finalize,
    footnotes,
    inset_tick_labels,
    set_theme,
    top_legend,
)

set_theme()

# Vote shares per year, % (TIMBRO Authoritarian Populism Index),
# read off the original chart: (right wing, left wing).
SHARES = {
    1980: (1.0, 9.7), 1981: (1.0, 10.0), 1982: (0.8, 9.7), 1983: (1.2, 9.1),
    1984: (1.2, 8.9), 1985: (1.1, 8.6), 1986: (1.5, 8.5), 1987: (1.7, 7.9),
    1988: (2.3, 7.9), 1989: (3.0, 8.0), 1990: (2.9, 7.1), 1991: (4.2, 6.0),
    1992: (5.0, 6.0), 1993: (4.6, 5.6), 1994: (4.5, 5.7), 1995: (5.3, 5.8),
    1996: (5.3, 5.9), 1997: (5.5, 6.3), 1998: (5.7, 5.7), 1999: (5.9, 5.2),
    2000: (6.8, 5.0), 2001: (7.5, 4.8), 2002: (8.6, 4.5), 2003: (9.0, 4.4),
    2004: (9.7, 4.5), 2005: (10.6, 4.7), 2006: (10.9, 3.7), 2007: (10.6, 4.0),
    2008: (11.2, 4.0), 2009: (11.4, 4.1), 2010: (12.1, 4.0), 2011: (12.4, 4.0),
    2012: (11.8, 4.8), 2013: (11.4, 5.7), 2014: (11.4, 5.7), 2015: (12.2, 6.9),
    2016: (13.2, 6.3), 2017: (13.6, 6.4), 2018: (15.0, 6.5), 2019: (15.8, 6.8),
}

C_LEFT = "#B2D0DC"  # pale blue sampled from the original

years = list(SHARES)
right = [SHARES[y][0] for y in years]
left = [SHARES[y][1] for y in years]

fig, ax = plt.subplots(figsize=(6.2, 5.8))

bars_right = ax.bar(years, right, width=0.5, color=C_RED, zorder=2)
bars_left = ax.bar(years, left, width=0.5, bottom=right, color=C_LEFT, zorder=2)

ax.set_xlim(1979.2, 2020.2)
ax.set_ylim(0, 25)
ax.set_yticks(range(0, 26, 5))
ax.set_xticks([1980, 1990, 2000, 2010, 2019])
ax.set_xticklabels(["1980", "90", "2000", "10", "19"])
inset_tick_labels(ax)

finalize(
    ax,
    title="How Europe’s populists are changing",
    descriptor="Europe, aggregated populist votes*, %",
    source="",  # owned by footnotes() below so the note packs alongside it
    footnote_lines=3,  # note row + blank spacer row above the source
)
top_legend(fig, [bars_left, bars_right], ["Left wing", "Right wing"], fontsize=9)
footnotes(
    fig,
    "*Index of 33 countries\n",  # trailing newline adds a line of air above the source
    source="Source: [TIMBRO](https://populismindex.com/)",
    max_width_frac=0.3,  # force the note onto its own row, as in the original
)

out = Path(__file__).resolve().parent / "populist_votes.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved populist votes chart")
