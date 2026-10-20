#!/usr/bin/env python3
"""Fail if the action matrix or the docs all-actions table drifts from the data.

Both views render from layouts/_partials/action-matrix.html:

- the site matrix at data/integrations.json matrix.path (/integrations/actions/),
- the docs table at matrix.docsPath (/docs/reference/platforms/actions/),
  through the {{< all-actions >}} shortcode.

Expected cells come straight from the data: every action in data/actions.json
(rows, in groups[] order, then vocabulary order) by every platform in
data/integrations.json (columns, catalog order). A cell is supported when the
platform's data/platforms/<id>.yaml lists the action, coming-soon when the
platform is coming soon, and none otherwise.

--source checks the data alone (run by make check-schemas): every action's
group is a groups[].id, every group holds an action, platform YAML uses only
vocabulary ids, matrix statuses are supported, coming-soon, none in that
order, and supported platforms come before coming-soon ones.

With a build directory it also checks the built pages: the matrix and the
table hold exactly the expected cells and rows with the expected status and
link, in order; every link resolves to a built page and, with a #fragment,
to an element with that id there; /integrations/ and the home page link to
the matrix; the docs page calls the shortcode and carries no hand-written
table; neither page carries an em dash.

Usage: check_action_matrix.py --source
       check_action_matrix.py [BUILD_DIR]
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
EM_DASH = "\u2014"
STATUSES = ("supported", "coming-soon", "none")
SHORTCODE_RE = re.compile(r"\{\{<\s*all-actions\s*>\}\}")
MD_TABLE_RE = re.compile(r"^\|\s*Action\s*\|", re.M)


# ---------- data ----------

def load_json(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def yaml_action_ids(root: Path, platform_id: str) -> list[str] | None:
    path = root / "data" / "platforms" / f"{platform_id}.yaml"
    if not path.is_file():
        return None
    return [
        line.split("id:", 1)[1].strip().strip("\"'")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("  - id:")
    ]


def check_source(root: Path) -> list[str]:
    problems: list[str] = []
    actions = load_json(root, "data/actions.json")
    integrations = load_json(root, "data/integrations.json")
    group_ids = [g["id"] for g in actions.get("groups", [])]
    if not group_ids:
        problems.append("data/actions.json has no groups")
    if len(set(group_ids)) != len(group_ids):
        problems.append("data/actions.json groups repeat an id")
    vocab = [a["id"] for a in actions["actions"]]
    if len(set(vocab)) != len(vocab):
        problems.append("data/actions.json actions repeat an id")
    used = set()
    for a in actions["actions"]:
        group = a.get("group")
        if group not in group_ids:
            problems.append(f"action {a['id']} has group {group!r}, not a groups[].id")
        else:
            used.add(group)
    for gid in group_ids:
        if gid not in used:
            problems.append(f"group {gid} holds no action")

    matrix = integrations.get("matrix")
    if not matrix:
        problems.append("data/integrations.json has no matrix block")
    else:
        ids = tuple(s.get("id") for s in matrix.get("statuses", []))
        if ids != STATUSES:
            problems.append(f"matrix statuses are {ids}, want {STATUSES}")

    seen_soon = False
    for item in integrations["platforms"]:
        if item["status"] == "coming-soon":
            seen_soon = True
        elif seen_soon:
            problems.append(
                f"supported platform {item['id']} follows a coming-soon one; list supported platforms first"
            )
        ids = yaml_action_ids(root, item["id"])
        if item["status"] == "supported" and ids is None:
            problems.append(f"supported platform {item['id']} has no data/platforms/{item['id']}.yaml")
        for aid in ids or []:
            if aid not in vocab:
                problems.append(f"data/platforms/{item['id']}.yaml lists unknown action {aid!r}")
    return problems


def expected(root: Path) -> dict:
    """Rows, columns and cells both views must show, from the data alone."""
    actions = load_json(root, "data/actions.json")
    integrations = load_json(root, "data/integrations.json")
    platforms = integrations["platforms"]
    order: list[str] = []
    groups: list[str] = []
    for g in actions["groups"]:
        members = [a["id"] for a in actions["actions"] if a.get("group") == g["id"]]
        if members:
            groups.append(g["id"])
        order.extend(members)
    cells: dict[str, tuple[str, str | None]] = {}
    keys: list[str] = []
    for aid in order:
        for item in platforms:
            pid = item["id"]
            docs = item["docs"]
            listed = yaml_action_ids(root, pid) or []
            if item["status"] == "coming-soon":
                cell = ("coming-soon", docs)
            elif aid in listed:
                cell = ("supported", f"{docs}#action-{aid}")
            else:
                cell = ("none", None)
            key = f"{aid}:{pid}"
            keys.append(key)
            cells[key] = cell
    return {
        "groups": groups,
        "actions": order,
        "platforms": [p["id"] for p in platforms],
        "keys": keys,
        "cells": cells,
        "matrix": integrations.get("matrix", {}),
    }


# ---------- built HTML ----------

class Collector(HTMLParser):
    """Collect matrix cells, table rows, ids and the first link in each."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.platforms: list[str] = []
        self.groups: list[str] = []
        self.actions: list[str] = []
        self.cells: list[tuple[str, str, str | None]] = []
        self.rows: list[tuple[str, str, str | None]] = []
        self.hrefs: list[str] = []
        self.markers: dict[str, int] = {}
        self._cell: list | None = None
        self._row: list | None = None
        self._row_th = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for marker in ("data-action-matrix", "data-action-table", "data-matrix-link"):
            if marker in a:
                self.markers[marker] = self.markers.get(marker, 0) + 1
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if "data-matrix-platform" in a:
            self.platforms.append(a["data-matrix-platform"])
        if "data-matrix-group" in a:
            self.groups.append(a["data-matrix-group"])
        if "data-matrix-action" in a:
            self.actions.append(a["data-matrix-action"])
        if tag == "td" and "data-matrix-cell" in a:
            self._cell = [a["data-matrix-cell"], a.get("data-status", ""), None]
        elif tag == "a" and self._cell is not None and self._cell[2] is None:
            self._cell[2] = a.get("href")
        if tag == "tr" and "data-row" in a:
            self._row = [a["data-row"], a.get("data-status", ""), None]
            self._row_th = False
        elif self._row is not None and tag == "th":
            self._row_th = True
        elif tag == "a" and self._row is not None and self._row_th and self._row[2] is None:
            self._row[2] = a.get("href")

    def handle_endtag(self, tag):
        if tag == "td" and self._cell is not None:
            self.cells.append(tuple(self._cell))
            self._cell = None
        if tag == "th" and self._row is not None:
            self._row_th = False
        if tag == "tr" and self._row is not None:
            self.rows.append(tuple(self._row))
            self._row = None


