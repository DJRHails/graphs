# graphs

Economist-style chart theme for matplotlib and seaborn — global theme, title-stack
finaliser with renderer-measured wrapping, on-grid axis labels, direct line labels,
CI bands, and a catalogue of chart helpers (bars, dumbbells, thermometers, bump
charts, lollipops). IBM Plex Sans typography and a curated palette.

## Install

```bash
pip install djrhails-graphs
```

PyPI distribution is `djrhails-graphs` because the bare name `graphs` is taken.
The import package is `graphs`.

## Quick start

```python
import matplotlib.pyplot as plt
import numpy as np

from graphs import finalize, label_lines, save_chart, set_theme, subplots

set_theme()

x = np.arange(12)
fig, ax = subplots("wide")
ax.plot(x, 40 + 2.1 * x, label="Series A")
ax.plot(x, 58 - 1.3 * x, label="Series B")
label_lines(ax)
finalize(
    ax,
    title="State the finding, not the topic",
    descriptor="Country, metric, unit",
    source="Source: Organisation",
)
save_chart(__file__)
```

`finalize()` does the heavy lifting: auto-sized margins, title stack with the
delta marker (titles auto-wrap to the figure width), numeric y labels seated
on gridlines that extend under them, source line, right-hand y-axis.

**[SKILL.md](./SKILL.md) is the full manual** — design principles, headline
conventions, the complete API table, and a when-to-use index of 39 worked
examples in [`examples/`](./examples/).

### Palette

```python
from graphs import PALETTE, colors, C_RED, C_RED_BRAND, C_SPINE, C_GRID, C_LABEL
```

Nine named colours in `PALETTE` (red-led default cycle); structural greys for
spines/grid/labels/source; `cycle_for(chart_type)` for per-chart-type orders.

### Typography

IBM Plex Sans (headlines) and IBM Plex Sans Condensed (everything else) are
loaded automatically. If already registered in matplotlib's font manager, no
download occurs. Otherwise TTFs are fetched from `github.com/IBM/plex` on
first use and cached inside the installed package.

Fallback chain: IBM Plex Sans Condensed → IBM Plex Sans → Verdana → Arial →
DejaVu Sans.

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

## License

MIT. See [LICENSE](./LICENSE).
