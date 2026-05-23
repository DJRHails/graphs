# graphs

Economist-style chart theme for matplotlib and seaborn — global theme, title-stack
finaliser, direct line labels, CI bands, horizontal bars, and dumbbell charts.
Uses IBM Plex Sans typography and a curated 8-colour palette.

Version: 0.3.0

## Install

```bash
pip install djrhails-graphs
```

PyPI distribution is `djrhails-graphs` because the bare name `graphs` is taken.
The import package is `graphs`.

## Quick start

```python
import matplotlib.pyplot as plt
from graphs import ci_fill, finalize, label_lines, set_theme

set_theme()

fig, ax = plt.subplots()
fig.subplots_adjust(top=0.68, bottom=0.14, left=0.06, right=0.88)

ax.plot(x, y, label="Series A")
label_lines(ax)
finalize(
    ax,
    title="Bold chart title",
    descriptor="Country, metric, unit",
    source="Source: Organisation",
)
```

See `examples/` for runnable scripts:

- `line_chart.py` — multi-series line with CI bands + direct labels
- `faceted_chart.py` — three-panel faceted layout with panel labels
- `bar_chart.py` — horizontal bar with max-value highlight
- `dumbbell_chart.py` — before/after comparison with legend

## Public API

| Function | Purpose |
|----------|---------|
| `set_theme()` | Apply global rcParams (figure, axes, ticks, fonts, palette) |
| `finalize(ax, title, descriptor, source, *, y_axis_right, title_x, y_start, autoscale_y)` | Title stack, red rule, source line, y-axis tidy-up |
| `label_lines(ax, ...)` | Direct end-of-line labels with collision avoidance |
| `smart_legend(ax, ...)` | Pick the emptiest corner of the axes |
| `ci_fill(ax, x, y_lo, y_hi, *, color)` | Confidence-interval band |
| `bar_h(ax, categories, values, *, highlight_max)` | Horizontal bar chart |
| `dumbbell(ax, categories, start, end, ...)` | Dot-and-line before/after chart |
| `panel_label(ax, label)` | Bold panel sub-heading for facets |

### Palette

```python
from graphs import colors, C_BG, C_RED, C_SPINE, C_GRID, C_LABEL, C_TEXT, C_CI
```

Sequence `colors` (red primary, blue, teal, green, yellow, mauve, slate, coral).

### Typography

IBM Plex Sans is loaded automatically. If already registered in matplotlib's
font manager, no download occurs. Otherwise TTFs are fetched from
`github.com/IBM/plex` on first use and cached inside the installed package.

Fallback chain: IBM Plex Sans → Verdana → Arial → DejaVu Sans.

## License

MIT. See [LICENSE](./LICENSE).
