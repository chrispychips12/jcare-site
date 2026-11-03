REQUIREMENTS = [
    "NDIS Worker Screening Check",
    "National Police Check",
    "First Aid and CPR",
    "licence",
    "Right to work in Australia",
]


def test_careers_is_a_blue_band(page):
    section = page.find("section", id="careers")
    assert "band" in section["class"]


def test_pay_and_terms(page):
    text = page.find("section", id="careers").get_text(" ", strip=True)
    assert "SCHADS" in text and "MA000100" in text
    assert "casual" in text.lower()


def test_requirements_checklist(page):
    items = [li.get_text(" ", strip=True) for li in page.select("#careers ul.checklist > li")]
    assert len(items) == 5
    for needle, item in zip(REQUIREMENTS, items):
        assert needle.lower() in item.lower()


def test_careers_has_no_apply_email_button(page):
    # V1 removed the mailto apply button; V5 adds an accent button, but it goes to the form
    assert page.select_one('#careers a[href^="mailto:"]') is None


def test_apply_goes_to_form_in_staff_mode(page):
    a = page.select_one('#careers a.btn-accent[data-mode="staff"]')
    assert a["href"] == "#contact"
    # V10 (findings Clarify 3): "Apply below" was vague about where "below" is
    assert a.get_text(strip=True) == "Apply now"


def test_requirements_behind_disclosure(page):
    d = page.select_one("#careers details.requirements")
    assert d.find("summary").get_text(strip=True) == "What you'll need before your first shift"
    assert d.select("ul.checklist > li")


def test_careers_surface_is_short(page):
    s = page.find("section", id="careers")
    assert s.find("h2").get_text(strip=True) == "Work with one person, close to home."
    facts = [li.get_text(strip=True) for li in s.select("ul.facts > li")]
    # V10 (findings Distill 3): the award moved out of the lead into the fact, so it is said once
    assert facts == ["Same client, not a new house every shift", "SCHADS award rates (MA000100)", "Work close to home"]
    surface = " ".join(el.get_text(" ", strip=True) for el in s.select(".careers-copy, ul.facts"))
    assert surface.count("SCHADS") == 1, surface
    assert s.select_one("ul.facts")["role"] == "list"
    assert "Certificate III" in s.select_one("details.requirements").get_text()


def test_retention_slot_kept(root):
    assert "<!-- RETENTION SLOT: owner-approved commitments only. -->" in (root / "index.html").read_text()


def test_no_unapproved_retention_commitments_rendered(page):
    text = page.get_text(" ").lower()
    for phrase in ["two weeks ahead", "referral bonus", "monthly check-in", "paid progress", "paid cpr"]:
        assert phrase not in text
