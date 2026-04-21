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
        prompt = command[-1]
        self.assertEqual(command[:2], ["codex.cmd", "exec"])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertIn("-C", command)
        self.assertIn("--output-schema", command)
        self.assertIn("-o", command)
        self.assertIn("source.map.md", prompt)
        self.assertIn("book.blueprint.md", prompt)
        self.assertIn("输出内容里只能是 `source.map.md` 正文", prompt)
        self.assertIn("把完整的 `source.map.md` 正文放进 `source_map` 字段", prompt)
        self.assertIn("当前已有的标题顺序、字段名和骨架；只填内容，不要自创结构", prompt)
        self.assertIn("章节只作为定位信息", prompt)
        self.assertIn("## Batch 01 (EP01-05):", prompt)
        self.assertIn("### EP01:", prompt)
        self.assertIn("**source_chapter_span**:", prompt)
        self.assertIn("**must-keep_beats**:", prompt)
        self.assertIn("**function_signals**:", prompt)
        self.assertIn("**ending_function**:", prompt)
        self.assertIn("**irreversibility_level**:", prompt)
        self.assertIn("**must-not-add / must-not-jump**:", prompt)
        self.assertIn("function_signals", prompt)
        self.assertIn("ending_function", prompt)
        self.assertIn("irreversibility_level", prompt)
        self.assertIn("1-3 分钟动态浮动", prompt)
        self.assertIn("平均按 2 分钟/集", prompt)
        self.assertIn("must-keep_beats` 必须写成 3-5 条", prompt)
        self.assertIn("每一条都必须以标签开头", prompt)
        self.assertIn("【信息】", prompt)
        self.assertIn("【关系】", prompt)
        self.assertIn("【动作】", prompt)
        self.assertIn("【钩子】", prompt)
        self.assertIn("不能只复述集标题或抽象氛围词", prompt)
        self.assertIn("相邻两集如果只是重复同一种羞辱、盘问、试探、误会", prompt)
        self.assertIn("必须保护角色知识边界", prompt)
        self.assertIn("source_chapter_span` 已经包含硬事件本体", prompt)
        self.assertIn("当前集就必须正面承载这个事件", prompt)
        self.assertIn("【钩子】` 可以卡在硬事件发生后的余波", prompt)
        self.assertIn("不能在 source span 已经写出事件本体时，还把本集写成“等待期间”", prompt)
        self.assertIn("不得用 `must-not-add / must-not-jump` 人为压住 source span 已经发生的主事件", prompt)
        self.assertIn("source_chapter_span` 已含鉴定结果正文，但 `must-keep_beats` 还写“鉴定等待期间”", prompt)
        self.assertIn("source_chapter_span` 已含公开揭露或正式登场，但 `【钩子】` 还写“即将介绍出场”", prompt)
        self.assertIn("让 writer 看完后知道“这一集必须完成什么变化”", prompt)
        self.assertEqual(mock_run.call_args.kwargs["cwd"], root)
        self.assertEqual(
            source_map_output,
            "# Source Map\n\n- mapping_status: complete\n",
        )


if __name__ == "__main__":
    unittest.main()
