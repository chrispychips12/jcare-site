"""Hero ground (V9): the Soffit WebGL2 gradient, adapted per the owner's asset brief, under an
Atelier-style circle window. Contracts that can be checked without a GPU live here; the visual
and pixel checks are recorded in the task report."""

import re

import pytest

from conftest import _block_after, contrast

JCARE_COLOURS = {
    "bgColor": "#061B4A",
    "colorA": "#0A3A9E",
    "colorB": "#2B6FD4",
    "colorC": "#0593C6",
    "colorD": "#E4F5C8",
}


@pytest.fixture
def soffit(root) -> str:
    return (root / "assets" / "soffit.js").read_text(encoding="utf-8")


def _config(js: str) -> dict[str, str]:
    block = _block_after(js, "const BASE =")
    return dict(re.findall(r"(\w+):\s*(\"#[0-9A-Fa-f]{6}\"|-?[\d.]+)", block))


def test_loaded_deferred_and_local(page):
    srcs = {s["src"]: s for s in page.find_all("script", src=True)}
    assert "assets/soffit.js" in srcs and srcs["assets/soffit.js"].has_attr("defer")


def test_canvases_are_decorative_and_start_hidden(page):
    canvases = page.select("canvas[data-soffit]")
    assert [c["data-soffit"] for c in canvases] == ["hero", "footer"]
    for canvas in canvases:
        assert "soffit" in canvas["class"]
        assert canvas.has_attr("hidden"), "no-JS / no-WebGL visitors keep the CSS field"
        assert canvas.find_parent(attrs={"aria-hidden": "true"}) is not None
    assert canvases[0].find_parent("section", class_="hero")
    assert canvases[1].find_parent("footer")


def test_css_field_fallback_is_present(page, css):
    for host in [page.find("section", class_="hero"), page.find("footer")]:
        assert host.select_one(".bookend-field")
    assert "radial-gradient" in _block_after(css, "\n.bookend-field {")


def test_engine_initialises_every_canvas(soffit):
    assert 'querySelectorAll("canvas[data-soffit]")' in soffit
    assert "PRESETS" in soffit and "footer:" in soffit


def test_shader_colour_maths_is_verbatim(soffit):
    for line in [
        "vec3 c = mix(uColorA, uColorB, smoothstep(0.00, 0.36, t));",
        "c = mix(c, uColorD, smoothstep(0.66, 1.00, t));",
        "col += uColorD * uGlow * pow(f, 4.0);",
        "col = mix(uBg, col, smoothstep(0.0, max(0.01, uSink), f) * 0.90 + 0.10);",
        "f = clamp((f - uMidpoint) * uContrast + 0.5, 0.0, 1.0);",
        "#version 300 es",
    ]:
        assert line in soffit, line


def test_recoloured_through_config_only(soffit):
    cfg = _config(soffit)
    assert "#E4F5C8" in soffit
    for key, hex_ in JCARE_COLOURS.items():
        assert cfg[key].strip('"').upper() == hex_, key
    for purple in ["#3a0f6b", "#7b3fd9", "#c43ff0", "#f02be0"]:
        assert purple not in soffit.lower()
    assert float(cfg["maxDpr"]) == 1


def test_engine_rules(soffit):
    assert re.search(r"getContext\(\s*\"webgl2\"", soffit)
    for needle in [
        "alpha: false", "antialias: false", "depth: false", "stencil: false",
        "IntersectionObserver", "visibilitychange", "prefers-reduced-motion: reduce",
        "0.105", "0.043", "4.167", "36.7", "2.2", "0.06",
        "drawArrays",
    ]:
        assert needle in soffit, needle
    # One frame is drawn before the first requestAnimationFrame, so the canvas never shows blank
    assert soffit.index("drawArrays") < soffit.index("requestAnimationFrame(")


def test_engine_cannot_throw_to_the_page(soffit):
    body = "\n".join(l for l in soffit.splitlines() if not l.lstrip().startswith("//")).strip()
    assert body.startswith("(") and body.rstrip(";").endswith(")()"), "one IIFE, nothing at top level"
    assert "try {" in soffit and "catch" in soffit
    for banned in ["fetch(", "XMLHttpRequest", "http://", "https://", "innerHTML"]:
        assert banned not in soffit, banned
    assert "not available" not in soffit.lower(), "no 'WebGL is not available' message on fallback"


