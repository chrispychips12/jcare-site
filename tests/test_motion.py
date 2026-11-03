def test_script_is_deferred_and_local(page):
    # V9 adds the Soffit engine as its own deferred local file (asset brief rule 4)
    scripts = [s for s in page.find_all("script") if s.get("src")]
    assert [s["src"] for s in scripts] == ["main.js", "assets/soffit.js"]
    assert all(s.has_attr("defer") for s in scripts)


def test_hidden_state_only_applies_after_js(css):
    # The reveal start state must be scoped under .js-reveal so no-JS users see everything
    assert ".js-reveal [data-reveal]" in css
    assert "\n[data-reveal] {" not in css and "\n[data-reveal]{" not in css


def test_js_respects_reduced_motion(root):
    js = (root / "main.js").read_text()
    assert "prefers-reduced-motion: reduce" in js
    assert "IntersectionObserver" in js


def test_reduced_motion_kills_animation(css):
    block = css[css.index("@media (prefers-reduced-motion: reduce)"):]
    assert "animation: none" in block and "transition: none" in block


def test_no_autoplay_loops(css):
    assert "infinite" not in css


def test_details_animation_respects_reduced_motion(css):
    # The reduced-motion kill switch (*, *::before, *::after) does not match ::details-content,
    # so its transition must only exist when motion is allowed.
    import re
    from conftest import _block_after

    marker = "@media (prefers-reduced-motion: no-preference)"
    allowed = ""
    start = 0
    while marker in css[start:]:
        at = css.index(marker, start)
        allowed += _block_after(css[at:], marker)
        start = at + len(marker)

    rules = [r for r in re.findall(r"[^{}]*::details-content[^{}]*\{[^{}]*\}", css) if "transition" in r]
    assert rules, "expected an animated ::details-content rule"
    outside = css
    for r in rules:
        assert r.strip() in allowed, r
    for r in re.findall(r"[^{}]*::details-content[^{}]*\{[^{}]*\}", allowed):
        outside = outside.replace(r, "", 1)
    assert not [r for r in re.findall(r"[^{}]*::details-content[^{}]*\{[^{}]*\}", outside) if "transition" in r]


def _no_preference_spans(css):
    """(start, end) character spans of every @media (prefers-reduced-motion: no-preference) block."""
    marker = "@media (prefers-reduced-motion: no-preference)"
    spans, start = [], 0
    while marker in css[start:]:
        at = css.index(marker, start)
        open_at = css.index("{", at)
        depth, i = 0, open_at
        while True:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        spans.append((at, i))
        start = at + len(marker)
    return spans


def test_every_animation_only_exists_when_motion_is_allowed(css):
    # Keyframe and scroll-driven motion (V9) must never exist outside a no-preference block, so
    # reduced motion gets none of it even where the * kill switch cannot reach (::details-content,
    # scroll timelines). The only animation declarations allowed outside are the kill switch itself.
    import re

    spans = _no_preference_spans(css)
    assert spans
    for m in re.finditer(r"(?<![-\w])(animation(?:-name|-timeline|-range)?)\s*:\s*([^;}]*)", css):
        if m[2].strip().startswith("none"):
            continue
        assert any(a <= m.start() <= b for a, b in spans), f"outside no-preference: {m[0]!r}"
    for m in re.finditer(r"@keyframes\s+[\w-]+", css):
        assert any(a <= m.start() <= b for a, b in spans), m[0]


def test_no_animation_repeats(css):
    import re

    # Every keyframe animation plays once, longhand or shorthand. (Soffit's motion is JS and
    # settles on its own; see tests/test_soffit.py.)
    for m in re.finditer(r"animation-iteration-count:\s*([^;}]+)", css):
        assert m[1].strip() == "1", m[0]
    for m in re.finditer(r"(?<![-\w])animation:\s*([^;}]+)", css):
        value = re.sub(r"\([^()]*\)", "", m[1])  # drop var(), cubic-bezier() arguments
        for part in value.split(","):
            counts = [t for t in part.split() if re.fullmatch(r"\d*\.?\d+", t)]
            assert all(float(c) == 1 for c in counts), f"repeat count in {m[0]!r}"
            assert "infinite" not in part


