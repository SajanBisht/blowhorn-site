#!/usr/bin/env python3
"""Fail if the built site dropped the theme contract.

Signal is the production homepage. Reveille is today's look, previewable at
/home-reveille/ (front matter theme: reveille) and via ?theme=. Activity and
platform counts in copy must match data/integrations.json.

Usage: check_theme.py BUILD_DIR
"""

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def counts():
    data = json.loads((ROOT / "data/integrations.json").read_text(encoding="utf-8"))
    platforms = 0
    activities = 0
    soon = 0
    for item in data["platforms"]:
        if item["status"] == "supported":
            platforms += 1
            activities += len(item["actions"])
        elif item["status"] == "coming-soon":
            soon += 1
    return platforms, activities, soon


class AttrCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html_theme = None
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_theme = attrs.get("data-theme")
        if attrs.get("id"):
            self.ids.add(attrs["id"])

    def handle_data(self, data):
        self.text.append(data)


def parse(path: Path) -> AttrCollector:
    collector = AttrCollector()
    collector.feed(path.read_text(encoding="utf-8"))
    return collector


def main(root: Path) -> int:
    problems = []
    themes = json.loads((ROOT / "data/themes.json").read_text(encoding="utf-8"))
    if themes["default"] != "signal":
        problems.append("data/themes.json default is not signal")

    index = root / "index.html"
    if not index.is_file():
        problems.append("/index.html is not published")
    else:
        page = parse(index)
        html = index.read_text(encoding="utf-8")
        if page.html_theme != "signal":
            problems.append(f"/index.html data-theme is {page.html_theme!r}, want signal")
        if "Priced per profile, not per channel." not in html:
            problems.append("/index.html is missing the pricing headline")
        platforms, activities, soon = counts()
        if str(platforms) not in html:
            problems.append(f"/index.html is missing the supported platform count {platforms}")
        if str(activities) not in html:
            problems.append(f"/index.html is missing the activity count {activities}")
        if str(soon) not in html:
            problems.append(f"/index.html is missing the coming-soon count {soon}")
        if 'data-demo-card="github"' in html:
            problems.append("/index.html demo posts to GitHub")
        if ">Say it once. Say it everywhere.<" in html:
            problems.append("/index.html still uses the old platforms headline")
        if "theme" not in html or "data-theme" not in html:
            problems.append("/index.html is missing the theme preview hook")

    reveille = root / "home-reveille/index.html"
    if not reveille.is_file():
        problems.append("/home-reveille/index.html is not published")
    else:
        page = parse(reveille)
        html = reveille.read_text(encoding="utf-8")
        if page.html_theme != "reveille":
            problems.append(
                f"/home-reveille/index.html data-theme is {page.html_theme!r}, want reveille"
            )
        if "Say it once. Say it everywhere." not in html:
            problems.append("/home-reveille/index.html lost today's platforms headline")
        if 'id="how"' not in html or "army" not in html:
            problems.append("/home-reveille/index.html lost the army / how section")

    catalog = root / "integrations/index.html"
    if not catalog.is_file():
        problems.append("/integrations/index.html is not published")
    else:
        page = parse(catalog)
        if "integrations-title" not in page.ids:
            problems.append("/integrations/index.html#integrations-title is gone")

    for item in problems:
        print(f"theme: {item}", file=sys.stderr)
    print(f"checked theme contract, {len(problems)} broken")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_theme.py BUILD_DIR", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
