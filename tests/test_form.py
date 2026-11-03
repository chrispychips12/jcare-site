def test_switch_is_a_radio_group(page):
    sw = page.select_one("#contact form.contact-form fieldset.switch")
    assert sw.find("legend")
    radios = sw.select('input[type="radio"][name="mode"]')
    assert [r["value"] for r in radios] == ["client", "staff"]
    assert radios[0].has_attr("checked")
    for r in radios:
        assert sw.find("label", attrs={"for": r["id"]})


def test_every_control_is_labelled(page):
    form = page.select_one("form.contact-form")
    for el in form.select("input:not([type=radio]), select, textarea"):
        assert form.find("label", attrs={"for": el["id"]}), el.get("name")


def test_shared_required_fields(page):
    form = page.select_one("form.contact-form")
    for name in ["name", "contact"]:
        el = form.find(attrs={"name": name})
        assert el.has_attr("required")


def test_client_and_staff_fieldsets(page):
    form = page.select_one("form.contact-form")
    client = form.select_one("fieldset.fields-client")
    staff = form.select_one("fieldset.fields-staff")
    assert {e["name"] for e in client.select("select, input, textarea")} >= {"for", "funding", "suburb", "message"}
    assert {e["name"] for e in staff.select("select, input, textarea")} >= {"suburb_staff", "screening", "driving", "about"}
    funding = [o.get_text(strip=True) for o in client.find(attrs={"name": "funding"}).find_all("option")]
    assert "Self managed NDIS" in funding and "Plan managed NDIS" in funding


def test_css_switches_without_js(css):
    assert ':has(input[value="staff"]:checked)' in css


def test_form_is_honest_preview(page, root):
    form = page.select_one("form.contact-form")
    assert not form.has_attr("action")
    assert "doesn't send yet" in page.select_one("p.preview-note").get_text()
    js = (root / "main.js").read_text()
    assert "preventDefault" in js and "reportValidity" in js and "nothing has been sent" in js


def test_mode_links_wired(root):
    js = (root / "main.js").read_text()
    assert "data-mode" in js
