import re


def test_hero_copy_is_short(page):
    hero = page.find("section", class_="hero")
    # V9 splits the h1 into two line spans for the reveal, so join text nodes with a space
    assert hero.find("h1").get_text(" ", strip=True) == "Support that turns up."
    lead = hero.find("p", class_="lead").get_text(" ", strip=True)
    assert len(lead.split()) <= 25


def test_hero_buttons_are_the_fork(page):
    # V9 controller ruling: "Work with us" opens the careers band (pay and requirements first);
    # careers "Apply below" then opens the form in staff mode. "Get support" still preselects client.
    hero = page.find("section", class_="hero")
    links = hero.select(".hero-actions a")
    assert [(a.get_text(strip=True), a["href"], a.get("data-mode")) for a in links] == [
        ("Get support", "#contact", "client"),
        ("Work with us", "#careers", None),
    ]
    assert "btn-accent" in links[0]["class"]


def test_headline_reveals_by_line(page):
    h1 = page.find("h1")
    lines = h1.select(":scope > .line > span")
    assert [l.get_text(strip=True) for l in lines] == ["Support that", "turns up."]


def test_atelier_composition(page):
    hero = page.find("section", class_="hero")
    window = hero.select_one(".bookend-window")
    assert window and window["aria-hidden"] == "true" and not window.find(["a", "button"])
    mark = hero.select_one(".bookend-wordmark")
    assert mark["aria-hidden"] == "true" and mark.get_text(strip=True) == "JCare"
    # Copy, then the window, then the actions: the phone order the brief asks for
    # V9b renames the shared layers bookend-* (the footer reuses them)
    order = [el["class"][0] for el in hero.select(".hero-copy, .bookend-window, .hero-actions")]
    assert order == ["hero-copy", "bookend-window", "hero-actions"]


def test_no_gradient_text(css):
    assert "background-clip: text" not in css and "background-clip:text" not in css


def test_old_orbit_and_fork_gone(page, css):
    assert page.find(class_="orbit") is None
    assert page.find("nav", class_="fork") is None
    assert "@keyframes spin" not in css and "@keyframes drift" not in css


def test_hero_texture_present(root, css):
    svg = (root / "assets" / "rings.svg").read_text()
    assert svg.count("<circle") >= 6
    assert "rings.svg" in css


def test_print_block(css):
    block = css[css.index("@media print"):]
    assert ".js-reveal [data-reveal]" in block and "opacity: 1" in block


def test_color_mix_has_fallback(css):
    for rule in re.findall(r"\{[^{}]*color-mix[^{}]*\}", css):
        assert "rgba(" in rule, rule


def test_section_spacing_token(css):
    assert "--space-section" in css and "padding-block: var(--space-section)" in css
    # V9 rhythm: drenched bands breathe more than light sections
    assert "--space-band" in css and "padding-block: var(--space-band)" in css


def test_banner_has_logo(page):
    header = page.find("header", class_="site-header")
    assert header and header.find_parent("main") is None
    logo = header.find("img", src="assets/logo.png")
    assert logo and logo["alt"] == "JCare Quality Services"
    assert logo.get("width") == "276" and logo.get("height") == "108"


def test_single_h1_in_hero(page):
    h1s = page.find_all("h1")
    assert len(h1s) == 1
    assert h1s[0].find_parent("section", class_="hero")


def test_hero_says_what_we_do(page):
    hero = page.find("section", class_="hero")
    assert hero.find("p", class_="eyebrow").get_text(strip=True) == "Disability and community support"


def test_outer_ring_dropped_on_one_column_layouts(css):
    # On phones the window sits between the lead and the actions with a ~28px gap; the outer
    # ring (46px out) crossed the lead, so it only shows in the two-column layout.
    import re
    from conftest import _block_after

    block = _block_after(css, "@media (max-width: 59.99rem) {\n  .bookend-window .ring-2")
    assert re.search(r"\.bookend-window \.ring-2\s*\{[^}]*display:\s*none", "@media{" + block)
    inner = float(re.search(r"\.bookend-window \.ring \{[^}]*inset:\s*-(\d+)px", css)[1])
    gap_min = 1.75 * 16
    assert inner < gap_min, "inner ring must clear the copy above the window"
