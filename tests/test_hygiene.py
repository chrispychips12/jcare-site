import json
import re

from conftest import PERSONAL_EMAIL, PRIVATE_PATTERNS, committed_text_files, private_hits


def test_pages_excludes_private_folders(root):
    cfg = (root / "_config.yml").read_text()
    for name in ["docs", "tests", "README.md"]:
        assert name in cfg


def test_no_phone_address_or_personal_email_in_any_committed_file(root):
    # V9b: the repo goes public. Scan every committed text file (site, config, README, and the
    # tests themselves) with patterns, so no test needs to carry the real data it guards against.
    files = committed_text_files(root)
    names = {f.name for f in files}
    assert {"index.html", ".gitignore", "conftest.py", "soffit.js"} <= names
    assert not {"logo.png"} & names and not any(f.suffix == ".woff2" for f in files)
    for f in files:
        hits = private_hits(f.read_text(encoding="utf-8", errors="replace"))
        assert not hits, f"{f.relative_to(root)}: {hits}"


def test_privacy_patterns_catch_what_they_should():
    # Synthetic examples only, assembled at runtime so this file never contains a matching string.
    samples = {
        "Australian mobile": "04" + "12 345 678",
        "Australian mobile, hyphens": "04" + "12-345-678",
        "Australian mobile, +61": "+6" + "1 412 345 678",
        "Australian mobile, +61 hyphens": "+6" + "1-412-345-678",
        "landline": "(0" + "2) 9876 5432",
        "tel link": "href=te" + "l:123",
        "street address": "12 " + "Example Street",
        "state and postcode": "N" + "SW 2000",
    }
    for name, text in samples.items():
        assert re.search(PRIVATE_PATTERNS[name.split(",")[0]], text), name
    assert re.search(PERSONAL_EMAIL, "someone@" + "gmail.com")
    assert not private_hits("JCare Quality Services Pty Ltd, ABN 88 627 060 851, jcare.services@yahoo.com")


def test_email_only_in_footer(page):
    mailtos = page.select('a[href^="mailto:"]')
    assert mailtos, "footer email link missing"
    for a in mailtos:
        assert a.find_parent("footer") is not None


def test_json_ld_has_no_contact_details(page):
    data = json.loads(page.find("script", type="application/ld+json").string)
    for key in ["telephone", "address", "email"]:
        assert key not in data
    assert data["taxID"] == "88 627 060 851"


def test_comments_carry_no_commitments(root):
    html = (root / "index.html").read_text()
    comments = " ".join(re.findall(r"<!--(.*?)-->", html, re.S)).lower()
    for banned in ["referral bonus", "paid cpr", r"check-ins?\b", "roster notice", "paid note"]:
        assert not re.search(banned, comments), banned


def test_header_is_minimal(page):
    header = page.find("header", class_="site-header")
    assert header.find("a", class_="logo")["href"] == "./"
    assert header.find("a", class_="contact-pill")["href"] == "#contact"
    hrefs = [a["href"] for a in header.find("nav", attrs={"aria-label": "Main"}).find_all("a")]
    assert hrefs == ["#support", "#how-we-work", "#careers"]


def test_logo_is_light(root):
    assert (root / "assets" / "logo.png").stat().st_size < 40_000
