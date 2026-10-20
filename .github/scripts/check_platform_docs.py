#!/usr/bin/env python3
"""Fail if platform docs drift from the shared actions table.

Every supported platform in data/integrations.json must have a docs page
that calls {{< supported-actions "id" >}} and whose built HTML renders
table.supported-actions from layouts/_partials/supported-actions.html.

Every page under content/en/docs/reference/platforms/ (except the section
index) must render that table and must not carry a hand-written action
list or table. Other docs pages that list a platform's actions the same
way (a Supported actions heading, or a markdown table of Action / What
it does) fail too.

Usage: check_platform_docs.py [BUILD_DIR]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHORTCODE_RE = re.compile(r'\{\{<\s*supported-actions\s+"([^"]+)"\s*>\}\}')
HEADING_RE = re.compile(r"^## Supported actions\s*$", re.M)
TABLE_HEADER_RE = re.compile(
    r"^\|\s*Action\s*\|\s*What it does\s*\|",
    re.M,
)
EM_DASH = "\u2014"
REQUIRED_HEADERS = ("Action", "What it does", "Limits / notes", "Example")


def integrations(root: Path) -> dict:
    return json.loads((root / "data" / "integrations.json").read_text(encoding="utf-8"))


def content_page(root: Path, docs: str) -> Path:
    return root / "content" / "en" / (docs.strip("/") + ".md")


def built_page(build_dir: Path, docs: str) -> Path:
    return build_dir / (docs.strip("/") + "/index.html")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def strip_front_matter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end < 0:
        return text
    return text[end + 4 :]


def check_shortcode_block(root: Path, path: Path, platform_id: str, text: str) -> list[str]:
    problems: list[str] = []
    label = rel(root, path)
    body = strip_front_matter(text)
    if EM_DASH in body:
        problems.append(f"{label} contains an em dash")
    match = SHORTCODE_RE.search(body)
    if not match:
        problems.append(f"{label} does not call supported-actions")
        return problems
    if match.group(1) != platform_id:
        problems.append(
            f"{label} calls supported-actions {match.group(1)!r}, want {platform_id!r}"
        )
    if len(SHORTCODE_RE.findall(body)) != 1:
        problems.append(f"{label} calls supported-actions more than once")
    heading = HEADING_RE.search(body)
    if not heading:
        problems.append(f"{label} has no '## Supported actions' heading")
        return problems
    after = body[heading.end() :].lstrip("\n")
    first = after.splitlines()[0] if after.splitlines() else ""
    if not SHORTCODE_RE.match(first.strip()):
        problems.append(
            f"{label} '## Supported actions' is not followed by the supported-actions shortcode"
        )
    rest = after.split("\n", 1)[1] if "\n" in after else ""
    extra = []
    for line in rest.splitlines():
        if line.startswith("## "):
            break
        if line.strip():
            extra.append(line)
    if extra:
        problems.append(
            f"{label} has a hand-written action list between the shortcode and the next heading"
        )
    return problems


def check_handwritten_tables(root: Path, path: Path, text: str) -> list[str]:
    body = strip_front_matter(text)
    if TABLE_HEADER_RE.search(body):
        return [f"{rel(root, path)} carries a hand-written Action / What it does table"]
    return []


def check_source(root: Path) -> list[str]:
    problems: list[str] = []
    data = integrations(root)
    platforms_dir = root / "content" / "en" / "docs" / "reference" / "platforms"
    docs_dir = root / "content" / "en" / "docs"
    seen: set[Path] = set()

    for item in data["platforms"]:
        pid = item["id"]
        docs = item.get("docs") or ""
        page = content_page(root, docs)
        if item["status"] == "supported":
            yaml_path = root / "data" / "platforms" / f"{pid}.yaml"
            if not yaml_path.is_file():
                problems.append(
                    f"supported platform {pid} has no {rel(root, yaml_path)}"
                )
            if not page.is_file():
                problems.append(f"supported platform {pid} has no docs page at {docs}")
                continue
        elif not page.is_file():
            continue
        seen.add(page.resolve())
        text = page.read_text(encoding="utf-8")
        problems.extend(check_shortcode_block(root, page, pid, text))
        problems.extend(check_handwritten_tables(root, page, text))

    if platforms_dir.is_dir():
        for page in sorted(platforms_dir.glob("*.md")):
            if page.name.startswith("_"):
                continue
            if page.resolve() in seen:
                continue
            text = page.read_text(encoding="utf-8")
            body = strip_front_matter(text)
            if HEADING_RE.search(body) or SHORTCODE_RE.search(body):
                problems.append(
                    f"{rel(root, page)} lists platform actions but is not a platform in data/integrations.json"
                )
            problems.extend(check_handwritten_tables(root, page, text))

    if docs_dir.is_dir():
        skip = platforms_dir.resolve() if platforms_dir.is_dir() else None
        for page in sorted(docs_dir.rglob("*.md")):
            if skip and (page.parent.resolve() == skip or skip in page.resolve().parents):
                continue
            text = page.read_text(encoding="utf-8")
            body = strip_front_matter(text)
            if HEADING_RE.search(body) and not SHORTCODE_RE.search(body):
                problems.append(
                    f"{rel(root, page)} lists supported actions without the shared shortcode"
                )
            problems.extend(check_handwritten_tables(root, page, text))

    return problems


def check_built(build_dir: Path, root: Path) -> list[str]:
    problems: list[str] = []
    data = integrations(root)
    for item in data["platforms"]:
        docs = item.get("docs") or ""
        html_path = built_page(build_dir, docs)
        if item["status"] == "supported" and not html_path.is_file():
            problems.append(
                f"supported platform {item['id']} built page missing: {html_path}"
            )
            continue
        if not html_path.is_file():
            continue
        html = html_path.read_text(encoding="utf-8")
        marker = f'data-supported-actions="{item["id"]}"'
        if marker not in html:
            problems.append(
                f"{docs} does not render the shared actions table for {item['id']}"
            )
            continue
        tables = html.count('class="supported-actions"')
        if tables != 1:
            problems.append(
                f"{docs} has {tables} supported-actions tables, want 1"
            )
        for header in REQUIRED_HEADERS:
            needle = f'<th scope="col">{header}</th>'
            if needle not in html:
                problems.append(f"{docs} table is missing the {header!r} column")
        if EM_DASH in html:
            problems.append(f"{docs} contains an em dash")
        if item["status"] == "supported" and 'id="examples"' not in html:
            problems.append(f"{docs} lost the Examples heading from the shared table")
        if item["status"] == "coming-soon" and ">None yet<" not in html:
            problems.append(f"{docs} coming-soon table is missing the None yet row")
    return problems


def run(root: Path, build_dir: Path | None) -> list[str]:
    problems = check_source(root)
    if build_dir is not None:
        problems.extend(check_built(build_dir, root))
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    build_dir = Path(argv[0]) if argv else ROOT / "public"
    problems = run(ROOT, build_dir if build_dir.is_dir() else None)
    if not build_dir.is_dir():
        problems.append(
            f"build dir {build_dir} is missing; run make build-production first"
        )
    for item in problems:
        print(f"platform-docs: {item}", file=sys.stderr)
    print(f"checked platform docs, {len(problems)} broken")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
