# graphs

Economist-style chart theme for matplotlib and seaborn — global theme, title-stack
finaliser with renderer-measured wrapping, on-grid axis labels, direct line labels,
CI bands, and a catalogue of chart helpers (bars, dumbbells, thermometers, bump
charts, lollipops). IBM Plex Sans typography and a curated palette.

It exists so that charts in the author's research and writing come out in one
consistent, publication-ready house style without hand-tuning each figure. The
same tree is both the `djrhails-graphs` PyPI package and the `graph-design` agent
skill ([`SKILL.md`](./SKILL.md)). **Status: active** — version 0.19.0 on PyPI,
95 commits since the May 2026 extraction from the author's dotfiles, last change
October 2026.

## Key takeaways

- **One call, `finalize()`, turns a plain matplotlib axes into a finished chart** —
  margins, title stack, on-grid y labels, source line. See [Quick start](#quick-start).
- **The layout engine is covered by a local test suite, not by CI.** 217 tests pass
  on a fresh `uv sync` (Python 3.13, 2026-10-17); no workflow runs them on push.
  [confidence: ~90% that the tested layout rules hold at this commit] See
  [What is verified](#what-is-verified-and-how).
- **Visual quality is checked by eye**, through 44 worked examples in
  [`examples/`](./examples/) and a side-by-side comparison harness against Economist
  originals. There are no automated image-diff tests.
  See [What is verified](#what-is-verified-and-how).
- **Conventions are enforced, not just documented**: `finalize()` raises on a
  hardcoded y-axis label, and two ast-grep rules lint chart code.
  See [Load-bearing design decisions](#load-bearing-design-decisions).
- **Main limitations**: matplotlib only; first use downloads fonts over the network;
  examples need Python 3.12+; the comparison reference images are not shipped.
  See [Scope and limitations](#scope-and-limitations).

Confidence tags are an assessment of the evidence in this repo (sample sizes, seeds,
intervals), added in a 2026-10 README audit; they are not new measurements.

**Contents:** [Install](#install) · [Quick start](#quick-start) ·
[Load-bearing design decisions](#load-bearing-design-decisions) ·
[What is verified](#what-is-verified-and-how) ·
[Scope and limitations](#scope-and-limitations) · [Provenance](#provenance) ·
[Development](#development) · [License](#license)

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

## Load-bearing design decisions

The library's value rests on two things more than on any single helper:

- **Layout is measured, not guessed.** `finalize()` sizes margins and wraps titles
  from renderer-measured text extents (`graphs/_finalize.py`), and `verify_layout()`
  warns when any text crosses the figure edge — because `savefig(bbox_inches="tight")`
  would otherwise silently widen the canvas instead of failing. Most of the test
  files in [`tests/`](./tests/) exercise this engine.
- **The style rules are enforced in code.** `finalize()` raises `ValueError` on a
  non-empty `ax.set_ylabel(...)` (opt out with `allow_ylabel=True` for twin axes or
  coordinate plots), and [`enforcement/`](./enforcement/README.md) ships ast-grep
  rules for the same convention plus a warning against captioning CI machinery.
  The rationale for the conventions themselves is in [SKILL.md](./SKILL.md) and
  [`references/`](./references/); it is a style judgement, not a measured result.

## What is verified and how

| Claim | Support | Confidence |
| --- | --- | --- |
| The test suite passes at this commit | `uv sync && uv run pytest -q`: 217 passed, 12 warnings, 2026-10-17, Python 3.13. The warnings are `verify_layout` `UserWarning`s raised by tests that exercise overflow paths. | high (~95%) |
| Tests run automatically on every change | Not true: [`.github/workflows/`](./.github/workflows/) holds LFS integrity, PyPI release and a dotfiles notifier, none of which runs `pytest`. | — |
| Releases reach PyPI | [`release.yml`](./.github/workflows/release.yml) publishes on a version tag or an untagged version on `main`; PyPI lists 0.19.0. | high (~95%) |
| Charts look right | 44 example scripts with committed PNGs, reviewed by eye; `examples/build_comparisons.py` stacks Economist originals above the replicas. No pixel-diff tests. | moderate — a reviewer's judgement |
| Used downstream | [RELEASING.md](./RELEASING.md) describes the dotfiles skill submodule and repos that pin a release tag. | high that it is consumed; usage breadth not measured |

## Scope and limitations

- **matplotlib/seaborn only.** Not for d3, plotly or spreadsheets.
- **Network on first use** unless IBM Plex is already installed: fonts are fetched
  from GitHub and cached in `graphs/_fonts_cache/`. If the download fails, the
  failure is logged only at `DEBUG` level and rendering silently falls back to
  DejaVu Sans (`graphs/_fonts.py`), so text metrics and layout will differ.
- **Python versions.** The package declares `>=3.10`; the examples need 3.12+ because
  `scipy` (example-only) is pinned for 3.12+ in `pyproject.toml`. Only 3.13 was run
  for this audit.
- **Loose runtime pins.** `requirements.txt` sets lower bounds only (matplotlib ≥ 3.7,
  numpy ≥ 1.24); only the versions in `uv.lock` were tested, and a different
  matplotlib could plausibly shift measured layout.
- **Example PNGs are in Git LFS**, so a clone without `git-lfs` gets pointer files.
- **Comparison images are not redistributed.** The harness downloads the Medium-hosted
  references, and `examples/fetch_refs.py` downloads the 2019 daily-chart grid, but the
  other `local_ref` entries must be supplied by hand under
  `examples/comparisons/_originals/`. `build_comparisons.py` stops at the first one
  that is missing.
- The most important missing piece is **CI that runs the tests**: today a regression
  is caught only if someone runs `pytest` locally before merging.

## Provenance

The code was extracted from the author's dotfiles in May 2026 (first commit,
`feat: initial release of graphs (extracted from dotfiles)`) and has grown through
small PRs, several followed by a code-review fix-up PR (the
`fix: resolve code review findings` commits). The chart conventions follow the
Economist's published style and its "Mistakes, we've drawn a few" redesigns, which
the examples replicate. This README section and the verification table were written
from the repo's code, workflows and history plus one local test run; no other
measurements were taken.

## Development

```bash
uv sync               # installs the dev group (pytest, scipy for the examples)
uv run pytest -q      # the test suite
```

Hot reload during chart iteration:

    uv run graphs-watch

Watches `graphs/` and `examples/` for `.py` changes and re-renders the
affected examples + the comparison strip in parallel. The watcher routes
by path:

- `graphs/**/*.py` or `examples/_data.py` → regen all examples + comparisons
- `examples/build_comparisons.py` → comparisons only
- `examples/<name>.py` → that one example + comparisons

Releases are cut with `bumpver`; see [RELEASING.md](./RELEASING.md).

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
