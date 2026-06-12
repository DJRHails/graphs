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