def built_file(build_dir: Path, path: str) -> Path:
    path = path.strip("/")
    if not path:
        return build_dir / "index.html"
    if path.endswith(".html"):
        return build_dir / path
    return build_dir / path / "index.html"


def parse(path: Path) -> Collector:
    c = Collector()
    c.feed(path.read_text(encoding="utf-8"))
    return c


_page_ids: dict[Path, set[str]] = {}


def check_link(build_dir: Path, label: str, href: str) -> list[str]:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return [f"{label} links off-site to {href}"]
    target = built_file(build_dir, parts.path)
    if not target.is_file():
        return [f"{label} links to {href}, which has no built page"]
    if parts.fragment:
        ids = _page_ids.get(target)
        if ids is None:
            ids = parse(target).ids
            _page_ids[target] = ids
        if parts.fragment not in ids:
            return [f"{label} links to {href}, but that page has no id={parts.fragment!r}"]
    return []


def compare(label: str, want: dict, got: list[tuple[str, str, str | None]]) -> list[str]:
    problems: list[str] = []
    keys = [k for k, _, _ in got]
    missing = [k for k in want["keys"] if k not in keys]
    extra = [k for k in keys if k not in want["cells"]]
    if missing:
        problems.append(f"{label} is missing {len(missing)} cell(s): {', '.join(missing[:6])}")
    if extra:
        problems.append(f"{label} has {len(extra)} cell(s) the data doesn't: {', '.join(extra[:6])}")
    if len(keys) != len(set(keys)):
        problems.append(f"{label} repeats a cell")
    if not missing and not extra and keys != want["keys"]:
        problems.append(f"{label} cells are out of order (groups, then actions, then platforms)")
    for key, status, href in got:
        if key not in want["cells"]:
            continue
        want_status, want_href = want["cells"][key]
        if status != want_status:
            problems.append(f"{label} {key} is {status!r}, data says {want_status!r}")
        if want_href is None:
            if href is not None and label.startswith("matrix"):
                problems.append(f"{label} {key} links to {href}, want no link")
        elif href != want_href:
            problems.append(f"{label} {key} links to {href!r}, want {want_href!r}")
    return problems


