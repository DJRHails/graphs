# Relative framing

When to plot data **relative to a baseline or reference** — indexed,
normalized, anomaly, share, % change, per-capita — instead of as absolute
values, and how to label and mark the reference so the framing is honest
and unambiguous.

> A relative chart says "compared to *what?*" The descriptor and a marked
> reference line must answer that in the chart itself. An unlabelled
> relative axis is the single most common way these charts mislead.

## When to reframe — relative beats absolute when

- **The levels are incomparable but the *change* is the story.** Series of
  different magnitudes (one country's GDP vs another's, gold vs the S&P)
  don't share a y-axis honestly — **index to a common moment** so every
  line starts together and you read divergence in growth, not size. (See
  `index_chart.py`, `gold_rally.py`.)
- **The absolute number is meaningless without a yardstick.** A
  temperature in °C, a wage in €, a refugee count — the reader can't judge
  "high or low" without a comparison. Reframe as an **anomaly vs a baseline
  period** (`australia_heat.py`, `arctic_warming.py`, `european_warming.py`),
  a **ratio to a threshold** (`affordability_chart.py`), or **plot the
  reference alongside** (`co2_emissions.py`, `us_refugees.py`,
  `generational_politics.py`).
- **Direction around a neutral point is the point.** Surplus vs deficit,
  warmer vs cooler, above vs below average — use a **signed deviation around
  zero** so the sign carries the meaning (`eu_balance.py`,
  `australia_heat.py`).
- **The mix matters more than the total.** Who's gaining share — **share of
  total / 100% stacked** (`plastic_bottles.py`, `christianity.py`,
  `alcohol_drinkers.py`, `spending_convergence.py`).
- **A population/denominator difference would otherwise dominate.**
  Per-capita / per-GDP / per-unit normalizes out the size effect
  (`co2_emissions.py` per person, `pensions.py` % of GDP).

**Keep absolute** when the magnitude *is* the message (US trade deficit in
$bn, daily hours of media), when the reader needs to act on the raw number,
or when there's no honest common baseline. Don't index for the sake of it.

## Pick the kind — match the technique to the comparison

| Technique | Use when | Worked example |
|---|---|---|
| **Index to 100** | series of different magnitudes; "growth since a common moment" | `index_chart.py` (2015=100), `gold_rally.py` (Jan 1st 2025=100) |
| **Anomaly vs a baseline period** | a level only legible against a "normal" (climate, long-run mean) | `european_warming.py`, `australia_heat.py`, `arctic_warming.py` |
| **Signed deviation around zero** | direction (above/below, surplus/deficit) is the story | `eu_balance.py`, `australia_heat.py` |
| **Difference vs a reference group** | every value read against one chosen category | `uber_tips.py` (vs male drivers 21-25) |
| **Ratio / relative to a threshold** | "above the line = X, below = not"; proportional distance | `affordability_chart.py` (wage ÷ rent, threshold 1.0) |
| **Share of total / 100% stacked** | composition and how the mix shifts | `plastic_bottles.py`, `christianity.py`, `alcohol_drinkers.py` |
| **% change / % year on year** | rate of change matters more than level | CPI quick-start, survey "% responding" (`brexit.py`) |
| **Per-capita / per-denominator** | normalize out a size/population effect | `co2_emissions.py`, `pensions.py` |
| **Plot the reference alongside** | the gap between actual and a benchmark is the point | `us_refugees.py` (cap line), `co2_emissions.py` (global avg), `generational_politics.py` (national avg) |

For **proportional change across different magnitudes**, a **log scale**
reads equal % steps as equal distance (`affordability_chart.py`). Don't
log a chart whose point is absolute level.

## Choose and name the baseline

- **Name the normalization in the descriptor, every time.** The descriptor
  *is* the y-axis label — it must state what the number is relative to.
  Patterns seen across the replicas, copy them verbatim:
  - index — `"Real GDP, index, 2015 = 100"`, `"Returns, January 1st 2025=100"`
  - anomaly — `"Average temperature anomalies by continent\nRelative to the 1991-2020 average, °C"`, `"Deviation from 1961-90 average, °C"`, `"…relative to 1951-1980 average"`
  - reference group — `"Expected tip by Uber driver's age and gender\nRelative to male drivers aged 21-25, $"`
  - share — `"% of total"`, `"Global consumption spending, % of total"`
  - per-denominator — `"CO₂ emissions per person, 2017, tonnes"`, `"…% of GDP"`
  - rate — `"% year on year"`, `"% responding"`, `"% agreeing by generation"`
