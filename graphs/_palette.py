"""Economist-style colour palette and visual constants.

Adapted from The Economist's web chart style guide, with two project overrides:

1. **Backgrounds are transparent**, not the styleguide `#E9EDF0` pale blue-grey.
2. **Accent red stays `#bf352b`** (our brand). The styleguide reserves the
   bright `#E3120B` for the masthead marker and uses `#DB444B` (duller dusty
   red) for data series — we collapse both roles into our single red so the
   title rule and the highlighted data element share one accent.
"""

from collections.abc import Iterator, Mapping

# ----------------------------------------------------------------------------
# Background and structural colours
# ----------------------------------------------------------------------------
# Default to white. Pass `bg=C_BG_TRANSPARENT` to `set_theme()` for a
# transparent background, or `bg=C_BG_TINT` for the styleguide pale
# blue-grey.
C_BG = "#FFFFFF"
C_BG_TRANSPARENT = "none"
C_BG_TINT = "#E9EDF0"  # styleguide "BOXES/NAV" tint — opt-in

# Spine and grid greys — same as before, slightly desaturated for transparency.
C_SPINE = "#1A1A1A"  # zero-baseline + bottom spine
C_GRID = "#D9D9D9"  # horizontal gridlines
C_LABEL = "#404040"  # dark slate — primary text (was #1A1A1A near-black)
C_TEXT = "#3F5661"  # body text (subtitle, source, ticks)
C_LABEL_MUTED = "#758D99"  # secondary text (FORECAST / ESTIMATE / "Other")
C_SOURCE = "#404040"  # source/footnote text — 75% black per Economist styleguide
C_BOX_FILL = "#E9EDF0"  # callout boxes, highlight panels (styleguide c22.5 k15)

# ----------------------------------------------------------------------------
# Accent red — single source of truth
# ----------------------------------------------------------------------------
# Styleguide separates brand red (#E3120B, masthead) from data red (#DB444B).
# We use one accent for both roles. Keep #bf352b unless explicitly overridden.
C_RED = "#bf352b"
C_RED_BRAND = "#E3120B"  # styleguide masthead red — opt-in only
C_RED_DATA = "#DB444B"  # styleguide data red — opt-in only

# Salmon CI band — kept from previous version, complements our red.
C_CI = "#f5c5b8"

# ----------------------------------------------------------------------------
# Main data palette (9 colours, styleguide order)
# ----------------------------------------------------------------------------
# Named entries so chart-type orderings can reference them by role rather than
# by index. The default `colors` cycle leads with our red so single-series
# charts pick it up automatically.
PALETTE = {
    "red": "#bf352b",  # our accent (replaces #DB444B from the styleguide)
    "blue": "#006BA2",
    "cyan": "#3EBCD2",
    "green": "#379A8B",
    "yellow": "#EBB434",
    "olive": "#B4BA39",
    "purple": "#9A607F",
    "gold": "#D1B07C",
    "grey": "#758D99",
}

# Default cycle — red first so unmarked single-series charts get the accent.
colors = [
    PALETTE["red"],
    PALETTE["blue"],
    PALETTE["cyan"],
    PALETTE["green"],
    PALETTE["yellow"],
    PALETTE["purple"],
    PALETTE["grey"],
    PALETTE["olive"],
    PALETTE["gold"],
]

# ----------------------------------------------------------------------------
# Per-chart-type colour orders (from the Economist web styleguide)
# ----------------------------------------------------------------------------
# Use `cycle_for(chart_type)` to get the recommended order. Pass the result
# to `ax.set_prop_cycle(color=...)` before plotting.
_CYCLES = {
    "bar": ["blue", "cyan", "yellow", "green", "red", "purple"],
    "bar_stacked": ["blue", "cyan", "yellow", "green", "red", "blue"],
    "line": ["cyan", "red", "yellow", "blue", "green", "purple"],
    "scatter": ["cyan", "red", "yellow", "blue", "green", "purple"],
    "bubble": ["cyan", "red", "yellow", "blue", "green", "purple"],
    "thermometer": ["cyan", "red", "yellow", "blue", "green", "purple"],
}


def cycle_for(chart_type: str) -> list[str]:
    """Return the styleguide colour order for a given chart type.

    Args:
        chart_type: One of "bar", "bar_stacked", "line", "scatter", "bubble",
            "thermometer". Unknown types fall back to the default cycle.
    """
    names = _CYCLES.get(chart_type)
    if names is None:
        return list(colors)
    return [PALETTE[n] for n in names]


# ----------------------------------------------------------------------------
# Special-purpose colours
# ----------------------------------------------------------------------------
C_OTHER = PALETTE["grey"]  # "Other" / "Don't know" buckets
C_HIGHLIGHT_PANEL = "#E9EDF0"  # subtle event-period band (web)
C_HIGHLIGHT_PANEL_RED = "#f5c5b8"  # red-tinted event band (rare emphasis)


