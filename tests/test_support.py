SERVICES = [
    "Personal care",
    "Help around the house",
    "Life skills",
    "Social interaction and community",
    "Therapy support",
    "Transport and driver services",
]


def test_support_section_lists_six_services_in_order(page):
    section = page.find("section", id="support")
    assert section.find("h2")
    # V10 (findings Harden 5, V3-5 deferred minor): the names are spans, not h3s. WebKit folds a
    # heading inside <summary> into the button's name, so iOS VoiceOver may never expose it.
    names = [h.get_text(strip=True) for h in section.select("ul.services > li .tile-name")]
    assert names == SERVICES


def test_service_detail_is_behind_a_tap(page):
    tiles = page.select("#support ul.services > li > details.tile")
    assert len(tiles) == 6
    for t in tiles:
        assert t.find("summary").find("span", class_="tile-name")
        assert len(t.find("p").get_text(strip=True)) > 30


def test_services_list_keeps_semantics(page):
    assert page.select_one("#support ul.services")["role"] == "list"


def test_funding_note_is_disclosed(page):
    d = page.select_one("#support details.note-disclosure")
    # V10 (findings Clarify 2): private funding is not a plan
    assert d.find("summary").get_text(strip=True) == "What funding can we take?"
    text = d.get_text(" ", strip=True).lower()
    for phrase in ["self managed", "plan managed", "privately funded", "agency managed"]:
        assert phrase in text


def test_area_line(page):
    # V9 (findings Layout 3 / Distill 1-2): the area and funding line replaces the support lead,
    # which repeated the hero. "Not NDIS registered" stays behind the disclosure (controller ruling).
    area = page.select_one("#support p.area")
    assert "lead" in area["class"]
    assert len(page.select("#support p.lead")) == 1
    assert "registered" not in area.get_text().lower()
    text = area.get_text(" ", strip=True)
    for suburb in ["Campbelltown", "Liverpool", "Bankstown"]:
        assert suburb in text


def test_dropped_services_absent(page):
    text = page.get_text(" ").lower()
    for banned in ["brick", "labour", "painting"]:
        assert banned not in text


def test_tile_disclosure_css(css):
    # Height animates where supported, instant elsewhere; default marker hidden; tap target >= 44px
    assert "interpolate-size: allow-keywords" in css
    assert "::details-content" in css
    assert "::-webkit-details-marker" in css
    for selector in [".tile > summary", ".note-disclosure > summary"]:
        assert _min_height_px(_rule(css, selector)) >= 44, selector


def test_funding_section_and_css_gone(page, css):
    assert page.find("section", id="funding") is None
    assert ".funding-layout" not in css and ".areas" not in css


def _rule(css, selector):
    from conftest import _block_after
    return _block_after(css, "\n" + selector + " {")


def _min_height_px(block):
    import re
    m = re.search(r"min-height:\s*([\d.]+)(px|rem)", block)
    value, unit = float(m[1]), m[2]
    return value * 16 if unit == "rem" else value


def test_feature_tile_breaks_the_grid(page, css):
    tiles = page.select("#support ul.services > li")
    assert "is-feature" in tiles[0].get("class", [])
    assert sum("is-feature" in t.get("class", []) for t in tiles) == 1
    assert ".services > li.is-feature" in css
