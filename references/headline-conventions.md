# Headline conventions

Full conventions for the three strings passed to `finalize(title=, descriptor=, source=)`.

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

### Descriptor — label the y-axis, in one breath

The descriptor's first duty is to **name what's plotted: the measured
quantity and its units** — in effect, it is the y-axis label written out.
Read the title and descriptor *together*: between them they must answer
"what is this number?" Because the title is usually a wink (it states the
finding, not the metric), the descriptor is where the metric actually
gets named. A descriptor that gives only scope and period — leaving the
quantity itself unnamed — sends the reader hunting. This is the single
most common descriptor failure.

State, in order:

- **Subject — the measured quantity** (what the y-axis *is*). The part a
  wink title can't supply.
- **Geography or scope** (where / which subset)
- **Period or year** (when)
- **Units** (%, $bn, °C, years, log scale, m)

Wrapping is automatic; force a semantic break with `\n` (a semibold
subject lead over the scope/unit line). Examples — each names the
quantity:

- `"Average temperature anomalies by continent\nRelative to the 1991-2020 average, °C"`
  (`european_warming.py`; wink title "The Great European Bake Off")
- `"Average age gap of married couples*, by income of wife, years"`
- `"Eastern European economies, real GDP growth, 2010–2024, % year on year"`
- `"United States, CPI, % year on year"`

**Exception — when the title already names the metric.** If the title is
*literally descriptive* of the y-axis, the descriptor may drop the
quantity and carry only scope, period and scale. Only then is a
scope-only descriptor correct:

| Title | Descriptor | Why it works |
|---|---|---|
| `"Average wage* relative to renters' wage†"` | `"Selected European cities, 2025, log scale"` | The title *is* the y-axis label; the descriptor only adds the missing scope / period / scale. |
| `"Priced out"` (a wink) | `"Average wage relative to renters' wage, selected European cities, 2025, log scale"` | The wink says nothing about the metric, so the descriptor must name it. |

Same chart, different descriptors — driven by whether the title carries
the metric. Taken alone, `"Selected European cities, 2025, log scale"` is
**not** a model descriptor: it names where and when but never *what*, and
only reads correctly beneath a title that already does.

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
