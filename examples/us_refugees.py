# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica: The Economist daily chart on US refugee resettlement.

Annual refugee admissions (bars) against the presidential annual cap
(red line), fiscal years 1980-2020. Bars use a light neutral grey so the
red cap line carries the story: the Trump-era collapse at the right
edge.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import C_RED, finalize, footnotes, save_chart, set_theme, year_ticks

set_theme()

# Admissions per fiscal year, '000 (Refugee Processing Centre).
ADMISSIONS = {
    1980: 207.1, 1981: 159.3, 1982: 98.1, 1983: 61.2, 1984: 70.4,
    1985: 67.7, 1986: 62.1, 1987: 64.5, 1988: 76.5, 1989: 107.1,
    1990: 122.1, 1991: 113.4, 1992: 115.5, 1993: 114.2, 1994: 111.7,
    1995: 99.0, 1996: 75.7, 1997: 70.1, 1998: 76.2, 1999: 85.1,
    2000: 72.1, 2001: 68.9, 2002: 26.8, 2003: 28.3, 2004: 52.8,
    2005: 53.8, 2006: 41.1, 2007: 48.2, 2008: 60.1, 2009: 74.6,
    2010: 73.3, 2011: 56.4, 2012: 58.2, 2013: 69.9, 2014: 70.0,
    2015: 69.9, 2016: 85.0, 2017: 53.7, 2018: 22.5, 2019: 30.0,
}

# Presidential determination ceiling per fiscal year, '000. FY2017 shows
# the 50k operative cap set by executive order rather than the 110k
# determination it replaced.
CAPS = {
    1980: 231.7, 1981: 217.0, 1982: 140.0, 1983: 90.0, 1984: 72.0,
    1985: 70.0, 1986: 67.0, 1987: 70.0, 1988: 87.5, 1989: 116.5,
    1990: 125.0, 1991: 131.0, 1992: 142.0, 1993: 132.0, 1994: 121.0,
    1995: 112.0, 1996: 90.0, 1997: 78.0, 1998: 83.0, 1999: 91.0,
    2000: 90.0, 2001: 80.0, 2002: 70.0, 2003: 70.0, 2004: 70.0,
    2005: 70.0, 2006: 70.0, 2007: 70.0, 2008: 80.0, 2009: 80.0,
    2010: 80.0, 2011: 80.0, 2012: 76.0, 2013: 70.0, 2014: 70.0,
    2015: 70.0, 2016: 85.0, 2017: 50.0, 2018: 45.0, 2019: 30.0,
    2020: 18.0,
}

# Deliberate departure from the original's pale blue: a light neutral grey
# keeps the bars recessive so the red cap line carries the story.
C_BAR = "#C4C4C4"

fig, ax = plt.subplots(figsize=(6.0, 5.2))

ax.bar(list(ADMISSIONS), list(ADMISSIONS.values()), width=0.78, color=C_BAR, zorder=2)
ax.plot(list(CAPS), list(CAPS.values()), color=C_RED, linewidth=2.2, zorder=3)

# Original sets this label larger and bolder than highlight_label's fixed
# 8.5pt, so render it directly.
ax.text(1982.0, 208, "Annual cap", color=C_RED, fontsize=10.5, fontweight="bold", va="center")

ax.set_xlim(1979.2, 2021.5)
ax.set_ylim(0, 250)
ax.set_yticks(range(0, 251, 50))
year_ticks(ax, [1980, 1990, 2000, 2010, 2020])
ax.get_xticklabels()[-1].set_ha("center")  # original centres the final "20"
ax.set_xlabel("Fiscal years ending September 30th")

finalize(
    ax,
    title="The days when America settled more refugees than anywhere else are over",
    descriptor="United States, refugee resettlement, ’000",
    footnote_lines=2,  # x-axis label sits between the ticks and the source
)
footnotes(fig, source="Source: Refugee Processing Centre")

save_chart(__file__)
