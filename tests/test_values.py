import re

VALUE_NAMES = ["People depend on us", "Follow their lead", "Say it early, take it well", "Do it properly"]


def test_four_promises_in_order(page):
    names = [p.get_text(strip=True) for p in page.select("#how-we-work ul.values > li p.value-name")]
    assert names == VALUE_NAMES


def test_each_card_has_one_statement(page):
    for li in page.select("#how-we-work ul.values > li"):
        assert len(li.find_all("h3")) == 1


def test_carousel_is_accessible(page, root):
    c = page.select_one("#how-we-work .carousel")
    assert c["aria-roledescription"] == "carousel" and c.get("aria-label")
    ul = c.select_one("ul.values")
    assert ul["role"] == "list" and ul["tabindex"] == "0"
    js = (root / "main.js").read_text()
    assert "carousel-next" in js and "carousel-prev" in js


def test_roster_card_removed(page):
    assert page.select_one(".roster-card") is None


def test_carousel_buttons_hidden_without_js(page):
    for cls, label in [("carousel-prev", "Previous promise"), ("carousel-next", "Next promise")]:
        b = page.select_one(f"#how-we-work button.{cls}")
        assert b["aria-label"] == label and b["type"] == "button"
        assert b.has_attr("hidden")
    dots = page.select_one("#how-we-work .carousel-dots")
    assert dots["aria-hidden"] == "true"


def test_carousel_scrolls_and_snaps(css):
    from conftest import _block_after
    # V9: the track rule is shared by both carousels (.carousel-track), not .values only
    assert "scroll-snap-type: x mandatory" in _block_after(css, "\n.carousel-track {")
    assert "scroll-snap-align" in css


def test_carousel_js_honours_reduced_motion(root):
    js = (root / "main.js").read_text()
    assert "scrollBy" in js and '"smooth"' in js and '"auto"' in js


def test_values_not_numbered(page):
    assert page.select_one("#how-we-work ol") is None


def test_area_spelled_correctly(page):
    text = page.get_text(" ")
    assert "Campbelltown" in text
    assert "Cambelltown" not in text
    for suburb in ["Liverpool", "Bankstown"]:
        assert suburb in text


def test_no_founding_year(page):
    text = page.get_text(" ").lower()
    assert not re.search(r"(since|established|founded)\s+(in\s+)?(19|20)\d\d", text)


def test_how_we_work_is_drenched_with_one_lime_card(page):
    s = page.find("section", id="how-we-work")
    assert "band" in s["class"]
    cards = s.select("ul.values > li")
    lime = [c for c in cards if "is-lime" in c.get("class", [])]
    assert lime == cards[:1], "exactly one lime card, the first promise"


def test_band_carousel_dot_is_not_a_second_lime(css):
    # One lime per screen: the lime card already carries how we work, so the current dot on a
    # band is a light pill, not lime.
    from conftest import _block_after

    rule = _block_after(css, "\n.band .dot.is-current {")
    assert "var(--accent)" not in rule and "background: var(--on-field)" in rule
