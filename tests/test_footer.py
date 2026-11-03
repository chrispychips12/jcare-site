"""Footer (V9b): a bookend of the hero. Same Soffit ground, circle window, ring and faded
wordmark, mirrored (circle left, copy right on wide screens), with the closing actions and the
site's only email address."""

import re

from conftest import _block_after


def _footer(page):
    return page.find("footer", class_="site-footer")


def test_one_contentinfo_footer_outside_main(page):
    footers = page.find_all("footer")
    assert len(footers) == 1 and footers[0].find_parent("main") is None
    assert "bookend" in footers[0]["class"]


def test_bookend_layers(page):
    f = _footer(page)
    canvas = f.find("canvas", attrs={"data-soffit": True})
    assert canvas and canvas.has_attr("hidden") and canvas.find_parent(attrs={"aria-hidden": "true"})
    assert f.select_one(".bookend-ground .bookend-field")
    window = f.select_one(".bookend-window")
    assert window["aria-hidden"] == "true" and window.select(".ring")
    mark = f.select_one(".bookend-wordmark")
    assert mark["aria-hidden"] == "true" and mark.get_text(strip=True) == "JCare"


def test_content_in_order(page):
    f = _footer(page)
    h2 = f.find("h2")
    assert h2 and "—" not in h2.get_text()
    pills = f.select(".footer-actions a")
    assert [(a.get_text(strip=True), a["href"], a.get("data-mode")) for a in pills] == [
        ("Get support", "#contact", "client"),
        ("Work with us", "#careers", None),
    ]
    assert "btn-accent" in pills[0]["class"] and "btn-ghost" in pills[1]["class"]
    nav = f.find("nav", attrs={"aria-label": "Footer"})
    assert [(a.get_text(strip=True), a["href"]) for a in nav.find_all("a")] == [
        ("What we do", "#support"), ("How we work", "#how-we-work"), ("Careers", "#careers"), ("Contact us", "#contact"),
    ]
    text = f.get_text(" ", strip=True)
    order = [
        text.index(h2.get_text(" ", strip=True)), text.index("Get support"), text.index("What we do"),
        text.index("Monday to Friday, 9am to 5pm"), text.index("jcare.services@yahoo.com"),
        text.index("JCare Quality Services Pty Ltd · ABN 88 627 060 851"), text.index("Back to top"),
    ]
    assert order == sorted(order)
    top = f.find("a", string="Back to top")
    assert top["href"] in ("#main", "#top")


def test_one_lime_in_the_footer(page):
    assert len(_footer(page).select(".btn-accent")) == 1


def test_mirrored_on_wide_screens(css):
    wide = _block_after(css, "@media (min-width: 60rem) {\n  .footer-layout")
    assert re.search(r'grid-template-areas:\s*"window copy"', wide)


def test_footer_reads_on_the_scrim(css):
    # Same ink and scrim as the hero, so the hero's static contrast guard covers the footer too
    rule = _block_after(css, "\n.bookend {")
    assert "color: var(--hero-ink)" in rule
    assert "var(--hero-scrim)" in _block_after(css, "\n.bookend-window {")
