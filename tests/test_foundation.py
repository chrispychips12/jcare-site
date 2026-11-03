import pytest

from conftest import contrast

# (foreground token, background token, minimum ratio)
TEXT_PAIRS = [
    ("ink", "paper", 4.5),
    ("ink-2", "paper", 4.5),
    ("ink", "panel", 4.5),
    ("ink-2", "panel", 4.5),
    ("link", "paper", 4.5),
    ("link", "panel", 4.5),
    ("on-field", "field-deep", 4.5),
    ("on-field", "field-mid", 4.5),
    ("on-accent", "accent", 4.5),
    ("paper", "ink", 4.5),  # checked option in the contact switch
    # V9 additions
    ("on-field", "field-glow", 4.5),  # careers / footer mesh glow that can sit under copy
    ("ink", "panel-tint", 4.5),  # feature tile in the services grid
    ("ink-2", "panel-tint", 4.5),
    ("ink", "panel", 4.5),  # promise cards, quote cards and the requirements panel on bands
    ("ink-2", "panel", 4.5),  # quote attribution
    ("hero-ink", "hero-wash", 4.5),  # hero copy on the scrim colour (alpha composite: test_soffit)
    ("link", "panel-tint", 3.0),  # the plus mark on the feature tile is non-text, 3:1
]
# Non-text: focus rings and the lime fill against the bands (WCAG 1.4.11)
UI_PAIRS = [
    ("accent", "field-deep", 3.0),
    ("on-field", "field-mid", 3.0),  # V9: focus ring on bands is on-field (lime on mid is 2.3:1)
    ("on-field", "field-glow", 3.0),
    ("focus", "paper", 3.0),
    ("focus", "panel", 3.0),
]


def test_cname_is_apex_domain(root):
    assert (root / "CNAME").read_text() == "jcarequalityservices.com.au\n"


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("fg,bg,minimum", TEXT_PAIRS + UI_PAIRS)
def test_token_contrast(tokens, theme, fg, bg, minimum):
    t = tokens[theme]
    ratio = contrast(t[fg], t[bg])
    assert ratio >= minimum, f"{theme}: --{fg} on --{bg} is {ratio:.2f}, needs {minimum}"


def test_sky_is_never_a_text_background(css):
    assert "background: var(--field-sky)" not in css
    assert "background-color: var(--field-sky)" not in css


def test_logo_greens_not_in_css(css):
    assert "#2E9B40" not in css.upper()
    assert "#1B7430" not in css.upper()


def test_reduced_motion_block_exists(css):
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_fonts_self_hosted(root, css, page):
    for name in [
        "bricolage-grotesque-500", "bricolage-grotesque-600",
        # V10 (findings Optimize 2): Plex Mono is subset to Basic Latin and renamed per its OFL
        "atkinson-hyperlegible-400", "atkinson-hyperlegible-700", "jcare-mono-400",
    ]:
        f = root / "assets" / "fonts" / f"{name}.woff2"
        assert f.exists() and f.stat().st_size > 1000, name
        assert f"assets/fonts/{name}.woff2" in css
    assert "fonts.googleapis" not in css
    assert not page.find("link", href=lambda h: h and "googleapis" in h)


def test_document_basics(page):
    assert page.html["lang"] == "en-AU"
    assert page.find("meta", attrs={"name": "viewport"})
    assert page.title and page.title.string.strip()
    skip = page.find("a", class_="skip")
    assert skip and skip["href"] == "#main"
    first_focusable = page.find(["a", "button"])
    assert first_focusable is skip
    assert page.find("main", id="main")


def test_no_pure_white_or_black(css):
    # Tinted neutrals only (impeccable colour law; V9 brief). Print keeps its own ink.
    import re

    screen = re.sub(r"/\*.*?\*/", "", css[: css.index("@media print")], flags=re.S)
    for bad in [r"#fff\b", r"#ffffff\b", r"#000\b", r"#000000\b", r"rgba\(255,\s*255,\s*255", r"rgba\(0,\s*0,\s*0", r"(?<![-\w])white(?![-\w])", r"(?<![-\w])black(?![-\w])"]:
        assert not re.search(bad, screen, re.I), bad


