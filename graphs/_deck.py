"""Deck variants — the chart without its headline furniture.

A deck slide carries the claim as slide text, so a figure embedded in a
deck should start at the chart itself: no marker, no title, no source
line, no footnotes. Everything the chart needs to stand alone stays —
axis labels, tick labels, legends, ``y_axis_label`` blocks,
``panel_label`` headings, callouts and the data.

The descriptor is the one conditional piece: in this house style the
descriptor IS the y-axis label (``finalize`` polices ``set_ylabel``), so
stripping it from a chart with no other y-axis labelling leaves bare
0–100 axes nobody can read. :func:`save_deck_variant` therefore keeps
the descriptor whenever the figure has no ``y_axis_label`` block and no
axes-level ylabel, and strips it (with the rest of the headline) when
either is present.

``finalize`` and ``footnotes`` tag every headline artist they create
(``_graphs_deck_strip``; the descriptor's artists additionally carry
``_graphs_deck_descriptor``); :func:`save_deck_variant` removes the
tagged artists from a pickled clone of the figure and saves the result
as ``<stem>_deck<suffix>`` beside the full chart.
"""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path

import matplotlib.pyplot as plt

from graphs._finalize import _y_axis_label_specs


def _has_y_axis_labelling(fig) -> bool:
    """True when the chart carries y-axis labelling that survives the strip.

    Either a :func:`~graphs.y_axis_label` block (its artists still live on
    the figure) or an axes-level ylabel — which ``finalize`` only lets
    through as ``allow_ylabel=True``, i.e. a deliberate coordinate-plot or
    ``twinx`` label.
    """
    if _y_axis_label_specs(fig):
        return True
    return any(ax.get_ylabel().strip() for ax in fig.axes)


def _strip_headline(fig, *, keep_descriptor: bool = False) -> int:
    """Remove the artists tagged by ``finalize``/``footnotes``; return the count found.

    A figure ``suptitle`` is headline furniture too (scripts that title a
    multi-panel figure with a raw ``fig.suptitle`` used to need a manual
    ``_graphs_deck_strip`` tag) — it is removed unconditionally.

    With ``keep_descriptor=True`` the descriptor's artists (tagged
    ``_graphs_deck_descriptor`` by ``finalize``) stay on the figure. They
    still count toward the return value — the count answers "did finalize
    run?", not "how many were removed" — so a kept descriptor never trips
    the caller's nothing-to-strip warning.
    """
    found = 0
    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None and suptitle.get_text():
        suptitle.remove()
        found += 1
    for artist in (*list(fig.texts), *list(fig.artists)):
        if artist is suptitle:  # already gone; a manually tagged suptitle must not double-remove
            continue
        if not getattr(artist, "_graphs_deck_strip", False):
            continue
        found += 1
        if keep_descriptor and getattr(artist, "_graphs_deck_descriptor", False):
            continue
        artist.remove()
    return found


def save_deck_variant(fig, path, *, dpi: int = 150) -> Path:
    """Save ``<stem>_deck<suffix>`` beside ``path`` — the chart without its
    marker, title, source line and footnotes.

    The descriptor stays when it is the chart's only y-axis labelling (no
    ``y_axis_label`` block, no axes ylabel): the descriptor is the house
    style's y-axis label, and a deck variant without any statement of the
    measured quantity is unreadable. A kept descriptor keeps its footnote
    markers even though the footnotes themselves are stripped — prefer a
    marker-free first descriptor line on charts that lean on this.

    Call it after ``finalize`` (and ``footnotes``, if used) and after saving
    the full chart. The figure is cloned via pickle so the live figure is
    untouched; when a figure won't pickle (e.g. a ``lambda`` inside a
    ``FuncFormatter``) the strip happens in place instead — make this the
    figure's last save in that case.

    Args:
        fig: The finalized figure.
        path: Path the full chart was saved to; the deck path derives from
            it (``figures/foo.png`` → ``figures/foo_deck.png``).
        dpi: Raster resolution; matches ``save_chart``'s 150 default.

    Returns:
        The path of the written deck variant.
    """
    path = Path(path)
    deck_path = path.with_name(f"{path.stem}_deck{path.suffix or '.png'}")
    try:
        target = pickle.loads(pickle.dumps(fig))
        cloned = True
    except Exception:
        target, cloned = fig, False
    keep_descriptor = not _has_y_axis_labelling(target)
    if _strip_headline(target, keep_descriptor=keep_descriptor) == 0:
        warnings.warn(
            "save_deck_variant: no headline artists found to strip — call it "
            "after finalize()/footnotes(), or this graphs is older than the "
            "figure code expects.",
            UserWarning,
            stacklevel=2,
        )
    target.savefig(deck_path, dpi=dpi, bbox_inches="tight")
    if cloned:
        plt.close(target)
    return deck_path
