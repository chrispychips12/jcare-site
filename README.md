# jcare-site

Static landing page for JCare Quality Services. Served by GitHub Pages from `main`.

- Preview: `python3 -m http.server 8000`, then open http://localhost:8000
- Tests: `uv run --no-project --with pytest --with beautifulsoup4 pytest -q`
- Before launch: the owner confirms written consent for each testimonial; then remove `data-consent="pending"` and the `xfail` in `tests/test_launch_gate.py`

## Fonts

All self-hosted, all under the SIL Open Font License 1.1; each licence ships beside the fonts in `assets/fonts/`.

- Bricolage Grotesque, The Bricolage Grotesque Project Authors: `OFL-BricolageGrotesque.txt`
- Atkinson Hyperlegible, Braille Institute of America: `OFL-AtkinsonHyperlegible.txt`
- JCare Mono, a Basic Latin subset of IBM Plex Mono (IBM Corp.), renamed as the Reserved Font Name clause requires of a modified version: `OFL-JCareMono.txt`