def check_built(build_dir: Path, root: Path) -> list[str]:
    problems: list[str] = []
    want = expected(root)
    m = want["matrix"]
    if not m:
        return ["data/integrations.json has no matrix block"]

    page = built_file(build_dir, m["path"])
    if not page.is_file():
        problems.append(f"action matrix page {m['path']} was not built")
    else:
        c = parse(page)
        label = f"matrix {m['path']}"
        if c.markers.get("data-action-matrix") != 1:
            problems.append(f"{label} must render the shared matrix exactly once")
        if c.platforms != want["platforms"]:
            problems.append(f"{label} columns are {c.platforms}, data says {want['platforms']}")
        if c.groups != want["groups"]:
            problems.append(f"{label} groups are {c.groups}, data says {want['groups']}")
        if c.actions != want["actions"]:
            problems.append(f"{label} rows are {c.actions}, data says {want['actions']}")
        problems.extend(compare(label, want, c.cells))
        for _, _, href in c.cells:
            if href:
                problems.extend(check_link(build_dir, label, href))
        if EM_DASH in page.read_text(encoding="utf-8"):
            problems.append(f"{label} contains an em dash")

    docs = built_file(build_dir, m["docsPath"])
    if not docs.is_file():
        problems.append(f"docs all-actions page {m['docsPath']} was not built")
    else:
        c = parse(docs)
        label = f"docs table {m['docsPath']}"
        if c.markers.get("data-action-table") != 1:
            problems.append(f"{label} must render the shared table exactly once")
        problems.extend(compare(label, want, c.rows))
        for key, status, href in c.rows:
            if not href:
                problems.append(f"{label} {key} has no link in its action cell")
                continue
            problems.extend(check_link(build_dir, label, href))
            if key in want["cells"] and want["cells"][key][1] is None:
                pid = key.split(":", 1)[1]
                docs_path = next(
                    (p["docs"] for p in load_json(root, "data/integrations.json")["platforms"] if p["id"] == pid),
                    None,
                )
                if href != docs_path:
                    problems.append(f"{label} {key} links to {href!r}, want the platform page {docs_path!r}")
        if EM_DASH in docs.read_text(encoding="utf-8"):
            problems.append(f"{label} contains an em dash")

    source = root / "content" / "en" / (m["docsPath"].strip("/") + "/_index.md")
    if not source.is_file():
        problems.append(f"no docs source page at {source.relative_to(root)}")
    else:
        text = source.read_text(encoding="utf-8")
        if len(SHORTCODE_RE.findall(text)) != 1:
            problems.append(f"{source.relative_to(root)} must call {{{{< all-actions >}}}} once")
        if MD_TABLE_RE.search(text):
            problems.append(f"{source.relative_to(root)} carries a hand-written action table")

    for path in ("/", "/integrations/"):
        target = built_file(build_dir, path)
        if not target.is_file():
            problems.append(f"{path} was not built")
            continue
        c = parse(target)
        if m["path"] not in c.hrefs:
            problems.append(f"{path} does not link to the action matrix at {m['path']}")
    return problems


def run(root: Path, build_dir: Path | None) -> list[str]:
    problems = check_source(root)
    if build_dir is not None:
        problems.extend(check_built(build_dir, root))
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--source"]:
        problems = check_source(ROOT)
        what = "action matrix data"
    else:
        build_dir = Path(argv[0]) if argv else ROOT / "public"
        if build_dir.is_dir():
            problems = run(ROOT, build_dir)
        else:
            problems = check_source(ROOT) + [
                f"build dir {build_dir} is missing; run make build-production first"
            ]
        what = "action matrix and docs table"
    for item in problems:
        print(f"action-matrix: {item}", file=sys.stderr)
    print(f"checked {what}, {len(problems)} broken")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
