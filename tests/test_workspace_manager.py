"""Regression tests for workspace naming and path safety."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from workspace_manager import WorkspaceManager  # noqa: E402


class WorkspaceManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.manager = WorkspaceManager(str(self.base))

    def tearDown(self):
        self.temp.cleanup()

    def inferred_label(self, description):
        result = self.manager._infer_project_name(description)
        # Names end in a hyphen and the current YYYYMMDD date.
        self.assertRegex(result, r"-\d{8}$")
        return result[:-9]

    def test_inference_matches_documented_chinese_examples(self):
        examples = {
            "写一个处理CSV的脚本": "CSV处理脚本",
            "帮我写一个处理CSV的脚本": "CSV处理脚本",
            "帮我写一个Python脚本来处理CSV文件": "CSV处理脚本",
            "创建React登录组件": "React登录组件",
            "分析销售数据": "销售数据分析",
            "修复认证bug": "认证bug修复",
            "搭建API服务器": "API服务器",
        }
        for description, expected in examples.items():
            with self.subTest(description=description):
                self.assertEqual(self.inferred_label(description), expected)

    def test_empty_description_uses_safe_fallback(self):
        self.assertEqual(self.inferred_label(""), "项目")

    def test_create_workspace_rejects_path_traversal(self):
        for name in ("../outside", "sub/child", r"..\outside", ".", "..", ""):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.manager.create_workspace(name)

    def test_archive_cannot_delete_directory_outside_work_root(self):
        outside = self.base / "outside"
        outside.mkdir()
        marker = outside / "keep.txt"
        marker.write_text("keep", encoding="utf-8")

        with self.assertRaises(ValueError):
            self.manager.archive_workspace("../outside")

        self.assertTrue(marker.exists())
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_resolve_path_rejects_path_like_filename(self):
        self.manager.create_workspace("safe")
        for filename in ("../outside.txt", r"..\outside.txt", "/tmp/outside.txt", ".."):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    self.manager.resolve_path(filename, "safe")

    def test_workspace_symlink_cannot_escape_work_root(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.manager.work_dir.mkdir(parents=True, exist_ok=True)
        (self.manager.work_dir / "escape").symlink_to(outside, target_is_directory=True)

        with self.assertRaises(ValueError):
            self.manager.switch_workspace("escape")

    def test_clean_temp_rejects_symlink_directory(self):
        workspace = self.manager.create_workspace("safe")
        external_temp = self.base / "external-temp"
        external_temp.mkdir()
        temp_dir = workspace / "temp"
        temp_dir.rmdir()
        temp_dir.symlink_to(external_temp, target_is_directory=True)

        with self.assertRaises(ValueError):
            self.manager.clean_temp("safe")

    def test_cli_returns_friendly_error_for_unsafe_name(self):
        script = ROOT / "workspace_manager.py"
        completed = subprocess.run(
            [sys.executable, str(script), "create", "../outside"],
            cwd=str(self.base),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("工作空间名称", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