def test_repeat_check_catches_shorthand():
    import re

    bad = ".x { animation: rise 1s 3; }"
    m = re.search(r"(?<![-\w])animation:\s*([^;}]+)", bad)
    counts = [t for t in re.sub(r"\([^()]*\)", "", m[1]).split() if re.fullmatch(r"\d*\.?\d+", t)]
    assert counts == ["3"]


def test_motion_tokens_replace_default_ease(css):
    import re

    assert "--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)" in css
    # No CSS default `ease` keyword anywhere (findings: 8 uses before V9)
    assert not re.search(r"\bease\b(?!-)", css), re.search(r".{40}\bease\b(?!-).{10}", css)


def test_scroll_driven_motion_is_feature_gated(css):
    assert "@supports (animation-timeline: scroll())" in css
    assert "@supports (animation-timeline: view())" in css


def test_reveal_has_safety_nets(root):
    js = (root / "main.js").read_text()
    assert "hashchange" in js and "focusin" in js


USER_TRIGGERED = (".form-done", ".is-swapping", ".switch", ".mode-set", "details", ".carousel", ".dot", ".btn", ".tile", ".mark")


def _ms(token, root_tokens):
    import re

    token = token.strip()
    m = re.fullmatch(r"var\((--[\w-]+)\)", token)
    if m:
        if m[1] not in root_tokens:
            return None  # an easing token, not a time
        token = root_tokens[m[1]]
    m = re.fullmatch(r"([\d.]+)(ms|s)", token)
    return float(m[1]) * (1000 if m[2] == "s" else 1) if m else None


def _user_triggered_timings(css):
    """(label, total ms) for every transition or animation on a user-triggered selector, delay
    included. Comments are stripped first so their words never count as a selector. V10: the old
    blanket skip of every `.hero` selector is gone (it would have hidden a slow `.hero .btn`
    hover); the hero's on-load entrance matches no user-triggered keyword, so it needs no skip."""
    import re
    from conftest import _block_after

    root = dict(re.findall(r"(--dur-[\w-]+):\s*([\d.]+m?s)", _block_after(css, ":root")))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if not any(k in selector for k in USER_TRIGGERED):
            continue
        for prop, value in re.findall(r"(?<![-\w])(transition|animation|transition-duration|animation-duration|transition-delay|animation-delay)\s*:\s*([^;]+)", body):
            if value.strip().startswith("none"):
                continue
            for part in value.split(","):
                times = [t for t in (_ms(x, root) for x in re.findall(r"var\(--[\w-]+\)|[\d.]+m?s\b", part)) if t is not None]
                out.append((f"{selector.strip()} {prop}: {part.strip()}", sum(times[:2])))
    return out


def test_user_triggered_motion_is_450ms_or_less(css):
    # Global constraint: user-triggered transitions (and the one-shot animations a user action
    # starts: the success message, the heading swap) finish within 450ms, delay included.
    timings = _user_triggered_timings(css)
    assert len(timings) > 10
    slow = [(label, ms) for label, ms in timings if ms > 450]
    assert not slow, slow


def test_user_triggered_check_now_covers_hero_selectors(css):
    # V9 deferred minor: the check used to skip any selector containing ".hero".
    planted = css + "\n.hero .btn:hover { transition: transform 600ms var(--ease-out-expo); }\n"
    assert any(ms > 450 and ".hero .btn" in label for label, ms in _user_triggered_timings(planted))


def test_interpolate_size_only_when_motion_is_allowed(css):
    # V3-5 deferred minor: the motion guard covered transitions, not interpolate-size, which is
    # what lets <details> animate its height. It must only exist inside a no-preference block.
    import re

    spans = _no_preference_spans(css)
    hits = [m.start() for m in re.finditer(r"interpolate-size\s*:", css)]
    assert hits
    for at in hits:
        assert any(a <= at <= b for a, b in spans), css[at:at + 60]
