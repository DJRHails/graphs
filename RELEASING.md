# Releasing djrhails-graphs

This repo is **both** the `djrhails-graphs` PyPI package **and** the `graph-design`
agent skill (same tree). A release has to reach three kinds of consumer, so the
version lives in three files and is kept in lockstep by `bumpver`:

| file | field | consumed by |
| --- | --- | --- |
| `pyproject.toml` | `version` + `[tool.bumpver] current_version` | the wheel / PyPI |
| `graphs/__init__.py` | `__version__` | `import graphs; graphs.__version__` |
| `SKILL.md` | frontmatter `version:` | the vendored agent skill |

## Cut a release (one command, on `main`)

```bash
uv run --with bumpver bumpver update --patch   # or --minor / --major
git push --follow-tags origin main             # if bumpver's push didn't run
```

`bumpver` rewrites the three version files, commits `bump version X -> Y`, tags
`vY`, and pushes. The tag push triggers [`.github/workflows/release.yml`](.github/workflows/release.yml),
which builds the sdist+wheel and publishes to PyPI via OIDC trusted publishing.

**Do the bump as its own commit on `main` — never fold it into a feature PR.** A
version bump squash-merged from a PR drops bumpver's branch-local tag, so the
release never fires (that is how 0.11.1 and 0.11.2 shipped code with no tag and no
wheel). If it happens anyway, the release workflow **self-heals**: a push to `main`
whose `__version__` has no matching `vX.Y.Z` tag gets tagged and published
automatically. So "the version in code" is the single source of truth.

## Sync the consumers after a release

- **The agent skill** is vendored as a git submodule in `~/.files` at
  `modules/agents/skills/graph-design`. Point it at the new release and commit the
  bump in the `.files` superproject:

  ```bash
  git -C ~/.files submodule update --remote --recursive modules/agents/skills/graph-design
  git -C ~/.files commit -am "graph-design: bump to vY"
  ```

- **Downstream pins** (any repo that pins `djrhails-graphs` to a tag, e.g.
  touchstone's `pyproject.toml` `{ git = "…graphs.git", tag = "vX" }`) bump the tag
  and refresh the lock:

  ```bash
  # in the consumer repo, after editing the tag in pyproject.toml
  uv lock --upgrade-package djrhails-graphs
  ```
