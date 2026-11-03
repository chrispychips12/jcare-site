"""Launch gate: every published quote needs the person's confirmed consent.

The three testimonials (V9b) are the owner's real customers' words, captioned by role ("A family
member") until consent; at most a first name after it. Until the owner confirms each person's
written consent, each figure carries data-consent="pending". While any remain this test is
EXPECTED to fail, so it is marked xfail(strict=True):

- Consent confirmed and the attributes removed, but the mark left: the test passes, strict xfail
  turns that into a failure, and the suite tells you to delete the mark. (The README's
  before-launch checklist says the same.)
- Mark removed while consent is still pending: the test fails.

If a quote's consent is refused, delete that quote, not just its attribute.
"""

import pytest


@pytest.mark.xfail(strict=True, reason="owner must confirm each person's consent to publish their quote")
def test_testimonial_consent_confirmed(page):
    assert page.select('[data-consent="pending"]') == [], "quotes still awaiting consent"
    assert page.select("[data-placeholder]") == [], "placeholder content still on the page"
