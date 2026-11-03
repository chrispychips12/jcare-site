import struct


def test_logo_is_the_supplied_png(root):
    data = (root / "assets" / "logo.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (276, 108)


def test_backgrounds_are_small_svgs(root):
    for name in ["grain.svg", "rings.svg"]:
        f = root / "assets" / name
        assert f.read_text().lstrip().startswith("<svg")
        assert f.stat().st_size < 5_000, name


def test_field_is_token_driven_css_not_a_baked_svg(root, css):
    # V9 (findings Colorize 2, audit P1): field.svg baked light-mode hexes into the mesh, so dark
    # mode could only dim it. The meshes are now CSS gradients built from theme tokens.
    assert not (root / "assets" / "field.svg").exists()
    assert "field.svg" not in css
    from conftest import _block_after
    mesh = _block_after(css, "\n.band::before {")
    assert mesh.count("radial-gradient") >= 2
    assert "var(--field-deep)" in mesh and "var(--field-mid)" in mesh


def test_favicon_linked(page, root):
    assert (root / "favicon.svg").exists()
    assert page.find("link", rel="icon", href="favicon.svg")


def test_dark_mode_designs_the_bands_instead_of_dimming_them(css, tokens):
    # V9 replaces the old dark-mode rule (.band::before at 0.45 opacity, which turned both bands
    # into flat navy: audit P1) with dark field tokens that keep chroma. The old test asserted
    # the dimming; this asserts its replacement.
    from conftest import _block_after

    dark = _block_after(css, "@media (prefers-color-scheme: dark)")
    assert ".band::before" not in dark
    for name in ["field-deep", "field-mid", "field-sky"]:
        assert tokens["dark"][name] != tokens["light"][name], name
