# jcare-site

Static landing page for JCare Quality Services. Served by GitHub Pages from `main`.

- Preview: `python3 -m http.server 8000`, then open http://localhost:8000
- Tests: `uv run --no-project --with pytest --with beautifulsoup4 --with fonttools --with brotli pytest -q`

## Before launch

In this order. Each of the first two has a strict `xfail` in `tests/test_launch_gate.py` that turns the suite red if it is half done.

1. The owner confirms written consent for each testimonial; then remove `data-consent="pending"` and the `xfail` on `test_testimonial_consent_confirmed`. If someone declines, delete their quote.
2. Connect the form service (with the owner's approval): give the form its `action`, remove both preview notes (`.preview-note` and `.steps-note`) and the preview success copy, then remove the `xfail` on `test_form_is_connected`.
3. Only then enable GitHub Pages and point the domain's DNS at it. Making the repository public does not enable Pages; that is a separate setting.

## Fonts

All self-hosted, all under the SIL Open Font License 1.1; each licence ships beside the fonts in `assets/fonts/`.

- Bricolage Grotesque, The Bricolage Grotesque Project Authors: `OFL-BricolageGrotesque.txt`
- Atkinson Hyperlegible, Braille Institute of America: `OFL-AtkinsonHyperlegible.txt`
- JCare Mono, a Basic Latin subset of IBM Plex Mono (IBM Corp.), renamed as the Reserved Font Name clause requires of a modified version: `OFL-JCareMono.txt`
