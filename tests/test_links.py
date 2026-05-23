"""Tests for the markdown-link helpers in `graphs._links`."""

from graphs._links import strip_links


def test_no_links_passthrough():
    text = "Source: scripts/figure_x.py"
    clean, spans = strip_links(text)
    assert clean == text
    assert spans == []


def test_https_link_strips_to_display_and_emits_span():
    text = "Source: [BLS](https://www.bls.gov/) and [BIS](https://www.bis.org/)"
    clean, spans = strip_links(text)
    assert clean == "Source: BLS and BIS"
    assert spans == [
        (len("Source: "), len("Source: BLS"), "https://www.bls.gov/"),
        (len("Source: BLS and "), len("Source: BLS and BIS"), "https://www.bis.org/"),
    ]


def test_http_link_recognised():
    clean, spans = strip_links("see [docs](http://example.com)")
    assert clean == "see docs"
    assert spans == [(len("see "), len("see docs"), "http://example.com")]


def test_relative_path_target_strips_without_span():
    """Non-URL targets render as plain display text — no `set_url` annotation.

    Regression test for the bug where source lines like
    `[scripts/foo.py](scripts/foo.py)` rendered literally with brackets
    because the old regex required `https?://`.
    """
    clean, spans = strip_links(
        "Source: [scripts/figure_x.py](scripts/figure_x.py)"
    )
    assert clean == "Source: scripts/figure_x.py"
    assert spans == []


def test_mixed_url_and_relative_targets():
    text = "Sources: [paper](https://arxiv.org/abs/2025.0001); [scripts/x.py](scripts/x.py)"
    clean, spans = strip_links(text)
    assert clean == "Sources: paper; scripts/x.py"
    assert spans == [(len("Sources: "), len("Sources: paper"), "https://arxiv.org/abs/2025.0001")]


def test_uppercase_scheme_recognised():
    clean, spans = strip_links("see [foo](HTTPS://example.com)")
    assert clean == "see foo"
    assert spans == [(len("see "), len("see foo"), "HTTPS://example.com")]


def test_other_scheme_treated_as_non_url():
    """ftp://, file://, mailto: etc. are stripped to display text, no span."""
    clean, spans = strip_links("contact [hi](mailto:foo@bar.com)")
    assert clean == "contact hi"
    assert spans == []
