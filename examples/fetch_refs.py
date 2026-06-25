# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow", "numpy", "requests"]
# ///
"""Fetch + segment reference images for the daily-chart replicas.

Downloads the Economist "2019 daily charts" grid (Medium-hosted) and cuts
it into per-chart cells named by replica slug, landing in
``examples/comparisons/_originals/`` (gitignored — the references aren't
ours to redistribute).

A second, non-downloadable reference (a 3x2 grid of 2025-26 daily charts
shared via clipboard) is segmented the same way when a local copy exists
at ``_originals/daily_2026_grid.png``.

Cells whose slug is ``None`` are maps or pictograms — out of scope for a
matplotlib-only replica — and are not extracted.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
ORIG_DIR = HERE / "comparisons" / "_originals"
ORIG_DIR.mkdir(parents=True, exist_ok=True)

MEDIUM_URL = (
    "https://miro.medium.com/v2/resize:fit:4800/format:webp/"
    "1*I6Sz_bMCmW0ZKjnWJPWOaw.png"
)

# (row, col) → slug. None = map/pictogram, skipped.
MEDIUM_SLUGS: dict[tuple[int, int], str | None] = {
    (0, 0): "australia_heat",
    (0, 1): None,  # chicken-size pictogram
    (0, 2): None,  # Europe safe-injection-sites map
    (0, 3): "malaria",
    (0, 4): None,  # Venezuela exodus map
    (0, 5): "co2_emissions",
    (0, 6): "christianity",
    (0, 7): "graduate_pay",
    (1, 0): None,  # world PM2.5 map
    (1, 1): "generational_politics",
    (1, 2): "uber_tips",
    (1, 3): "us_refugees",
    (1, 4): None,  # third-languages world map
    (1, 5): "polluted_cities",
    (1, 6): "arctic_warming",
    (1, 7): "trump_sanctions",
    (2, 0): "populist_votes",
    (2, 1): None,  # Congo rainforest map
    (2, 2): "plastic_bottles",
    (2, 3): "alcohol_drinkers",
    (2, 4): "language_speed",
    (2, 5): "london_roads",
    (2, 6): "elderly_screens",
    (2, 7): "wework",
}

# Standalone references downloaded by direct URL (not part of any grid).
DIRECT_REFS: dict[str, str] = {
    "european_warming": (
        "https://www.economist.com/cdn-cgi/image/width=600,quality=100,"
        "format=auto/content-assets/images/20260627_STC320.png"
    ),
}

DAILY_GRID = ORIG_DIR / "daily_2026_grid.png"
DAILY_COLS = [(0, 386), (386, 784), (784, 1165)]
DAILY_ROWS = [(0, 487), (487, 978)]
DAILY_SLUGS: dict[tuple[int, int], str | None] = {
    (0, 0): "millennial_parents",
    (0, 1): "bad_bunny",
    (0, 2): "spending_convergence",
    (1, 0): "gold_rally",
    (1, 1): None,  # AI-adoption world map
    (1, 2): "nuclear_warheads",
}


def _ink(im: Image.Image) -> np.ndarray:
    """Per-pixel deviation from the dominant background colour, 0..1."""
    arr = np.asarray(im).astype(float)
    flat = arr.reshape(-1, 3)
    sample = flat[:: max(1, len(flat) // 100_000)]
    vals, counts = np.unique(sample, axis=0, return_counts=True)
    bg = vals[counts.argmax()]
    return np.abs(arr - bg).max(axis=2) / 255.0


def _content_bands(profile: np.ndarray, min_size: int) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    start = None
    for i, c in enumerate(profile > 0.01):
        if c and start is None:
            start = i
        elif not c and start is not None:
            bands.append((start, i))
            start = None
    if start is not None:
        bands.append((start, len(profile)))
    return [b for b in bands if b[1] - b[0] >= min_size]


def _red_tag_row_starts(im: Image.Image, cols: list[tuple[int, int]]) -> list[int]:
    """Row starts = clustered y-positions of the red Economist tag in most columns."""
    arr = np.asarray(im).astype(float)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    red = (r > 150) & (g < 80) & (b < 80)
    votes = np.zeros(im.height, dtype=int)
    for x0, _ in cols:
        votes += (red[:, x0 : x0 + 70].sum(axis=1) >= 15).astype(int)
    tag_ys = np.where(votes >= len(cols) * 3 // 4)[0]
    starts: list[int] = []
    for y in tag_ys:
        if not starts or y - starts[-1] > 100:
            starts.append(int(y))
    return starts


def _save_cell(
    im: Image.Image, ink: np.ndarray, box: tuple[int, int, int, int], slug: str
) -> None:
    x0, y0, x1, y1 = box
    block = ink[y0:y1, x0:x1]
    ys, xs = np.where(block > 0.02)
    cell = im.crop(
        (
            max(0, x0 + int(xs.min()) - 4),
            max(0, y0 + int(ys.min()) - 4),
            min(im.width, x0 + int(xs.max()) + 5),
            min(im.height, y0 + int(ys.max()) + 5),
        )
    )
    dest = ORIG_DIR / f"{slug}.png"
    cell.save(dest)
    print(f"  → {dest.name} {cell.size}")


def fetch_medium() -> None:
    raw = ORIG_DIR / "daily_2019_grid.webp"
    if not raw.exists():
        print(f"↓ {MEDIUM_URL}")
        resp = requests.get(
            MEDIUM_URL, timeout=60, headers={"User-Agent": "graphs-skill/0.3"}
        )
        resp.raise_for_status()
        raw.write_bytes(resp.content)
    im = Image.open(raw).convert("RGB")
    ink = _ink(im)
    cols = _content_bands(ink.mean(axis=0), min_size=100)
    row_starts = _red_tag_row_starts(im, cols)
    edges = [y - 8 for y in row_starts] + [im.height]
    print(f"daily_2019_grid: {len(cols)} cols x {len(row_starts)} rows")
    for (r, c), slug in MEDIUM_SLUGS.items():
        if slug is None:
            continue
        x0, x1 = cols[c]
        _save_cell(im, ink, (x0, edges[r], x1, edges[r + 1]), slug)


def fetch_direct() -> None:
    """Download standalone references (single charts, not grid cells)."""
    for slug, url in DIRECT_REFS.items():
        dest = ORIG_DIR / f"{slug}.png"
        if dest.exists():
            print(f"  ✓ {dest.name} (cached)")
            continue
        print(f"↓ {url}")
        resp = requests.get(
            url, timeout=60, headers={"User-Agent": "graphs-skill/0.3"}
        )
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        print(f"  → {dest.name}")


def fetch_daily_grid() -> None:
    if not DAILY_GRID.exists():
        print(f"skip daily 2026 grid: {DAILY_GRID} not present (clipboard-sourced)")
        return
    im = Image.open(DAILY_GRID).convert("RGB")
    ink = _ink(im)
    print(f"daily_2026_grid: {len(DAILY_COLS)} cols x {len(DAILY_ROWS)} rows")
    for (r, c), slug in DAILY_SLUGS.items():
        if slug is None:
            continue
        x0, x1 = DAILY_COLS[c]
        y0, y1 = DAILY_ROWS[r]
        _save_cell(im, ink, (x0, y0, x1, y1), slug)


if __name__ == "__main__":
    fetch_medium()
    fetch_daily_grid()
    fetch_direct()
