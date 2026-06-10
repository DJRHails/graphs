---
name: graph-design
description: >
  Economist-style chart theme for matplotlib/seaborn. Provides a global theme,
  and a variety of chart types. Use when generating graphs with matplotlib and seaborn. 
---

# graph-design

Economist-style data-visualisation system for matplotlib and seaborn.

> **Source is external.** Vendored as a submodule from
> [`DJRHails/graphs`](https://github.com/DJRHails/graphs). Install with
> `pip install djrhails-graphs` (or `pip install
> git+https://github.com/DJRHails/graphs.git`). Import as `graphs`.

## Quick start

A two-series line chart with direct labels, a footnote marker, and a packed
footnote-plus-source row — the conventions the library is built for.

```python
import matplotlib.pyplot as plt
import numpy as np

from graphs import set_theme, finalize, footnotes, label_lines

set_theme()

months = np.arange(24)
us = 2.0 + 4.0 * np.exp(-months / 9) + np.random.default_rng(0).normal(0, 0.25, 24)
eu = 1.8 + 4.5 * np.exp(-months / 11) + np.random.default_rng(7).normal(0, 0.30, 24)

fig, ax = plt.subplots(figsize=(7, 4.4))
ax.plot(months, us, label="United States")
ax.plot(months, eu, label="Euro area")
label_lines(ax)

finalize(
    ax,
    title="Cooling off",
    descriptor="Headline CPI*, % change on a year earlier, monthly",
)
footnotes(
    fig,
    "*All-items consumer price index",
    source="Sources: [US Bureau of Labor Statistics](https://www.bls.gov/); "
           "[Eurostat](https://ec.europa.eu/eurostat)",
)

plt.savefig("inflation.png", bbox_inches="tight", dpi=150)
```

Save to `quick.py` and run; the output sits next to it. `finalize()`
auto-sizes margins, and `footnotes()` packs the note and source onto one
row when they fit, wrapping when they don't — leave `source=` off
`finalize()` so they belong to the same line.

### Default visual conventions

Behaviour that's automatic unless you override it:

- **Title marker is the favicon triangle** (`marker="delta"`). The hollow
  red triangle is drawn inline at the title baseline, sized to the cap
  height. Pass `marker="rule"` for the legacy short red rule above the
  title, or `marker="none"` to suppress entirely.
- **Footnote markers auto-superscript.** `*, †, ‡, §, **, ††, ‡‡, §§`
  render as superscripts anywhere they appear in titles, descriptors,
  source lines, or footnote bodies — write plain text, the renderer
  handles the typography.
- **Frameless legends are default** for both `smart_legend()` and
  `top_legend()`. Boxed legends are opt-in.
- **Source + footnotes use `C_SOURCE`** (`#404040`, the styleguide's
  75% black) — slightly darker than `C_LABEL` so attribution reads as
  metadata, not as data.
- **`finalize(auto_layout=True)` (default)** sizes `subplots_adjust`
  margins to fit the title-stack and source line. Set `auto_layout=False`
  on faceted charts that need explicit `hspace`/`wspace` control.
- **Long footnotes word-wrap automatically.** `footnotes(wrap=True)` is the
  default — overflowing notes break to multiple lines that stack above the
  source line, and the chart shifts up to reserve room. No need to hand-
  break with `\n`.
- **Orphan footnote markers warn.** `footnotes(check_anchors=True)` (default)
  raises a `UserWarning` when a note starts with `*` / `†` / `‡` / `§`
  that isn't found in the title, descriptor, axis labels, or any in-chart
  text. Anchor the marker by adding it after a word in the descriptor
  (e.g. `descriptor="Verified contracts* per TVL bucket"`).

### Vertical bar charts (plug-and-play)

For the common "one bar per category" layout, the three-helper combo
collapses ~30 lines of per-script spine/grid/tick boilerplate:

```python
bars = bar_v(ax, labels, values, log=True)               # spines, grid, ticks
bar_value_labels(ax, bars, fmt="{:,}", skip_zero=True)   # value above each bar
bar_sublabels(ax, bars, [f"n={n}" for n in counts])      # denominator below
finalize(ax, title="…", descriptor="…", source="…")
```

`bar_v` highlights the max in `C_RED` by default; pass `highlight_idx=` to
spotlight a specific bar, or `highlight_max=False` to skip. `bar_sublabels`
auto-pads the x-tick labels down so the sublabel band doesn't collide.


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

## Headline conventions

The three strings passed to `finalize(title=, descriptor=, source=)` carry
distinct jobs. Get them wrong and a technically correct chart still reads
as a draft.

### Title — state the finding, ideally with a wink

- **Says what the data says**, not what it is. "Eastern promise", not
  "GDP growth, 2010–2024".
- **≤ 50 characters.** Has to fit one line at 12pt bold across a 7-inch
  figure.
- **Punchy, often a play on words.** Examples from our replicas:
  "Eastern promise" (`corbyn.py`), "Mind un-stretched" (`dogs.py`),
  "Bremorse" (`brexit.py`), "A bit left-field" (`us_trade.py`),
  "Closing the gap" (`affordability_chart.py`), "Free markets and free
  workers" (`pensions.py`).
- **No units, no dates, no geography.** That's the descriptor's job.

### Descriptor — the meat, in one breath

State exactly what's plotted. Include:

- **Subject** (what's measured)
- **Geography or scope** (where / which subset)
- **Period or year** (when)
- **Units** (%, $bn, log scale, m)

Wrapping is automatic; you can also force a break with `\n`. Examples:

- `"Selected European cities, 2025, log scale"`
- `"Russia-Ukraine war, February 24th 2022 to May 14th 2026, m"`
- `"Average age gap of married couples*, by income of wife, years"`
- `"United States, CPI, % year on year"`

Footnote markers (`*`, `†`, `‡`, `§`) auto-superscript anywhere in the
title or descriptor — write plain text.

### Footnotes — clarify specific words, not the whole chart

Attach via `footnotes(fig, "*Cohabiting", "†Employed with an income",
source=...)`. The leading character pairs to the marker in the
title/descriptor. Three common categories:

- **Method clarifications** — `"*Cohabiting"`,
  `"*Based on location of workplace, not residence"`
- **Threshold definitions** — `"†30% of which is enough to pay rent on
  an average one-bedroom flat"`
- **Inclusion criteria** — `"*Where at least 50 are registered per year"`

### Source — always cite, label by entity or by file

- **External data** — name the source(s) by entity. Use `Source:` for one,
  `Sources:` for many.
  - `"Source: World Happiness Report 2026"`
  - `"Sources: DMSP Nighttime Lights; ESA; EUMETSAT; Institute for the
    Study of War; AEI's Critical Threats Project; NASA; WorldPop; The
    Economist"`
- **Internal / synthetic / experimental** — label by Python file name.
  - `"Source: bump_chart.py"`
  - `"Source: synthetic data, scatter_chart.py"`
- Pass via `finalize(source=...)` for simple cases, or
  `footnotes(..., source=...)` when packing alongside footnote markers.

**Hyperlinks in source / footnote text.** Use markdown link syntax:

```python
footnotes(
    fig,
    source="Source: [US Bureau of Labor Statistics](https://www.bls.gov/)",
)
```

SVG and PDF outputs preserve the link as an `<a href>` wrapper. PNG strips
URLs silently. The library only recognises `http://` and `https://` schemes.
Avoid placing a footnote marker (`*`, `†`) inside the `[display]` text — the
URL is dropped with a `UserWarning` because the marker splits the rendered
text into chunks the URL can't span.

### Before / after

| | Title | Descriptor | Source |
|---|---|---|---|
| Bad  | `"GDP growth rate, 2010–2024"` | `"Eastern Europe"` | `"BLS"` |
| Good | `"Eastern promise"` | `"Eastern European economies, real GDP growth, 2010–2024, % year on year"` | `"Source: World Bank"` |

The "bad" version puts the descriptor in the title slot and leaves the
finding unsaid. The "good" version makes the chart's point in the title,
moves units / geography / period to the descriptor, and names the source
by entity.

## Palette

Nine main colours in `PALETTE`: red, blue, cyan, green, yellow, olive,
purple, gold, grey. Default cycle leads with red. Pull a chart-type-specific
order with `cycle_for("bar" | "bar_stacked" | "line" | "scatter" | "bubble"
| "thermometer")`. `snapshot_palette(n, *, accent=None)` returns a
chronological slate→accent ramp for the "snapshots of the same series over
time" pattern.

Structural greys (all automatic in the theme): `C_SPINE` (zero-baseline
only), `C_GRID`, `C_LABEL`, `C_LABEL_MUTED`, `C_SOURCE` (75% black —
source + footnotes), `C_CI`, `C_BOX_FILL`, `C_BG`, `C_BG_TINT`,
`C_BG_TRANSPARENT`, `C_HIGHLIGHT_PANEL`, `C_HIGHLIGHT_PANEL_RED`.

Style overrides to apply on top:

- **Chronological categories** → light-to-dark tints of one colour, not the
  cycle. Use `snapshot_palette()`.
- **"Other" / "Don't know"** → `C_OTHER` (slate grey).
- **Positive vs. negative** → only differentiate by colour for *meaningful*
  pairs (imports/exports, gain/loss).

## API

### Theme, finalisation, layout

| Function                                                            | Purpose                                                |
|---------------------------------------------------------------------|--------------------------------------------------------|
| `set_theme(bg=None, transparent=True)`                              | Apply theme globally. Call once.                       |
| `finalize(ax, title, descriptor, source, *, marker="delta", auto_layout=True, …)` | Title stack, optional marker, source line, y-axis right. Auto-sizes margins. |
| `panel_label(ax, label)`                                            | Bold sub-heading + dark rule (faceted charts).         |
| `footnotes(fig, *notes, source=None, wrap=True, check_anchors=True)` | Smart-packing footnote strip + optional source line. Auto-superscripts `*, †, ‡, §, **, ††, ‡‡, §§`. Long notes word-wrap to fit the figure (`wrap=True`, default). Warns when a leading marker has no anchor in the title/descriptor (`check_anchors=True`). |
| `y_axis_label(ax, text, *, unit=None)`                              | Horizontal title above the y-axis; `unit=` renders below in muted colour. |
| `year_axis(ax, *, abbreviate=True)`                                 | Date x-axis formatter: first year full, subsequent two-digit. |

### Chart helpers

| Function                                                            | Purpose                                                |
|---------------------------------------------------------------------|--------------------------------------------------------|
| `cycle_for(chart_type) → list[str]`                                 | Recommended colour order for a chart type.             |
| `snapshot_palette(n, *, accent=None)`                               | Chronological slate→accent ramp for snapshot lines.    |
| `bar_h(ax, categories, values, *, highlight_max=True)`              | Horizontal bars; max in `C_RED` by default.            |
| `bar_v(ax, categories, values, *, highlight_max=True, log=False, headroom=1.25, y_formatter=None)` | Vertical bars; handles spine/grid/tick boilerplate. `log=True` gives symlog + auto decade ticks. |
| `bar_value_labels(ax, bars, *, fmt="{:,.0f}", formatter=None, fontsize=9)` | Annotate each bar with its value above the bar. Pass `formatter` for currency / mixed units. |
| `bar_sublabels(ax, bars, labels, *, fontsize=8, offset_pt=4)`       | Per-bar secondary text below the baseline (denominators, "n=…"). Auto-pads x-tick labels down to clear the band. |
| `dumbbell(ax, categories, start, end, *, label_start, label_end)`   | Before/after dot-and-line. Defaults red→blue.          |
| `thermometer(ax, categories, values, *, series_labels, dot=True)`   | Tick-and-dot ranked categories. Warns above 4 series.  |
| `threshold_lollipop(ax, categories, values, *, threshold=1.0)`      | Horizontal lollipop with fixed centre + leader lines.  |
| `bump_chart(ax, ranks, *, highlight, aspect=…)`                     | Rank-over-time PCHIP-smoothed lines with white halo at crossings. |
| `scatter_standard(ax, x, y)`                                        | General-trend scatter, 50% opacity, no stroke.         |
| `scatter_highlight(ax, x, y)`                                       | Outlier / labelled scatter, 100% opacity.              |
| `scatter_category(ax, x, y)`                                        | Bubble dot, 50% fill + 0.3px stroke for overlap.       |
| `trend_line(ax, x, y)`                                              | Dashed 1px trend line.                                 |
| `smoothed_line(ax, x, y, *, color)`                                 | Three-layer scatter + CI band + smoothed line.         |
| `ci_fill(ax, x, lo, hi, *, color=None)`                             | CI band. Salmon by default; pass colour to match line. |

### Annotations

| Function                                                            | Purpose                                                |
|---------------------------------------------------------------------|--------------------------------------------------------|
| `callout(ax, xy, text, *, xytext, arrow=True)`                      | Pale-fill text callout with optional arrow.            |
| `highlight_panel(ax, x_start, x_end, *, label=None)`                | Vertical event-period band.                            |
| `highlight_label(ax, xy, text, *, role="primary")`                  | Single-point label. `"secondary"` = grey/caps/light.   |
| `index_marker(ax, x, *, y=100)`                                     | Red rule + black dot for index charts.                 |
| `broken_axis(ax, *, axis="y", side="left")`                         | Non-zero-baseline squiggle. Line/scatter/thermometer.  |
| `number_box(ax, xy, n)`                                             | Numbered cross-reference box.                          |
| `threshold_arrows(ax, threshold, *, left_text, right_text)`         | Directional label pair straddling a threshold.         |

### Labels, axes, legends

| Function                                                            | Purpose                                                |
|---------------------------------------------------------------------|--------------------------------------------------------|
| `label_lines(ax, *, stroke=False)`                                  | Direct labels at line ends with collision avoidance.   |
| `inset_tick_labels(ax, *, axis="x")`                                | First tick label `ha="left"`, last `ha="right"`.       |
| `italicize_labels(ax, labels)`                                      | Italicise specific tick labels in place.               |
| `style_labels(ax, *, italic=(), bold=())`                           | Per-label italic/bold preserving tick colour.          |
| `color_axis(ax, side, color, *, spine=True, ticks=True)`            | Colour a spine + ticks + labels to match a series.     |
| `right_axis(ax)`                                                    | Apply right-axis convention to a panel.                |
| `smart_legend(ax)`                                                  | Frameless legend in the emptiest corner.               |
| `top_legend(fig, handles, labels, *, x=0.02)`                       | Frameless top-anchored legend under the title-stack.   |

### Verification

| Function                                                            | Purpose                                                |
|---------------------------------------------------------------------|--------------------------------------------------------|
| `verify_layout(fig, *, tolerance=0.005)`                            | Warn when any text artist (tick labels, titles, legends, footnotes) extends past the figure bounds. Catches the class of bug where `savefig(bbox_inches="tight")` silently expands the saved canvas to fit overflow. Auto-called by `footnotes()`. |

## Workflow

### Build

1. `set_theme()`.
2. (If not the default cycle) `ax.set_prop_cycle(color=cycle_for("…"))`.
3. Plot — `ci_fill` and `highlight_panel` first so they sit behind the data.
4. Annotate — `callout`, `highlight_label`, `index_marker`, `broken_axis`.
5. Direct label — `label_lines(ax)` over `smart_legend(ax)` for line charts.
6. `finalize(ax, title, descriptor, source)` last — auto-sizes margins.
7. Faceted: `panel_label()` per axes; call `fig.subplots_adjust(...,
   hspace=…, wspace=…)` first, then `finalize()` on the first axes with
   `title_x` pinned, `y_start=0.075`, and `auto_layout=False`.

### Review

**Building the chart is half the job. Reading it back is the other half.**
Every figure should be opened (with the `Read` tool inline, or in a viewer)
and evaluated against the story it was made to tell. Don't ship a draft.

For each rendered figure, answer three questions before moving on:

1. **Does the chart tell its intended story at a glance?**
   If the reader needs body text to know what to look at, the title is
   doing too little. Re-read the title — does it state the *finding*, or
   only the topic? "Eastern promise" tells you what to see; "GDP growth,
   2010–2024" doesn't. Iterate until the title carries the story alone.

2. **Is every element earning its place?**
   Bars at the rounding-noise threshold, legends that duplicate direct
   labels, gridlines that don't anchor anything, sub-labels nobody will
   read, decimal places past the data's precision — cut them. **Less data
   often makes the point sharper.** A six-row table reduced to its three
   meaningful rows is a better chart, not a smaller one. Apply the
   "Every element earns its place" core principle ruthlessly.

3. **Is this the right chart type?**
   Switching costs nothing — the script is ten lines.
   - Six-bucket bar chart trying to show "climbs then dips"? → **line
     chart**.
   - Two-series grouped bars comparing the same metric at two points in
     time? → **dumbbell**.
   - Scatter with 200 points and a single highlight? → **histogram +
     `callout`** (or `scatter_standard` + `scatter_highlight`).
   - Pie / doughnut with more than four slices? → **`bar_h`** ranked.
   - "How does X depend on Y" with strong trend? → **`smoothed_line`**,
     not raw scatter.
   - Long-form ranking change over time? → **`bump_chart`**, not stacked
     bars.

   The chart-type table in `cycle_for()` and the per-type rules in the
   core design principles are the reference.

If any answer is "no" or "kind of", iterate — re-title, cut elements, or
switch chart type. The first render is a draft. `verify_layout()` (auto-
called from `footnotes()`) catches mechanical overflow bugs, but it
cannot tell you whether the chart is *good* — that part is editorial,
not mechanical.

## Development

Hot reload during chart iteration:

    uv run graphs-watch

Watches `graphs/` and `examples/` for `.py` changes and re-renders the
affected examples + the comparison strip in parallel. The watcher routes
by path:

- `graphs/**/*.py` or `examples/_data.py` → regen all examples + comparisons
- `examples/build_comparisons.py` → comparisons only
- `examples/<name>.py` → that one example + comparisons

### Comparison harness

`examples/build_comparisons.py` composes side-by-side images for visual
review:

- `url`-kind entries download a Medium-hosted PNG and stack it above our
  replica (used for the "Mistakes, we've drawn a few" redesigns).
- `local_ref`-kind entries use a local reference image (e.g. the styleguide
  page for the thermometer chart).

Generated comparisons land in `examples/comparisons/<name>.png` (gitignored —
the reference images aren't ours to redistribute).

`examples/fetch_refs.py` populates `examples/comparisons/_originals/` for the
daily-chart replicas: it downloads the Economist "2019 daily charts" grid and
cuts it into per-chart reference cells (rows are located via the red Economist
tag that tops every chart — blank-gap heuristics misfire on detached
titles/footnotes).

CSVs fetched at runtime by example scripts are cached under
`examples/.data/` via `examples/_data.py::load_csv_text(url)`.

## Examples

Runnable scripts in `examples/`. Each one is the worked example for a
specific helper or pattern combination.

- [`bar_chart.py`](./examples/bar_chart.py) — `bar_h` synthetic demo with default `highlight_max=True`.
- [`dumbbell_chart.py`](./examples/dumbbell_chart.py) — `dumbbell` before/after + right-aligned `top_legend` via `ax._dumbbell_handles`.
- [`faceted_chart.py`](./examples/faceted_chart.py) — three-panel layout: `panel_label` per axes, `right_axis`, `ci_fill`, `y_start=0.075` + `auto_layout=False`.
- [`scatter_chart.py`](./examples/scatter_chart.py) — `scatter_standard` + `scatter_highlight` + `trend_line` + `callout` for the outliers.
- [`thermometer_chart.py`](./examples/thermometer_chart.py) — `thermometer(dot=False)` 3-series variant, x-axis on top, frameless `top_legend`.
- [`index_chart.py`](./examples/index_chart.py) — `index_marker` + `highlight_panel` (Pandemic band) + secondary `highlight_label` + `broken_axis` + `label_lines`.
- [`line_chart.py`](./examples/line_chart.py) — `smoothed_line` (scatter + CI band + trend), custom `_LineBandHandler` legend, `year_axis(set_locator=False)`, `footnotes(source=)`.
- [`bump_chart.py`](./examples/bump_chart.py) — `bump_chart` with `highlight=`, `colors=` override, `right_labels=True`, `x_labels_top=True`, `aspect=0.85`; real WHR data via `_data.py`.
- [`corbyn.py`](./examples/corbyn.py) — `bar_h` + `style_labels(italic=, bold=)` for per-row emphasis; full-range scale fixes the original truncation.
- [`dogs.py`](./examples/dogs.py) — twin y-axis with `color_axis(spine=False, ticks=False)`, manual series titles via `render_text_with_superscripts`, `footnotes(source=)` packing two notes alongside the source.
- [`brexit.py`](./examples/brexit.py) — `scatter_standard` + Savitzky-Golay smoothed line, manual year ticks + `year_axis(set_locator=False)` + `inset_tick_labels` + `broken_axis(axis="both")`.
- [`us_trade.py`](./examples/us_trade.py) — stacked two-panel `sharex=True` layout: `panel_label`, `right_axis`, `inset_tick_labels`, source delegated to `footnotes(source=…)`.
- [`pensions.py`](./examples/pensions.py) — same-hue scatter with opacity-for-emphasis, italic OECD label via `FontProperties`, `y_axis_label(unit="% of GDP")`.
- [`eu_balance.py`](./examples/eu_balance.py) — side-by-side panels of pos+neg stacked bars, shared `top_legend`, `right_axis`, `footnotes(source=)`.
- [`affordability_chart.py`](./examples/affordability_chart.py) — `threshold_lollipop(threshold=1.0)` on a log x-axis + `threshold_arrows` straddling the threshold + two-note `footnotes`.
- [`age_gap_chart.py`](./examples/age_gap_chart.py) — chronological snapshot lines via `snapshot_palette(4)`, in-chart series labels, `broken_axis(side="right")`, right-anchored `footnotes(y=, x=)`.

### Daily-chart replicas

Faithful replicas of Economist daily charts (references via
`examples/fetch_refs.py`; comparisons via `examples/build_comparisons.py`).
Useful as worked examples of less-common chart shapes:

- [`australia_heat.py`](./examples/australia_heat.py) — diverging annual bars (positive red / negative blue) around a zero baseline.
- [`malaria.py`](./examples/malaria.py) — history line splitting into three dashed forecast paths inside a `highlight_panel` FORECAST band.
- [`co2_emissions.py`](./examples/co2_emissions.py) — variable-width Mekko bars (height = per-person CO2, width = population) + dashed global-average rule.
- [`christianity.py`](./examples/christianity.py) — two-point slope chart with endpoint dots and stacked value labels.
- [`graduate_pay.py`](./examples/graduate_pay.py) — dense `scatter_standard` cloud with reversed x-axis and a solid trend curve.
- [`generational_politics.py`](./examples/generational_politics.py) — survey-wave lines with PCHIP smoothing, gap segments in lighter tint, dotted average.
- [`uber_tips.py`](./examples/uber_tips.py) — vertical dumbbell/lollipop pairs with a ringed reference marker.
- [`us_refugees.py`](./examples/us_refugees.py) — annual bars + stepped policy-cap line (real published data).
- [`polluted_cities.py`](./examples/polluted_cities.py) — two-block ranked table with colour-graded value chips.
- [`arctic_warming.py`](./examples/arctic_warming.py) — latitude-profile dot-line over translucent range bars, x-axis on top.
- [`trump_sanctions.py`](./examples/trump_sanctions.py) — `bar_v` time series on presidential-era `highlight_panel` bands.
- [`populist_votes.py`](./examples/populist_votes.py) — 40-year two-series stacked bars, pixel-extracted values.
- [`plastic_bottles.py`](./examples/plastic_bottles.py) — stacked percentage bars + locator-globe inset.
- [`alcohol_drinkers.py`](./examples/alcohol_drinkers.py) — pictogram legend strip over three stacked 100% bars.
- [`language_speed.py`](./examples/language_speed.py) — two-panel ridgeline densities with `direction_label` cues.
- [`london_roads.py`](./examples/london_roads.py) — day×hour heatmap with discrete sampled colour scale and hand-built legend.
- [`elderly_screens.py`](./examples/elderly_screens.py) — two-panel stacked areas with shared scale.
- [`wework.py`](./examples/wework.py) — per-metric banded panels with paired bars and per-panel scales.
- [`millennial_parents.py`](./examples/millennial_parents.py) — `snapshot_palette` generation lines vs mother's age.
- [`bad_bunny.py`](./examples/bad_bunny.py) — survey `bar_h` with x-axis on top.
- [`spending_convergence.py`](./examples/spending_convergence.py) — converging pair of lines, truncated axis signalled with `broken_axis`.
- [`gold_rally.py`](./examples/gold_rally.py) — indexed returns lines with `index_marker` and month-letter ticks.
- [`nuclear_warheads.py`](./examples/nuclear_warheads.py) — stacked `barh` inventories, top axis/legend, dashed forecast box.
