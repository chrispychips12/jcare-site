# jcare-site

Static landing page for JCare Quality Services. Served by GitHub Pages from `main`.

- Preview: `python3 -m http.server 8000`, then open http://localhost:8000
- Tests: `uv run --no-project --with pytest --with beautifulsoup4 pytest -q`
- Before launch: the owner confirms written consent for each testimonial; then remove `data-consent="pending"` and the `xfail` in `tests/test_launch_gate.py`
