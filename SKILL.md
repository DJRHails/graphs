---
name: graph-design
description: >
  Economist-style chart theme for matplotlib/seaborn. Provides a global theme,
  title-stack finaliser, direct line labels, CI bands, horizontal bars,
  thermometers, scatter dot variants, annotation/highlight helpers, and a
  per-chart-type colour palette. Uses IBM Plex Sans + IBM Plex Sans Condensed
  typography and a curated 9-colour palette with transparent backgrounds.
---

# graph-design

Economist-style data-visualisation system for matplotlib and seaborn.

> **Source is external.** Vendored as a submodule from
> [`DJRHails/graphs`](https://github.com/DJRHails/graphs). Install with
> `pip install djrhails-graphs` (or `pip install
> git+https://github.com/DJRHails/graphs.git`). Import as `graphs`.

## Project overrides vs. the Economist styleguide

Three deliberate deviations — documented because they're not surprises:

1. **White backgrounds.** `C_BG = "#FFFFFF"`. Styleguide uses `#E9EDF0`.
   `set_theme(bg=C_BG_TINT)` for the styleguide tint;
   `set_theme(bg=C_BG_TRANSPARENT, transparent=True)` for transparent PNGs.
2. **Single accent red.** `C_RED = "#bf352b"` covers both the styleguide's
   masthead red (`#E3120B`) and data red (`#DB444B`). Both originals are
   exposed as `C_RED_BRAND` / `C_RED_DATA`.
3. **IBM Plex Sans + IBM Plex Sans Condensed** instead of Econ Sans / Cnd.

Everything else follows the styleguide and is applied automatically by
`set_theme()` and `finalize()` — fonts, tick colours, spine handling, source
placement, y-axis-right, font auto-download, etc.

## Quick start

```python
from graphs import set_theme, finalize, label_lines

set_theme()

fig, ax = plt.subplots()
fig.subplots_adjust(top=0.68, bottom=0.14, left=0.06, right=0.88)
ax.plot(x, y, label="Series A")
label_lines(ax)
finalize(
    ax,
    title="Inflation eases as energy costs fall",
    descriptor="United States, CPI, % year on year",
    source="Source: BLS",
)
```

For faceted charts: bump `top` to ~0.72 and pass `y_start=0.075` to `finalize`.

## Core design principles

Rules the helpers were built to enforce. When in doubt, satisfy the most.

- **Title does the talking** — state the finding, not the topic. Subtitle
  carries units, geography, time range.
- **Every element earns its place** — if removing it doesn't hurt
  comprehension, remove it.
- **Put information where the reader's eye is already going** — labels next
  to what they label.
- **Direct labelling beats legends.** (See `label_lines`.)
- **Each chart type has its own conventions.** Pick the type first, then
  apply its rules. (See `cycle_for`.)
- **Hue communicates kind; saturation communicates importance.** Same-kind
  differentiation uses saturation or opacity, not a new hue.
- **Brand colour and data colour are separated** — `C_RED` is reserved for
  emphasis, not as the default fill.
- **Four categories is a working ceiling** for thermometer / bubble / pie /
  doughnut. The fix is usually a different chart, not more colours.
- **Don't truncate scales** to fit the comparison.
- **The chart type carries assumptions** — lines imply continuity, bars
  imply discrete categories.
- **Axis scaling is editorial, not neutral.**
- **Double scales need discipline** — align zero lines, match axis colour to
  its line. Otherwise split or index.
- **One chart, one baseline.** If you can't combine cleanly, split.
- **Signal non-zero baselines visually** — `broken_axis()` on line /
  thermometer / scatter. **Never on bar/column** (use a thermometer).
- **Annotations are first-class elements** — callouts, highlight panels,
  event markers have their own typography and geometry.
- **Mobile is a redesign, not a resize.**
- **Negative space is engineered** — the paddings and axis ends are
  deliberate.
- **Sometimes the right answer is less data** — cut or show an average.
- **The chart is responsible to the reader, not to the data.** Misleading,
  confusing, pointless — three failure modes every chart has to pass.

## Palette

Nine main colours in `PALETTE`: red, blue, cyan, green, yellow, olive,
purple, gold, grey. Default cycle leads with red. Pull a chart-type-specific
order with `cycle_for("bar" | "bar_stacked" | "line" | "scatter" | "bubble"
| "thermometer")`.

Structural greys (all automatic in the theme): `C_SPINE` (zero-baseline
only), `C_GRID`, `C_LABEL`, `C_LABEL_MUTED`, `C_CI`, `C_BOX_FILL`, `C_BG`,
`C_BG_TINT`.

Style overrides to apply on top:

- **Chronological categories** → light-to-dark tints of one colour, not the
  cycle.
- **"Other" / "Don't know"** → `C_OTHER` (slate grey).
- **Positive vs. negative** → only differentiate by colour for *meaningful*
  pairs (imports/exports, gain/loss).

## API

| Function                                                            | Purpose                                                |
|---------------------------------------------------------------------|--------------------------------------------------------|
| `set_theme(bg=None, transparent=True)`                              | Apply theme globally. Call once.                       |
| `finalize(ax, title, descriptor, source, …)`                        | Title stack, red rule, source line, y-axis right.      |
| `panel_label(ax, label)`                                            | Bold sub-heading + dark rule (faceted charts).         |
| `cycle_for(chart_type) → list[str]`                                 | Recommended colour order for a chart type.             |
| `bar_h(ax, categories, values, *, highlight_max=True)`              | Horizontal bars; max in `C_RED` by default.            |
| `dumbbell(ax, categories, start, end, *, label_start, label_end)`   | Before/after dot-and-line. Defaults red→blue.          |
| `thermometer(ax, categories, values, *, series_labels, dot=True)`   | Tick-and-dot ranked categories. Warns above 4 series.  |
| `scatter_standard(ax, x, y)`                                        | General-trend scatter, 50% opacity, no stroke.         |
| `scatter_highlight(ax, x, y)`                                       | Outlier / labelled scatter, 100% opacity.              |
| `scatter_category(ax, x, y)`                                        | Bubble dot, 50% fill + 0.3px stroke for overlap.       |
| `trend_line(ax, x, y)`                                              | Dashed 1px trend line.                                 |
| `ci_fill(ax, x, lo, hi, *, color=None)`                             | CI band. Salmon by default; pass colour to match line. |
| `callout(ax, xy, text, *, xytext, arrow=True)`                      | Pale-fill text callout with optional arrow.            |
| `highlight_panel(ax, x_start, x_end, *, label=None)`                | Vertical event-period band.                            |
| `highlight_label(ax, xy, text, *, role="primary")`                  | Single-point label. `"secondary"` = grey/caps/light.   |
| `index_marker(ax, x, *, y=100)`                                     | Red rule + black dot for index charts.                 |
| `broken_axis(ax, *, x=0)`                                           | Non-zero-baseline squiggle. Line/scatter/thermometer.  |
| `number_box(ax, xy, n)`                                             | Numbered cross-reference box.                          |
| `label_lines(ax, *, stroke=False)`                                  | Direct labels at line ends with collision avoidance.   |
| `smart_legend(ax)`                                                  | Legend in the emptiest corner by data-ink overlap.     |

## Workflow

1. `set_theme()`.
2. `fig.subplots_adjust()` for title/source headroom.
3. (If not the default cycle) `ax.set_prop_cycle(color=cycle_for("…"))`.
4. Plot — `ci_fill` and `highlight_panel` first so they sit behind the data.
5. Annotate — `callout`, `highlight_label`, `index_marker`, `broken_axis`.
6. Direct label — `label_lines(ax)` over `smart_legend(ax)` for line charts.
7. `finalize(ax, title, descriptor, source)` last.
8. Faceted: `panel_label()` per axes; `finalize()` on the first axes with
   `title_x` pinned and `y_start=0.075`.

## Examples

Runnable scripts in `examples/`.

**Synthetic demos:**

- [`line_chart.py`](./examples/line_chart.py) — multi-series + CI bands + `label_lines`
- [`faceted_chart.py`](./examples/faceted_chart.py) — three panels + `panel_label`
- [`bar_chart.py`](./examples/bar_chart.py) — `bar_h` with max highlight
- [`dumbbell_chart.py`](./examples/dumbbell_chart.py) — `dumbbell` before/after
- [`thermometer_chart.py`](./examples/thermometer_chart.py) — ranked categories
- [`scatter_chart.py`](./examples/scatter_chart.py) — standard + highlight + trend line
- [`index_chart.py`](./examples/index_chart.py) — `index_marker`, `broken_axis`, `highlight_panel`, secondary `highlight_label`

**Replications of "Mistakes, we've drawn a few"** (Sarah Leo, The Economist
2019 — fixed versions of charts the author publicly critiqued). Raw CSVs
in `examples/data/`:

- [`corbyn.py`](./examples/corbyn.py) — Facebook likes, full-range bars (fixes truncated scale)
- [`dogs.py`](./examples/dogs.py) — dog weight vs. neck size, proportionally-comparable double axis (fixes cherry-picked scales)
- [`brexit.py`](./examples/brexit.py) — Brexit polls, scatter + smoothed trend + 33% baseline headroom (fixes jagged line on individual polls)
- [`us_trade.py`](./examples/us_trade.py) — US trade vs. manufacturing, stacked panels (fixes forced double-axis with two baselines)
- [`pensions.py`](./examples/pensions.py) — OECD pension spending, opacity-for-emphasis (fixes "50 shades of blue")
- [`eu_balance.py`](./examples/eu_balance.py) — euro-area balances, four countries + Others (fixes 10-country rainbow stack)
