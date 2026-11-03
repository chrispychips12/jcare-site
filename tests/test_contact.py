import json


def test_no_contact_form_or_embeds(page):
    # The contact form is the one form on the page; nothing is embedded from elsewhere.
    assert len(page.find_all("form")) == 1
    assert page.find("iframe") is None


def test_footer(page):
    footer = page.find("footer")
    assert footer.find_parent("main") is None
    text = footer.get_text(" ", strip=True).replace("\xa0", " ")  # the ABN uses non-breaking spaces
    assert "JCare Quality Services Pty Ltd" in text
    assert "88 627 060 851" in text
    assert "Monday to Friday, 9am to 5pm" in text
    assert footer.find("a", href="mailto:jcare.services@yahoo.com")
    # ABN only: no street address and no phone line (patterns, so no real data lives in tests)
    from conftest import private_hits

    assert not private_hits(str(footer)), private_hits(str(footer))
    assert "Phone" not in text


def test_quotes_only_in_the_testimonials_section(page):
    # V9b: the owner's real quotes are on the page, launch-gated on consent
    # (tests/test_launch_gate.py). This check holds before AND after launch: quotes live only in
    # #testimonials, never elsewhere on the page.
    quotes = page.find_all("blockquote")
    assert quotes
    for q in quotes:
        assert q.find_parent("section", id="testimonials") is not None


def test_local_business_json_ld(page):
    data = json.loads(page.find("script", type="application/ld+json").string)
    assert data["@type"] == "LocalBusiness"
    assert "Campbelltown" in data["areaServed"]
    assert data["url"] == "https://jcarequalityservices.com.au/"


def test_open_graph(page):
    assert page.find("meta", property="og:title")
    assert page.find("meta", property="og:description")


def test_heading_levels_never_skip(page):
    levels = [int(h.name[1]) for h in page.find_all(["h1", "h2", "h3", "h4"])]
    assert levels[0] == 1
    for prev, cur in zip(levels, levels[1:]):
        assert cur <= prev + 1, f"h{prev} followed by h{cur}"


def test_every_in_page_link_has_a_target(page):
    ids = {el["id"] for el in page.find_all(id=True)}
    for a in page.find_all("a", href=True):
        if a["href"].startswith("#"):
            assert a["href"][1:] in ids, a["href"]


def test_every_img_has_alt(page):
    for img in page.find_all("img"):
        assert img.has_attr("alt")


def test_no_unconfirmed_reply_time_promise(page):
    assert "business day" not in page.get_text(" ").lower()
