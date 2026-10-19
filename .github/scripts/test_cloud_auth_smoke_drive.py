"""Unit tests for cloud-auth-smoke/drive.py's offline helpers (no network, no CLI)."""

import importlib.util
import pathlib
import unittest

SPEC = importlib.util.spec_from_file_location(
    "drive", pathlib.Path(__file__).parent / "cloud-auth-smoke" / "drive.py")
drive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drive)


class RedactTest(unittest.TestCase):
    def test_a_logged_url_keeps_host_and_path_and_drops_every_query_value(self):
        url = "http://127.0.0.1:5999/callback?bh_state=s&token=SECRET&ref=r"
        self.assertEqual(drive.redact(url), "http://127.0.0.1:5999/callback")
        self.assertNotIn("SECRET", drive.redact("https://cloud.blowhorn.ai/login?flow=f&login_challenge=SECRET"))


class TrailingJsonTest(unittest.TestCase):
    def test_the_cli_answer_after_its_authorize_line_is_the_one_read(self):
        out = '{"event": "authorize", "authorize_url": "https://x/login?source=s"}\n{\n  "ok": true,\n  "signed_in": true\n}\n'
        self.assertEqual(drive.trailing_json(out), {"ok": True, "signed_in": True})

    def test_no_json_is_none(self):
        self.assertIsNone(drive.trailing_json("ERROR: nothing\n"))


class FlowTest(unittest.TestCase):
    def test_a_page_without_a_flow_is_a_failure_that_names_the_page(self):
        with self.assertRaises(drive.Failure) as ctx:
            drive.flow_id("https://cloud.blowhorn.ai/registered?secret=1")
        self.assertIn("https://cloud.blowhorn.ai/registered", str(ctx.exception))
        self.assertNotIn("secret", str(ctx.exception))

    def test_messages_gather_the_flow_and_its_fields(self):
        flow = {"messages": [{"text": "Account not active yet. Did you forget to verify your email address?"}],
                "nodes": [{"attributes": {"name": "password"}, "messages": [{"text": "too short"}]}]}
        self.assertEqual(len(drive.messages(flow)), 2)


if __name__ == "__main__":
    unittest.main()
