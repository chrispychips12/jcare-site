"""V10 refine: clarify, harden, adapt, optimize, polish (docs/impeccable-findings.md, local only).

Each test names the finding it pins. Where the behaviour lives in JS, the test pins the source
shape; the behaviour itself was checked in a browser (see the V10 report)."""

import json
import re

from conftest import _block_after, committed_text_files


def _js(root):
    return (root / "main.js").read_text()


def _rule(css, selector):
    return _block_after(css, "\n" + selector + " {")


# Clarify ------------------------------------------------------------------------------------


def test_nav_label_matches_the_section_it_opens(page):
    # Clarify 1: the nav said "What we do", the section said "What we help with"
    nav = page.select_one('header nav[aria-label="Main"] a[href="#support"]').get_text(strip=True)
    eyebrow = page.select_one("#support .eyebrow").get_text(strip=True)
    assert nav == eyebrow == "What we do"


def test_submit_names_what_it_sends(page, root):
    # Clarify 4: "Send" became "Send message"; staff mode stays "Send application"
    assert page.select_one(".form-submit").get_text(strip=True) == "Send message"
    js = _js(root)
    assert '"Send application" : "Send message"' in js


def test_contact_field_has_a_hint(page):
    # Clarify 6
    field = page.find("input", id="f-contact")
    hint = page.find(id="f-contact-hint")
    assert hint and hint.get_text(strip=True) == "Whichever is easier for you."
    assert "f-contact-hint" in field["aria-describedby"].split()


def test_footer_hours_say_office_hours_and_match_json_ld(page):
    # Clarify 7 (ruling: the footer hours are office hours)
    hours = page.select_one("footer .hours").get_text(strip=True)
    assert hours == "Office hours: Monday to Friday, 9am to 5pm"
    spec = json.loads(page.find("script", type="application/ld+json").string)["openingHoursSpecification"][0]
    assert spec["dayOfWeek"] == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    assert (spec["opens"], spec["closes"]) == ("09:00", "17:00")


def test_errors_in_the_pages_own_voice(page, root):
    # Clarify 5 / Harden 1: each required field has an inline error slot it is described by, and
    # the messages are the page's, set through setCustomValidity rather than browser bubbles.
    for name in ["name", "contact"]:
        field = page.find(attrs={"name": name})
        slot = page.find(id=f"{field['id']}-error")
        assert slot is not None and slot.name == "p" and "field-error" in slot["class"]
        assert slot.get_text(strip=True) == "", "empty until a submit fails"
        assert slot["id"] in field["aria-describedby"].split()
    js = _js(root)
    assert "Add your name so we know who to reply to." in js
    assert "Add a phone number or email so we can reply." in js
    assert 'setAttribute("aria-invalid", "true")' in js


# Harden -------------------------------------------------------------------------------------


def test_whitespace_only_name_is_empty_and_thanks_never_reads_thanks_comma_dot(root):
    # Harden 1 (V6 deferred minor): "   " passed `required` and produced "Thanks, ."
    js = _js(root)
    assert "!field.value.trim()" in js
    assert "Thanks, ${first}" in js and '"Thanks."' in js
    assert "Thanks, ${first}. This is a preview" not in js, "no unguarded first-name message"


def test_without_js_nothing_can_be_posted(page, css, root):
    # Harden 2 (V6 deferred minor): a static host answers a POST with an error page and the
    # visitor loses what they typed. The submit ships disabled (so Enter cannot submit either)
    # and hidden; JS enables it. A note says where the email address is instead.
    form = page.select_one("form.contact-form")
    submit = form.select_one(".form-submit")
    assert submit["type"] == "submit" and submit.has_attr("disabled")
    assert form.get("method") == "post", "never GET: it would put personal details in the URL"
    assert "display: none" in _rule(css, ".contact-form:not(.is-enhanced) .form-actions")
    assert "display: none" in _rule(css, ".contact-form.is-enhanced .form-nojs")
    note = form.select_one(".form-nojs")
    assert "JavaScript" in note.get_text()
    link = note.find("a")
    assert link["href"] == "#footer-email"
    assert page.find(id="footer-email").find_parent("footer") is not None
    assert "submit.disabled = false" in _js(root)


