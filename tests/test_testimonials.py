"""Testimonials (V9, real quotes in V9b): in the shared carousel, between how we work and careers."""

import re

from conftest import _block_after


def _section(page):
    return page.find("section", id="testimonials")


def test_sits_between_how_we_work_and_careers(page):
    ids = [s.get("id") for s in page.find("main").find_all("section", recursive=False)]
    i = ids.index("testimonials")
    assert ids[i - 1] == "how-we-work" and ids[i + 1] == "careers", ids


QUOTES = [
    ("We've used JCare for a year now and have never been let down on quality or promptness. "
     "When family and friends ask for a recommendation, JCare is always my first.", "A family member"),
    ("JCare was there for our family with a helping hand when it mattered most. Many thanks to all "
     "the staff, and may you continue to support the community.", "A client's family"),
    ("Great staff, actually the best!", "A client"),
]


def test_section_is_labelled_and_no_longer_a_placeholder(page):
    s = _section(page)
    assert not s.has_attr("data-placeholder")
    assert s.get("aria-labelledby") and s.find(id=s["aria-labelledby"])


def test_region_is_labelled_what_people_say(page):
    region = _section(page).select_one('[role="region"]')
    assert region["aria-label"] == "What people say"
    assert region["aria-roledescription"] == "carousel"
    assert region.has_attr("data-carousel")


def test_the_three_real_quotes_verbatim(page):
    figures = _section(page).select("ul.carousel-track > li figure")
    got = [(f.find("blockquote").get_text(" ", strip=True), f.find("figcaption").get_text(" ", strip=True)) for f in figures]
    assert got == QUOTES


def test_captions_are_roles_or_first_names_only(page):
    # Holds before AND after launch. Until consent is confirmed the captions are roles
    # ("A family member"); afterwards at most a first name plus an optional role. Never a surname,
    # an email address or any detail. (Consent itself is owned by tests/test_launch_gate.py.)
    import re

    for fig in _section(page).select("figure"):
        cap = fig.find("figcaption").get_text(" ", strip=True)
        role = re.fullmatch(r"An? [a-z][a-z' ]*", cap)
        first_name = re.fullmatch(r"[A-Z][a-z]+(, [a-z ]+)?", cap)
        assert role or first_name, cap
        assert "@" not in cap and len(cap.split()) <= 4
    assert not _section(page).select(".sample-tag")


def test_no_caption_text_inside_html_comments(root, page):
    # Comments ship in the page source: never repeat a caption (a role today, a name later) there.
    import re

    html = (root / "index.html").read_text()
    comments = " ".join(re.findall(r"<!--(.*?)-->", html, re.S)).lower()
    captions = [c.get_text(" ", strip=True).lower() for c in _section(page).select("figcaption")]
    assert captions
    for cap in captions:
        # Whole phrase only: "a client" must not match inside "a client's face"
        assert not re.search(rf"(?<![\w']){re.escape(cap)}(?![\w'])", comments), cap


def test_portraits_are_abstract_local_svgs(page, root):
    for img in _section(page).select("figure img"):
        src = img["src"]
        assert src.startswith("assets/placeholders/") and src.endswith(".svg"), src
        assert img["alt"] == "", "portraits are decorative"
        assert img.get("width") and img.get("height")
        svg = (root / src).read_text()
        assert svg.lstrip().startswith("<svg")
        assert (root / src).stat().st_size < 2_000, src
        # Abstract shapes only: no embedded photos, no text, nothing fetched
        for banned in ["<image", "<text", "base64", "href="]:
            assert banned not in svg, (src, banned)
        assert "radialGradient" in svg, "soft mesh-gradient tile"


def test_controls_are_labelled_and_hidden_without_js(page):
    s = _section(page)
    for cls, label in [("carousel-prev", "Previous quote"), ("carousel-next", "Next quote")]:
        b = s.select_one(f"button.{cls}")
        assert b["aria-label"] == label and b["type"] == "button" and b.has_attr("hidden")


def test_slides_announce_position(page):
    for carousel in page.select("[data-carousel]"):
        slides = carousel.select("ul.carousel-track > li")
        n = len(slides)
        for i, li in enumerate(slides, 1):
            assert li["aria-roledescription"] == "slide"
            assert li["aria-label"] == f"{i} of {n}"


def test_one_shared_carousel_initialiser(root, page):
    js = (root / "main.js").read_text()
    assert js.count("function initCarousel") == 1
    assert 'querySelectorAll("[data-carousel]")' in js
    assert 'document.querySelector(".carousel")' not in js, "no per-carousel copy of the behaviour"
    assert len(page.select("[data-carousel]")) == 2


def test_carousel_buttons_meet_target_size(css):
    block = _block_after(css, "\n.carousel-btn {")
    assert "width: 48px" in block and "height: 48px" in block


def _landmark_name(page, el):
    if el.get("aria-label"):
        return el["aria-label"].strip()
    if el.get("aria-labelledby"):
        return " ".join(page.find(id=i).get_text(" ", strip=True) for i in el["aria-labelledby"].split())
    return None


def test_no_two_landmarks_share_a_name(page):
    named = page.select('section[aria-labelledby], section[aria-label], [role="region"], nav, aside, form[aria-label]')
    names = [n.rstrip(".").lower() for n in (_landmark_name(page, el) for el in named) if n]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, dupes
