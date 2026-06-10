# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow", "requests"]
# ///
"""Build comparison images for the "Mistakes, we've drawn a few" replicas.

For each chart this script either downloads a Medium-hosted reference
image (showing the Economist's original next to their redesign) or
loads a local reference (e.g. a styleguide page), and stacks our
replica below it with section captions. Output lands in
``examples/comparisons/`` — gitignored, since the reference images
aren't ours to redistribute.

Two entry kinds:
  * ``("url", "replica.png")`` — download + dual-caption ("original vs redesign").
  * ``{"local_ref": "_originals/<file>", "replica": "<file>.png",
       "ref_caption": "...", "replica_caption": "..."}`` — local single-reference.
"""

from __future__ import annotations

from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "comparisons"
ORIG_DIR = OUT_DIR / "_originals"
OUT_DIR.mkdir(exist_ok=True)
ORIG_DIR.mkdir(exist_ok=True)

# Chart key → entry. Two entry shapes are supported (see module docstring).
CHARTS: dict[str, dict] = {
    "corbyn": {
        "url": "https://miro.medium.com/v2/resize:fit:1400/1*9QE_yL3boSLqopJkSBfL5A.png",
        "replica": "corbyn.png",
    },
    "dogs": {
        "url": "https://miro.medium.com/v2/resize:fit:1400/1*RER4tyXsS086M1Y0K7bz_Q.png",
        "replica": "dogs.png",
    },
    "brexit": {
        "url": "https://miro.medium.com/v2/resize:fit:1400/1*9GzHVtm4y_LeVmFCjqV3Ww.png",
        "replica": "brexit.png",
    },
    "us_trade": {
        "url": "https://miro.medium.com/v2/resize:fit:1400/1*Ilu1H37M1soUh1GHhDa_IA.png",
        "replica": "us_trade.png",
    },
    "pensions": {
        "url": "https://miro.medium.com/v2/resize:fit:1400/1*4RND--Bo31DVfiziaa-HBA.png",
        "replica": "pensions.png",
    },
    "eu_balance": {
        "url": "https://miro.medium.com/v2/resize:fit:1400/1*GB8vGeGzMeueEbkpGTTZVQ.png",
        "replica": "eu_balance.png",
    },
    "thermometer_chart": {
        "local_ref": "_originals/thermometer.jpg",
        "replica": "thermometer_chart.png",
        "ref_caption": "Economist styleguide reference (page 17: thermometer charts)",
        "replica_caption": "Our replica using the graphs skill",
    },
    "bump_chart": {
        "local_ref": "_originals/bump.png",
        "replica": "bump_chart.png",
        "ref_caption": "Economist reference (bump chart)",
        "replica_caption": "Our replica using the graphs skill",
    },
    "line_chart": {
        "local_ref": "_originals/line_chart.png",
        "replica": "line_chart.png",
        "ref_caption": "Economist reference (line + scatter + CI band)",
        "replica_caption": "Our replica using the graphs skill",
    },
    "affordability_chart": {
        "local_ref": "_originals/affordability.png",
        "replica": "affordability_chart.png",
        "ref_caption": "Economist reference (threshold lollipop)",
        "replica_caption": "Our replica using the graphs skill",
    },
    "age_gap_chart": {
        "local_ref": "_originals/age_gap.png",
        "replica": "age_gap_chart.png",
        "ref_caption": "Economist reference (chronological snapshot lines)",
        "replica_caption": "Our replica using the graphs skill",
    },
}

