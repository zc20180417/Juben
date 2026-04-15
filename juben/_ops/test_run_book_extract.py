import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "_ops" / "run_book_extract.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_book_extract_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RunBookExtractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()

    def test_main_invokes_claude_with_blueprint_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("小说正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text("# Book Blueprint\n", encoding="utf-8")

            with mock.patch.object(self.module, "ROOT", root), \
                 mock.patch.object(self.module.subprocess, "run") as mock_run:
                mock_run.return_value.returncode = 0
                rc = self.module.main(["--novel-file", "novel.md"])

        self.assertEqual(rc, 0)
        command = mock_run.call_args.args[0]
        prompt = command[-1]
        self.assertEqual(command[:3], ["claude", "-p", "--dangerously-skip-permissions"])
        self.assertIn("book.blueprint.md", prompt)
        self.assertIn("主线", prompt)
        self.assertIn("集数建议", prompt)
        self.assertIn("角色弧光", prompt)
        self.assertIn("章节只作为定位信息", prompt)
        self.assertIn("1-3 分钟动态浮动", prompt)
        self.assertIn("平均按 2 分钟/集", prompt)
        self.assertIn("recommended_total_episodes", prompt)
        self.assertEqual(mock_run.call_args.kwargs["cwd"], root)


if __name__ == "__main__":
    unittest.main()