# ----------------------------------------------------------------------------
# Concept colours — one meaning per hue across a figure set
# ----------------------------------------------------------------------------
class ConceptColors(Mapping[str, str]):
    """Read-only concept → hex map; see :func:`concept_colors`."""

    def __init__(self, resolved: dict[str, str]) -> None:
        self._colors = dict(resolved)

    def __getitem__(self, concept: str) -> str:
        try:
            return self._colors[concept]
        except KeyError:
            raise KeyError(
                f"no colour for concept {concept!r}; known concepts: "
                f"{sorted(self._colors)}. Add it to the concept_colors() map "
                "shared by the figure set rather than picking a one-off colour."
            ) from None

    def __iter__(self) -> Iterator[str]:
        return iter(self._colors)

    def __len__(self) -> int:
        return len(self._colors)

    def __repr__(self) -> str:
        return f"ConceptColors({self._colors!r})"


def _resolve_color(concept: str, color: str) -> str:
    if color in PALETTE:
        return PALETTE[color].lower()
    if color.startswith("#") and len(color) in (4, 7):
        return color.lower()
    raise ValueError(
        f"concept {concept!r}: colour {color!r} is neither a PALETTE name "
        f"({', '.join(PALETTE)}) nor a #rgb / #rrggbb hex"
    )


def concept_colors(mapping: Mapping[str, str]) -> ConceptColors:
    """Fix one colour per concept for a whole figure set.

    Define the map once in a module every figure script imports, then
    colour each concept through it everywhere it appears — its line or bar,
    its direct label, value labels, group labels and token chips — so a
    reader who learns "blue = after RL" on the first figure reads every
    later figure without a legend. The deck/paper variants inherit the
    colours unchanged.

        COLORS = concept_colors({"Base model": "grey", "Cue": "yellow",
                                 "After RL": "blue"})
        ax.bar(x, y, color=COLORS["After RL"])

    Args:
        mapping: Concept name → ``PALETTE`` name (``"blue"``) or hex string.

    Returns:
        A read-only mapping of concept → hex. Looking up an unmapped concept
        raises ``KeyError`` naming the known concepts.

    Raises:
        ValueError: On an unknown colour name, or when two concepts share a
            colour — a shared hue makes the two concepts indistinguishable,
            which is the ambiguity the map exists to prevent.
    """
    resolved = {concept: _resolve_color(concept, color) for concept, color in mapping.items()}
    owners: dict[str, str] = {}
    for concept, hex_color in resolved.items():
        if hex_color in owners:
            raise ValueError(
                f"concepts {owners[hex_color]!r} and {concept!r} share colour "
                f"{hex_color}; give each concept its own hue"
            )
        owners[hex_color] = concept
    return ConceptColors(resolved)


# ----------------------------------------------------------------------------
# Chronological snapshot ramp
# ----------------------------------------------------------------------------
def _hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{int(round(c * 255)):02x}" for c in rgb)


def _mix(a: str, b: str, t: float) -> str:
    """Linear-interpolate between two hex colours; t in [0, 1]."""
    ra, ga, ba = _hex_to_rgb(a)
    rb, gb, bb = _hex_to_rgb(b)
    return _rgb_to_hex((ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t))


def snapshot_palette(n: int, *, accent: str | None = None) -> list[str]:
    """Generate a chronological colour ramp slate → accent across ``n`` steps.

    Used for "snapshot lines" charts where each line is the same metric at a
    different point in time, oldest → newest. Earlier snapshots fade to
    muted slate-greys; the most recent snapshot is the accent colour at full
    saturation, so the eye reads "today" first.

    Args:
        n: Number of snapshots (≥ 2 for a meaningful ramp).
        accent: Final colour. Defaults to ``PALETTE["red"]``.

    Returns:
        List of ``n`` hex strings, ordered oldest → newest.
    """
    if n < 1:
        return []
    end = accent or PALETTE["red"]
    if n == 1:
        return [end]

    # Old end: dark slate. Penultimate: light tint of the accent (≈25% accent).
    # Inter-stops: 0 → dark slate, mid → light grey, then → light accent → accent.
    dark = C_LABEL  # "#3F5661"
    light_grey = "#B7C6CF"  # bridge tone between slate and the accent tint
    light_accent = _mix("#FFFFFF", end, 0.35)  # pale tint of the accent

    # Four canonical stops; resample to n.
    stops = [dark, light_grey, light_accent, end]
    if n == 2:
        return [dark, end]
    if n == 3:
        return [dark, light_accent, end]
    if n == 4:
        return stops

    # n > 4: linear interp along the 4-stop ramp.
    out = []
    for i in range(n):
        u = i * (len(stops) - 1) / (n - 1)
        lo = int(u)
        hi = min(lo + 1, len(stops) - 1)
        out.append(_mix(stops[lo], stops[hi], u - lo))
    return out