def test_success_message_is_focused_not_a_live_region(page):
    # Harden 3 (V6 deferred minor): role=status plus a focus move read the message twice
    done = page.select_one(".form-done")
    assert not done.has_attr("role") and not done.has_attr("aria-live")
    assert done["tabindex"] == "-1"


def test_no_heading_inside_any_summary(page):
    # Harden 5 (V3-5 deferred minor)
    for summary in page.find_all("summary"):
        assert not summary.find(re.compile(r"^h[1-6]$")), summary


def test_carousel_says_where_a_button_press_landed(page, root):
    # Harden 4 (V3-5 deferred minor): slides carry "n of N" in the markup, and a button press is
    # announced once the scroll settles through a polite status line. Scrolling never writes it.
    for carousel in page.select("[data-carousel]"):
        status = carousel.select(".carousel-status")
        assert len(status) == 1 and status[0]["aria-live"] == "polite" and "sr-only" in status[0]["class"]
        assert not carousel.select_one(".carousel-track").has_attr("aria-live")
    js = _js(root)
    update = js[js.index("const update = () => {"): js.index("let announceTimer")]
    assert "status" not in update, "scroll updates must not announce"
    assert "scrollend" in js


def test_disclosures_print_open_and_carousels_print_stacked(css, root):
    # Harden 7 (V3-5 deferred minor): print hid closed <details> content
    js = _js(root)
    assert '"beforeprint"' in js and '"afterprint"' in js and "d.open = true" in js
    printed = css[css.index("@media print"):]
    assert "details::details-content" in printed
    assert re.search(r"\.carousel-track \{[^}]*display: block", printed)


def test_long_names_wrap_in_the_success_message(css):
    # Harden 8
    assert "overflow-wrap: anywhere" in _rule(css, ".form-done p")


# Adapt --------------------------------------------------------------------------------------


def test_nav_shows_on_phones_and_at_200_percent_zoom(css):
    # Adapt 1: under 48rem the nav was display: none, so phones and 200% zoom lost it. It is now a
    # second header row, no menu button and no overlay.
    # Fix round 1: the links are a second header row at every width (DOM order logo, pill, nav)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css[: css.index("@media print")]):
        if ".site-header" in selector:
            assert "display: none" not in body, selector.strip()
    assert "flex-basis: 100%" in _rule(css, ".site-header nav")
    assert "min-height: 44px" in _rule(css, ".site-header nav a")


def test_short_narrow_viewports_keep_the_hero_actions_on_screen(css):
    # Adapt 2: measured at 640x400 (200% zoom of 1280x800), the actions end on the first screen
    short = _block_after(css, "@media (max-height: 36rem)")
    assert short.index("padding-top: 7.75rem") > short.index("padding-block: 5rem 5rem"), "after the shorthand"


def test_open_tiles_sit_in_a_row_on_narrow_phones(css):
    # Adapt 3: an open tile kept its tall column summary, leaving dead space over the paragraph
    block = _block_after(css, "@media (max-width: 39.99rem) {\n  .tile[open] > summary")
    assert "flex-direction: row" in block and "min-height: 4.5rem" in block


# Optimize -----------------------------------------------------------------------------------


def test_heading_face_is_preloaded(page, css):
    # Optimize 1: the h1 is the likely LCP element
    link = page.find("link", rel="preload")
    assert link["href"] == "assets/fonts/bricolage-grotesque-600.woff2"
    assert link["as"] == "font" and link["type"] == "font/woff2" and link.has_attr("crossorigin")
    assert link["href"] in css
    head = page.find("head")
    tags = [t for t in head.find_all(True, recursive=False)]
    assert tags.index(link) < tags.index(head.find("link", rel="stylesheet"))


def test_mono_face_is_a_basic_latin_subset(root, css):
    # Optimize 2: Plex Mono served a few eyebrow labels at 14.7 KB
    mono = re.search(r'@font-face \{ font-family: "JCare Mono";[^}]*\}', css)
    assert mono and "unicode-range: U+0020-007E" in mono[0]
    assert (root / "assets/fonts/jcare-mono-400.woff2").stat().st_size < 10_000
    assert not (root / "assets/fonts/ibm-plex-mono-400.woff2").exists()
    assert '--font-mono: "JCare Mono"' in css


# Onboard ------------------------------------------------------------------------------------


