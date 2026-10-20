#!/usr/bin/env python3
"""Shared line/text/card types: both role and use-case data $ref
schemas/defs/cast-page.schema.json, and a bad card fails both.

Run with `make test-scripts` (CI runs it too).
"""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED_ID = "https://blowhorn.ai/schemas/defs/cast-page.schema.json"
AJV = ["npx", "--yes", "ajv-cli@5.0.0", "validate", "--strict=false"]
REFS = ["-r", str(ROOT / "schemas/defs/cast-page.schema.json")]


def ajv(schema, data_path):
    return subprocess.run(
        AJV + ["-s", str(schema)] + REFS + ["-d", str(data_path)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


class CastPageSchemaTest(unittest.TestCase):
    def test_both_schemas_ref_shared_defs(self):
        for name in ("roles.schema.json", "use-cases.schema.json"):
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            for key in ("line", "text", "card"):
                self.assertEqual(
                    schema["definitions"][key],
                    {"$ref": f"{SHARED_ID}#/definitions/{key}"},
                    msg=f"{name} definitions.{key} must $ref the shared schema",
                )

    def test_valid_data_passes(self):
        for schema, data in (
            ("schemas/roles.schema.json", "data/roles.json"),
            ("schemas/use-cases.schema.json", "data/use-cases.json"),
        ):
            result = ajv(ROOT / schema, ROOT / data)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_bad_card_fails_roles_and_use_cases(self):
        cases = (
            ("schemas/roles.schema.json", "data/roles.json", "roles"),
            ("schemas/use-cases.schema.json", "data/use-cases.json", "use_cases"),
        )
        for schema, data, key in cases:
            with self.subTest(data=data):
                payload = json.loads((ROOT / data).read_text(encoding="utf-8"))
                broken = copy.deepcopy(payload)
                broken[key][0]["pains"][0]["t"] = "A title with an em dash — here"
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".json",
                    encoding="utf-8",
                    delete=False,
                ) as tmp:
                    json.dump(broken, tmp)
                    tmp_path = Path(tmp.name)
                try:
                    result = ajv(ROOT / schema, tmp_path)
                    self.assertNotEqual(
                        result.returncode,
                        0,
                        f"{data}: em-dash card title should fail validation",
                    )
                    combined = result.stderr + result.stdout
                    self.assertTrue(
                        combined.strip(),
                        f"{data}: ajv should report why the card failed",
                    )
                finally:
                    tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
