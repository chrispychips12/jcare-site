import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def root() -> Path:
    return ROOT


@pytest.fixture
def page() -> BeautifulSoup:
    return BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")


@pytest.fixture
def css() -> str:
    return (ROOT / "styles.css").read_text(encoding="utf-8")


def _block_after(text: str, marker: str) -> str:
    """Return the body of the first {...} block that opens after `marker`, braces balanced."""
    start = text.index(marker)
    open_at = text.index("{", start)
    depth, i = 0, open_at
    while True:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_at + 1 : i]
        i += 1


def _hex_tokens(block: str) -> dict[str, str]:
    return {m[0]: m[1].upper() for m in re.findall(r"--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})\s*;", block)}


@pytest.fixture
def tokens(css: str) -> dict[str, dict[str, str]]:
    light = _hex_tokens(_block_after(css, ":root"))
    dark_media = _block_after(css, "@media (prefers-color-scheme: dark)")
    dark = {**light, **_hex_tokens(_block_after(dark_media, ":root"))}
    return {"light": light, "dark": dark}


def contrast(a: str, b: str) -> float:
    def lum(h: str) -> float:
        h = h.lstrip("#")
        c = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# Privacy: patterns that catch private contact details WITHOUT naming any real data. The repo is
# public, so tests must never carry the real fragments they guard against.
PRIVATE_PATTERNS = {
    "Australian mobile": r"(\+?61[\s-]?|\b0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}\b",
    "landline": r"\(0\d\)\s?\d{4}\s?\d{4}",
    "tel link": r"\btel\s*:",
    "street address": r"\b\d{1,4}\s+[A-Z][a-z]+\s+(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr)\b",
    "state and postcode": r"\bNSW\s+\d{4}\b",
}
PERSONAL_EMAIL = r"@(gmail|hotmail|outlook|optusnet|icloud)\.[a-z]"

BINARY_EXT = {".woff2", ".woff", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf"}
SKIP_DIRS = {"docs", ".git", ".pytest_cache", "__pycache__"}
SKIP_FILES = {".DS_Store"}


def committed_text_files(root: Path) -> list[Path]:
    """Every non-binary file that is (or will be) committed: everything outside docs/ (local only),
    git internals and test caches. Binary means a known binary extension or a NUL byte; anything
    else is scanned, whatever its extension (including .claude/ if it ever appears)."""
    out = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if not p.is_file() or set(rel.parts) & SKIP_DIRS or p.name in SKIP_FILES:
            continue
        if p.suffix.lower() in BINARY_EXT or b"\0" in p.read_bytes()[:8192]:
            continue
        out.append(p)
    return out


def private_hits(text: str) -> list[str]:
    hits = [name for name, pat in PRIVATE_PATTERNS.items() if re.search(pat, text)]
    if re.search(PERSONAL_EMAIL, text, re.I):
        hits.append("personal email domain")
    return hits
