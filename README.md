# graphs

Economist-style chart theme for matplotlib and seaborn — global theme, title-stack
finaliser with renderer-measured wrapping, on-grid axis labels, direct line labels,
CI bands, and a catalogue of chart helpers (bars, dumbbells, thermometers, bump
charts, lollipops). IBM Plex Sans typography and a curated palette.

It exists so that charts in my research and writing come out in one consistent,
publication-ready house style without hand-tuning each figure. The same tree is
both the `djrhails-graphs` PyPI package and the `graph-design` agent skill
([`SKILL.md`](./SKILL.md)).

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
conventions, the complete API table, and a when-to-use index of 44 worked
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

### Layout and style checks

`finalize()` sizes margins and wraps titles from renderer-measured text extents,
and `verify_layout()` warns when any text crosses the figure edge, because
`savefig(bbox_inches="tight")` would otherwise silently widen the canvas.

`finalize()` raises `ValueError` on a non-empty `ax.set_ylabel(...)`; pass
`allow_ylabel=True` for twin axes or coordinate plots.
[`enforcement/`](./enforcement/README.md) ships ast-grep rules for the same
convention, plus one against captioning CI machinery.

## Limitations

- **matplotlib/seaborn only.** Not for d3, plotly or spreadsheets.
- **Network on first use** unless IBM Plex is already installed. If the font
  download fails, a warning is logged and rendering falls back to DejaVu Sans, so
  text metrics and layout will differ.
- **Python versions.** The package declares `>=3.10`, but the examples need 3.12+
  (their `scipy` dependency is pinned for 3.12+), and CI tests 3.13 only.
- **Loose runtime pins.** `requirements.txt` sets lower bounds only (matplotlib ≥ 3.7,
  numpy ≥ 1.24). CI tests the versions in `uv.lock`; a different matplotlib may shift
  measured layout.
- **Visual output is checked by eye**, through the worked examples and the
  comparison harness. There are no image-diff tests.
- **Example PNGs are in Git LFS**, so a clone without `git-lfs` gets pointer files.
- **Comparison reference images are not shipped.** See
  [Comparison harness](#comparison-harness).

## Development

```bash
uv sync               # installs the dev group (pytest, scipy for the examples)
uv run pytest -q      # the test suite
```

[`ci.yml`](./.github/workflows/ci.yml) runs the tests on Python 3.13 on every pull
request and push to `main`, and fails if the IBM Plex fonts don't load rather than
testing against the DejaVu fallback. A few `verify_layout` warnings in the test
output are expected: they come from tests that exercise the overflow paths.

Hot reload during chart iteration:

    uv run graphs-watch

Watches `graphs/` and `examples/` for `.py` changes and re-renders the
affected examples + the comparison strip in parallel. The watcher routes
by path:

- `graphs/**/*.py` or `examples/_data.py` → regen all examples + comparisons
- `examples/build_comparisons.py` → comparisons only
- `examples/<name>.py` → that one example + comparisons

Releases are cut with `bumpver`; see [RELEASING.md](./RELEASING.md).
[`release.yml`](./.github/workflows/release.yml) publishes to PyPI only after the
test suite passes.

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
titles/footnotes). The other `local_ref` images must be put in
`examples/comparisons/_originals/` by hand; `build_comparisons.py` stops at the
first one that is missing.

CSVs fetched at runtime by example scripts are cached under
`examples/.data/` via `examples/_data.py::load_csv_text(url)`.

## License

MIT. See [LICENSE](./LICENSE).
