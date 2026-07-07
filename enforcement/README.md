# graph-design enforcement

Structural lint rules that mechanically enforce the
[graph-design conventions](../SKILL.md#rules-at-a-glance) a reviewer would
otherwise have to catch by eye. These key on the *shape* of the syntax tree, so
they cover what a regex can't.

## Rules

- **`rules/no-hardcoded-ylabel.yml`** — flags a hardcoded non-empty
  `ax.set_ylabel("...")`. The title/descriptor *is* the y-axis label
  ([Headline conventions](../SKILL.md#headline-conventions)): name the quantity
  in `finalize(descriptor=...)` and leave `ax.set_ylabel("")`. It matches the
  `string_content` node (the text *between* the quotes), so it flags `"text"`,
  `'text'`, and f-strings while skipping `""` and whitespace-only labels.
  `severity: error` — a hardcoded label is a convention violation the author
  should fix, not merely note. `graphs.finalize()` enforces the identical rule
  at runtime (it raises `ValueError` on a non-empty y-label), so a chart is
  caught whether it is linted or just run. The AST can't see the genuine
  exceptions — a `twinx()` secondary axis, a coordinate plot (ROC/scatter), or a
  faceted panel with a per-panel quantity. At such a site, add a trailing
  `# ast-grep-ignore: no-hardcoded-ylabel` with the reason (the runtime twin
  opts out with `finalize(..., allow_ylabel=True)`).

- **`rules/no-ci-machinery-in-text.yml`** — flags "Wilson" / "bootstrap" /
  "95% CI" / "whisker" inside any string passed to `finalize()` or
  `footnotes()`. Statistics machinery appears in ink only
  ([Headline conventions](../references/headline-conventions.md)): draw the
  whiskers and `ci_fill` bands, never caption them. Scoped to those two calls,
  so computing helpers (`wilson_ci(...)`, bootstrap functions) are untouched.
  `severity: warning` while existing charts are swept; escalate to `error`
  once a consuming repo is clean.

## Using it in a consuming repo

Either (a) add this dir to your `sgconfig.yml` `ruleDirs:` when the skill is
vendored/submoduled at a known path, or (b) copy the rule files into your
own `.ast-grep/rules/`. Run via `ast-grep scan` under pre-commit / CI. Keep one
canonical source — don't re-derive the rule (the `string_content` match is
non-obvious, and the naive `regex: '\S'` on the whole `string` node over-fires
on `""` because the node text includes the quotes).

## Testing

`cd enforcement && ast-grep test` (uses `sgconfig.yml`).
