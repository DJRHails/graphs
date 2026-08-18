# Headline conventions

Full conventions for the strings passed to `finalize(title=, descriptor=,
source=)` and `footnotes(...)`. Derived from two hand-review rounds over
touchstone research figures (2026-07-07); every worked example below is a
real before → after from those rounds.

The figure text is an **inverted pyramid**. Each row answers the reader's
next question, and every fact sits on the lowest row that still serves it:

| Row | Question it answers | Carries | Never carries |
|---|---|---|---|
| Title | What question does this graph answer? | The graph's question, simple and specific, in plain reader-facing language. Coined terms starred\* or rewritten away. | Takeaway claims (brittle — they rot on a re-run), new winks, second clauses, condition tags, methodology. |
| Descriptor | What exactly is plotted? | Measured quantity + axis mapping, one sentence — or nothing, if an on-chart label already names it. | Model ids, protocol knobs, sample sizes, condition tags, CI machinery. |
| Footnotes | What do the words mean; under what conditions? | Starred definitions first (with a concrete example), then conditions + model. | CI/whisker mechanics, epistemic status tags, project-internal commentary. |
| Source | Where is this from? | `Source: <dataset> (N=…); <script>` | A bare filename; an unnamed dataset; a placeholder N. |

Two global bans cut across every row:

- **Statistics machinery appears in ink only.** Draw the whiskers and the
  bands; never caption them. "95% Wilson CI", "bootstrap CI band",
  "Whiskers: 95% Wilson CI on the total rate" — all deleted in review,
  every time they appeared, in every row including the source line.
- **The figure speaks to an external reader.** No project-internal
  references ("the two-factor prediction", "RESEARCH flagged this…"), no
  epistemic status tags ("an unvalidated instrument") — status and
  confidence live in the research doc, not on the figure. If a footnote
  needs the lab notebook to parse, rewrite or cut it.

## Title — the graph's question, simple and specific

Revised 2026-08-18 (maintainer review): titles pose the graph's question;
they no longer state the takeaway claim. The earlier claim-title convention
("Claude Opus 4.8 outscores the specialised guard models") proved brittle
in practice — a data-derived title rots the moment a re-run, a model bump,
or a new slice moves the number, to the point of needing verb hacks
(`"lifts" if b >= f else "drops"`) to stay honest — and it duplicates the
finding that already lives in the chart and the surrounding prose. The
question form names what the graph is *for* and stays true on every
re-render.

- **Pose the question in plain reader-facing language.**
  - ✗ `"Outclassing the guardians"` (wink, topic-only)
  - ✗ `"Claude Opus 4.8 outscores the specialised guard models"`
    (takeaway claim — brittle)
  - ✓ `"How do the guard models compare on policy-violation F1?"`
  - ✗ `"The budgeted watchlist lifts mismatch AUROC from 0.967 to 0.987"`
    → ✓ `"How well does each arm separate matched harm from its
    negatives?"`
- **Specific enough that the chart visibly answers it.** "How does
  category distance influence cross-firing?" is answerable by the drawn
  panels; "What about cross-firing?" is not. If the drawn data can't
  settle the question, it's the wrong question (or the wrong chart).
- **One question.** No appendix clauses, no stacked sub-questions.
- **Where the finding goes instead:** the chart itself (emphasis colour,
  direct labels, callouts on the load-bearing comparison) and the caption
  or surrounding prose, which can carry the quantified claim and be
  updated with the text around it.
