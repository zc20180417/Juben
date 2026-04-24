import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "_ops" / "run_book_map.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_book_map_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RunBookMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()

    def test_main_invokes_codex_with_source_map_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("小说正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text("# Book Blueprint\n\n## 主线\n已填写\n", encoding="utf-8")
            source_map = project / "source.map.md"
            source_map.write_text("# Source Map\n\n- mapping_status: pending_book_extraction\n", encoding="utf-8")
            run_manifest = project / "run.manifest.md"
            run_manifest.write_text("run manifest", encoding="utf-8")
            entry = root / "harness" / "framework" / "entry.md"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("entry", encoding="utf-8")

            with mock.patch.object(self.module, "ROOT", root), \
                 mock.patch.object(self.module, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.module, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.module, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.module, "ENTRY", entry), \
                 mock.patch.object(self.module, "_resolve_llm_cli", return_value=("codex", "codex.cmd")), \
                 mock.patch.object(self.module.subprocess, "run") as mock_run:
                def _fake_run(command, **kwargs):
                    output_index = command.index("-o") + 1
                    output_path = Path(command[output_index])
                    output_path.write_text(
                        json.dumps({"source_map": "# Source Map\n\n- mapping_status: complete\n"}),
                        encoding="utf-8",
                    )
                    return mock.Mock(returncode=0, stdout="", stderr="")

                mock_run.side_effect = _fake_run
                mock_run.return_value.returncode = 0
                rc = self.module.main(
                    [
                        "--novel-file",
                        "novel.md",
                        "--episodes",
                        "4",
                        "--batch-size",
                        "2",
                        "--strategy",
                        "original_fidelity",
                        "--intensity",
                        "light",
                    ]
                )
                source_map_output = source_map.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        command = mock_run.call_args.args[0]
        prompt = mock_run.call_args.kwargs["input"].decode("utf-8")
        self.assertEqual(command[:2], ["codex.cmd", "exec"])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertIn("-C", command)
        self.assertIn("--output-schema", command)
        self.assertIn("-o", command)
        self.assertEqual(command[-1], "-")
        self.assertIn("source.map.md", prompt)
        self.assertIn("book.blueprint.md", prompt)
        self.assertIn("## Batch 01 (EP01-05):", prompt)
        self.assertIn("### EP01:", prompt)
        self.assertIn("**source_chapter_span**:", prompt)
        self.assertIn("**must-keep_beats**:", prompt)
        self.assertIn("**must-not-add / must-not-jump**:", prompt)
        self.assertIn("**ending_function**:", prompt)
        self.assertIn("每一集都应当是一个可以成立的短剧单元", prompt)
        self.assertIn("一集至少要形成一个完整主戏", prompt)
        self.assertIn("首集尤其不能薄", prompt)
        self.assertIn("`must-keep_beats` 保持 3-5 条", prompt)
        self.assertIn("不要把分集切成“提纲式事件切片”", prompt)
        self.assertNotIn("**function_signals**:", prompt)
        self.assertNotIn("**density_anchor**:", prompt)
        self.assertNotIn("**scene_plan**:", prompt)
        self.assertNotIn("**irreversibility_level**:", prompt)
        self.assertNotIn("primary_function=intrusion", prompt)
        self.assertNotIn("exposure_mode=public/private", prompt)
        self.assertNotIn("target_scene_count", prompt)
        self.assertNotIn("target_delta_count", prompt)
        self.assertNotIn("target_length_band", prompt)
        self.assertNotIn("stop_when", prompt)
        self.assertEqual(mock_run.call_args.kwargs["cwd"], root)
        self.assertEqual(
            source_map_output,
            "# Source Map\n\n- mapping_status: complete\n",
        )

    def test_main_accepts_existing_complete_source_map_when_backend_returns_status_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("小说正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text("# Book Blueprint\n\n## 主线\n已填写\n", encoding="utf-8")
            source_map = project / "source.map.md"
            source_map.write_text(
                "# Source Map\n\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-05): 标题\n"
                "### EP01: 标题\n"
                "**source_chapter_span**: 第1章前半\n"
                "**must-keep_beats**:\n"
                "- 【信息】已存在完整映射\n",
                encoding="utf-8",
            )
            run_manifest = project / "run.manifest.md"
            run_manifest.write_text("run manifest", encoding="utf-8")
            entry = root / "harness" / "framework" / "entry.md"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("entry", encoding="utf-8")

            with mock.patch.object(self.module, "ROOT", root), \
                 mock.patch.object(self.module, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.module, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.module, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.module, "ENTRY", entry), \
                 mock.patch.object(self.module, "_resolve_llm_cli", return_value=("codex", "codex.cmd")), \
                 mock.patch.object(self.module.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="当前 source.map 已完整", stderr="")):
                rc = self.module.main(
                    [
                        "--novel-file",
                        "novel.md",
                        "--episodes",
                        "4",
                        "--batch-size",
                        "2",
                        "--strategy",
                        "original_fidelity",
                        "--intensity",
                        "light",
                    ]
                )

        self.assertEqual(rc, 0)


def _override_test_main_invokes_codex_with_source_map_prompt(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        project = root / "harness" / "project"
        framework = root / "harness" / "framework"
        project.mkdir(parents=True)
        framework.mkdir(parents=True)
        novel = root / "novel.md"
        novel.write_text("第1章\n内容", encoding="utf-8")
        blueprint = project / "book.blueprint.md"
        blueprint.write_text("# Book Blueprint\n", encoding="utf-8")
        source_map = project / "source.map.md"
        source_map.write_text("# Source Map\n", encoding="utf-8")
        run_manifest = project / "run.manifest.md"
        run_manifest.write_text("manifest", encoding="utf-8")
        entry = framework / "entry.md"
        entry.write_text("entry", encoding="utf-8")
        template = framework / "map-book-prompt.template.md"
        template.write_text("episodes={{episodes}}\n{{source_map_rel}}\n", encoding="utf-8")
        prompts = project / "prompts"
        with mock.patch.object(self.module, "ROOT", root), \
             mock.patch.object(self.module, "BOOK_BLUEPRINT", blueprint), \
             mock.patch.object(self.module, "SOURCE_MAP", source_map), \
             mock.patch.object(self.module, "RUN_MANIFEST", run_manifest), \
             mock.patch.object(self.module, "ENTRY", entry), \
             mock.patch.object(self.module, "MAP_PROMPT_TEMPLATE", template), \
             mock.patch.object(self.module, "PROMPTS_DIR", prompts):
            rc = self.module.main([
                "--novel-file", "novel.md",
                "--episodes", "4",
                "--batch-size", "2",
                "--strategy", "original_fidelity",
                "--intensity", "light",
            ])
            self.assertEqual(rc, 0)
            self.assertIn("episodes=4", (prompts / "map-book.prompt.md").read_text(encoding="utf-8"))


def _override_test_main_accepts_existing_complete_source_map_when_backend_returns_status_text(self) -> None:
    source = Path(self.module.__file__).read_text(encoding="utf-8")
    self.assertNotIn("subprocess.run", source)
    self.assertFalse(hasattr(self.module, "_resolve_llm_cli"))


RunBookMapTests.test_main_invokes_codex_with_source_map_prompt = _override_test_main_invokes_codex_with_source_map_prompt
RunBookMapTests.test_main_accepts_existing_complete_source_map_when_backend_returns_status_text = _override_test_main_accepts_existing_complete_source_map_when_backend_returns_status_text


if __name__ == "__main__":
    unittest.main()