def test_no_pause_toggle_any_more(page, css, soffit):
    # V9b owner request: WCAG 2.2.2 is met by settling, not by a button
    html = str(page)
    assert "motion-toggle" not in html and "Pause background motion" not in html
    assert ".motion-toggle" not in css
    assert "localStorage" not in soffit


def _const_ms(soffit, name):
    m = re.search(rf"const {name} = (\d+);", soffit)
    assert m, name
    return int(m[1])


def test_settles_after_load_and_after_input(soffit):
    # WCAG 2.2.2 by design: auto-motion stops within 5s of load; input wakes it, idle settles it
    assert _const_ms(soffit, "SETTLE_MS") <= 4000
    assert _const_ms(soffit, "SETTLE_MS") + _const_ms(soffit, "RAMP_MS") <= 5000
    assert 1000 <= _const_ms(soffit, "IDLE_MS") <= 3500
    assert "setInterval" not in soffit and "setTimeout" not in soffit, "nothing wakes on a timer"


def test_wakes_only_on_user_input(soffit):
    for event in ["pointermove", "pointerdown", "touchmove", "wheel", "keydown"]:
        assert f'"{event}"' in soffit, event
    # Not "scroll": scroll anchoring and layout shift scroll the page without a person doing it
    assert '"scroll"' not in soffit
    # Reduced motion short-circuits every wake
    assert re.search(r"const wake = \(\) => \{\s*if \(reduce\.matches[^)]*\) return;", soffit)


def _rgba_token(block: str, name: str):
    m = re.search(rf"--{name}:\s*rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", block)
    assert m, name
    return tuple(int(m[i]) for i in (1, 2, 3)), float(m[4])


def _blend(rgb, alpha, under_hex):
    u = [int(under_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(alpha * a + (1 - alpha) * b):02X}" for a, b in zip(rgb, u))


def _over(rgb_hex, alpha, under_hex):
    rgb = [int(rgb_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)]
    return _blend(rgb, alpha, under_hex)


def _grain_opacity(css, theme):
    from conftest import _block_after

    light = float(re.search(r"\.bookend-grain \{[^}]*opacity:\s*([\d.]+)", css)[1])
    if theme == "light":
        return light
    dark_rule = re.search(r"\.bookend-grain \{[^}]*\}", _block_after(css, "@media (prefers-color-scheme: dark) {\n  .bookend-grain"))
    m = re.search(r"opacity:\s*([\d.]+)", dark_rule[0]) if dark_rule else None
    return float(m[1]) if m else light


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_hero_copy_holds_contrast_over_any_pixel(css, tokens, soffit, root, theme):
    """The copy sits on the scrim, outside the circle window. Whatever the gradient (live or CSS
    fallback) paints underneath, from pure black (vignette) to pure white (glow), the stack that
    sits between the gradient and the copy must keep the hero ink at 4.5:1 or better:
    scrim, then grain (its darkest or lightest grain pixel, either colour), then the wordmark tint."""
    light = _block_after(css, ":root")
    dark = _block_after(_block_after(css, "@media (prefers-color-scheme: dark)"), ":root")
    block = light if theme == "light" else dark
    rgb, alpha = _rgba_token(block, "hero-scrim") if "--hero-scrim" in block else _rgba_token(light, "hero-scrim")
    tint_rgb, tint_a = _rgba_token(block, "hero-tint") if "--hero-tint" in block else _rgba_token(light, "hero-tint")
    tint_hex = "#" + "".join(f"{v:02X}" for v in tint_rgb)
    # grain.svg paints noise at up to 0.5 alpha (its colour matrix), scaled by the layer opacity
    svg = (root / "assets" / "grain.svg").read_text()
    grain_alpha = float(re.search(r"0 0 0 ([\d.]+) 0\"", svg)[1]) * _grain_opacity(css, theme)
    t = tokens[theme]
    ink = t["hero-ink"]
    under = ["#000000", "#FFFFFF", *JCARE_COLOURS.values(), t["field-deep"], t["field-mid"], t["field-sky"], t["accent"]]
    for u in under:
        scrimmed = _blend(rgb, alpha, u)
        for grain in ["#000000", "#FFFFFF"]:
            for with_tint in (False, True):
                px = _over(grain, grain_alpha, scrimmed)
                if with_tint:
                    px = _over(tint_hex, tint_a, px)
                ratio = contrast(ink, px)
                assert ratio >= 4.5, f"{theme}: under {u}, grain {grain}, tint {with_tint}: {ratio:.2f}"


def test_canvas_off_in_print(css):
    block = css[css.index("@media print"):]
    assert ".soffit" in block and ".bookend-ground" in block