def test_what_happens_next_is_a_disclosed_numbered_sequence(page, css):
    # Onboard: one numbered list per mode, behind a tap (one sentence on the surface), no timing
    d = page.select_one("#contact details.next-steps")
    assert d.find("summary").get_text(strip=True) == "What happens after you send?"
    for cls in ["next-client", "next-staff"]:
        ol = d.select_one(f"ol.{cls}")
        assert ol is not None and len(ol.find_all("li")) == 3
    text = d.get_text(" ").lower()
    for promise in ["day", "hour", "week", "within"]:
        assert promise not in text, promise
    assert "display: none" in _rule(css, ".next-staff")


# Polish -------------------------------------------------------------------------------------


def test_field_radius_is_a_token(css):
    # Polish 1: the scale is --radius-sm / --radius / --radius-lg plus pills
    assert "--radius-sm: 12px" in css
    assert not re.search(r"border-radius:\s*12px", css)


def test_footer_text_rows_match_the_link_rows(css):
    # Polish 2 (V1 deferred minor): uneven spacing round the email link
    rule = _rule(css, ".footer-meta .hours, .footer-meta .legal")
    assert "padding-block: 0.5625rem" in rule and "line-height: 1.625rem" in rule  # 9+26+9 = 44px


def test_no_em_dashes_in_anything_shipped(root):
    # Copy law, applied to every committed text file outside tests/ (which must name the
    # character to test for it)
    for f in committed_text_files(root):
        if "tests" in f.relative_to(root).parts:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        assert "—" not in text, f.relative_to(root)


def test_hygiene_scan_covers_svg_and_config(root):
    # V1 deferred minor: the scan used to skip SVG and _config.yml
    names = {f.relative_to(root).as_posix() for f in committed_text_files(root)}
    assert {"_config.yml", "assets/rings.svg", "assets/placeholders/portrait-1.svg", "favicon.svg"} <= names


# V10 fix round 1 -----------------------------------------------------------------------------

FONT_LICENCES = {
    "Bricolage Grotesque": "OFL-BricolageGrotesque.txt",
    "Atkinson Hyperlegible": "OFL-AtkinsonHyperlegible.txt",
    "JCare Mono": "OFL-JCareMono.txt",
}


def test_every_font_family_ships_its_ofl(root, css):
    # The OFL requires the licence to accompany every redistributed copy of the fonts
    families = set(re.findall(r'@font-face \{ font-family: "([^"]+)"', css))
    assert families == set(FONT_LICENCES), families
    for family, name in FONT_LICENCES.items():
        text = (root / "assets" / "fonts" / name).read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE Version 1.1" in text, name
        assert "Copyright" in text.split("SIL OPEN FONT LICENSE")[0], name
    mono = (root / "assets" / "fonts" / "OFL-JCareMono.txt").read_text(encoding="utf-8")
    head = mono.split("SIL OPEN FONT LICENSE")[0]
    assert "modified" in head.lower() and "IBM Plex Mono" in head and "Reserved Font Name" in head


def test_licences_credited_in_readme(root):
    readme = (root / "README.md").read_text()
    assert "## Fonts" in readme
    for family, name in FONT_LICENCES.items():
        assert family in readme and name in readme, family


def test_licence_files_are_scanned_but_not_weighed(root):
    names = {f.name for f in committed_text_files(root)}
    assert set(FONT_LICENCES.values()) <= names, "the privacy scan reads the licence files"
    from test_budget import SHIPPED

    assert not any(p.endswith(".txt") for p in SHIPPED)


def test_mono_name_table_is_renamed_and_licensed(root):
    # Needs fonttools + brotli; the standard suite command skips it. Run with
    # `--with fonttools --with brotli` to exercise it.
    import pytest

    tt = pytest.importorskip("fontTools.ttLib")
    pytest.importorskip("brotli")
    font = tt.TTFont(root / "assets" / "fonts" / "jcare-mono-400.woff2")
    names = {r.nameID: r.toUnicode() for r in font["name"].names}
    assert "SIL Open Font License" in names.get(13, "")
    assert "scripts.sil.org/OFL" in names.get(14, "")
    for i in (1, 4, 6, 16):
        assert "Plex" not in names.get(i, ""), (i, names.get(i))


