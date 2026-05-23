"""Markdown-style hyperlink support for source / footnote text.

Strings like ``"Source: [BLS](https://www.bls.gov/)"`` should render as
``"Source: BLS"`` with the ``BLS`` substring carrying a URL annotation so
SVG/PDF backends emit ``<a href="...">`` wrappers around the affected glyphs.

This module provides:

* ``strip_links(text)`` — replace markdown links with their display text and
  return both the cleaned string and the character spans the URLs cover.
* ``apply_url_to_artists(artists, clean_text, spans)`` — given the list of
  ``Text`` artists the caller rendered for ``clean_text`` (in left-to-right
  order, one per chunk), call ``set_url(url)`` on each artist whose chunk
  falls entirely inside a link span.

For the common single-URL case (whole source line wraps one entity), the
helper degrades gracefully: every chunk inside the span gets the URL; PNG
silently drops it; SVG/PDF preserve it.

Limitations
~~~~~~~~~~~
* URL spans that cross chunk boundaries — e.g. a footnote marker inside the
  link's display text — emit a ``UserWarning`` and the URL is dropped for
  that span. Mark up either the marker outside the link, or accept the
  visual-only treatment.
* Only HTTP/HTTPS URLs are recognised (matches the markdown link regex).
"""

from __future__ import annotations

import re
import warnings

_LINK_PATTERN = re.compile(
    r"""(?x)              # verbose mode
    \[                    # opening bracket
    (?P<display>[^\]]+)   # display text — no nested brackets
    \]                    # closing bracket
    \(                    # opening paren
    (?P<url>https?://[^)]+)  # URL — http or https, no closing paren
    \)                    # closing paren
    """
)


def strip_links(text: str) -> tuple[str, list[tuple[int, int, str]]]:
    """Replace ``[display](url)`` with ``display``; return clean text + spans.

    Args:
        text: Source string containing zero or more markdown links.

    Returns:
        ``(clean_text, spans)`` where ``spans`` is a list of
        ``(start_char, end_char, url)`` tuples indexed into ``clean_text``.
        For strings without links, returns ``(text, [])``.
    """
    if "](" not in text:
        return text, []

    out: list[str] = []
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    last = 0
    for m in _LINK_PATTERN.finditer(text):
        prefix = text[last:m.start()]
        out.append(prefix)
        cursor += len(prefix)
        display = m.group("display")
        url = m.group("url")
        spans.append((cursor, cursor + len(display), url))
        out.append(display)
        cursor += len(display)
        last = m.end()
    out.append(text[last:])
    return "".join(out), spans


def apply_url_to_artists(
    artists: list,
    chunks: list[tuple[str, bool]],
    spans: list[tuple[int, int, str]],
) -> None:
    """Apply ``set_url`` to artists whose chunks fall inside a link span.

    ``artists`` and ``chunks`` are parallel lists in left-to-right order. The
    rendered text reconstructs to ``"".join(chunk for chunk, _ in chunks)``;
    each chunk's character offsets are computed by running totals. A chunk is
    URL-tagged when its half-open range ``[start, end)`` lies entirely within
    one of the ``spans``.

    Chunks that straddle a span boundary (e.g. a footnote marker inside the
    link's display text) trigger a ``UserWarning`` and the URL is dropped
    for that span. Mark up around the marker instead.
    """
    if not spans:
        return

    # Build per-chunk char ranges.
    offset = 0
    ranges: list[tuple[int, int]] = []
    for chunk, _is_sup in chunks:
        ranges.append((offset, offset + len(chunk)))
        offset += len(chunk)

    for span_start, span_end, url in spans:
        any_chunk_in_span = False
        straddle = False
        for (c_start, c_end), artist in zip(ranges, artists, strict=False):
            if c_end <= span_start or c_start >= span_end:
                continue  # chunk entirely outside span
            if c_start >= span_start and c_end <= span_end:
                any_chunk_in_span = True
                if artist is not None and hasattr(artist, "set_url"):
                    artist.set_url(url)
            else:
                straddle = True
        if straddle and not any_chunk_in_span:
            warnings.warn(
                f"graphs._links: URL span [{span_start}:{span_end}] -> "
                f"{url!r} straddles a chunk boundary (footnote marker inside "
                "link text?). URL dropped. Move the marker outside the "
                "[display](url) brackets.",
                stacklevel=2,
            )
        elif straddle:
            warnings.warn(
                f"graphs._links: URL span [{span_start}:{span_end}] -> "
                f"{url!r} partially overlaps a chunk; only fully-contained "
                "chunks were tagged.",
                stacklevel=2,
            )
