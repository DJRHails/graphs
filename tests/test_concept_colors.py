"""concept_colors: one fixed colour per concept across a figure set."""

import pytest

from graphs import PALETTE, concept_colors


def test_palette_names_and_hex_resolve():
    colors = concept_colors({"Base model": "grey", "After RL": "#2563EB"})
    assert colors["Base model"] == PALETTE["grey"].lower()
    assert colors["After RL"] == "#2563eb"
    assert list(colors) == ["Base model", "After RL"]
    assert len(colors) == 2


def test_unknown_concept_names_the_known_ones():
    colors = concept_colors({"Base model": "grey", "Cue": "yellow"})
    with pytest.raises(KeyError, match=r"'RL'.*\['Base model', 'Cue'\]"):
        colors["RL"]


def test_unknown_colour_name_fails_fast():
    with pytest.raises(ValueError, match="'Cue'.*'amber'"):
        concept_colors({"Cue": "amber"})


def test_two_concepts_one_colour_is_rejected():
    with pytest.raises(ValueError, match="'Base' and 'Control' share colour"):
        concept_colors({"Base": "grey", "Control": PALETTE["grey"]})


def test_shorthand_hex_is_the_same_colour():
    assert concept_colors({"Base": "#FA0"})["Base"] == "#ffaa00"
    with pytest.raises(ValueError, match="'Base' and 'Control' share colour #ffffff"):
        concept_colors({"Base": "#fff", "Control": "#ffffff"})


def test_malformed_hex_fails_fast():
    with pytest.raises(ValueError, match="'Cue'.*'#zzzzzz'"):
        concept_colors({"Cue": "#zzzzzz"})


def test_map_is_read_only():
    colors = concept_colors({"Base": "grey"})
    with pytest.raises(TypeError):
        colors["Base"] = "#000000"  # type: ignore[index]
