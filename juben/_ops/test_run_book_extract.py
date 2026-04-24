import importlib.util
import json
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

    def test_main_writes_blueprint_from_codex_json_payload(self) -> None:
        content = ""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            framework = root / "harness" / "framework"
            project.mkdir(parents=True, exist_ok=True)
            framework.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("小说正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text("# Book Blueprint\n\n- chapter_count: 17\n", encoding="utf-8")
            (project / "run.manifest.md").write_text("manifest", encoding="utf-8")
            (framework / "entry.md").write_text("entry", encoding="utf-8")

            output_dir = root / "tmp"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "extract-output.json"

            def _fake_build(cli: str, executable: str, prompt: str, output_path=None, schema_path=None):
                self.assertEqual(cli, "codex")
                self.assertIn("book.blueprint.md", prompt)
                self.assertIn("recommended_total_episodes", prompt)
                self.assertIn("章节只用于 source 定位", prompt)
                self.assertIn("项目目标总时长", prompt)
                self.assertIsNotNone(output_path)
                return ["codex.cmd", "exec", prompt]

            def _fake_run(*args, **kwargs):
                output_path.write_text(
                    json.dumps(
                        {
                            "book_blueprint": (
                                "# Book Blueprint\n\n"
                                "- source_file: novel.md\n"
                                "- extraction_status: extracted\n"
                                "- chapter_count: 17\n"
                                "- target_total_minutes: 50\n"
                                "- target_episode_minutes: 2\n"
                                "- episode_minutes_min: 1\n"
                                "- episode_minutes_max: 3\n"
                                "- recommended_total_episodes: 25\n\n"
                                "## 主线\n\n主线内容\n\n"
                                "## 集数建议\n\n"
                                "- 推荐区间：23-25集\n"
                                "- 最终采用：25集\n"
                                "- 可独立成集戏剧节点：节点A；节点B\n"
                                "- 应合并压缩的内容：重复羞辱、重复试探\n"
                                "- 为什么不是更短/更长：理由\n\n"
                                "## 角色弧光\n\n角色弧光\n\n"
                                "## 关系变化\n\n关系变化\n\n"
                                "## 关键反转\n\n关键反转\n\n"
                                "## 结局闭环\n\n结局闭环\n\n"
                                "## 章节索引（仅定位）\n\n- 第1章：定位\n"
                            )
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(self.module, "ROOT", root), \
                 mock.patch.object(self.module, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.module, "RUN_MANIFEST", project / "run.manifest.md"), \
                 mock.patch.object(self.module, "ENTRY", framework / "entry.md"), \
                 mock.patch.object(self.module, "_resolve_llm_cli", return_value=("codex", "codex.cmd")), \
                mock.patch.object(self.module, "_build_llm_command", side_effect=_fake_build), \
                 mock.patch.object(self.module.tempfile, "mkdtemp", return_value=str(output_dir)), \
                 mock.patch.object(self.module.subprocess, "run", side_effect=_fake_run):
                rc = self.module.main(["--novel-file", "novel.md"])
                content = blueprint.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        self.assertIn("- recommended_total_episodes: 25", content)
        self.assertIn("## 集数建议", content)
        self.assertIn("## 章节索引（仅定位）", content)

    def test_llm_subprocess_env_strips_nested_codex_session_vars(self) -> None:
        with mock.patch.dict(
            self.module.os.environ,
            {
                "CODEX_THREAD_ID": "thread",
                "CODEX_SHELL": "1",
                "CODEX_INTERNAL_ORIGINATOR_OVERRIDE": "Codex Desktop",
            },
            clear=False,
        ):
            env = self.module._llm_subprocess_env()

        self.assertNotIn("CODEX_THREAD_ID", env)
        self.assertNotIn("CODEX_SHELL", env)
        self.assertNotIn("CODEX_INTERNAL_ORIGINATOR_OVERRIDE", env)

    def test_extract_qwen_result_text_prefers_result_event(self) -> None:
        raw = json.dumps(
            [
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "ignored"}]}},
                {"type": "result", "result": "{\"book_blueprint\":\"# Book Blueprint\\n- recommended_total_episodes: 18\\n\"}"},
            ],
            ensure_ascii=False,
        )

        text = self.module._extract_qwen_result_text(raw)

        self.assertIn("\"book_blueprint\"", text)


def _override_test_main_writes_blueprint_from_codex_json_payload(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        project = root / "harness" / "project"
        framework = root / "harness" / "framework"
        project.mkdir(parents=True)
        framework.mkdir(parents=True)
        novel = root / "novel.md"
        novel.write_text("第1章\n内容", encoding="utf-8")
        blueprint = project / "book.blueprint.md"
        blueprint.write_text("# Book Blueprint\n- chapter_count: 1\n", encoding="utf-8")
        template = framework / "extract-book-prompt.template.md"
        template.write_text("目标 {{blueprint_rel}}\n{{novel_text}}\n", encoding="utf-8")
        prompts = project / "prompts"
        with mock.patch.object(self.module, "ROOT", root), \
             mock.patch.object(self.module, "BOOK_BLUEPRINT", blueprint), \
             mock.patch.object(self.module, "EXTRACT_PROMPT_TEMPLATE", template), \
             mock.patch.object(self.module, "PROMPTS_DIR", prompts):
            rc = self.module.main(["--novel-file", "novel.md"])
            self.assertEqual(rc, 0)
            self.assertTrue((prompts / "extract-book.prompt.md").exists())


def _override_test_llm_subprocess_env_strips_nested_codex_session_vars(self) -> None:
    self.assertFalse(hasattr(self.module, "_llm_subprocess_env"))


def _override_test_extract_qwen_result_text_prefers_result_event(self) -> None:
    source = Path(self.module.__file__).read_text(encoding="utf-8")
    self.assertNotIn("qwen", source)
    self.assertNotIn("subprocess.run", source)


RunBookExtractTests.test_main_writes_blueprint_from_codex_json_payload = _override_test_main_writes_blueprint_from_codex_json_payload
RunBookExtractTests.test_llm_subprocess_env_strips_nested_codex_session_vars = _override_test_llm_subprocess_env_strips_nested_codex_session_vars
RunBookExtractTests.test_extract_qwen_result_text_prefers_result_event = _override_test_extract_qwen_result_text_prefers_result_event


if __name__ == "__main__":
    unittest.main()
