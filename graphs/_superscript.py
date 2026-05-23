"""Automatic superscript rendering for footnote markers in text.

Strings like ``"Average wage* relative to renters' wage†"`` should render
``*`` and ``†`` as raised, smaller characters — the typographic convention
for footnote anchors. Callers don't need to use mathtext or markup; this
module detects markers automatically and renders the text as a sequence of
``Text`` artists positioned via the renderer.
"""

from __future__ import annotations

import matplotlib.font_manager as fm

from graphs._links import apply_url_to_artists

# Longest first so ``**`` matches before ``*``.
_FOOTNOTE_MARKERS: tuple[str, ...] = (
    "**",
    "‡‡",
    "§§",
    "††",
    "*",
    "†",
    "‡",
    "§",
)

# Typographic ratios — superscript chunks render at ``_SUP_SCALE`` of the
# base font size, with their baseline raised by ``_SUP_RISE`` of the base
# font size (matches the OpenType "sups" feature ballpark).
_SUP_SCALE: float = 0.80
_SUP_RISE: float = 0.1


def _split_for_superscript(text: str) -> list[tuple[str, bool]]:
    """Split ``text`` into (chunk, is_superscript) pairs at footnote markers.

    Markers stay attached to the preceding word (no leading whitespace inside
    the superscript chunk). Multi-char markers like ``**`` match before
    single-char ``*``. Returns an empty list for empty input.
    """
    if not text:
        return []

    out: list[tuple[str, bool]] = []
    buf: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        matched: str | None = None
        for marker in _FOOTNOTE_MARKERS:
            if text.startswith(marker, i):
                matched = marker
                break
        if matched is not None:
            if buf:
                out.append(("".join(buf), False))
                buf = []
            out.append((matched, True))
            i += len(matched)
        else:
            buf.append(text[i])
            i += 1
    if buf:
        out.append(("".join(buf), False))
    return out


def _has_marker(text: str) -> bool:
    """Cheap check — does ``text`` contain any footnote marker?"""
    return any(m in text for m in _FOOTNOTE_MARKERS)


def _subdivide_at_url_boundaries(
    chunks: list[tuple[str, bool]],
    line_offset: int,
    url_spans: list[tuple[int, int, str]],
) -> list[tuple[str, bool]]:
    """Further split marker-aware ``chunks`` at URL span start/end positions.

    ``chunks`` are the output of ``_split_for_superscript`` for a single line.
    ``line_offset`` is the line's start index in the original full string —
    needed because ``url_spans`` are indexed against that full string. Splits
    each chunk so URL boundaries always land on chunk boundaries; the
    downstream URL-tagging step can then mark whole chunks as belonging to a
    link without partial-coverage warnings.

    Returns a new list of chunks (no mutation). Preserves the
    ``is_superscript`` flag of the chunk being subdivided.
    """
    if not url_spans:
        return chunks

    # Collect breakpoints (relative to line start) where chunks must split.
    line_breaks: set[int] = set()
    for s_start, s_end, _ in url_spans:
        rel_start = s_start - line_offset
        rel_end = s_end - line_offset
        line_breaks.add(rel_start)
        line_breaks.add(rel_end)

    out: list[tuple[str, bool]] = []
    cursor = 0
    for chunk, is_sup in chunks:
        chunk_start = cursor
        chunk_end = cursor + len(chunk)
        # Find break points strictly inside this chunk.
        inner = sorted(b for b in line_breaks if chunk_start < b < chunk_end)
        if not inner:
            out.append((chunk, is_sup))
        else:
            last = chunk_start
            for b in inner:
                out.append((chunk[last - chunk_start : b - chunk_start], is_sup))
                last = b
            out.append((chunk[last - chunk_start :], is_sup))
        cursor = chunk_end
    return out