# Daily-chart replicas: references are per-chart cells cut from two grid
# images by fetch_refs.py (run it once to populate _originals/).
DAILY_REPLICAS = [
    "australia_heat",
    "malaria",
    "co2_emissions",
    "christianity",
    "graduate_pay",
    "generational_politics",
    "uber_tips",
    "us_refugees",
    "polluted_cities",
    "arctic_warming",
    "trump_sanctions",
    "populist_votes",
    "plastic_bottles",
    "alcohol_drinkers",
    "language_speed",
    "london_roads",
    "elderly_screens",
    "wework",
    "millennial_parents",
    "bad_bunny",
    "spending_convergence",
    "gold_rally",
    "nuclear_warheads",
]
CHARTS.update(
    {
        slug: {
            "local_ref": f"_originals/{slug}.png",
            "replica": f"{slug}.png",
            "ref_caption": "The Economist — original daily chart",
            "replica_caption": "Our replica using the graphs skill",
        }
        for slug in DAILY_REPLICAS
    }
)

DEFAULT_URL_TOP = "The Economist — original (left) vs. their redesign (right)"
DEFAULT_URL_BOTTOM = "Our replica using the graphs skill"

CAPTION_HEIGHT = 32
PAD = 16
BG = (255, 255, 255)
TEXT = (63, 86, 97)  # C_LABEL
MAX_REF_WIDTH = 1400  # cap local refs so they don't dwarf the replica


def _font(size: int = 14) -> ImageFont.ImageFont:
    for candidate in (
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _download(url: str, dest: Path) -> Path:
    if not dest.exists():
        print(f"  ↓ {url}")
        r = requests.get(url, timeout=30, headers={"User-Agent": "graphs-skill/0.2"})
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def _captioned(img: Image.Image, caption: str, font: ImageFont.ImageFont) -> Image.Image:
    """Return a copy of img with a caption strip on top."""
    new = Image.new("RGB", (img.width, img.height + CAPTION_HEIGHT), BG)
    new.paste(img.convert("RGB"), (0, CAPTION_HEIGHT))
    draw = ImageDraw.Draw(new)
    draw.text((PAD, 6), caption, fill=TEXT, font=font)
    return new


def _stack(top: Image.Image, bottom: Image.Image, out: Path) -> Path:
    target_w = max(top.width, bottom.width)
    if top.width != target_w:
        top = top.resize((target_w, round(top.height * target_w / top.width)))
    if bottom.width != target_w:
        bottom = bottom.resize((target_w, round(bottom.height * target_w / bottom.width)))

    gap = 12
    combined = Image.new("RGB", (target_w, top.height + bottom.height + gap), BG)
    combined.paste(top, (0, 0))
    combined.paste(bottom, (0, top.height + gap))
    combined.save(out, "PNG", optimize=True)
    print(f"  → {out.relative_to(HERE)}")
    return out


def build(key: str, entry: dict) -> Path:
    print(f"• {key}")
    replica_name = entry["replica"]
    replica_path = HERE / replica_name
    if not replica_path.exists():
        raise FileNotFoundError(f"Replica missing: {replica_path}")
    replica = Image.open(replica_path)
    font = _font(14)
    out = OUT_DIR / f"{key}.png"

    if "url" in entry:
        orig_path = _download(entry["url"], ORIG_DIR / f"{key}.png")
        orig = Image.open(orig_path)
        top = _captioned(orig, DEFAULT_URL_TOP, font)
        bottom = _captioned(replica, DEFAULT_URL_BOTTOM, font)
        return _stack(top, bottom, out)

    if "local_ref" in entry:
        ref_path = HERE / "comparisons" / entry["local_ref"]
        if not ref_path.exists():
            raise FileNotFoundError(f"Local reference missing: {ref_path}")
        ref = Image.open(ref_path)
        # Cap reference width so a giant styleguide scan doesn't dwarf the replica.
        if ref.width > MAX_REF_WIDTH:
            ref = ref.resize(
                (MAX_REF_WIDTH, round(ref.height * MAX_REF_WIDTH / ref.width))
            )
        top = _captioned(ref, entry.get("ref_caption", "Reference"), font)
        bottom = _captioned(replica, entry.get("replica_caption", "Our replica"), font)
        return _stack(top, bottom, out)

    raise ValueError(f"Entry {key!r} has neither 'url' nor 'local_ref'")


def main() -> None:
    for key, entry in CHARTS.items():
        build(key, entry)


if __name__ == "__main__":
    main()
