"""Deck variants — the chart without its headline furniture.

A deck slide carries the claim as slide text, so a figure embedded in a
deck should start at the chart itself: no marker, no title, no descriptor,
no source line, no footnotes. Everything the chart needs to stand alone
stays — axis labels, tick labels, legends, ``y_axis_label`` blocks,
``panel_label`` headings, callouts and the data.

``finalize`` and ``footnotes`` tag every headline artist they create
(``_graphs_deck_strip``); :func:`save_deck_variant` removes the tagged
artists from a pickled clone of the figure and saves the result as
``<stem>_deck<suffix>`` beside the full chart.
"""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path

import matplotlib.pyplot as plt


def _strip_headline(fig) -> int:
    """Remove every artist tagged by ``finalize``/``footnotes``; return the count.

    A figure ``suptitle`` is headline furniture too (scripts that title a
    multi-panel figure with a raw ``fig.suptitle`` used to need a manual
    ``_graphs_deck_strip`` tag) — it is removed unconditionally.
    """
    removed = 0
    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None and suptitle.get_text():
        suptitle.remove()
        removed += 1
    for artist in (*list(fig.texts), *list(fig.artists)):
        if artist is suptitle:  # already gone; a manually tagged suptitle must not double-remove
            continue
        if getattr(artist, "_graphs_deck_strip", False):
            artist.remove()
            removed += 1
    return removed


def save_deck_variant(fig, path, *, dpi: int = 150) -> Path:
    """Save ``<stem>_deck<suffix>`` beside ``path`` — the chart without its
    marker, title, descriptor, source line and footnotes.

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
    if _strip_headline(target) == 0:
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