- **Don't write winks.** The Economist house wink ("Eastern promise",
  "Bremorse") survives in the `examples/` replica gallery, not on research
  figures — a generated wink is nearly always worse than the plain
  question. An *existing* wink survives review only when it decodes on
  sight into the exact mechanism: "Marking your own homework" stayed (it
  *is* self-review, the experiment's manipulation), while "Anatomy of a
  miss" — a strong wink, but topic-only — lost to a plain question. The
  test: does the wink carry the story, or just gesture at the subject?
- **Jargon: star it or rewrite it away.** A coined term the title needs
  gets a `*` and a footnote definition (`continuity* rules`,
  `Crossfire*`, `guilt*`); jargon the reader doesn't need is rewritten
  out. Naming the dataset in the title is fine (`"DynaBench over-firing
  driven by continuity* rules"`).
- **No condition parentheticals** — "(semantic, thinking off)" is
  footnote material.
- **Length:** one line at 12pt bold — roughly ≤70 characters, shorter is
  better.

## Descriptor — what is plotted, or nothing

- **Default: measured quantity + axis mapping, one sentence.**
  `"DynaBench policy-violation F1 (FAIL = violation)"`;
  `"Per-decoy false-positive rate (watched-but-absent behaviours) vs
  watchlist length (log₂ x)"`. This is the y-axis label written out —
  keep `ax.set_ylabel("")` (see the enforcement note below).
- **The metric is named exactly once** across title / descriptor /
  on-chart label. If a `y_axis_label()` or panel labels already carry it,
  the descriptor may be *empty* — don't restate. If the title is
  literally descriptive of the metric, the descriptor carries only what's
  missing.
- **It may instead carry the one qualifying sentence that makes the title
  honest** — the mechanism (`"The robust Opus-specific gap is the CLERK
  legit-cover (recipient hidden in tool args + a legit clearing transfer
  of identical shape)."`) or the evidence-strength read (`"Limited
  evidence given the overlap; but the trend only seems to apply to
  same-category cross-fires."`) — but only if self-contained.
  `"Contradicts the two-factor prediction (arms coincide): …"` was
  rejected in review: the reader has no idea what the two-factor
  prediction is.
- **Evicted from the descriptor, always:** model ids ("Claude Opus 4.8 ·"
  → footnotes), protocol knobs ("localized protocol, uncapped budget,
  seed 0" → footnotes or deleted), condition tags ("identical haystack,
  semantic needle" → footnotes), sample sizes (→ source), CI machinery
  (→ nowhere).
- **Redundancy dies.** A descriptor clause the legend already states
  ("dotted = one global 1%-FPR cut…") is cut, not moved.
- **Say the parenthesis.** A parenthetical that *glosses* jargon should
  replace it: "harm load N (strands blended into one transcript)" →
  "Number of harmful strands blended into one transcript". Parens
  carrying genuine secondary qualifiers survive: "(pooled, categories
  with n>=5)".

**In code, the matplotlib y-axis label stays empty.** The descriptor (or a
`graphs.y_axis_label(ax, text, unit=...)` horizontal title) is the y-axis
label; a hardcoded `ax.set_ylabel("text")` duplicates or contradicts it.
Exceptions — a `twinx()` secondary axis or a coordinate plot (ROC: y=TPR,
x=FPR; scatter) whose axes are dimensions — pass
`finalize(..., allow_ylabel=True)`. Enforced twice: `finalize()` raises on
a non-empty y-label, and `enforcement/rules/no-hardcoded-ylabel.yml` flags
it at lint time. On a horizontal value chart (dumbbell, `bar_h`) whose
descriptor sits far from the value axis, a bare-metric `x_axis_label()`
("correctness AUROC") is welcome — especially under a surviving wink.

## Footnotes — definitions first, then conditions

- **Starred definitions lead**, written `*term: plain-words definition`,
  with a concrete example where one helps:
  - `*levels are the number of buckets that the score range supplies,
    e.g. 0-10 → 11 levels, 1-5 → 5 levels`
  - `*Crossfire is where a real harm triggers another category of
    monitor. So here cyber → X`
  - `*null: the completion runs out of tokens before the answer tag;
    scored as wrong.`
- **Anchor the star where the reader meets the term** — title,
  descriptor, a legend entry (`Self-attributed*`), or a panel label. Every
  non-obvious term *anywhere on the figure* gets a definition: a `cua`
  panel label needs one as much as a coined title term. (`footnotes()`
  warns on orphan markers; keep anchors real.)
- **Plain words in definitions.** "Opus 4.8's verbalised 0-100
  harmfulness score of the probed transcript", not "category-free read of
  the exact probed artifact".
- **Conditions + model come after the definitions**, blank-line separated:
  `"Official DynaGuard protocol, CoT mode, temperature 0.6; unparseable
  outputs scored wrong (N=0 for Opus 4.8)."` — note the count: any
  population a footnote mentions gets its number.
- **Banned here** (worth repeating): whisker/CI explanations, epistemic
  status tags, notebook commentary addressed to the project.

## Source — `Source: <dataset> (N=…); <script>`

- **Name the dataset by entity, attach its N, script last.** `Sources:`
  when several. External citations ride along. Real settled examples:
  - `Sources: DynaBench (n=543); DynaGuard (Hoover et al. 2025), Table 3;
    dynabench_replication.py`
  - `Source: SWE-bench Verified borderline patches (n=24/class);
    fig3_auroc_separation.py. After Khullar et al. (2026), Fig 3`
  - `Source: DynaBench dynamic-policy episodes (N=200/seed × 3 seeds);
    dynamic_policy_divide.py`
  - `Sources: RoganInglis/apps-control-arena (85 backdoors vs 67 clean);
    SHADE buried-harm traces; recall_by_granularity.py`
- **Sample sizes live here** (not in the descriptor): N is provenance.
- **Every N is computed, never gestured at.** A `(N=??)` or a bracketed
  `[N per cell?]` is a to-do marker, not shippable figure text — look the
  number up (the script's own outputs, `.data/output/`, the writeup)
  before committing.
- Synthetic or experimental data cites the generating file; pass via
  `finalize(source=...)`, or `footnotes(..., source=...)` when packing
  alongside footnote markers.

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

Footnote markers (`*`, `†`, `‡`, `§`) auto-superscript anywhere in the
title, descriptor, source, footnote bodies or legend entry texts — write
plain text.

## Before / after

A real pair from the review rounds (figures/dynaguard/dynabench_f1.png):

| | Before (rendered) | After (settled) |
|---|---|---|
| Title | Outclassing the guardians | How do the guard models compare on policy-violation F1?† |
| Descriptor | DynaBench policy-violation F1\*, FAIL = violation, n=543; official DynaGuard protocol, CoT mode, temperature 0.6 | DynaBench policy-violation F1 (FAIL = violation) |
| Footnotes | \*95% bootstrap CI over examples; unparseable outputs scored wrong | Official DynaGuard protocol, CoT mode, temperature 0.6; unparseable outputs scored wrong (N=0 for Opus 4.8). |
| Source | Sources: DynaGuard (Hoover et al. 2025), Table 3; dynabench_replication.py | Sources: DynaBench (n=543); DynaGuard (Hoover et al. 2025), Table 3; dynabench_replication.py |

Every move is downward or out: the wink becomes the graph's question,
protocol drops to footnotes, n drops to the source, and the CI caption
leaves the figure.

†This pair pre-dates the 2026-08-18 question-title revision; the review
round originally settled on the claim title "Claude Opus 4.8 outscores the
specialised guard models", shown here updated to the question form.
