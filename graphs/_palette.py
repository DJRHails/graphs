"""Economist-style colour palette and visual constants.

Adapted from The Economist's web chart style guide, with two project overrides:

1. **Backgrounds are transparent**, not the styleguide `#E9EDF0` pale blue-grey.
2. **Accent red stays `#bf352b`** (our brand). The styleguide reserves the
   bright `#E3120B` for the masthead marker and uses `#DB444B` (duller dusty
   red) for data series — we collapse both roles into our single red so the
   title rule and the highlighted data element share one accent.
"""

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
C_SPINE = "#1A1A1A"       # zero-baseline + bottom spine
C_GRID = "#D9D9D9"        # horizontal gridlines
C_LABEL = "#3F5661"       # dark slate — primary text (was #1A1A1A near-black)
C_TEXT = "#3F5661"        # body text (subtitle, source, ticks)
C_LABEL_MUTED = "#758D99"  # secondary text (FORECAST / ESTIMATE / "Other")
C_SOURCE = "#404040"      # source/footnote text — 75% black per Economist styleguide
C_BOX_FILL = "#E9EDF0"    # callout boxes, highlight panels (styleguide c22.5 k15)

# ----------------------------------------------------------------------------
# Accent red — single source of truth
# ----------------------------------------------------------------------------
# Styleguide separates brand red (#E3120B, masthead) from data red (#DB444B).
# We use one accent for both roles. Keep #bf352b unless explicitly overridden.
C_RED = "#bf352b"
C_RED_BRAND = "#E3120B"   # styleguide masthead red — opt-in only
C_RED_DATA = "#DB444B"    # styleguide data red — opt-in only

# Salmon CI band — kept from previous version, complements our red.
C_CI = "#f5c5b8"

# ----------------------------------------------------------------------------
# Main data palette (9 colours, styleguide order)
# ----------------------------------------------------------------------------
# Named entries so chart-type orderings can reference them by role rather than
# by index. The default `colors` cycle leads with our red so single-series
# charts pick it up automatically.
PALETTE = {
    "red":    "#bf352b",  # our accent (replaces #DB444B from the styleguide)
    "blue":   "#006BA2",
    "cyan":   "#3EBCD2",
    "green":  "#379A8B",
    "yellow": "#EBB434",
    "olive":  "#B4BA39",
    "purple": "#9A607F",
    "gold":   "#D1B07C",
    "grey":   "#758D99",
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
    "bar":           ["blue", "cyan", "yellow", "green", "red", "purple"],
    "bar_stacked":   ["blue", "cyan", "yellow", "green", "red", "blue"],
    "line":          ["cyan", "red", "yellow", "blue", "green", "purple"],
    "scatter":       ["cyan", "red", "yellow", "blue", "green", "purple"],
    "bubble":        ["cyan", "red", "yellow", "blue", "green", "purple"],
    "thermometer":   ["cyan", "red", "yellow", "blue", "green", "purple"],
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
C_OTHER = PALETTE["grey"]              # "Other" / "Don't know" buckets
C_HIGHLIGHT_PANEL = "#E9EDF0"          # subtle event-period band (web)
C_HIGHLIGHT_PANEL_RED = "#f5c5b8"      # red-tinted event band (rare emphasis)


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
    dark = C_LABEL          # "#3F5661"
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