def test_blue_carries_about_half_the_page(page):
    # Drenched rhythm (findings Colorize 4): hero, how we work, careers and footer are blue;
    # support, testimonials and contact are light. The header sits over the hero.
    main_sections = page.find("main").find_all("section", recursive=False)
    drenched = [s.get("id") or "hero" for s in main_sections if {"band", "hero"} & set(s.get("class", []))]
    assert drenched == ["hero", "how-we-work", "careers"], drenched
    # V9b: the footer is a bookend of the hero (Soffit ground), still blue
    assert "bookend" in page.find("footer")["class"]
    light = [s.get("id") for s in main_sections if not {"band", "hero"} & set(s.get("class", []))]
    assert light == ["support", "testimonials", "contact"]


def test_lime_is_only_ever_a_fill_under_navy(css):
    # Every rule that paints with the accent as a background also sets the on-accent text colour,
    # and the accent is never a text colour.
    import re

    for rule in re.findall(r"[^{}]*\{[^{}]*\}", css):
        body = rule[rule.index("{"):]
        assert not re.search(r"(?<![-\w])color:\s*var\(--accent\)", body), rule.strip()[:80]
        if re.search(r"background(?:-color)?:\s*var\(--accent\)", body):
            assert "color: var(--on-accent)" in body, rule.strip()[:80]


def _soft_light_white(c, a):
    """W3C soft-light of a white source over channel c (0..1), composited at alpha a."""
    d = ((16 * c - 12) * c + 4) * c if c <= 0.25 else c ** 0.5
    return (1 - a) * c + a * d


def _grain_soft_light(hex_, a):
    ch = [int(hex_.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return "#" + "".join(f"{round(_soft_light_white(c, a) * 255):02X}" for c in ch)


def test_band_mesh_keeps_mid_blue_and_dots_away_from_copy(css):
    # V9 review carry-in: on-field over --field-mid with the dots and grain on top drops under
    # 4.5:1, so in the bands the mid stop and the dot field sit at the bottom (behind cards,
    # panels and padding), never in the top half where the eyebrow, heading and lead are.
    import re
    from conftest import _block_after

    for marker in ["\n.band::before {", "\n.band-values::before {", "\n.band-careers::before {"]:
        for m in re.finditer(r"radial-gradient\(([^,]*?) at ([\d.]+)% ([\d.]+)%, var\(--field-mid\)", _block_after(css, marker)):
            assert float(m[3]) >= 85, (marker, m[0])
    dots = _block_after(css, "\n.band-dots {")
    for m in re.finditer(r"mask-image: radial-gradient\([^)]* at ([\d.]+)% ([\d.]+)%", dots):
        assert float(m[2]) >= 85, m[0]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_band_copy_holds_contrast_with_grain(css, tokens, theme):
    # The stops that CAN sit under band copy (deep and the text-safe glow), with the band grain
    # (white noise, soft-light, up to 0.5 alpha x the layer opacity) at its strongest pixel.
    import re
    from conftest import _block_after

    light = float(re.search(r"\n\.band::after \{[^}]*opacity:\s*([\d.]+)", css)[1])
    dark_block = _block_after(css, "@media (prefers-color-scheme: dark) {\n  .band::after")
    opacity = light if theme == "light" else float(re.search(r"opacity:\s*([\d.]+)", dark_block)[1])
    grain = 0.5 * opacity
    t = tokens[theme]
    for stop in ["field-deep", "field-glow"]:
        ratio = contrast(t["on-field"], _grain_soft_light(t[stop], grain))
        assert ratio >= 4.5, f"{theme}: on-field over {stop} + grain is {ratio:.2f}"
