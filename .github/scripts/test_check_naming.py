#!/usr/bin/env python3
"""Users see Blowhorn: never Layer5 Cloud or Blowhorn Cloud, and Layer5 only
in the footer and on the legal pages.

Run with `make test-scripts` (CI runs it too).
"""

import tempfile
import unittest
from pathlib import Path

import check_naming as check

PAGE = "<html><head>{head}</head><body><main>{main}</main><footer>{footer}</footer></body></html>"


def page(main="", footer="", head=""):
    return PAGE.format(main=main, footer=footer, head=head)


class TheServiceIsBlowhorn(unittest.TestCase):
    def build(self, pages):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for rel, html in pages.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
        return check.check(root)

    def test_blowhorn_and_its_sign_in_url_pass(self):
        failures, _ = self.build({"index.html": page(
            '<p>Sign in to your Blowhorn account at <a href="https://cloud.blowhorn.ai">cloud.blowhorn.ai</a>.</p>')})
        self.assertEqual(failures, [])

    def test_layer5_cloud_fails_even_in_the_footer(self):
        failures, _ = self.build({"index.html": page(footer="<p>Layer5 Cloud status</p>")})
        self.assertEqual(len(failures), 1)
        self.assertIn("Layer5 Cloud", failures[0])

    def test_blowhorn_cloud_fails_in_any_case(self):
        failures, _ = self.build({"docs/index.html": page("<p>Open blowhorn cloud.</p>")})
        self.assertEqual(len(failures), 1)

    def test_layer5_cloud_in_an_attribute_or_meta_fails(self):
        failures, _ = self.build({
            "a/index.html": page('<img src="x.png" alt="Layer5 Cloud">'),
            "b/index.html": page(head='<meta name="description" content="Built on Blowhorn Cloud">'),
        })
        self.assertEqual(len(failures), 2)

    def test_layer5_outside_the_footer_fails(self):
        failures, _ = self.build({"brand/index.html": page("<p>Marks of Layer5, Inc.</p>")})
        self.assertEqual(len(failures), 1)
        self.assertIn("outside the footer", failures[0])

    def test_layer5_in_the_footer_and_legal_pages_passes(self):
        failures, _ = self.build({
            "index.html": page(footer='<img src="l.svg" alt="Layer5 Blowhorn"><p>© Layer5, Inc.</p>'),
            "legal/terms/index.html": page("<p>An agreement with Layer5, Inc.</p>"),
            "legal/privacy/index.html": page("<p>Layer5 keeps the list.</p>"),
            "legal/index.html": page("<p>Policies of Layer5, Inc.</p>"),
        })
        self.assertEqual(failures, [])

    def test_repository_urls_ids_scripts_and_comments_pass(self):
        failures, _ = self.build({"index.html": page(
            '<!-- Layer5 green --><p id="on-layer5-cloud">'
            '<a href="https://github.com/layer5io/blowhorn-site">layer5io/blowhorn-site</a></p>'
            '<script>var x = "Layer5 Cloud";</script>')})
        self.assertEqual(failures, [])

    def test_pending_pages_are_reported_not_failed(self):
        failures, pending = self.build({"docs/reference/cli/auth/index.html": page("<p>Sign in to Layer5 Cloud.</p>")})
        self.assertEqual(failures, [])
        self.assertEqual(len(pending), 1)

    def test_main_fails_on_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "index.html").write_text(page("<p>Layer5 Cloud keeps it in sync.</p>"), encoding="utf-8")
            self.assertEqual(check.main(["check_naming.py", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