- **Pick a defensible baseline and disclose it.** A baseline period
  (1991-2020), an index date (2015), a reference group (male 21-25), a
  threshold (1.0) — the choice is editorial and changes the story. State
  it; if it needs justifying, use a footnote (`affordability_chart.py`'s
  `"†30% of which is enough to pay rent…"`).
- **The reference point should be a real, recognizable anchor** — a round
  index date, the global/OECD/national average, the policy cap — not an
  arbitrary midpoint.

## Mark the reference line — make the baseline unmistakable

- **Index level → `index_marker(ax, x, y=100)`.** Draws a thin red rule at
  the index value spanning the chart plus a black dot on the indexed point,
  so "= 100" is visually unambiguous. (`index_chart.py`, `gold_rally.py`.)
- **Anomaly / surplus-deficit straddling zero → the dark zero rule.**
  `finalize`'s `zero_rule=True` (default) draws a strong `C_SPINE`
  centreline on the zero baseline the data crosses, *under* the data lines,
  running the full gutter so "0" sits on it (`european_warming.py`). A bar
  chart that draws its own on-top `axhline(0)` keeps it (`eu_balance.py`,
  `australia_heat.py`) — `finalize` won't duplicate it.
- **Baseline on a different axis → suppress the auto rule.** When the value
  baseline is vertical (the y-axis is a coordinate like latitude),
  `finalize(zero_rule=False)` and draw your own `axvline(0)`
  (`arctic_warming.py`).
- **Reference group point → ring it and lead to it.** Mark the zero
  reference member with an edged/ringed marker, a short leader line, and a
  `"Reference"` label (`uber_tips.py`: the 21-25 male dot).
- **Reference *value* (average/cap/threshold) → a labelled line.** A dashed
  rule with an inline label — `"Global average 4.6"` (`co2_emissions.py`),
  a dotted `"National average"` (`generational_politics.py`), a red
  `"Annual cap"` line (`us_refugees.py`), or `threshold_arrows(threshold=1.0,
  left_text=…, right_text=…)` flanking the line (`affordability_chart.py`).
- **Share of total → the 0–100 axis is the baseline.** Set `ylim(0, 100)`
  (or `xlim`) and let the full-height stack carry it; no extra rule needed
  (`plastic_bottles.py`, `alcohol_drinkers.py`).
- **Non-zero baseline → signal it, never hide it.** An indexed or share
  chart cropped above zero must wear `broken_axis(ax)` (the heartbeat glyph
  in the tick-label column) on line / scatter / thermometer charts
  (`index_chart.py`, `spending_convergence.py`, `age_gap_chart.py`,
  `brexit.py`). **Never on a bar/column chart** — switch to a thermometer.

## Pitfalls

- **An unlabelled relative axis.** A bare "100" or "0" with no descriptor
  telling the reader the base date / baseline period / reference group is
  the cardinal sin. The marker shows *where* the baseline is; the descriptor
  says *what* it is. You need both.
- **Cherry-picked baseline.** Indexing to a trough or peak, or choosing a
  baseline period that flatters one series, fabricates the divergence.
  Pick a neutral anchor and disclose it.
- **Truncating a relative axis without the squiggle.** Cropping an index or
  share chart above zero exaggerates the swing — mark it with
  `broken_axis`, or start at zero. On bar charts, don't crop at all.
- **Mixing absolute and relative on one chart silently.** A per-capita
  height with an absolute-total area (`co2_emissions.py`) works only
  because *both* are named (descriptor: per person; on-bar labels: Gt).
  Label every quantity the chart shows.
- **Reframing when absolute was the point.** Indexing a deficit or a head
  count throws away the magnitude the reader came for. Reframe to expose a
  comparison, not by reflex.
- **A reference line that competes with the data.** Keep the benchmark
  recessive — dashed/dotted, muted or `C_SPINE`, *under* the data — unless
  the gap *to* it is the whole story, in which case make the bars recessive
  and the reference line the accent (`us_refugees.py`).
