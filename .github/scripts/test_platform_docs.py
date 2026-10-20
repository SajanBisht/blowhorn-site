#!/usr/bin/env python3
"""Platform docs must use the shared actions table, never a hand-written list.

Run with `make test-scripts` (CI runs it too).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import check_platform_docs as check

ROOT = Path(__file__).resolve().parents[2]

SUPPORTED_PAGE = """---
title: LinkedIn
---

Intro.

## Supported actions

{{< supported-actions "linkedin" >}}

## Related

- [All platforms](/docs/reference/platforms/)
"""

COMING_SOON_PAGE = """---
title: YouTube
---

**Coming soon.**

## Supported actions

{{< supported-actions "youtube" >}}

## Related

- [All platforms](/docs/reference/platforms/)
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PlatformDocsCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        data = json.loads((ROOT / "data/integrations.json").read_text(encoding="utf-8"))
        write(self.tmp / "data/integrations.json", json.dumps(data))
        shutil.copytree(ROOT / "data/platforms", self.tmp / "data/platforms")
        for item in data["platforms"]:
            page = check.content_page(self.tmp, item["docs"])
            body = COMING_SOON_PAGE if item["status"] == "coming-soon" else SUPPORTED_PAGE
            body = body.replace("linkedin", item["id"]).replace("youtube", item["id"])
            write(page, body)
        write(
            self.tmp / "content/en/docs/reference/platforms/_index.md",
            "---\ntitle: Platforms\n---\n",
        )
        write(
            self.tmp / "content/en/docs/how-to/publish/post-content.md",
            "---\ntitle: Post\n---\nRun the queue.\n",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_checked_in_source_passes(self):
        self.assertEqual(check.check_source(ROOT), [])

    def test_fixture_passes(self):
        self.assertEqual(check.check_source(self.tmp), [])

    def test_supported_platform_missing_page_fails(self):
        page = check.content_page(self.tmp, "/docs/reference/platforms/linkedin/")
        page.unlink()
        problems = check.check_source(self.tmp)
        self.assertTrue(
            any("linkedin" in p and "no docs page" in p for p in problems), problems
        )

    def test_page_without_shortcode_fails(self):
        page = check.content_page(self.tmp, "/docs/reference/platforms/linkedin/")
        write(
            page,
            "---\ntitle: LinkedIn\n---\n\n## Supported actions\n\n- Post\n- Comment\n",
        )
        problems = check.check_source(self.tmp)
        self.assertTrue(
            any("does not call supported-actions" in p for p in problems), problems
        )

    def test_handwritten_table_fails(self):
        page = check.content_page(self.tmp, "/docs/reference/platforms/linkedin/")
        write(
            page,
            SUPPORTED_PAGE
            + "\n| Action | What it does |\n| --- | --- |\n| Post | Publishes |\n",
        )
        problems = check.check_source(self.tmp)
        self.assertTrue(any("hand-written Action" in p for p in problems), problems)

    def test_recap_between_shortcode_and_heading_fails(self):
        page = check.content_page(self.tmp, "/docs/reference/platforms/linkedin/")
        text = page.read_text(encoding="utf-8")
        write(
            page,
            text.replace(
                '{{< supported-actions "linkedin" >}}',
                '{{< supported-actions "linkedin" >}}\n\nPosts to the feed from a row.\n',
            ),
        )
        problems = check.check_source(self.tmp)
        self.assertTrue(any("hand-written action list" in p for p in problems), problems)

    def test_other_docs_action_table_fails(self):
        write(
            self.tmp / "content/en/docs/how-to/publish/post-content.md",
            "---\ntitle: Post\n---\n\n| Action | What it does |\n| --- | --- |\n| Post | Publishes |\n",
        )
        problems = check.check_source(self.tmp)
        self.assertTrue(
            any("post-content.md" in p and "hand-written" in p for p in problems),
            problems,
        )

    def test_built_html_missing_table_fails(self):
        build = self.tmp / "public"
        data = json.loads((self.tmp / "data/integrations.json").read_text(encoding="utf-8"))
        for item in data["platforms"]:
            write(
                check.built_page(build, item["docs"]),
                "<html><body><p>no table</p></body></html>",
            )
        problems = check.check_built(build, self.tmp)
        self.assertTrue(
            any("does not render the shared actions table" in p for p in problems),
            problems,
        )

    def test_built_html_shared_table_passes(self):
        build = self.tmp / "public"
        headers = "".join(f'<th scope="col">{h}</th>' for h in check.REQUIRED_HEADERS)
        data = json.loads((self.tmp / "data/integrations.json").read_text(encoding="utf-8"))
        for item in data["platforms"]:
            extra = (
                '<h2 id="examples">Examples</h2>'
                if item["status"] == "supported"
                else '<th scope="row">None yet</th>'
            )
            write(
                check.built_page(build, item["docs"]),
                "<html><body>"
                f'<section data-supported-actions="{item["id"]}">'
                f'<table class="supported-actions"><thead><tr>{headers}</tr></thead>'
                f"<tbody><tr>{extra}</tr></tbody></table></section>"
                "</body></html>",
            )
        self.assertEqual(check.check_built(build, self.tmp), [])


if __name__ == "__main__":
    unittest.main()
