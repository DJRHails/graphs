# Paper figures

How the house style adapts when the figure goes into a paper rather than an
article or a deck. Distilled in part from Sophie Wang's
[notes on writing a paper](https://www.sophielwang.com/blog/paper-writing)
(figure tips credited there to Phillip Isola); the worked references are
[`paper_cue_bars.py`](../examples/paper_cue_bars.py),
[`paper_benchmark_grid.py`](../examples/paper_benchmark_grid.py) (`row_emphasis`) and
[`paper_training_curves.py`](../examples/paper_training_curves.py) (`column_emphasis`) —
all three share one `concept_colors` map, as a paper's figures would.

## The caption carries the headline

A paper figure sits under a caption that states its question and its
conditions, so the in-figure title, source line and footnotes would say
everything twice. Build the chart with the full headline anyway — it is
what the chart says in the repo, in review and in a slide — and ship the
headline-free variant to the paper:

```python
save_chart(__file__, deck=True, formats=("png", "pdf"))
# -> fig.png, fig.pdf, fig_deck.png, fig_deck.pdf  (the _deck pair goes in the paper)
```

The `_deck` variant is the paper/caption variant: one strip serves both a
slide (the slide text carries the claim) and a paper (the caption does). It
keeps the descriptor when that is the chart's only statement of the measured
quantity, so the axis never goes unlabelled.

Size the figure at the paper's text width with `subplots("manuscript")`
(5.5in): embedded at its own width, 9pt ticks read as 9pt on the page.

## Vector output, text as text

`set_theme()` embeds TrueType (`pdf.fonttype = 42`) and keeps SVG text as
`<text>` (`svg.fonttype = "none"`), so `formats=("pdf",)` / `("svg",)` give
figures whose labels stay sharp at any zoom and can be selected, searched
and copied. Matplotlib's default (Type 3 glyph outlines) looks the same on
screen but breaks text search and some journal PDF pipelines. If the paper's
PDF is later compressed, choose settings that keep vectors and fonts rather
than downsampling the figures to images.

## Concept colours — one meaning per hue, across the whole set

A paper is a sequence of figures, and the reader learns its colour code once.
Fix it in one module every figure script imports:

```python
# figures/colors.py
from graphs import concept_colors

COLORS = concept_colors({
    "Base model": "grey",   # the control is neutral
    "Cue": "yellow",
    "After RL": "blue",
    "Chicken": "red",       # the story's own concept may take the accent
})
```

How it should work:

- **Every appearance of a concept uses its colour**: the bar or line, the
  value label above it, the bracket and group label below it, the token chip
  that names it. Coloured text is what lets a figure drop its legend — the
  reader matches label to mark by hue. Darken the hue for text so it reads on
  white (yellow especially).
- **A hue belongs to one concept for the whole set.** `concept_colors` refuses
  two concepts with one colour, and a lookup of an unmapped concept raises
  with the known names — add the concept to the shared map rather than
  picking a one-off colour in a single figure.
- **The control or baseline is grey**; the concept the paper is about can
  take `C_RED`, in which case don't also spend red on generic emphasis in
  that set.
- **Use the full hue range** between concepts. A narrow palette (three blues)
  costs contrast exactly where the reader must tell conditions apart.
- **Comparable elements share a shade level** — the same tint for every
  chip fill, the same darkening for every value label — so a difference in
  shade never reads as a difference in data.
- Variants (`_deck`, PDF) inherit the colours unchanged; nothing to redo.

## Literal tokens in monospace

Sans for labels (it sets the figure apart from the paper's serif body text),
monospace for anything literal: tokens, prompts, code, file names. The theme
maps `fontfamily="monospace"` to IBM Plex Mono — the same superfamily as the
Plex Sans labels, so a literal sits on the line at matching height and
weight. Set a literal as a chip: a monospace tick label (or text) with a
rounded box tinted in its concept's colour, as in `paper_cue_bars.py`. Plex
Mono has no `␣` (U+2423) glyph; show a leading space another way.

## Two-level x-axis

Per-bar labels go on major ticks; the group each run of bars belongs to goes
on minor ticks a pad lower, with a rule in the group's colour between the two
rows. `finalize` reserves both rows (minor tick labels count toward the
bottom band). Set `ax.xaxis.remove_overlapping_locs = False` when a group
label sits exactly under a bar, or matplotlib silently drops it.

## Spacing and order

- **Spacing groups.** Panels that sit close are compared first.
  `row_emphasis(fig)` (one entity per row, compare across it) and
  `column_emphasis(fig)` (the transpose) widen the gap between groups to the
  larger measured gap plus 18pt, before `finalize`.
- **Panel order follows the explanation.** Lead with what the reader must
  understand first (what changed in the model), end with the consequence
  (training efficiency), even if the experiments ran in the other order.

## Sketch the figure before the experiment

Storyboard each figure before running it: sketch the axes, the conditions and
the result you expect. The sketch turns an intuition into a falsifiable
prediction, and when the result disagrees with it the disagreement is the
finding — redraw the figure around what happened, not what was planned.