NEXT_CLIENT = ["You tell us a little about the support you need.", "Someone from our team reads it.", "We talk through what might help."]
NEXT_STAFF = ["You tell us a little about you.", "Someone from our team reads it.", "We talk through the work we have."]


def test_next_steps_are_neutral_and_say_it_is_a_preview(page):
    d = page.select_one("#contact details.next-steps")
    assert [li.get_text(strip=True) for li in d.select("ol.next-client li")] == NEXT_CLIENT
    assert [li.get_text(strip=True) for li in d.select("ol.next-staff li")] == NEXT_STAFF
    assert "Preview: this form doesn't send yet." in d.get_text(" ", strip=True)
    text = d.get_text(" ").lower()
    for promise in ["plan support around", "close to home", "check your screening"]:
        assert promise not in text, promise


def test_header_visual_order_is_dom_order(page, css):
    # The contact pill comes before the nav in the DOM, so the phone layout (pill on row one,
    # links on row two) needs no `order`, and the tab order matches what you see.
    header = page.find("header", class_="site-header")
    kids = header.select_one(".wrap").find_all(True, recursive=False)
    assert ["logo" in k.get("class", []) for k in kids] == [True, False, False]
    assert "contact-pill" in kids[1].get("class", []) and kids[2].name == "nav", kids
    css_no_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css_no_comments):
        if ".site-header" in selector:
            assert not re.search(r"(?<![-\w])order\s*:", body), selector.strip()


def test_repeated_carousel_announcement_is_re_announced(root):
    js = _js(root)
    announce = js[js.index("const announce = () => {"): js.index("const go = ")]
    assert 'status.textContent = ""' in announce
    assert "requestAnimationFrame" in announce or "setTimeout" in announce


# Final fix wave -------------------------------------------------------------------------------


def test_readme_before_launch_order_and_full_test_command(root):
    readme = (root / "README.md").read_text()
    assert "--with pytest --with beautifulsoup4 --with fonttools --with brotli pytest -q" in readme
    launch = readme[readme.index("## Before launch"):]
    steps = [launch.index(k) for k in ["consent", "form service", "GitHub Pages"]]
    assert steps == sorted(steps), "consent, then the form, and only then Pages and DNS"
    assert "public does not enable" in launch.lower()


def test_steps_note_is_not_styled_as_a_panel(css):
    # The funding panel rule used to be `.note-disclosure p`, which also boxed the preview note
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S)):
        if "background: var(--panel)" in body and ".note-disclosure" in selector:
            assert ":not(.steps-note)" in selector, selector.strip()
    assert "\n.note-disclosure > p:not(.steps-note) {" in css


def test_contact_lead_promises_nothing_until_the_form_is_live(page):
    assert page.select_one("#contact .contact-intro p.lead").get_text(strip=True) == "Tell us a little about you."
    assert "in touch" not in page.select_one("#contact .contact-intro p.lead").get_text()


def test_abn_never_breaks_across_lines(root, page):
    html = (root / "index.html").read_text()
    assert "ABN 88&nbsp;627&nbsp;060&nbsp;851" in html
    assert "ABN 88 627" not in html
    assert '"taxID": "88 627 060 851"' in html, "JSON-LD keeps plain spaces"


def test_one_short_viewport_block(css):
    assert css.count("@media (max-height: 36rem)") == 1


def test_soffit_motion_after_load_is_four_seconds_in_total(root):
    soffit = (root / "assets" / "soffit.js").read_text()
    ms = {n: int(re.search(rf"const {n} = (\d+);", soffit)[1]) for n in ["SETTLE_MS", "RAMP_MS"]}
    assert ms["SETTLE_MS"] + ms["RAMP_MS"] <= 4000, ms


def test_soffit_keyboard_wake_ignores_navigation_keys(root):
    soffit = (root / "assets" / "soffit.js").read_text()
    assert 'addEventListener("keydown", onKey)' in soffit
    assert 'addEventListener("keydown", wake)' not in soffit
    for key in ["Tab", "Shift", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Control", "Alt", "Meta"]:
        assert f'"{key}"' in soffit, key


def test_soffit_asks_for_the_low_power_gpu(root):
    soffit = (root / "assets" / "soffit.js").read_text()
    assert 'powerPreference: "low-power"' in soffit and "high-performance" not in soffit