def render_text_with_superscripts(
    fig,
    x: float,
    y: float,
    text: str,
    *,
    fontsize: float,
    fontproperties: fm.FontProperties,
    color: str,
    va: str = "bottom",
    ha: str = "left",
    linespacing: float = 1.2,
    transform=None,
    url_spans: list[tuple[int, int, str]] | None = None,
):
    """Render ``text`` as a sequence of ``Text`` artists with superscripts.

    Splits ``text`` on footnote markers (``*``, ``†``, ``‡``, ``§`` and their
    doubled forms) and renders each chunk separately, with markers shown at
    a reduced size and raised baseline. Multi-line strings (``\\n``) are
    supported: each line is split and laid out independently, with the
    vertical advance computed from ``fontsize * linespacing``.

    Falls back to a single ``fig.text(...)`` call when no marker is present,
    preserving identical layout for strings that don't need processing.

    Args:
        fig: The figure to draw on.
        x: Anchor x in ``transform`` coords (defaults to ``fig.transFigure``).
        y: Anchor y in ``transform`` coords. Interpreted per ``va``.
        text: Text to render.
        fontsize: Base font size in points.
        fontproperties: Font properties for non-superscript chunks.
        color: Text colour.
        va: Vertical alignment, as for ``Text`` (``"bottom"``, ``"top"``,
            ``"center"``, ``"baseline"``). Applies to the whole block.
        ha: Horizontal alignment. Only ``"left"`` is supported when markers
            are present; ``"right"`` / ``"center"`` fall through to a
            measure-then-shift pass.
        linespacing: Line height multiplier (matches matplotlib's
            ``Text.linespacing``).
        transform: Coordinate transform; defaults to ``fig.transFigure``.

    Returns:
        The first (top-most) ``Text`` artist for the block, matching the
        return contract of ``fig.text`` when callers want a handle.
    """
    if transform is None:
        transform = fig.transFigure

    if not _has_marker(text) and not url_spans:
        return fig.text(
            x,
            y,
            text,
            transform=transform,
            fontsize=fontsize,
            fontproperties=fontproperties,
            color=color,
            va=va,
            ha=ha,
            linespacing=linespacing,
        )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = transform.inverted()

    lines = text.split("\n")
    n_lines = len(lines)

    # Vertical advance per line in transform-y units.
    fig_h_px = fig.get_figheight() * fig.dpi
    px_per_y = fig_h_px  # transFigure y in [0,1] over fig height
    # Generalise: 1 unit of transform-y corresponds to how many pixels?
    _, y0_px = transform.transform((0, 0))
    _, y1_px = transform.transform((0, 1))
    px_per_y = abs(y1_px - y0_px) or fig_h_px
    line_advance_y = (fontsize * linespacing) / 72.0 * fig.dpi / px_per_y

    # Vertical-align the block by adjusting the starting line's y.
    if va == "bottom":
        line_ys = [y + (n_lines - 1 - i) * line_advance_y for i in range(n_lines)]
        # Each line uses va="bottom" so baselines stack from y upward.
    elif va == "top":
        line_ys = [y - i * line_advance_y for i in range(n_lines)]
    elif va == "baseline":
        # Bottom line's baseline sits at y; lines above stacked upward.
        line_ys = [y + (n_lines - 1 - i) * line_advance_y for i in range(n_lines)]
    else:  # "center"
        total = (n_lines - 1) * line_advance_y
        top = y + total / 2
        line_ys = [top - i * line_advance_y for i in range(n_lines)]

    # Horizontal pixel advance helper.
    sup_fontsize = fontsize * _SUP_SCALE
    rise_px = fontsize * _SUP_RISE / 72.0 * fig.dpi

    first_artist = None

    # Collect (chunk, artist) pairs across all lines so we can apply URL
    # spans after rendering. Spans are indexed against the full ``text``
    # (including newlines), so we track a global character offset.
    all_chunks: list[tuple[str, bool]] = []
    all_artists: list = []
    global_offset = 0

    for line_idx, line in enumerate(lines):
        if line_idx > 0:
            # Account for the newline character separating logical lines.
            all_chunks.append(("\n", False))
            all_artists.append(None)
            global_offset += 1
        chunks = _split_for_superscript(line)
        if url_spans:
            chunks = _subdivide_at_url_boundaries(chunks, global_offset, url_spans)
        if va == "bottom":
            line_va = "bottom"
        elif va == "top":
            line_va = "top"
        elif va == "baseline":
            line_va = "baseline"
        else:
            line_va = "center"
        ly = line_ys[line_idx]

        # For ha != "left", measure full line width first so we can offset.
        if ha != "left":
            total_px = 0.0
            for chunk, is_sup in chunks:
                if not chunk:
                    continue
                fs = sup_fontsize if is_sup else fontsize
                t = fig.text(0, 0, chunk, fontsize=fs, fontproperties=fontproperties)
                bb = t.get_window_extent(renderer=renderer)
                total_px += bb.width
                t.remove()
            # Convert x anchor in transform coords to pixels, then shift.
            anchor_px = transform.transform((x, 0))[0]
            if ha == "right":
                cursor_px = anchor_px - total_px
            else:  # center
                cursor_px = anchor_px - total_px / 2
        else:
            cursor_px = transform.transform((x, 0))[0]

        for chunk, is_sup in chunks:
            if not chunk:
                continue
            fs = sup_fontsize if is_sup else fontsize
            # Translate cursor pixel x back into transform coords.
            cx = inv.transform((cursor_px, 0))[0]
            cy = ly
            if is_sup:
                cy_px = transform.transform((0, ly))[1] + rise_px
                cy = inv.transform((0, cy_px))[1]
            artist = fig.text(
                cx,
                cy,
                chunk,
                transform=transform,
                fontsize=fs,
                fontproperties=fontproperties,
                color=color,
                va=line_va,
                ha="left",
            )
            if first_artist is None:
                first_artist = artist
            bb = artist.get_window_extent(renderer=renderer)
            cursor_px += bb.width
            all_chunks.append((chunk, is_sup))
            all_artists.append(artist)
            global_offset += len(chunk)

    if url_spans:
        apply_url_to_artists(all_artists, all_chunks, url_spans)

    return first_artist
