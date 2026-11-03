import re


SHIPPED = [
    "index.html", "styles.css", "main.js", "favicon.svg",
    "assets/soffit.js", "assets/grain.svg", "assets/rings.svg",
    "assets/placeholders/portrait-1.svg", "assets/placeholders/portrait-2.svg",
    "assets/placeholders/portrait-3.svg",
]


def test_shipped_list_covers_every_asset(root):
    # Anything new under assets/ (except the logo and fonts, counted separately) must be listed,
    # so it is weighed and scanned for external requests.
    found = {
        p.relative_to(root).as_posix()
        for p in (root / "assets").rglob("*")
        if p.is_file() and p.name != "logo.png" and "fonts" not in p.parts and p.name != ".DS_Store"
    }
    assert found <= set(SHIPPED), found - set(SHIPPED)


def test_weight_budget_excluding_logo(root):
    total = sum((root / p).stat().st_size for p in SHIPPED)
    total += sum(f.stat().st_size for f in (root / "assets" / "fonts").glob("*.woff2"))
    assert total < 200_000, f"{total} bytes"


EXTERNAL = re.compile(
    r"""(?:src|srcset|href)\s*=\s*["']?\s*(?:https?:)?//|url\(\s*["']?\s*(?:https?:)?//|@import|fetch\(|XMLHttpRequest|new\s+Image\(""",
    re.IGNORECASE,
)


def test_no_external_runtime_requests(root):
    for name in SHIPPED:
        text = (root / name).read_text(encoding="utf-8")
        if name == "index.html":
            text = re.sub(r"<a\s[^>]*>", "", text)
        m = EXTERNAL.search(text)
        assert m is None, f"{name}: {m.group(0)!r}"


def test_external_request_pattern_catches_cdn_script():
    assert EXTERNAL.search('<script src="https://example.com/x.js"></script>')
    assert EXTERNAL.search("a{background:url(//cdn.example.com/x.png)}")
    assert EXTERNAL.search("fetch('/x')")
    assert not EXTERNAL.search('<svg xmlns="http://www.w3.org/2000/svg"><g filter="url(#blur)"/></svg>')
