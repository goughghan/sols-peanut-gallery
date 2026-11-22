# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
EXAMPLES = ROOT / "examples"


class ContractTests(unittest.TestCase):
    CASES = (
        ("reaction-request.schema.json", "reaction-text.json"),
        ("reaction-request.schema.json", "reaction-catalog.json"),
        ("delivery.schema.json", "delivery-text.json"),
        ("acknowledgment.schema.json", "acknowledgment.json"),
        ("pairing-request.schema.json", "pairing-request.json"),
        ("pairing-response.schema.json", "pairing-response.json"),
        ("catalog.schema.json", "catalog-empty.json"),
    )

    @staticmethod
    def load_json(path: Path):
        with path.open("r", encoding="utf-8") as source:
            return json.load(source)

    def test_schemas_are_valid_draft_2020_12(self):
        for path in sorted(CONTRACTS.glob("*.schema.json")):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(self.load_json(path))

    def test_examples_match_contracts(self):
        checker = FormatChecker()
        for schema_name, example_name in self.CASES:
            with self.subTest(example=example_name):
                validator = Draft202012Validator(
                    self.load_json(CONTRACTS / schema_name), format_checker=checker)
                errors = list(validator.iter_errors(self.load_json(EXAMPLES / example_name)))
                self.assertEqual([], errors)

    def test_queue_tool_requires_exactly_one_content_source(self):
        tools = self.load_json(CONTRACTS / "mcp-tools.json")["tools"]
        self.assertEqual(["find_display_items", "queue_display"],
                         [tool["name"] for tool in tools])
        validator = Draft202012Validator(
            tools[1]["inputSchema"], format_checker=FormatChecker())
        base = {"request_id": "55555555-5555-4555-8555-555555555555"}
        self.assertFalse(list(validator.iter_errors({**base, "emoji": "🙂"})))
        self.assertFalse(list(validator.iter_errors(
            {**base, "reaction_id": "example-placeholder"})))
        self.assertFalse(list(validator.iter_errors({**base, "caption": "Caption only."})))
        self.assertTrue(list(validator.iter_errors(
            {**base, "emoji": "🙂", "reaction_id": "example-placeholder"})))

    def test_examples_contain_no_live_configuration(self):
        forbidden = ("192.168.", "tunnel_", "org-", "sk-")
        for path in sorted(EXAMPLES.glob("*.json")):
            with self.subTest(example=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertFalse(any(value in text for value in forbidden))


if __name__ == "__main__":
    unittest.main()
