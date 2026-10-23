#!/usr/bin/env python3
"""Tests for the docs-sync self-triggered site checks.

sync-docs.yml pushes the docs-sync branch with github.token, and pushes and
pull requests made with that token never start pull_request or push
workflows, so site.yml would stay silent on the sync PR. The workflow must
therefore start site.yml on that branch itself with workflow_dispatch, behind
the docs-sync-start-checks make target like every other CI step. It must also
merge the PR itself once those checks pass — behind the docs-sync-merge make
target — because master has no branch protection for GitHub's own auto-merge
to wait on, and start the master site run that deploys the merge, which the
token's push would otherwise never start either.

Run with `make test-scripts` (CI runs it too).
"""

import os
import re
import stat
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "sync-docs.yml"
SITE_WORKFLOW = ROOT / ".github" / "workflows" / "site.yml"
SCRIPT = HERE / "sync-docs-start-checks.sh"
MERGE_SCRIPT = HERE / "sync-docs-merge.sh"
MAKEFILE = ROOT / "Makefile"
README = ROOT / "README.md"
DEPLOY = ROOT / "docs" / "deploy.md"


class SyncDocsWorkflowTest(unittest.TestCase):
    def test_site_workflow_accepts_dispatch(self):
        text = SITE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", text)

    def test_sync_job_may_start_workflows(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions: write", text)

    def test_sync_starts_site_checks_through_make(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make docs-sync-start-checks", text)
        self.assertNotIn("gh workflow run", text)

    def test_sync_skips_the_trigger_without_changes(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("changed=false", text)
        self.assertIn("steps.pr.outputs.changed != 'false'", text)

    def test_trigger_script_dispatches_site_checks(self):
        self.assertTrue(SCRIPT.is_file())
        mode = os.stat(SCRIPT).st_mode
        self.assertTrue(mode & stat.S_IXUSR, "script must be executable")
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("gh workflow run site.yml --ref", text)

    def test_makefile_defines_the_trigger_target(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^docs-sync-start-checks:")
        self.assertIn("sync-docs-start-checks.sh", text)
        self.assertIn("docs-sync-start-checks", text.split(".PHONY:")[-1])

    def test_no_new_secret_or_app(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        secrets = set(re.findall(r"secrets\.([A-Za-z0-9_]+)", text))
        self.assertEqual(secrets, {"DMG_SOURCE_TOKEN"})
        lowered = text.lower()
        self.assertNotIn("personal access token", lowered)
        self.assertNotIn("github app", lowered)

    def test_readme_lists_the_trigger_target(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("docs-sync-start-checks", text)

    def test_deploy_docs_say_the_sync_starts_the_checks(self):
        text = DEPLOY.read_text(encoding="utf-8")
        self.assertIn("docs-sync-start-checks", text)
        self.assertIn("workflow_dispatch", text)

    def test_sync_merges_through_make(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make docs-sync-merge", text)

    def test_merge_script_waits_for_checks_then_merges_and_deploys(self):
        self.assertTrue(MERGE_SCRIPT.is_file())
        mode = os.stat(MERGE_SCRIPT).st_mode
        self.assertTrue(mode & stat.S_IXUSR, "script must be executable")
        text = MERGE_SCRIPT.read_text(encoding="utf-8")
        # The dispatched site run is the only gate: the script must wait
        # for that check by name (an instant check like DCO registering
        # first must not satisfy the wait), watch it to completion before
        # the merge, and dispatch the master deploy run after it, because
        # the token's merge starts no push workflows.
        self.assertIn("Lint, build and check", text)
        self.assertLess(
            text.index('gh pr checks "$pr" --watch'),
            text.index('gh pr merge "$pr" --squash'),
        )
        self.assertIn("gh workflow run site.yml --ref master", text)
        # GitHub's own auto-merge must not be armed: master has no branch
        # protection, so it would merge before the checks finish.
        self.assertNotRegex(text, r"gh pr merge[^\n]*--auto")

    def test_makefile_defines_the_merge_target(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^docs-sync-merge:")
        self.assertIn("sync-docs-merge.sh", text)
        self.assertIn("docs-sync-merge", text.split(".PHONY:")[-1])

    def test_readme_lists_the_merge_target(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("docs-sync-merge", text)

    def test_deploy_docs_say_the_sync_merges(self):
        text = DEPLOY.read_text(encoding="utf-8")
        self.assertIn("docs-sync-merge", text)


if __name__ == "__main__":
    unittest.main()
