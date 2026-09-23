from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPOSITORY_ROOT
    / "skills"
    / "reconcile-json-localization"
    / "scripts"
    / "audit_json_parity.py"
)


class AuditJsonParityTest(unittest.TestCase):
    def run_audit(
        self,
        source_text: str,
        target_text: str,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            source = directory / "en.json"
            target = directory / "zh-CN.json"
            source.write_text(source_text, encoding="utf-8")
            target.write_text(target_text, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    str(target),
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_matching_structure_and_tokens_pass(self) -> None:
        source = json.dumps(
            {
                "greeting": "Welcome, {name}",
                "help": '<a href="/help" title="Help">Read [docs](/guide)</a>',
                "settings": {"enabled": True},
                "steps": ["Open", "Save"],
            }
        )
        target = json.dumps(
            {
                "greeting": "欢迎，{name}",
                "help": '<a href="/help" title="帮助">阅读[文档](/guide)</a>',
                "settings": {"enabled": True},
                "steps": ["打开", "保存"],
            },
            ensure_ascii=False,
        )

        completed = self.run_audit(source, target)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "mechanical_parity")
        self.assertEqual(report["summary"], {"errors": 0, "reviews": 0})
        self.assertEqual(report["coverage"]["percent"], 100.0)
        self.assertEqual(report["coverage"]["unresolved"], 0)

    def test_reports_structural_and_contract_differences(self) -> None:
        source = json.dumps(
            {
                "missing": "Add me",
                "ordered": {"first": "One", "second": "Two"},
                "count": 2,
                "enabled": True,
                "items": ["Hello {name}", "Done", "Last"],
            }
        )
        target = json.dumps(
            {
                "extra": "Remove me",
                "ordered": {"second": "二", "first": "一"},
                "count": "2",
                "enabled": False,
                "items": ["你好", ""],
            },
            ensure_ascii=False,
        )

        completed = self.run_audit(source, target)

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        kinds = {finding["kind"] for finding in report["errors"]}
        self.assertTrue(
            {
                "missing_key",
                "extra_key",
                "key_order_mismatch",
                "type_mismatch",
                "scalar_value_mismatch",
                "array_length_mismatch",
                "protected_token_mismatch",
                "empty_translation",
            }.issubset(kinds)
        )

    def test_duplicate_key_is_an_input_error(self) -> None:
        completed = self.run_audit(
            '{"duplicate": "first", "duplicate": "second"}',
            '{"duplicate": "重复"}',
        )

        self.assertEqual(completed.returncode, 2)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "input_error")
        self.assertIn("duplicate key", report["message"])

    def test_nonstandard_json_constants_are_input_errors(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                completed = self.run_audit(
                    f'{{"value": {constant}}}',
                    f'{{"value": {constant}}}',
                )
                self.assertEqual(completed.returncode, 2)
                report = json.loads(completed.stdout)
                self.assertEqual(report["status"], "input_error")
                self.assertIn("non-standard JSON constant", report["message"])

    def test_identical_natural_language_requires_semantic_review(self) -> None:
        completed = self.run_audit(
            '{"action": "Continue"}',
            '{"action": "Continue"}',
        )

        self.assertEqual(completed.returncode, 3)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "review_required")
        kinds = {finding["kind"] for finding in report["reviews"]}
        self.assertIn("untranslated_identical", kinds)
        self.assertEqual(report["coverage"]["review_required"], 1)

    def test_brand_is_discovered_but_not_automatically_decided(self) -> None:
        completed = self.run_audit(
            '{"action": "Sign in with GitHub"}',
            '{"action": "使用 GitHub 登录"}',
        )

        self.assertEqual(completed.returncode, 3)
        report = json.loads(completed.stdout)
        candidates = {
            item["value"]: item for item in report["sourceEnglishCandidates"]
        }
        self.assertEqual(
            candidates["GitHub"],
            {"value": "GitHub", "kind": "mixed_identifier", "count": 1},
        )
        self.assertNotIn("allowances", report)

    def test_partial_english_requires_semantic_review(self) -> None:
        completed = self.run_audit(
            '{"action": "Connect your GitHub account to continue"}',
            '{"action": "连接你的 GitHub account 以继续"}',
        )

        self.assertEqual(completed.returncode, 3)
        report = json.loads(completed.stdout)
        finding = next(
            item for item in report["reviews"] if item["kind"] == "unprotected_english"
        )
        self.assertEqual(finding["fragments"], ["GitHub", "account"])

    def test_different_all_english_target_requires_semantic_review(self) -> None:
        completed = self.run_audit(
            '{"action": "Please try again"}',
            '{"action": "Retry"}',
        )

        self.assertEqual(completed.returncode, 3)
        report = json.loads(completed.stdout)
        kinds = {finding["kind"] for finding in report["reviews"]}
        self.assertIn("english_only_target", kinds)

    def test_exact_protected_syntax_must_match(self) -> None:
        cases = {
            "url": ("Visit https://old.example.com", "访问 https://new.example.com"),
            "inline_code": ("Run `npm install`", "运行 `npm remove`"),
            "email": ("Email help@example.com", "发送邮件到 other@example.com"),
            "path": ("Open /etc/app.conf", "打开 /tmp/app.conf"),
            "flag": ("Use --verbose", "使用 --quiet"),
            "version": ("Requires v1.2.3", "需要 v9.9.9"),
            "markdown": ("Read [docs](/guide)", "阅读[文档](/other)"),
        }
        for name, (source_value, target_value) in cases.items():
            with self.subTest(name=name):
                completed = self.run_audit(
                    json.dumps({"message": source_value}),
                    json.dumps({"message": target_value}, ensure_ascii=False),
                )
                self.assertEqual(completed.returncode, 1, completed.stdout)
                report = json.loads(completed.stdout)
                kinds = {finding["kind"] for finding in report["errors"]}
                self.assertIn("protected_token_mismatch", kinds)

    def test_placeholder_inside_translatable_html_attribute_is_protected(self) -> None:
        completed = self.run_audit(
            '{"message": "<span title=\\"Hello {name}\\">Welcome</span>"}',
            '{"message": "<span title=\\"你好\\">欢迎</span>"}',
        )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        finding = next(
            item
            for item in report["errors"]
            if item["kind"] == "protected_token_mismatch"
        )
        self.assertIn("brace:name", finding["missing"])

    def test_all_machine_html_attributes_must_remain_exact(self) -> None:
        completed = self.run_audit(
            '{"link": "<a href=\\"/settings\\" target=\\"_blank\\" rel=\\"help\\">Settings</a>"}',
            '{"link": "<a href=\\"/settings\\" target=\\"_self\\" rel=\\"nofollow\\">设置</a>"}',
        )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        finding = next(
            item
            for item in report["errors"]
            if item["kind"] == "protected_token_mismatch"
        )
        self.assertIn("html_attribute:0:target=_blank", finding["missing"])
        self.assertIn("html_attribute:0:rel=nofollow", finding["extra"])

    def test_html_tag_order_and_nesting_must_remain_exact(self) -> None:
        completed = self.run_audit(
            '{"message": "<b><i>Hello</i></b>"}',
            '{"message": "<i><b>你好</b></i>"}',
        )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        kinds = {finding["kind"] for finding in report["errors"]}
        self.assertIn("protected_token_mismatch", kinds)

    def test_identical_findings_are_aggregated_by_path(self) -> None:
        completed = self.run_audit(
            json.dumps(
                {
                    "a": "Please try again.",
                    "b": "Please try again.",
                    "c": "Please try once more.",
                }
            ),
            json.dumps(
                {
                    "a": "Please try again.",
                    "b": "Please try again.",
                    "c": "Retry",
                }
            ),
        )

        self.assertEqual(completed.returncode, 3)
        report = json.loads(completed.stdout)
        # summary counts review paths; the reviews array holds aggregated groups.
        self.assertEqual(report["summary"], {"errors": 0, "reviews": 3})
        self.assertEqual(len(report["reviews"]), 2)
        identical = next(
            item
            for item in report["reviews"]
            if item["kind"] == "untranslated_identical"
        )
        self.assertEqual(identical["paths"], ["/a", "/b"])

    def test_untranslated_html_attribute_requires_review(self) -> None:
        completed = self.run_audit(
            '{"link": "<a href=\\"/settings\\" title=\\"Open settings\\">Settings</a>"}',
            '{"link": "<a href=\\"/settings\\" title=\\"Open settings\\">设置</a>"}',
        )

        self.assertEqual(completed.returncode, 3)
        report = json.loads(completed.stdout)
        finding = next(
            item for item in report["reviews"] if item["kind"] == "unprotected_english"
        )
        self.assertEqual(finding["fragments"], ["Open", "settings"])


if __name__ == "__main__":
    unittest.main()
