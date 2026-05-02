import contextlib
import io
import importlib.util
import json
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "_ops" / "run_writer.py"


def _load_run_writer_module():
    spec = importlib.util.spec_from_file_location("run_writer_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RunWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_writer = _load_run_writer_module()

    @staticmethod
    def _invoked_prompt(call) -> str:
        stdin_text = call.kwargs.get("stdin_text")
        if stdin_text is not None:
            return stdin_text
        return call.args[0][-1]

    @staticmethod
    def _json_sidecar(path: Path) -> Path:
        return path.with_suffix(".json")

    def _write_batch_brief(self, root: Path) -> None:
        brief_dir = root / "harness" / "project" / "batch-briefs"
        brief_dir.mkdir(parents=True, exist_ok=True)
        (brief_dir / "batch03_EP11-15.md").write_text("# brief\n", encoding="utf-8")

    def _write_source_fixture(self, root: Path) -> None:
        project = root / "harness" / "project"
        project.mkdir(parents=True, exist_ok=True)

        (project / "run.manifest.md").write_text(
            "# Run Manifest\n\n- source_file: novel.md\n",
            encoding="utf-8",
        )
        (project / "source.map.md").write_text(
            "\n".join(
                [
                    "# Source Map",
                    "",
                    "## Batch 03 (EP11-15)",
                    "",
                    "### EP11: test",
                    "**source_chapter_span**: 第1章前半",
                    "**knowledge_boundary**:",
                    "- EP11 女主不知道陌生男人姓名",
                    "",
                    "### EP12: test",
                    "**source_chapter_span**: 第1章后半",
                    "**knowledge_boundary**:",
                    "- EP12 双方已互知姓名",
                    "",
                    "### EP13: test",
                    "**source_chapter_span**: 第2章",
                    "**knowledge_boundary**:",
                    "- EP13 按现场公开信息称呼",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "novel.md").write_text(
            "\n".join(
                [
                    "第1章 错认",
                    "",
                    "前半第一段。",
                    "",
                    "前半第二段。",
                    "",
                    "后半第三段。",
                    "",
                    "后半第四段。",
                    "",
                    "第2章 认亲",
                    "",
                    "第二章内容。",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_build_episode_source_excerpt_splits_chapter_halves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_source_fixture(root)

            with mock.patch.object(self.run_writer, "ROOT", root):
                ep11 = self.run_writer._build_episode_source_excerpt("batch03", "EP-11")
                ep12 = self.run_writer._build_episode_source_excerpt("batch03", "EP-12")

                ep11_text = ep11.read_text(encoding="utf-8")
                ep12_text = ep12.read_text(encoding="utf-8")
                ep11_payload = json.loads(self._json_sidecar(ep11).read_text(encoding="utf-8"))
                ep12_payload = json.loads(self._json_sidecar(ep12).read_text(encoding="utf-8"))

                self.assertIn("- source_span: 第1章前半", ep11_text)
                self.assertIn("- excerpt_tier: baseline", ep11_text)
                self.assertIn("前半第一段。", ep11_text)
                self.assertNotIn("后半第三段。", ep11_text)
                self.assertIn("## Must-Keep Names", ep11_text)
                self.assertIn("## Forbidden Fill", ep11_text)
                self.assertNotIn("## Reusable Source Lines", ep11_text)
                self.assertNotIn("## Scene Modes", ep11_text)
                self.assertNotIn("## Must-Keep Long Lines", ep11_text)
                self.assertNotIn("## Abstract Narration To Externalize", ep11_text)
                self.assertEqual(ep11_payload["excerpt_tier"], "baseline")
                self.assertIn("event_anchors", ep11_payload)
                self.assertNotIn("reusable_source_lines", ep11_payload)
                self.assertNotIn("scene_modes", ep11_payload)
                self.assertLess(len(self._json_sidecar(ep11).read_bytes()), len(ep11.read_bytes()))

                self.assertIn("- source_span: 第1章后半", ep12_text)
                self.assertIn("后半第三段。", ep12_text)
                self.assertNotIn("前半第一段。", ep12_text)
                self.assertEqual(ep12_payload["excerpt_tier"], "baseline")

    def test_build_episode_source_excerpt_accepts_bulleted_source_span(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            (project / "run.manifest.md").write_text(
                "# Run Manifest\n\n- source_file: novel.md\n",
                encoding="utf-8",
            )
            (project / "source.map.md").write_text(
                "\n".join(
                    [
                        "# Source Map",
                        "",
                        "## Batch 02 (EP06-10)",
                        "",
                        "### EP06: test",
                        "- **source_chapter_span**: 第2章",
                        "- **must-keep_beats**:",
                        "  - 第二章事件",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "novel.md").write_text(
                "\n".join(
                    [
                        "第1章 开场",
                        "",
                        "第一章内容。",
                        "",
                        "第2章 发布会",
                        "",
                        "第二章内容。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root):
                excerpt = self.run_writer._build_episode_source_excerpt("batch02", "EP-06")
                text = excerpt.read_text(encoding="utf-8")
                payload = json.loads(self._json_sidecar(excerpt).read_text(encoding="utf-8"))

        self.assertIn("- source_span: 第2章", text)
        self.assertIn("第二章内容。", text)
        self.assertNotIn("第一章内容。", text)
        self.assertEqual(payload["source_span"], "第2章")

    def test_build_episode_source_excerpt_keeps_strong_sections_for_reveal_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            (project / "run.manifest.md").write_text(
                "# Run Manifest\n\n- source_file: novel.md\n",
                encoding="utf-8",
            )
            (project / "source.map.md").write_text(
                "\n".join(
                    [
                        "# Source Map",
                        "",
                        "## Batch 03 (EP11-15)",
                        "",
                        "### EP15: test",
                        "**source_chapter_span**: 第1章",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "novel.md").write_text(
                "\n".join(
                    [
                        "第1章 揭露",
                        "",
                        "主持人走上台，时鸢站在灯下。",
                        "这一巴掌，彻底打醒了所有人。",
                        "刘美兰厉声道：你这是什么态度？亲生父母就在眼前，你一点都不激动、不感恩吗？",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root):
                ep15 = self.run_writer._build_episode_source_excerpt("batch03", "EP-15")
                ep15_text = ep15.read_text(encoding="utf-8")
                ep15_payload = json.loads(self._json_sidecar(ep15).read_text(encoding="utf-8"))

        self.assertIn("- excerpt_tier: strong_scene", ep15_text)
        self.assertIn("## Scene Modes", ep15_text)
        self.assertIn("## Source Usage Boundary", ep15_text)
        self.assertNotIn("## Must-Keep Long Lines", ep15_text)
        self.assertIn("## Abstract Narration To Externalize", ep15_text)
        self.assertEqual(ep15_payload["excerpt_tier"], "strong_scene")
        self.assertIn("scene_modes", ep15_payload)
        self.assertNotIn("must_keep_long_lines", ep15_payload)
        self.assertIn("abstract_narration", ep15_payload)

    def test_build_episode_source_excerpt_uses_low_risk_tier_for_reusable_non_strong_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            (project / "run.manifest.md").write_text(
                "# Run Manifest\n\n- source_file: novel.md\n",
                encoding="utf-8",
            )
            (project / "source.map.md").write_text(
                "\n".join(
                    [
                        "# Source Map",
                        "",
                        "## Batch 03 (EP11-15)",
                        "",
                        "### EP12: test",
                        "**source_chapter_span**: 第1章",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "novel.md").write_text(
                "\n".join(
                    [
                        "第1章 日常",
                        "",
                        "“回来了。”",
                        "“知道了。”",
                        "她把门带上。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root):
                ep12 = self.run_writer._build_episode_source_excerpt("batch03", "EP-12")
                ep12_text = ep12.read_text(encoding="utf-8")
                ep12_payload = json.loads(self._json_sidecar(ep12).read_text(encoding="utf-8"))
                profile = self.run_writer._episode_rule_profile(ep12)
                ep12_markdown_size = len(ep12.read_bytes())
                ep12_json_size = len(self._json_sidecar(ep12).read_bytes())

        self.assertIn("- excerpt_tier: low_risk", ep12_text)
        self.assertIn("## Source Usage Boundary", ep12_text)
        self.assertNotIn("## Reusable Source Lines", ep12_text)
        self.assertNotIn("## Scene Modes", ep12_text)
        self.assertNotIn("## Must-Keep Long Lines", ep12_text)
        self.assertNotIn("## Abstract Narration To Externalize", ep12_text)
        self.assertEqual(profile["excerpt_tier"], "low_risk")
        self.assertEqual(ep12_payload["excerpt_tier"], "low_risk")
        self.assertNotIn("reusable_source_lines", ep12_payload)
        self.assertNotIn("scene_modes", ep12_payload)
        self.assertLess(ep12_json_size, ep12_markdown_size)

    def test_episode_rule_profile_prefers_json_payload_when_both_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            excerpt = Path(tmp) / "EP-11.source.md"
            excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-11",
                        "",
                        "- excerpt_tier: strong_scene",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- legacy line",
                        "",
                        "## Forbidden Fill",
                        "- legacy fill",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            excerpt.with_suffix(".json").write_text(
                json.dumps(
                    {
                        "episode": "EP-11",
                        "source_span": "Chapter 1",
                        "excerpt_tier": "low_risk",
                        "event_anchors": ["Intro", "\"Come in.\""],
                        "must_keep_names": ["Ava"],
                        "forbidden_fill": ["extra_guest_lines"],
                        "reusable_source_lines": ["Come in."],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            profile = self.run_writer._episode_rule_profile(excerpt)

        self.assertEqual(profile["excerpt_tier"], "low_risk")
        self.assertEqual(profile["must_keep_names"], ["Ava"])
        self.assertEqual(profile["forbidden_fill"], ["extra_guest_lines"])
        self.assertFalse(profile["reusable_lines_present"])
        self.assertEqual(profile["scene_modes"], [])

    def test_build_episode_source_excerpt_compacts_baseline_original_excerpt(self) -> None:
        excerpt = "\n\n".join(
            [
                "Chapter One",
                "She enters.",
                "Ava sees the box.",
                "She keeps walking.",
                "Footsteps get closer.",
            ]
        )

        compacted = self.run_writer._compact_original_excerpt(
            excerpt,
            excerpt_tier="baseline",
            must_keep_names=["Ava"],
            reusable_lines=[],
        )

        self.assertIn("Ava sees the box.", compacted)
        self.assertIn("Footsteps get closer.", compacted)
        self.assertNotIn("She keeps walking.", compacted)
        self.assertEqual(len(self.run_writer._excerpt_paragraphs(compacted)), 5)

    def test_build_episode_source_excerpt_compacts_low_risk_original_excerpt(self) -> None:
        excerpt = "\n\n".join(
            [
                "Chapter One",
                "She sits down.",
                '\"Come in.\"',
                "She puts the cup back.",
                '\"Eat first.\"',
            ]
        )

        compacted = self.run_writer._compact_original_excerpt(
            excerpt,
            excerpt_tier="low_risk",
            must_keep_names=[],
            reusable_lines=["Come in."],
        )

        self.assertIn('"Come in."', compacted)
        self.assertIn('"Eat first."', compacted)
        self.assertNotIn("She puts the cup back.", compacted)
        self.assertEqual(len(self.run_writer._excerpt_paragraphs(compacted)), 5)

    def test_fidelity_helpers_derive_names_modes_and_long_lines(self) -> None:
        excerpt = (
            "亲子鉴定结果出来了，主持人走上台，时鸢站在灯下。"
            "苏雨柔脸色发白。"
            "刘美兰厉声道：你这是什么态度？亲生父母就在眼前，你一点都不激动、不感恩吗？"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "voice-anchor.md").write_text(
                "\n".join(
                    [
                        "# Voice Anchor",
                        "",
                        "### 时鸢",
                        "### 苏雨柔",
                        "### 刘美兰",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "character.md").write_text("# Character Reference\n", encoding="utf-8")
            with mock.patch.object(self.run_writer, "ROOT", root):
                names = self.run_writer._extract_must_keep_names(excerpt)
                long_lines = self.run_writer._extract_must_keep_long_lines(
                    excerpt,
                    ["你这是什么态度？亲生父母就在眼前，你一点都不激动、不感恩吗？"],
                )

        self.assertEqual(names[:3], ["时鸢", "苏雨柔", "刘美兰"])
        self.assertIn("你这是什么态度？亲生父母就在眼前，你一点都不激动、不感恩吗？", long_lines)

    def test_reusable_and_long_lines_preserve_source_quotes_without_relation_filter(self) -> None:
        excerpt = (
            "刘美兰看着她，迟迟没有开口。"
            "苏雨柔低声道：“爸，妈，她会不会是……姐姐当年走失的妹妹？”"
            "苏振宏皱眉道：“你叫什么名字？”"
        )

        reusable_lines = self.run_writer._extract_reusable_source_lines(excerpt)
        long_lines = self.run_writer._extract_must_keep_long_lines(excerpt, reusable_lines)

        self.assertIn("爸，妈，她会不会是……姐姐当年走失的妹妹？", reusable_lines)
        self.assertIn("爸，妈，她会不会是……姐姐当年走失的妹妹？", long_lines)
        self.assertIn("你叫什么名字？", reusable_lines)

    def test_episode_rule_profile_falls_back_to_tier_inference_when_metadata_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            excerpt = Path(tmp) / "EP-11.source.md"
            excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-11",
                        "",
                        "## Original Excerpt",
                        "“回来了。”",
                        "",
                        "## Reusable Source Lines",
                        "- 回来了。",
                        "",
                        "## Must-Keep Names",
                        "- 时鸢",
                        "",
                        "## Forbidden Fill",
                        "- 宾客甲",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            profile = self.run_writer._episode_rule_profile(excerpt)

        self.assertEqual(profile["excerpt_tier"], "low_risk")

    def test_extract_abstract_narration_to_externalize(self) -> None:
        excerpt = (
            "这是她事业最风光的时刻。"
            "所有人的目光，像刀子一样扎在苏雨柔身上。"
            "发布会现场恢复平静。"
            "她眼底满是压不住的激动和心疼。"
        )

        abstract_lines = self.run_writer._extract_abstract_narration_to_externalize(excerpt)

        self.assertIn("这是她事业最风光的时刻", abstract_lines)
        self.assertIn("所有人的目光，像刀子一样扎在苏雨柔身上", abstract_lines)
        self.assertIn("发布会现场恢复平静", abstract_lines)
        self.assertIn("她眼底满是压不住的激动和心疼", abstract_lines)

    def test_source_excerpt_requires_fidelity_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            excerpt = Path(tmp) / "EP-15.source.md"
            excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "（当前片段未抽到必须保长句的台词；仍应优先保留原文递进）",
                        "",
                        "## Abstract Narration To Externalize",
                        "（当前片段未抽到必须外化的抽象叙述；仍要避免把小说总结句原样落进 `△`）",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertTrue(self.run_writer._source_excerpt_requires_fidelity_rewrite(excerpt))

            excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-12",
                        "",
                        "## Scene Modes",
                        "- default_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "（当前片段未抽到必须保长句的台词；仍应优先保留原文递进）",
                        "",
                        "## Abstract Narration To Externalize",
                        "（当前片段未抽到必须外化的抽象叙述；仍要避免把小说总结句原样落进 `△`）",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertFalse(self.run_writer._source_excerpt_requires_fidelity_rewrite(excerpt))

    def test_rule_profile_signals_and_minimal_rule_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            excerpt = Path(tmp) / "EP-15.source.md"
            excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "- result_confirmation_scene",
                        "- pressure_scene",
                        "",
                        "## Must-Keep Names",
                        "- 时鸢",
                        "",
                        "## Must-Keep Long Lines",
                        "- 长句测试",
                        "",
                        "## Abstract Narration To Externalize",
                        "- 抽象句测试",
                        "",
                        "## Forbidden Fill",
                        "- 宾客甲",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            profile = self.run_writer._episode_rule_profile(excerpt)
            episode_facts = {
                "function_signals": {
                    "opening_function": "intrusion",
                    "middle_functions": ["escalation", "confrontation"],
                    "strong_function_tags": ["intrusion", "escalation", "hook"],
                },
                "ending_function": "locked_in",
                "irreversibility_level": "hard",
            }
            signals = self.run_writer._rule_profile_signals(profile, episode_facts)
            rule_pack = self.run_writer._build_minimal_rule_pack(
                profile,
                episode_facts,
                include_adjacent_boundary=True,
            )
            self_check = self.run_writer._build_minimal_self_check(profile, episode_facts)

        self.assertEqual(
            signals,
                [
                    "tier:strong_scene",
                    "pressure_scene",
                    "must_keep_names",
                    "must_keep_long_lines",
                "abstract_externalization",
                "forbidden_fill",
            ],
        )
        self.assertIn("运行时最小规则包", rule_pack)
        for token in (
            "`strong_scene`",
            "`must_keep_names`",
            "`must_keep_long_lines`",
            "`abstract_narration`",
            "`forbidden_fill`",
            "`pressure_scene`",
            "`reusable_source_lines`",
        ):
            self.assertIn(token, rule_pack)
        for token in (
            "`opening=intrusion`",
            "别先写无推进的说明性总述",
            "`middle=confrontation`",
            "明确可拍的反制动作",
            "默认别用 `OS` 总结局面",
            "2-3 ",
        ):
            self.assertIn(token, rule_pack)
        for legacy_token in ("城市夜色", "穿着", "姐姐", "亲生女儿", "拦门", "逼近", "压话", "夺物", "车锁", "导航"):
            self.assertNotIn(legacy_token, rule_pack)
        self.assertIn("交稿前最小自检", self_check)
        for section in ("beats：", "顺序：", "壳层：", "场次：", "叙述：", "节奏：", "原句：", "长句：", "强场：", "外化："):
            self.assertIn(section, self_check)
        self.assertIn("能不用 `OS` 就不用", self_check)
        self.assertIn("前几拍已直接进入异常或被迫应对", self_check)
        self.assertIn("默认 `OS=0`", self_check)
        self.assertIn("2-3 ", self_check)

    def test_scene_function_hint_helpers_removed_from_writer(self) -> None:
        self.assertFalse(hasattr(self.run_writer, "_scene_function_rhythm_hint"))
        self.assertFalse(hasattr(self.run_writer, "_scene_function_ending_requirement"))
        self.assertFalse(hasattr(self.run_writer, "_scene_function_irreversibility_hint"))

    def test_writer_runtime_does_not_depend_on_external_semantic_config(self) -> None:
        source = Path(self.run_writer.__file__).read_text(encoding="utf-8")
        self.assertNotIn("WRITER_SEMANTIC_CONFIG_PATH", source)
        self.assertNotIn("REVEAL_SCENE_KEYWORDS = (", source)
        self.assertNotIn("PRESSURE_SCENE_KEYWORDS = (", source)
        self.assertNotIn("RESULT_CONFIRMATION_SCENE_KEYWORDS = (", source)
        self.assertNotIn("EARLY_SIBLING_RELATION_LABEL_RE = re.compile", source)
        self.assertFalse(hasattr(self.run_writer, "WRITER_SEMANTIC_CONFIG_PATH"))

    def test_minimal_runtime_guidance_is_shorter_than_previous_wording(self) -> None:
        profile = {
            "excerpt_tier": "low_risk",
            "scene_modes": ["reveal_scene"],
            "must_keep_names": ["时鸢"],
            "must_keep_long_lines": [],
            "abstract_narration": [],
            "forbidden_fill": ["宾客甲"],
            "reusable_lines_present": True,
        }

        episode_facts = {
            "function_signals": {
                "opening_function": "intrusion",
                "middle_functions": ["escalation"],
                "strong_function_tags": ["intrusion", "hook"],
            },
            "ending_function": "confrontation_pending",
            "irreversibility_level": "medium",
        }

        current_rule_pack = self.run_writer._build_minimal_rule_pack(
            profile,
            episode_facts,
            include_adjacent_boundary=True,
        )
        current_self_check = self.run_writer._build_minimal_self_check(profile, episode_facts)

        legacy_rule_pack = "\n".join(
            [
                "运行时最小规则包：",
                "- 以当前集 `event_anchors` 为硬事件顺序最高权威；若锚点里硬事件已经发生，不得再把它往后拖成“等待 / 前夜 / 即将揭晓”。",
                "- 当前集是 `low_risk`；先读 `reusable_source_lines`、`must_keep_names`、`forbidden_fill`，优先贴着原句和原文句意转写，不要自己补桥接句。",
                "- 默认禁止新增原文没有的新事件、新流程、新人物互动、新职业说明、新后台调度、新承接对白；只允许最小可拍转写和最小位置衔接。",
                "- 角色知道什么，只能按当场已公开的信息写；模型知道，不等于角色知道。",
                "- 读取 `voice-anchor.md` 时只参考气质与禁区，不复用例句，不把示例句写成口头禅。",
                "- 当前集若承接上一集，只能承接 1-2 个镜头后立刻进入新增推进；禁止整场重演上一集尾部。",
                "- `must_keep_names` 非空时，优先保留 source 已公开的人名与称谓，不要退化成“养女 / 宾客 / 男人 / 女人”这类泛称。",
                "- `reveal_scene`：一旦进入揭露拍点，直接写揭露本体，不得再补寒暄、抬杯、宾客附和、后台说明或拖延式铺垫。",
                "- 若草稿里出现 `forbidden_fill` 覆盖的新增内容，删掉后场意仍成立，则必须删除。",
            ]
        )
        legacy_self_check = "\n".join(
            [
                "交稿前最小自检：",
                "- 壳层检查：`△ / ♪ / 【镜头】： / 角色： / 角色（os）：` 各自独占一行，不混排。",
                "- 原句检查：`reusable_source_lines` 里能直接成立的句子，是否优先保留；若没有，必须是因为格式或信息顺序不允许。",
                "- 增写检查：删掉你新增的承接句、流程句、后台句后，场意若仍成立，就说明它不该存在，删掉。",
                "- 顺序检查：`event_anchors` 里已发生的硬事件，当前集是否已经正面写到，而不是继续拖后。",
                "- 人名检查：source 已公开的人名或称谓，是否被你弱化成泛称或简称。",
                "- 揭露检查：揭露前没有额外寒暄、宾客附和、反派 OS、场面话或后台说明。",
                "- 填充检查：`forbidden_fill` 覆盖的内容没有残留在正文里。",
            ]
        )

        self.assertLess(len(current_rule_pack.encode("utf-8")), 3000)
        self.assertIn("交稿前最小自检", current_self_check)
        self.assertIn("beats", current_self_check)
        self.assertIn("顺序", current_self_check)
        self.assertIn("场次", current_self_check)

    def test_strong_scene_rule_pack_adds_visible_detail_and_boundary_guards(self) -> None:
        profile = {
            "excerpt_tier": "strong_scene",
            "scene_modes": ["reveal_scene", "result_confirmation_scene", "pressure_scene"],
            "must_keep_names": ["ShiYuan"],
            "must_keep_long_lines": ["What attitude is this?"],
            "abstract_narration": ["Her eyes turned cold."],
            "forbidden_fill": ["backstage_flow"],
            "reusable_lines_present": True,
        }
        episode_facts = {
            "function_signals": {
                "opening_function": "intrusion",
                "middle_functions": ["escalation", "confrontation"],
                "strong_function_tags": ["intrusion", "escalation", "hook"],
            },
            "ending_function": "locked_in",
            "irreversibility_level": "hard",
            "density_anchor": {
                "target_scene_count": "3-4",
                "target_delta_count": "14-18",
                "target_length_band": "short_dense",
                "stop_when": "阴谋或异常已立 / 关系已极化 / 主角已做选择 / 集尾硬钩已落",
            },
        }

        rule_pack = self.run_writer._build_minimal_rule_pack(
            profile,
            episode_facts,
            include_adjacent_boundary=True,
        )
        self_check = self.run_writer._build_minimal_self_check(profile, episode_facts)

        for token in (
            "`pressure_scene`",
            "场次数按 beats 和 source 推进自然决定",
            "禁新增第一人称叙述",
        ):
            self.assertIn(token, rule_pack)

    def test_fidelity_rewrite_reasons(self) -> None:
        profile = {
            "scene_modes": ["reveal_scene", "result_confirmation_scene", "pressure_scene"],
            "must_keep_names": ["时鸢"],
            "must_keep_long_lines": ["长句测试"],
            "abstract_narration": ["抽象句测试"],
            "forbidden_fill": ["宾客甲"],
            "reusable_lines_present": True,
        }

        reasons = self.run_writer._fidelity_rewrite_reasons(profile)

        self.assertEqual(
            reasons,
            ["reveal_scene", "result_confirmation_scene", "pressure_scene", "must_keep_long_lines", "abstract_externalization"],
        )

    def test_span_to_excerpt_text_skips_decorative_trailing_half(self) -> None:
        novel_text = "\n".join(
            [
                "第1章 Example",
                "",
                "Alpha paragraph.",
                "",
                "----------------------------------------",
                "",
                "第2章 Next",
                "",
                "Beta paragraph.",
                "",
            ]
        )

        excerpt = self.run_writer._span_to_excerpt_text("第1章后半", novel_text)

        self.assertIn("Alpha paragraph.", excerpt)
        self.assertNotIn("----------------------------------------", excerpt)

    def test_build_batch_context_bundle_writes_structured_json_with_scene_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_batch_brief(root)
            project = root / "harness" / "project"
            framework = root / "harness" / "framework"
            project.mkdir(parents=True, exist_ok=True)
            framework.mkdir(parents=True, exist_ok=True)
            (project / "run.manifest.md").write_text(
                "# Run Manifest\n\n- source_file: novel.md\n",
                encoding="utf-8",
            )
            (project / "source.map.md").write_text(
                "\n".join(
                    [
                        "# Source Map",
                        "- adaptation_strategy: original_fidelity",
                        "- dialogue_adaptation_intensity: light",
                        "",
                        "## Batch 03 (EP11-15)",
                        "",
                        "### EP11: test",
                        "**source_chapter_span**: Chapter 1",
                        "**must-keep_beats**:",
                        "- Beat A",
                        "**knowledge_boundary**:",
                        "- Ava does not know the stranger name yet",
                        "**must-not-add / must-not-jump**:",
                        "- Skip A",
                        "**function_signals**:",
                        "- opening_function: intrusion",
                        "- middle_functions: escalation, confrontation",
                        "- strong_function_tags: intrusion, escalation, hook",
                        "**ending_function**: locked_in",
                        "**irreversibility_level**: hard",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (framework / "write-contract.md").write_text("# contract\n", encoding="utf-8")
            (framework / "writer-style.md").write_text("# style\n", encoding="utf-8")
            (root / "voice-anchor.md").write_text("# Voice Anchor\n\n### Ava\n", encoding="utf-8")
            (root / "character.md").write_text("# Character\n\n### Ava\n", encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root):
                markdown_path = self.run_writer._build_batch_context_bundle(
                    "batch03",
                    root / "harness" / "project" / "batch-briefs" / "batch03_EP11-15.md",
                )

            json_path = markdown_path.with_suffix(".json")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            legacy_payload = {
                "batch_id": "batch03",
                "authority": payload["authority"],
                "batch_facts": payload["batch_facts"],
                "contract_digest": {
                    "adaptation_strategy": "original_fidelity",
                    "dialogue_adaptation_intensity": "light",
                    "shell_format": [
                        "场EP-1：/ 场EP-2：/ 场EP-3：",
                        "日/夜",
                        "外/内",
                        "场景：",
                        "♪：",
                        "△：",
                        "【镜头】：",
                        "角色（os）：",
                    ],
                    "hard_constraints": [
                        "事件顺序以 source.map 与当前集 event_anchors 为最高权威",
                        "禁止新增原文没有的新事件、新流程、新职业说明、新承接对白",
                        "只能写 drafts/episodes/EP-XX.md",
                        "不得改 episodes/、state/、source.map、run.manifest",
                        "整集至少 2 场，按功能完成决定场数",
                    ],
                },
                "style_digest": {
                    "format_rules": [
                        "壳层语法逐行独占，不混排",
                        "优先写可拍动作与画面，不写 Markdown 场记",
                        "light 对话改编，不把示例句写成口头禅",
                    ],
                    "line_prefixes": payload["style_digest"]["line_prefixes"],
                },
                "quality_digest": {
                    "checks": [
                        "source 已发生硬事件不能继续后拖",
                        "删掉新增桥接句后场意仍成立就必须删除",
                        "场尾要留下新增推进，不停在情绪余波",
                        "抽象总结句优先改成可拍反应",
                    ]
                },
                "reference_names": payload["reference_names"],
            }
        self.assertEqual(payload["batch_id"], "batch03")
        self.assertIn("authority", payload)
        self.assertIn("batch_facts", payload)
        self.assertIn("contract_digest", payload)
        self.assertIn("style_digest", payload)
        self.assertIn("quality_digest", payload)
        self.assertIn("reference_names", payload)
        self.assertTrue(payload["batch_facts"]["episodes"])
        self.assertNotIn("scene_plan", payload["batch_facts"]["episodes"][0])
        self.assertNotIn("function_signals", payload["batch_facts"]["episodes"][0])
        self.assertEqual(payload["batch_facts"]["episodes"][0]["ending_function"], "locked_in")
        self.assertIn("knowledge_boundary", payload["batch_facts"]["episodes"][0])

    def test_main_skips_backend_when_all_drafts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            drafts.mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            (drafts / "EP-11.md").write_text("existing", encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_run_llm_subprocess"
            ) as mock_llm:
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])

        self.assertEqual(rc, 0)
        mock_llm.assert_not_called()

    def test_main_fails_when_batch_brief_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_run_llm_subprocess"
            ) as mock_llm:
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])

        self.assertEqual(rc, 1)
        mock_llm.assert_not_called()

    def test_main_invokes_llm_with_source_excerpt_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            drafts.mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)
            (drafts / "EP-11.md").write_text("existing", encoding="utf-8")

            def fake_rule_profile(path: Path) -> dict[str, object]:
                if "EP-12" in str(path):
                    return {
                        "scene_modes": ["reveal_scene"],
                        "must_keep_names": ["鏃堕涪"],
                        "must_keep_long_lines": ["闀垮彞娴嬭瘯"],
                        "forbidden_fill": ["fill_token"],
                        "abstract_narration": [],
                        "reusable_lines_present": True,
                    }
                return {
                    "scene_modes": [],
                    "must_keep_names": ["鏃堕涪"],
                    "must_keep_long_lines": [],
                    "forbidden_fill": ["fill_token"],
                    "abstract_narration": [],
                    "reusable_lines_present": True,
                }

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.object(
                self.run_writer, "_episode_rule_profile", side_effect=fake_rule_profile
            ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
                def fake_llm_subprocess(command, *, stdin_text=None, timeout_seconds=None):
                    if stdin_text and "创建并写完" in stdin_text:
                        (drafts / "EP-12.md").write_text("场12-1：\n时鸢：初稿\n", encoding="utf-8")
                        return 0, "", ""
                    return 0, '{"operations": []}', ""

                mock_llm.side_effect = fake_llm_subprocess
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

                bundle = root / "harness" / "project" / "state" / "batch-context" / "batch03.writer-context.md"
                bundle_json = bundle.with_suffix(".json")
                excerpt = root / "harness" / "project" / "state" / "source-excerpts" / "batch03" / "EP-12.source.md"
                excerpt_json = excerpt.with_suffix(".json")
                self.assertTrue(bundle.exists())
                self.assertTrue(bundle_json.exists())
                self.assertTrue(excerpt.exists())
                self.assertTrue(excerpt_json.exists())

        self.assertEqual(rc, 0)
        self.assertEqual(mock_llm.call_count, 2)

        first_prompt = self._invoked_prompt(mock_llm.call_args_list[0])
        second_prompt = self._invoked_prompt(mock_llm.call_args_list[1])
        self.assertIn("局部 source-fidelity patch JSON", second_prompt)
        self.assertIn("只输出 JSON", second_prompt)
        self.assertIn('"operations"', second_prompt)
        self.assertIn("start_line", second_prompt)
        self.assertIn("restore_names", second_prompt)
        self.assertIn("delete_fill_blocks", second_prompt)

        prompt = first_prompt
        self.assertIn("source-excerpts/batch03/EP-12.source.json", prompt)
        self.assertIn("batch-context/batch03.writer-context.json", prompt)
        self.assertIn("write-contract.md", prompt)
        self.assertIn("writer-style.md", prompt)
        self.assertIn("[SECTION:MARKER_FORMAT]", prompt)
        self.assertIn("[SECTION:SCENE_CRAFT]", prompt)
        self.assertIn("event_anchors", prompt)
        self.assertIn("must_keep_names", prompt)
        self.assertIn("forbidden_fill", prompt)
        self.assertIn("当前集角色知识边界", prompt)
        self.assertIn("称谓必须有现场来源", prompt)
        self.assertIn("运行时最小规则包", prompt)
        self.assertIn("交稿前最小自检", prompt)
        self.assertIn("`event_anchors` 定顺序", prompt)
        self.assertIn("默认禁新增 source 未给出的桥接性内容", prompt)
        self.assertIn("模型知道不等于角色知道", prompt)
        self.assertIn("`forbidden_fill` 命中后", prompt)
        self.assertIn("`reuse_original_lines=true`", second_prompt)
        self.assertIn("已编号 draft", second_prompt)
        self.assertIn("codex.cmd", mock_llm.call_args_list[0].args[0][0])
        self.assertIn("codex.cmd", mock_llm.call_args_list[1].args[0][0])
        self.assertEqual(mock_llm.call_args_list[0].args[0][-1], "-")
        self.assertEqual(mock_llm.call_args_list[1].args[0][-1], "-")
        self.assertEqual(mock_llm.call_args_list[0].kwargs["stdin_text"], first_prompt)
        self.assertEqual(mock_llm.call_args_list[1].kwargs["stdin_text"], second_prompt)

    def test_main_defaults_to_single_sequential_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)

            executor_instances = []

            class FakeExecutor:
                def __init__(self, max_workers):
                    self.max_workers = max_workers
                    executor_instances.append(self)

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def submit(self, fn, *args, **kwargs):
                    return types.SimpleNamespace(result=lambda: fn(*args, **kwargs))

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.object(
                self.run_writer, "ThreadPoolExecutor", FakeExecutor
            ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
                mock_llm.return_value = (0, "", "")
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

        self.assertEqual(rc, 0)
        self.assertEqual(len(executor_instances), 0)
        self.assertEqual(mock_llm.call_count, 1)
        first_prompt = self._invoked_prompt(mock_llm.call_args_list[0])
        prompt = first_prompt
        self.assertIn("EP-11 -> drafts/episodes/EP-11.md", prompt)
        self.assertIn("EP-12 -> drafts/episodes/EP-12.md", prompt)
        self.assertIn("write-contract.md", prompt)
        self.assertIn("writer-style.md", prompt)
        self.assertIn("[SECTION:SCENE_RULES]", prompt)
        self.assertIn("[SECTION:DIALOGUE_CRAFT]", prompt)
        self.assertIn("source-excerpts/batch03/EP-11.source.json", prompt)
        self.assertIn("event_anchors", prompt)
        self.assertNotIn("signals:", prompt)
        self.assertNotIn("ending=", prompt)
        self.assertIn("forbidden_fill", prompt)
        self.assertIn("批次顺序写作最小规则", prompt)
        self.assertIn("`event_anchors` 定顺序", prompt)
        self.assertIn("`must_keep_names`、`forbidden_fill` 守边界", prompt)
        self.assertIn("模型知道不等于角色知道", prompt)
        self.assertIn("knowledge_boundary：", prompt)
        self.assertIn("称谓必须有现场来源", prompt)

    def test_main_runs_batch_fidelity_rewrite_only_when_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)

            def fake_rule_profile(path: Path) -> dict[str, object]:
                if "EP-12" in str(path):
                    return {
                        "scene_modes": ["reveal_scene"],
                        "must_keep_names": [],
                        "must_keep_long_lines": ["闀垮彞娴嬭瘯"],
                        "forbidden_fill": ["fill_token"],
                        "abstract_narration": [],
                        "reusable_lines_present": True,
                    }
                return {
                    "scene_modes": [],
                    "must_keep_names": [],
                    "must_keep_long_lines": [],
                    "forbidden_fill": ["fill_token"],
                    "abstract_narration": [],
                    "reusable_lines_present": True,
                }

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.object(
                self.run_writer, "_episode_rule_profile", side_effect=fake_rule_profile
            ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
                def fake_llm_subprocess(command, *, stdin_text=None, timeout_seconds=None):
                    if stdin_text and "按顺序创建并写完以下草稿文件" in stdin_text:
                        drafts_dir = root / "drafts" / "episodes"
                        drafts_dir.mkdir(parents=True, exist_ok=True)
                        (drafts_dir / "EP-11.md").write_text("场11-1：\n时鸢：初稿\n", encoding="utf-8")
                        (drafts_dir / "EP-12.md").write_text("场12-1：\n时鸢：初稿\n", encoding="utf-8")
                        return 0, "", ""
                    return 0, '{"operations": []}', ""

                mock_llm.side_effect = fake_llm_subprocess
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

        self.assertEqual(rc, 0)
        self.assertEqual(mock_llm.call_count, 2)
        second_prompt = self._invoked_prompt(mock_llm.call_args_list[1])
        self.assertIn("局部 source-fidelity patch JSON", second_prompt)
        self.assertIn("EP-12", second_prompt)
        self.assertNotIn("EP-11 -> drafts/episodes/EP-11.md", second_prompt)

    def test_main_falls_back_to_per_episode_writer_when_batch_task_times_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.object(
                self.run_writer,
                "_run_sequential_batch_task",
                return_value=(["EP-11", "EP-12"], self.run_writer.LLM_TIMEOUT_RETURNCODE),
            ) as mock_batch_task, mock.patch.object(
                self.run_writer,
                "_run_writer_task",
                side_effect=[("EP-11", 0), ("EP-12", 0)],
            ) as mock_writer_task:
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

        self.assertEqual(rc, 0)
        mock_batch_task.assert_called_once()
        self.assertEqual(mock_writer_task.call_count, 2)

    def test_main_uses_parallelism_and_runs_each_target_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)

            executor_instances = []

            class FakeExecutor:
                def __init__(self, max_workers):
                    self.max_workers = max_workers
                    executor_instances.append(self)

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def submit(self, fn, *args, **kwargs):
                    return types.SimpleNamespace(result=lambda: fn(*args, **kwargs))

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.object(
                self.run_writer, "ThreadPoolExecutor", FakeExecutor
            ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
                mock_llm.return_value = (0, "", "")
                rc = self.run_writer.main(
                    ["--batch", "batch03", "--episodes", "EP-11,EP-12", "--parallelism", "2"]
                )

        self.assertEqual(rc, 0)
        self.assertEqual(len(executor_instances), 1)
        self.assertEqual(executor_instances[0].max_workers, 2)
        self.assertEqual(mock_llm.call_count, 2)
        prompts = [self._invoked_prompt(call) for call in mock_llm.call_args_list]
        episode_11_prompts = [prompt for prompt in prompts if "EP-11" in prompt and "EP-12" not in prompt]
        episode_12_prompts = [prompt for prompt in prompts if "EP-12" in prompt and "EP-11" not in prompt]
        self.assertEqual(len(episode_11_prompts), 1)
        self.assertEqual(len(episode_12_prompts), 1)
        self.assertFalse(any("source-fidelity rewrite pass" in prompt for prompt in prompts))

    def test_main_syntax_first_prompt_references_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
                mock_llm.return_value = (0, "", "")
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11", "--syntax-first"])

        self.assertEqual(rc, 0)
        mock_llm.assert_called_once()
        prompt = self._invoked_prompt(mock_llm.call_args)
        self.assertIn("passing-episode.sample.md", prompt)
        for section in ("任务目标：", "冲突优先级：", "当前集 beats 清单：", "运行时最小规则包：", "交稿前最小自检："):
            self.assertIn(section, prompt)
        self.assertIn("语法壳优先", prompt)
        self.assertIn("write-contract.md", prompt)
        self.assertIn("writer-style.md", prompt)
        self.assertIn("[SECTION:MARKER_FORMAT]", prompt)
        self.assertIn("[SECTION:SCENE_CRAFT]", prompt)
        self.assertIn("整集至少 2 场", prompt)
        self.assertIn("`△：`", prompt)
        self.assertIn("`角色（os）：`", prompt)

    def test_main_includes_lint_feedback_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
            self._write_batch_brief(root)
            self._write_source_fixture(root)

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
            ), mock.patch.dict(
                os.environ,
                {self.run_writer.LINT_FEEDBACK_ENV: "- too_many_hookless_scenes"},
                clear=False,
            ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
                mock_llm.return_value = (0, "", "")
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])

        self.assertEqual(rc, 0)
        prompt = self._invoked_prompt(mock_llm.call_args_list[0])
        self.assertIn("本次是 smoke lint 回修重写", prompt)
        self.assertIn("回修要求：", prompt)
        self.assertIn("too_many_hookless_scenes", prompt)
        self.assertIn("只修本次 lint 命中的问题", prompt)
        self.assertIn("source.map", prompt)

    def test_run_llm_command_with_retry_retries_transient_disconnects(self) -> None:
        transient = types.SimpleNamespace(
            returncode=1,
            stdout="stream disconnected - retrying sampling request",
            stderr="ERROR: Reconnecting...",
        )
        success = types.SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(
            self.run_writer,
            "_run_llm_subprocess",
            side_effect=[(transient.returncode, transient.stdout, transient.stderr), (success.returncode, success.stdout, success.stderr)],
        ) as mock_llm, mock.patch.object(self.run_writer.time, "sleep") as mock_sleep:
            rc = self.run_writer._run_llm_command_with_retry("codex", ["codex.cmd", "exec"])

        self.assertEqual(rc, 0)
        self.assertEqual(mock_llm.call_count, 2)
        mock_sleep.assert_called_once()

    def test_run_llm_command_with_retry_returns_timeout_code(self) -> None:
        with mock.patch.object(
            self.run_writer,
            "_run_llm_subprocess",
            return_value=(self.run_writer.LLM_TIMEOUT_RETURNCODE, "", ""),
        ) as mock_run, io.StringIO() as stderr_buf, contextlib.redirect_stderr(stderr_buf):
            rc = self.run_writer._run_llm_command_with_retry(
                "codex",
                ["codex.cmd", "exec"],
                timeout_seconds=12,
                context_label="EP-15 fidelity rewrite",
            )
            stderr_output = stderr_buf.getvalue()

        self.assertEqual(rc, self.run_writer.LLM_TIMEOUT_RETURNCODE)
        mock_run.assert_called_once()
        self.assertIn("EP-15 fidelity rewrite", stderr_output)

    def test_run_llm_command_with_retry_dumps_prompt_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ,
            {self.run_writer.PROMPT_DUMP_DIR_ENV: tmp},
            clear=False,
        ), mock.patch.object(
            self.run_writer,
            "_run_llm_subprocess",
            return_value=(0, "", ""),
        ):
            rc = self.run_writer._run_llm_command_with_retry(
                "codex",
                ["codex.cmd", "exec", "-"],
                stdin_text="prompt body",
                context_label="EP-01 draft",
            )

            dumped = sorted(Path(tmp).glob("*.txt"))

            self.assertEqual(rc, 0)
            self.assertEqual(len(dumped), 1)
            self.assertIn("EP-01_draft.attempt1", dumped[0].name)
            self.assertEqual(dumped[0].read_text(encoding="utf-8"), "prompt body")

    def test_single_episode_rewrite_uses_rewrite_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            (draft_dir / "EP-15.md").write_text("?15-1?\n?????\n", encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- ????",
                        "",
                        "## Abstract Narration To Externalize",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_run_llm_command_with_retry", return_value=0
            ) as mock_draft_retry, mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
                return_value=(0, '{"operations": []}'),
            ) as mock_patch_retry:
                episode, rc = self.run_writer._run_writer_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    batch_context_path=root / "bundle.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )

        self.assertEqual((episode, rc), ("EP-15", 0))
        self.assertEqual(mock_draft_retry.call_count, 1)
        self.assertEqual(mock_patch_retry.call_count, 1)
        self.assertEqual(
            mock_patch_retry.call_args.kwargs["timeout_seconds"],
            self.run_writer.SINGLE_EPISODE_REWRITE_TIMEOUT_SECONDS,
        )
        self.assertEqual(mock_patch_retry.call_args.kwargs["context_label"], "EP-15 fidelity patch")

    def test_fidelity_patch_timeout_keeps_draft_and_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_path = draft_dir / "EP-15.md"
            draft_text = "场15-1：\n△：原稿保留\n"
            draft_path.write_text(draft_text, encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- 长句测试",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
                return_value=(self.run_writer.LLM_TIMEOUT_RETURNCODE, ""),
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                rc = self.run_writer._apply_fidelity_patch_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

            self.assertEqual(rc, 0)
            self.assertEqual(draft_path.read_text(encoding="utf-8"), draft_text)
            self.assertEqual(mock_patch_retry.call_count, 1)
            self.assertIn("WARNING: fidelity patch timed out for EP-15", output)
            self.assertIn("keeping the draft and continuing without patch", output)

    def test_fidelity_patch_skips_whole_draft_candidate_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_path = draft_dir / "EP-15.md"
            draft_text = "\n".join(
                [
                    "场15-1",
                    "△：原稿保留。",
                    "时鸢：我要一个答案。",
                ]
            ) + "\n"
            draft_path.write_text(draft_text, encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- 你今天必须给我一个交代。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                rc = self.run_writer._apply_fidelity_patch_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

            self.assertEqual(rc, 0)
            self.assertEqual(draft_path.read_text(encoding="utf-8"), draft_text)
            mock_patch_retry.assert_not_called()
            self.assertIn("Fidelity patch scope: EP-15", output)
            self.assertIn("candidate_blocks=1", output)
            self.assertIn("Skip fidelity patch: EP-15", output)
            self.assertIn("skip_reason=whole_draft_fallback", output)

    def test_fidelity_patch_skips_low_priority_externalize_only_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_path = draft_dir / "EP-15.md"
            draft_text = "\n".join(
                [
                    "场15-1：",
                    "【镜头】：男人眼底满是压不住的激动和心疼。",
                    "△：她没接话。",
                ]
            ) + "\n"
            draft_path.write_text(draft_text, encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- default_scene",
                        "",
                        "## Abstract Narration To Externalize",
                        "- 男人眼底满是压不住的激动和心疼",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                rc = self.run_writer._apply_fidelity_patch_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

            self.assertEqual(rc, 0)
            self.assertEqual(draft_path.read_text(encoding="utf-8"), draft_text)
            mock_patch_retry.assert_not_called()
            self.assertIn("family_priority=low", output)
            self.assertIn("skip_reason=family_priority=low", output)

    def test_fidelity_patch_skips_when_candidate_span_too_wide(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_text = "\n".join(
                [
                    "场15-1：",
                    "时鸢：我要一个交代。",
                    "△：她没退。",
                    "时鸢：今天必须说清楚。",
                    "△：风压在门上。",
                    "时鸢：别再装了。",
                    "△：她盯着他。",
                    "时鸢：你欠我一个答案。",
                    "△：门外脚步压近。",
                    "时鸢：现在就说。",
                    "△：她把话压得更低。",
                    "时鸢：别逼我。",
                    "△：谁都没退。",
                ]
            ) + "\n"
            draft_path = draft_dir / "EP-15.md"
            draft_path.write_text(draft_text, encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- pressure_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- 你今天必须给我一个交代。",
                        "- 现在就把话说清楚。",
                        "- 你欠我的，今天一并还回来。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                rc = self.run_writer._apply_fidelity_patch_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

            self.assertEqual(rc, 0)
            self.assertEqual(draft_path.read_text(encoding="utf-8"), draft_text)
            mock_patch_retry.assert_not_called()
            self.assertIn("candidate_span=", output)
            self.assertIn("skip_reason=candidate_span=", output)

    def test_fidelity_patch_invalid_output_keeps_draft_and_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_path = draft_dir / "EP-15.md"
            draft_text = "场15-1：\n△：原稿保留\n"
            draft_path.write_text(draft_text, encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- 长句测试",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
                return_value=(0, "not-json"),
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                rc = self.run_writer._apply_fidelity_patch_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

            self.assertEqual(rc, 0)
            self.assertEqual(draft_path.read_text(encoding="utf-8"), draft_text)
            self.assertEqual(mock_patch_retry.call_count, 1)
            self.assertIn("WARNING: invalid fidelity patch output for EP-15", output)
            self.assertIn("keeping the draft and continuing without patch", output)

    def test_run_writer_task_logs_rewrite_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            (draft_dir / "EP-15.md").write_text("?15-1?\n?????\n", encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- ????",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_run_llm_command_with_retry", return_value=0
            ) as mock_draft_retry, mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
                return_value=(0, '{"operations": []}'),
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                episode, rc = self.run_writer._run_writer_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    batch_context_path=root / "bundle.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

        self.assertEqual((episode, rc), ("EP-15", 0))
        self.assertEqual(mock_draft_retry.call_count, 1)
        self.assertEqual(mock_patch_retry.call_count, 1)
        self.assertIn("Draft profile: EP-15 (excerpt_tier=strong_scene", output)
        self.assertIn("Run fidelity patch: EP-15 (excerpt_tier=strong_scene", output)
        self.assertIn("reveal_scene, must_keep_long_lines", output)
        self.assertIn("Fidelity patch scope: EP-15 (excerpt_tier=strong_scene", output)
        self.assertIn("candidate_blocks=", output)
        self.assertIn("families=restore_long_lines", output)
        self.assertIn("Applied fidelity patch: EP-15 (ops: 0, families_touched=none)", output)
    def test_run_writer_task_logs_skip_reason_for_non_rewrite_episode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_excerpt = root / "EP-11.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-11",
                        "",
                        "## Reusable Source Lines",
                        "- 原句测试",
                        "",
                        "## Must-Keep Names",
                        "- 时鸢",
                        "",
                        "## Forbidden Fill",
                        "- 宾客甲",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer, "_run_llm_command_with_retry", return_value=0
            ) as mock_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                episode, rc = self.run_writer._run_writer_task(
                    "batch03",
                    "EP-11",
                    root / "brief.md",
                    batch_context_path=root / "bundle.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

        self.assertEqual((episode, rc), ("EP-11", 0))
        self.assertEqual(mock_retry.call_count, 1)
        self.assertIn("Draft profile: EP-11 (excerpt_tier=low_risk", output)
        self.assertIn("Skip fidelity rewrite: EP-11 (excerpt_tier=low_risk", output)
        self.assertIn("signals=tier:low_risk, must_keep_names, forbidden_fill", output)
        self.assertIn("trigger: none", output)

    def test_run_llm_command_with_retry_does_not_retry_non_transient_failures(self) -> None:
        failure = types.SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="ERROR: writer contract violation",
        )

        with mock.patch.object(
            self.run_writer,
            "_run_llm_subprocess",
            return_value=(failure.returncode, failure.stdout, failure.stderr),
        ) as mock_llm, mock.patch.object(self.run_writer.time, "sleep") as mock_sleep:
            rc = self.run_writer._run_llm_command_with_retry("codex", ["codex.cmd", "exec"])

        self.assertEqual(rc, 1)
        self.assertEqual(mock_llm.call_count, 1)
        mock_sleep.assert_not_called()

    def test_resolve_llm_cli_respects_env_override(self) -> None:
        with mock.patch.dict(os.environ, {self.run_writer.LLM_CLI_ENV: "qwen"}, clear=False), mock.patch.object(
            self.run_writer, "_resolve_cli_executable", return_value="qwen.cmd"
        ):
            self.assertEqual(self.run_writer._resolve_llm_cli(), ("qwen", "qwen.cmd"))

    def test_prompts_require_externalizing_abstract_source_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Abstract Narration To Externalize",
                        "- 这一巴掌，彻底打醒了所有人",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            first_prompt = self.run_writer._build_writer_prompt(
                batch_id="batch03",
                episode="EP-15",
                brief_path=Path("harness/project/batch-briefs/batch03_EP11-15.md"),
                batch_context_path=Path("harness/project/state/batch-context/batch03.writer-context.md"),
                source_excerpt_path=source_excerpt,
            )
            second_prompt = self.run_writer._build_fidelity_rewrite_prompt(
                batch_id="batch03",
                episode="EP-15",
                brief_path=Path("harness/project/batch-briefs/batch03_EP11-15.md"),
                source_excerpt_path=source_excerpt,
                draft_text="场15-1：\n△：这一巴掌，彻底打醒了所有人。\n",
            )

        self.assertIn("`abstract_narration` 非空时", first_prompt)
        self.assertIn("把对应句意外化成可拍反应", first_prompt)
        self.assertIn("externalize_lines", second_prompt)
        self.assertIn("只输出 JSON", second_prompt)
        self.assertIn("start_line", second_prompt)
        self.assertIn("不要继续保留“彻底打醒了所有人”“现场恢复平静”“光芒万丈”“只剩敬畏”这类总结句", second_prompt)

    def test_build_rewrite_patch_spec(self) -> None:
        profile = {
            "scene_modes": ["reveal_scene", "pressure_scene"],
            "must_keep_names": ["时鸢", "苏雨柔"],
            "must_keep_long_lines": ["长句一", "长句二"],
            "abstract_narration": ["抽象句一"],
            "forbidden_fill": ["宾客甲", "流程卡"],
            "reusable_lines_present": True,
        }

        patch_spec = self.run_writer._build_rewrite_patch_spec(profile)
        rendered = self.run_writer._render_rewrite_patch_spec(patch_spec)

        self.assertEqual(
            patch_spec,
            {
                "scene_modes": ["reveal_scene", "pressure_scene"],
                "families": [
                    {
                        "problem_family": "restore_names",
                        "items": ["时鸢", "苏雨柔"],
                        "allowed_actions": ["replace"],
                    },
                    {
                        "problem_family": "restore_long_lines",
                        "items": ["长句一", "长句二"],
                        "allowed_actions": ["replace"],
                    },
                    {
                        "problem_family": "delete_fill_blocks",
                        "items": ["宾客甲", "流程卡"],
                        "allowed_actions": ["delete"],
                    },
                    {
                        "problem_family": "externalize_lines",
                        "items": ["抽象句一"],
                        "allowed_actions": ["replace"],
                    },
                ],
                "reuse_original_lines": True,
            },
        )
        self.assertIn('"problem_family": "restore_names"', rendered)
        self.assertIn('"allowed_actions": [', rendered)


    def test_rule_profile_signals_follow_source_excerpt_profile_only(self) -> None:
        profile = {
            "scene_modes": ["reveal_scene", "pressure_scene"],
            "must_keep_names": ["ShiYuan"],
            "must_keep_long_lines": ["long line"],
            "abstract_narration": [],
            "forbidden_fill": ["guest filler"],
            "reusable_lines_present": True,
        }
        episode_facts = {
            "function_signals": {
                "opening_function": "setup",
                "middle_functions": [],
                "strong_function_tags": [],
            },
            "ending_function": "closure",
            "irreversibility_level": "soft",
            "scene_plan": [
                {
                    "scene_num": 1,
                    "scene_id": "场1-1",
                    "primary_function": "setup",
                    "beat_focus": "Setup beat",
                    "beat_coverage": ["Setup beat"],
                    "exposure_mode": "public",
                    "target_delta_span": "4-5",
                    "ending_requirement": "Setup landed",
                    "stop_when": "Next scene takes over",
                    "irreversibility_hint": "State changed",
                    "rhythm_hint": "Mix short and progressive lines",
                    "ending_function": "",
                    "irreversibility_level": "",
                }
            ],
        }

        signals = self.run_writer._rule_profile_signals(profile, episode_facts)
        self.assertIn("reveal_scene", signals)
        self.assertIn("pressure_scene", signals)

    def test_excerpt_tier_follows_source_excerpt_profile_only(self) -> None:
        profile = {
            "excerpt_tier": "strong_scene",
            "scene_modes": ["reveal_scene", "pressure_scene"],
            "must_keep_names": [],
            "must_keep_long_lines": [],
            "abstract_narration": [],
            "forbidden_fill": [],
            "reusable_lines_present": False,
        }
        episode_facts = {
            "function_signals": {
                "opening_function": "setup",
                "middle_functions": [],
                "strong_function_tags": [],
            },
            "ending_function": "closure",
            "irreversibility_level": "soft",
            "scene_plan": [
                {
                    "scene_num": 1,
                    "scene_id": "场1-1",
                    "primary_function": "setup",
                    "beat_focus": "Setup beat",
                    "beat_coverage": ["Setup beat"],
                    "exposure_mode": "public",
                    "target_delta_span": "4-5",
                    "ending_requirement": "Setup landed",
                    "stop_when": "Next scene takes over",
                    "irreversibility_hint": "State changed",
                    "rhythm_hint": "Mix short and progressive lines",
                    "ending_function": "closure",
                    "irreversibility_level": "soft",
                }
            ],
        }

        self.assertEqual(
            self.run_writer._rule_profile_signals(profile, episode_facts),
            ["tier:strong_scene", "reveal_scene", "pressure_scene"],
        )

    def test_apply_patch_operations_to_text(self) -> None:
        draft = "scene-15-1\nalias: impossible.\nsummary: intense emotion.\n"
        rewritten = self.run_writer._apply_patch_operations_to_text(
            draft,
            [
                {
                    "block_id": "B01",
                    "problem_family": "restore_names",
                    "start_line": 2,
                    "end_line": 2,
                    "action": "replace",
                    "content": "SuYurou: impossible.",
                    "reason": "restore_names",
                },
                {
                    "block_id": "B01",
                    "problem_family": "externalize_lines",
                    "start_line": 3,
                    "end_line": 3,
                    "action": "replace",
                    "content": "action: she looks at ShiYuan, eyes reddening as her feet stay planted.",
                    "reason": "externalize_lines",
                },
            ],
        )

        self.assertEqual(
            rewritten,
            "scene-15-1\nSuYurou: impossible.\naction: she looks at ShiYuan, eyes reddening as her feet stay planted.\n",
        )

    def test_find_patch_candidate_blocks_targets_only_relevant_blocks(self) -> None:
        draft = "\n".join(
            [
                "scene-15-1",
                "action: gala lights settle.",
                "Guest A: This is lively.",
                "ShiYuan: I came here for one thing.",
                "action: her eyes hold intense emotion.",
                "SuYurou: What attitude is this? Your parents are right here.",
                "action: unrelated ending beat.",
            ]
        ) + "\n"
        patch_spec = {
            "scene_modes": ["reveal_scene", "pressure_scene"],
            "families": [
                {
                    "problem_family": "restore_names",
                    "items": ["SuYurou", "ShiYuan"],
                    "allowed_actions": ["replace"],
                },
                {
                    "problem_family": "restore_long_lines",
                    "items": ["What attitude is this? Your parents are right here."],
                    "allowed_actions": ["replace"],
                },
                {
                    "problem_family": "delete_fill_blocks",
                    "items": ["extra guest filler"],
                    "allowed_actions": ["delete"],
                },
                {
                    "problem_family": "externalize_lines",
                    "items": ["her eyes hold intense emotion."],
                    "allowed_actions": ["replace"],
                },
            ],
            "reuse_original_lines": True,
        }

        candidate_blocks = self.run_writer._find_patch_candidate_blocks(draft, patch_spec)
        rendered = self.run_writer._render_numbered_candidate_blocks(draft, candidate_blocks)

        self.assertEqual(
            candidate_blocks,
            [
                {
                    "block_id": "B01",
                    "start_line": 2,
                    "end_line": 7,
                    "problem_families": [
                        "restore_long_lines",
                        "restore_names",
                    ],
                }
            ],
        )
        self.assertIn("[Block B01 | lines 2-7 | families: restore_long_lines, restore_names]", rendered)
        self.assertIn("03: Guest A: This is lively.", rendered)
        self.assertIn("05: action: her eyes hold intense emotion.", rendered)

    def test_fidelity_rewrite_prompt_uses_candidate_blocks_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_excerpt = root / "EP-05.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-05",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Names",
                        "- SuYurou",
                        "- ShiYuan",
                        "",
                        "## Must-Keep Long Lines",
                        "- What attitude is this? Your parents are right here.",
                        "",
                        "## Abstract Narration To Externalize",
                        "- her eyes hold intense emotion.",
                        "",
                        "## Forbidden Fill",
                        "- extra guest filler",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            rewrite_prompt = self.run_writer._build_fidelity_rewrite_prompt(
                batch_id="batch03",
                episode="EP-05",
                brief_path=Path("harness/project/batch-briefs/batch03_EP11-15.md"),
                source_excerpt_path=source_excerpt,
                draft_text="\n".join(
                    [
                        "scene-05-1",
                        "action: gala lights settle.",
                        "Guest A: This is lively.",
                        "ShiYuan: I came here for one thing.",
                        "action: her eyes hold intense emotion.",
                        "SuYurou: What attitude is this? Your parents are right here.",
                        "action: unrelated ending beat.",
                        "action: fully unrelated distant bell.",
                    ]
                )
                + "\n",
                patch_spec={
                    "scene_modes": ["reveal_scene"],
                    "families": [
                        {
                            "problem_family": "restore_names",
                            "items": ["SuYurou", "ShiYuan"],
                            "allowed_actions": ["replace"],
                        },
                        {
                            "problem_family": "restore_long_lines",
                            "items": ["What attitude is this? Your parents are right here."],
                            "allowed_actions": ["replace"],
                        },
                        {
                            "problem_family": "delete_fill_blocks",
                            "items": ["extra guest filler"],
                            "allowed_actions": ["delete"],
                        },
                        {
                            "problem_family": "externalize_lines",
                            "items": ["her eyes hold intense emotion."],
                            "allowed_actions": ["replace"],
                        },
                    ],
                    "reuse_original_lines": True,
                },
                candidate_blocks=[
                    {
                        "block_id": "B01",
                        "start_line": 2,
                        "end_line": 7,
                        "problem_families": [
                            "delete_fill_blocks",
                            "externalize_lines",
                            "restore_long_lines",
                        ],
                    }
                ],
            )

        self.assertIn("候选句段", rewrite_prompt)
        self.assertIn("[Block B01 | lines 2-7 | families: delete_fill_blocks, externalize_lines, restore_long_lines]", rewrite_prompt)
        self.assertIn("03: Guest A: This is lively.", rewrite_prompt)
        self.assertNotIn("08: action: fully unrelated distant bell.", rewrite_prompt)
        self.assertIn('"block_id": "B01"', rewrite_prompt)
        self.assertIn('"problem_family": "restore_names"', rewrite_prompt)

    def test_normalize_patch_operations_rejects_invalid_family_action_combo(self) -> None:
        payload = {
            "operations": [
                {
                    "block_id": "B01",
                    "problem_family": "delete_fill_blocks",
                    "start_line": 2,
                    "end_line": 2,
                    "action": "replace",
                    "content": "should not be allowed",
                    "reason": "bad combo",
                }
            ]
        }
        candidate_blocks = [
            {
                "block_id": "B01",
                "start_line": 2,
                "end_line": 4,
                "problem_families": ["delete_fill_blocks"],
            }
        ]

        with self.assertRaises(ValueError):
            self.run_writer._normalize_patch_operations(payload, candidate_blocks)

    def test_build_writer_prompt_omits_global_state_and_exposes_beats_and_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            framework = root / "harness" / "framework"
            batch_briefs = project / "batch-briefs"
            batch_briefs.mkdir(parents=True, exist_ok=True)
            framework.mkdir(parents=True, exist_ok=True)
            (project / "run.manifest.md").write_text(
                "# Run Manifest\n- current batch brief: stale.md\n",
                encoding="utf-8",
            )
            (project / "source.map.md").write_text(
                "\n".join(
                    [
                        "# Source Map",
                        "",
                        "## Batch 03 (EP11-15): demo",
                        "",
                        "### EP11: demo",
                        "**source_chapter_span**: ch1",
                        "**must-keep_beats**:",
                        "- ????????",
                        "- ????????",
                        "- ????????",
                        "- ????????",
                        "**function_signals**:",
                        "- opening_function: intrusion",
                        "- middle_functions: escalation, confrontation",
                        "- strong_function_tags: intrusion, escalation, confrontation, hook",
                        "**ending_function**: locked_in",
                        "**irreversibility_level**: hard",
                        "**must-not-add / must-not-jump**:",
                        "- ??????",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            brief_path = batch_briefs / "batch03_EP11-15.md"
            brief_path.write_text(
                "# Batch Brief: EP-11 ~ EP-15\n"
                "- owned episodes: EP-11\n"
                "- source excerpt range: novel.md ch1\n"
                "- adjacent continuity: demo\n",
                encoding="utf-8",
            )
            (framework / "write-contract.md").write_text("# contract\n", encoding="utf-8")
            (framework / "writer-style.md").write_text("# style\n", encoding="utf-8")
            (framework / "passing-episode.sample.md").write_text("# sample\n", encoding="utf-8")
            source_excerpt = project / "state" / "source-excerpts" / "batch03" / "EP-11.source.json"
            source_excerpt.parent.mkdir(parents=True, exist_ok=True)
            source_excerpt.write_text(
                json.dumps(
                    {
                        "episode": "EP-11",
                        "source_span": "ch1",
                        "excerpt_tier": "low_risk",
                        "event_anchors": ["??", "??"],
                        "must_keep_names": ["??"],
                        "forbidden_fill": ["????"],
                        "reusable_source_lines": ["???????"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root):
                batch_context = self.run_writer._build_batch_context_bundle("batch03", brief_path)
                prompt = self.run_writer._build_writer_prompt(
                    "batch03",
                    "EP-11",
                    brief_path,
                    batch_context_path=batch_context,
                    source_excerpt_path=source_excerpt,
                )

        self.assertNotIn("story.state.md", prompt)
        self.assertNotIn("relationship.board.md", prompt)
        self.assertNotIn("open_loops.md", prompt)
        self.assertIn("write-contract.md", prompt)
        self.assertIn("[SECTION:MARKER_FORMAT]", prompt)
        self.assertIn("[SECTION:OS_RULES]", prompt)
        self.assertIn("[SECTION:SCENE_RULES]", prompt)
        self.assertIn("[SECTION:CHARACTER_KNOWLEDGE]", prompt)
        self.assertIn("[SECTION:PRE_SUBMIT_CHECK]", prompt)
        self.assertIn("writer-style.md", prompt)
        self.assertIn("[SECTION:NARRATIVE_POSTURE]", prompt)
        self.assertIn("[SECTION:SCENE_CRAFT]", prompt)
        self.assertIn("[SECTION:DIALOGUE_CRAFT]", prompt)
        self.assertIn("[SECTION:STYLE_RED_LINES]", prompt)
        self.assertIn("必读输入", prompt)
        self.assertIn("当前集 beats 清单", prompt)
        self.assertNotIn("????????????", prompt)
        self.assertIn("冲突优先级", prompt)
        self.assertIn("完成当前集全部 beats", prompt)
        self.assertIn("整集至少 2 场", prompt)
        self.assertNotIn("场次功能拆解", prompt)
        self.assertNotIn("当前集功能目标", prompt)
        self.assertNotIn("整集最大3", prompt)
        self.assertLess(len(prompt.encode("utf-8")), 10000)
    def test_build_sequential_prompt_uses_beats_driven_scene_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            framework = root / "harness" / "framework"
            batch_briefs = project / "batch-briefs"
            batch_briefs.mkdir(parents=True, exist_ok=True)
            framework.mkdir(parents=True, exist_ok=True)
            (project / "run.manifest.md").write_text("# Run Manifest\n- current batch brief: stale.md\n", encoding="utf-8")
            (project / "source.map.md").write_text(
                "\n".join(
                    [
                        "# Source Map",
                        "",
                        "## Batch 03 (EP11-15): demo",
                        "",
                        "### EP11: demo",
                        "**source_chapter_span**: ch1",
                        "**must-keep_beats**:",
                        "- ????????",
                        "- ????????",
                        "- ????????",
                        "- ????????",
                        "**function_signals**:",
                        "- opening_function: intrusion",
                        "- middle_functions: escalation, confrontation",
                        "- strong_function_tags: intrusion, escalation, confrontation, hook",
                        "**ending_function**: locked_in",
                        "**irreversibility_level**: hard",
                        "**must-not-add / must-not-jump**:",
                        "- ??????",
                        "",
                        "### EP12: demo",
                        "**source_chapter_span**: ch2",
                        "**must-keep_beats**:",
                        "- ????????",
                        "- ????????",
                        "- ????????",
                        "- ????????",
                        "**function_signals**:",
                        "- opening_function: escalation",
                        "- middle_functions: confrontation, reveal",
                        "- strong_function_tags: escalation, confrontation",
                        "**ending_function**: confrontation_pending",
                        "**irreversibility_level**: medium",
                        "**must-not-add / must-not-jump**:",
                        "- ???????????",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            brief_path = batch_briefs / "batch03_EP11-15.md"
            brief_path.write_text(
                "# Batch Brief: EP-11 ~ EP-15\n"
                "- owned episodes: EP-11, EP-12\n"
                "- source excerpt range: novel.md ch1 ~ ch2\n"
                "- adjacent continuity: demo\n",
                encoding="utf-8",
            )
            (framework / "write-contract.md").write_text("# contract\n", encoding="utf-8")
            (framework / "writer-style.md").write_text("# style\n", encoding="utf-8")
            (framework / "passing-episode.sample.md").write_text("# sample\n", encoding="utf-8")
            source_dir = project / "state" / "source-excerpts" / "batch03"
            source_dir.mkdir(parents=True, exist_ok=True)
            ep11 = source_dir / "EP-11.source.json"
            ep12 = source_dir / "EP-12.source.json"
            ep11.write_text(json.dumps({"episode": "EP-11", "excerpt_tier": "baseline", "event_anchors": ["a"], "must_keep_names": [], "forbidden_fill": []}, ensure_ascii=False), encoding="utf-8")
            ep12.write_text(json.dumps({"episode": "EP-12", "excerpt_tier": "baseline", "event_anchors": ["b"], "must_keep_names": [], "forbidden_fill": []}, ensure_ascii=False), encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root):
                batch_context = self.run_writer._build_batch_context_bundle("batch03", brief_path)
                prompt = self.run_writer._build_sequential_batch_writer_prompt(
                    "batch03",
                    ["EP-11", "EP-12"],
                    brief_path,
                    batch_context_path=batch_context,
                    source_excerpt_paths={"EP-11": ep11, "EP-12": ep12},
                )

        self.assertNotIn("story.state.md", prompt)
        self.assertNotIn("relationship.board.md", prompt)
        self.assertNotIn("open_loops.md", prompt)
        self.assertIn("write-contract.md", prompt)
        self.assertIn("[SECTION:MARKER_FORMAT]", prompt)
        self.assertIn("[SECTION:OS_RULES]", prompt)
        self.assertIn("[SECTION:SCENE_RULES]", prompt)
        self.assertIn("[SECTION:CHARACTER_KNOWLEDGE]", prompt)
        self.assertIn("[SECTION:PRE_SUBMIT_CHECK]", prompt)
        self.assertIn("writer-style.md", prompt)
        self.assertIn("[SECTION:NARRATIVE_POSTURE]", prompt)
        self.assertIn("[SECTION:SCENE_CRAFT]", prompt)
        self.assertIn("[SECTION:DIALOGUE_CRAFT]", prompt)
        self.assertIn("[SECTION:STYLE_RED_LINES]", prompt)
        self.assertIn("必读输入", prompt)
        self.assertIn("beats：", prompt)
        self.assertNotIn("signals:", prompt)
        self.assertNotIn("ending=", prompt)
        self.assertIn("整集至少 2 场", prompt)
        self.assertNotIn("scene_function_plan:", prompt)
        self.assertNotIn("功能：opening=intrusion", prompt)
        self.assertNotIn("整集最大3", prompt)
    def test_fidelity_patch_skips_whole_draft_candidate_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_dir = root / "drafts" / "episodes"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_path = draft_dir / "EP-15.md"
            draft_text = "\n".join(
                ["scene-15-1", *[f"action: filler beat {index}." for index in range(1, 25)]]
            ) + "\n"
            draft_path.write_text(draft_text, encoding="utf-8")
            source_excerpt = root / "EP-15.source.md"
            source_excerpt.write_text(
                "\n".join(
                    [
                        "# Source Excerpt: EP-15",
                        "",
                        "## Scene Modes",
                        "- reveal_scene",
                        "",
                        "## Must-Keep Long Lines",
                        "- This line does not appear in draft.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
                self.run_writer,
                "_run_llm_command_capture_with_retry",
            ) as mock_patch_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
                rc = self.run_writer._apply_fidelity_patch_task(
                    "batch03",
                    "EP-15",
                    root / "brief.md",
                    source_excerpt_path=source_excerpt,
                    cli="codex",
                    executable="codex.cmd",
                )
                output = stdout_buf.getvalue()

            self.assertEqual(rc, 0)
            self.assertEqual(draft_path.read_text(encoding="utf-8"), draft_text)
            mock_patch_retry.assert_not_called()
            self.assertIn("Fidelity patch scope: EP-15", output)
            self.assertIn("candidate_blocks=1", output)
            self.assertIn("Skip fidelity patch: EP-15", output)
            self.assertIn("skip_reason=whole_draft_fallback", output)


def _override_test_main_invokes_llm_with_source_excerpt_prompt(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
        self._write_batch_brief(root)
        self._write_source_fixture(root)

        with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
            self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
        ), mock.patch.object(
            self.run_writer, "_run_llm_subprocess"
        ) as mock_llm:
            mock_llm.return_value = (0, "", "")
            rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

    self.assertEqual(rc, 0)
    self.assertEqual(mock_llm.call_count, 1)
    prompt = self._invoked_prompt(mock_llm.call_args_list[0])
    self.assertIn("source-excerpts/batch03/EP-12.source.json", prompt)
    self.assertIn("batch-context/batch03.writer-context.json", prompt)
    self.assertIn("write-contract.md", prompt)
    self.assertIn("writer-style.md", prompt)
    self.assertNotIn("source-fidelity patch JSON", prompt)


def _override_test_main_does_not_run_batch_fidelity_rewrite_even_for_strong_scene(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
        self._write_batch_brief(root)
        self._write_source_fixture(root)

        with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
            self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
        ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
            mock_llm.return_value = (0, "", "")
            rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

    self.assertEqual(rc, 0)
    self.assertEqual(mock_llm.call_count, 1)
    prompt = self._invoked_prompt(mock_llm.call_args_list[0])
    self.assertIn("EP-12", prompt)
    self.assertNotIn("source-fidelity patch JSON", prompt)


def _override_test_main_ignores_lint_feedback_env_when_present(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)
        self._write_batch_brief(root)
        self._write_source_fixture(root)

        with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
            self.run_writer, "_resolve_llm_cli", return_value=("codex", "codex.cmd")
        ), mock.patch.dict(
            os.environ,
            {"JUBEN_WRITER_LINT_FEEDBACK": "- too_many_hookless_scenes"},
            clear=False,
        ), mock.patch.object(self.run_writer, "_run_llm_subprocess") as mock_llm:
            mock_llm.return_value = (0, "", "")
            rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])

    self.assertEqual(rc, 0)
    prompt = self._invoked_prompt(mock_llm.call_args_list[0])
    self.assertNotIn("smoke lint", prompt)
    self.assertNotIn("too_many_hookless_scenes", prompt)


def _override_test_single_episode_writer_task_no_longer_runs_rewrite(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        draft_dir = root / "drafts" / "episodes"
        draft_dir.mkdir(parents=True, exist_ok=True)
        (draft_dir / "EP-15.md").write_text("场15-1\n△：初稿\n", encoding="utf-8")
        source_excerpt = root / "EP-15.source.md"
        source_excerpt.write_text("# Source Excerpt: EP-15\n", encoding="utf-8")

        with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
            self.run_writer, "_run_llm_command_with_retry", return_value=0
        ) as mock_draft_retry, mock.patch.object(
            self.run_writer,
            "_run_llm_command_capture_with_retry",
            return_value=(0, '{"operations": []}'),
        ) as mock_patch_retry:
            episode, rc = self.run_writer._run_writer_task(
                "batch03",
                "EP-15",
                root / "brief.md",
                batch_context_path=root / "bundle.md",
                source_excerpt_path=source_excerpt,
                cli="codex",
                executable="codex.cmd",
            )

    self.assertEqual((episode, rc), ("EP-15", 0))
    self.assertEqual(mock_draft_retry.call_count, 1)
    self.assertEqual(mock_patch_retry.call_count, 0)


def _override_test_run_writer_task_logs_profile_without_rewrite(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_excerpt = root / "EP-11.source.md"
        source_excerpt.write_text("# Source Excerpt: EP-11\n", encoding="utf-8")
        with mock.patch.object(self.run_writer, "ROOT", root), mock.patch.object(
            self.run_writer, "_run_llm_command_with_retry", return_value=0
        ) as mock_retry, io.StringIO() as stdout_buf, contextlib.redirect_stdout(stdout_buf):
            episode, rc = self.run_writer._run_writer_task(
                "batch03",
                "EP-11",
                root / "brief.md",
                batch_context_path=root / "bundle.md",
                source_excerpt_path=source_excerpt,
                cli="codex",
                executable="codex.cmd",
            )
            output = stdout_buf.getvalue()

    self.assertEqual((episode, rc), ("EP-11", 0))
    self.assertEqual(mock_retry.call_count, 1)
    self.assertIn("Draft profile: EP-11", output)
    self.assertNotIn("fidelity patch", output.lower())


RunWriterTests.test_main_invokes_llm_with_source_excerpt_prompt = _override_test_main_invokes_llm_with_source_excerpt_prompt
RunWriterTests.test_main_runs_batch_fidelity_rewrite_only_when_needed = _override_test_main_does_not_run_batch_fidelity_rewrite_even_for_strong_scene
RunWriterTests.test_main_includes_lint_feedback_when_present = _override_test_main_ignores_lint_feedback_env_when_present
RunWriterTests.test_single_episode_rewrite_uses_rewrite_timeout = _override_test_single_episode_writer_task_no_longer_runs_rewrite
RunWriterTests.test_run_writer_task_logs_rewrite_reasons = _override_test_run_writer_task_logs_profile_without_rewrite
RunWriterTests.test_run_writer_task_logs_skip_reason_for_non_rewrite_episode = _override_test_run_writer_task_logs_profile_without_rewrite


def _override_test_patch_helpers_are_removed(self) -> None:
    removed_helpers = [
        "_source_excerpt_requires_fidelity_rewrite",
        "_fidelity_rewrite_reasons",
        "_build_rewrite_patch_spec",
        "_find_patch_candidate_blocks",
        "_build_fidelity_rewrite_prompt",
        "_normalize_patch_operations",
        "_apply_patch_operations_to_text",
        "_apply_fidelity_patch_task",
    ]
    for name in removed_helpers:
        self.assertFalse(hasattr(self.run_writer, name), name)


RunWriterTests.test_source_excerpt_requires_fidelity_rewrite = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_rewrite_reasons = _override_test_patch_helpers_are_removed
RunWriterTests.test_build_rewrite_patch_spec = _override_test_patch_helpers_are_removed
RunWriterTests.test_find_patch_candidate_blocks_targets_only_relevant_blocks = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_rewrite_prompt_uses_candidate_blocks_only = _override_test_patch_helpers_are_removed
RunWriterTests.test_normalize_patch_operations_rejects_invalid_family_action_combo = _override_test_patch_helpers_are_removed
RunWriterTests.test_apply_patch_operations_to_text = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_patch_timeout_keeps_draft_and_returns_success = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_patch_skips_whole_draft_candidate_scope = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_patch_skips_low_priority_externalize_only_scope = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_patch_skips_when_candidate_span_too_wide = _override_test_patch_helpers_are_removed
RunWriterTests.test_fidelity_patch_invalid_output_keeps_draft_and_returns_success = _override_test_patch_helpers_are_removed
def _override_test_rule_profile_and_runtime_pack_track_structure_not_patch_tokens(self) -> None:
    profile = {
        "excerpt_tier": "strong_scene",
        "scene_modes": ["reveal_scene", "pressure_scene", "result_confirmation_scene"],
        "must_keep_names": ["时鸢", "傅斯年"],
        "must_keep_long_lines": ["你这是什么态度？亲生父母就在眼前，你一点都不激动、不感恩吗？"],
        "abstract_narration": ["她眼里是压不住的风暴。"],
        "forbidden_fill": ["后台流程扩写"],
        "reusable_lines_present": True,
    }
    episode_facts = {
        "function_signals": {
            "opening_function": "intrusion",
            "middle_functions": ["escalation", "confrontation"],
        },
        "ending_function": "locked_in",
        "irreversibility_level": "hard",
        "scene_plan": [{"scene_id": "场1-1"}],
    }
    rule_pack = self.run_writer._build_minimal_rule_pack(
        profile, episode_facts, include_adjacent_boundary=False
    )
    self.assertNotIn("????????????", rule_pack)
    self.assertIn("角色只按当场已公开信息行动", rule_pack)
    self.assertNotIn("source-fidelity patch", rule_pack)


def _override_test_prompts_externalize_abstract_summary_without_patch_prompt(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_excerpt = root / "EP-11.source.md"
        source_excerpt.write_text(
            "# Source Excerpt: EP-11\n\n她眼里是压不住的风暴。", encoding="utf-8"
        )
        batch_context = root / "batch-context.json"
        batch_context.write_text("{}", encoding="utf-8")
        brief = root / "brief.md"
        brief.write_text("# brief", encoding="utf-8")
        with mock.patch.object(self.run_writer, "ROOT", root):
            prompt = self.run_writer._build_writer_prompt(
                batch_id="batch03",
                episode="EP-11",
                brief_path=brief,
                batch_context_path=batch_context,
                source_excerpt_path=source_excerpt,
            )
    self.assertIn("任务目标：", prompt)
    self.assertNotIn("patch JSON", prompt)


def _override_test_writer_prompt_does_not_inline_legacy_theme_tokens(self) -> None:
    source = Path(self.run_writer.__file__).read_text(encoding="utf-8")
    for token in ("车锁", "门锁", "导航", "驶离主路", "姐姐", "亲生女儿", "拦门", "逼近", "压话", "夺物"):
        self.assertNotIn(token, source)


RunWriterTests.test_rule_profile_signals_and_minimal_rule_pack = _override_test_rule_profile_and_runtime_pack_track_structure_not_patch_tokens
RunWriterTests.test_prompts_require_externalizing_abstract_source_summary = _override_test_prompts_externalize_abstract_summary_without_patch_prompt
RunWriterTests.test_writer_prompt_does_not_inline_legacy_theme_tokens = _override_test_writer_prompt_does_not_inline_legacy_theme_tokens


def _override_test_llm_execution_removed(self) -> None:
    source = Path(self.run_writer.__file__).read_text(encoding="utf-8")
    for name in [
        "_resolve_llm_cli",
        "_run_llm_subprocess",
        "_run_llm_command_with_retry",
        "_run_writer_task",
        "LLM_CLI_ENV",
        "PROMPT_DUMP_DIR_ENV",
    ]:
        self.assertFalse(hasattr(self.run_writer, name), name)
    self.assertNotIn("subprocess.run", source)
    self.assertNotIn("subprocess.Popen", source)
    self.assertNotIn("qwen", source)
    self.assertNotIn("claude", source)


def _override_test_main_writes_prompt_packet_only(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        brief_dir = root / "harness" / "project" / "batch-briefs"
        prompts = root / "harness" / "project" / "prompts"
        state = root / "harness" / "project" / "state"
        novel = root / "novel.md"
        for path in [brief_dir, prompts, state, root / "drafts" / "episodes"]:
            path.mkdir(parents=True, exist_ok=True)
        novel.write_text("第1章\n街头误认。", encoding="utf-8")
        (root / "harness" / "project" / "source.map.md").write_text(
            "# Source Map\n\n## Batch 03\n### EP11\n"
            "**source_chapter_span**: 第1章\n"
            "**must-keep_beats**:\n- 【信息】街头误认\n",
            encoding="utf-8",
        )
        (brief_dir / "batch03_EP11-11.md").write_text(
            "# Batch Brief\n- owned episodes: EP-11\n\n## Episode Mapping\n- EP-11：第1章\n  - 【信息】街头误认\n",
            encoding="utf-8",
        )
        with mock.patch.object(self.run_writer, "ROOT", root), \
             mock.patch.object(self.run_writer, "PROMPTS_DIR", prompts):
            rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])
            self.assertEqual(rc, 0)
            self.assertTrue((prompts / "batch03.EP-11.writer.prompt.md").exists())


RunWriterTests.test_main_invokes_llm_with_source_excerpt_prompt = _override_test_main_writes_prompt_packet_only
RunWriterTests.test_main_defaults_to_single_sequential_call = _override_test_main_writes_prompt_packet_only
RunWriterTests.test_main_uses_parallelism_and_runs_each_target_separately = _override_test_main_writes_prompt_packet_only
RunWriterTests.test_main_falls_back_to_per_episode_writer_when_batch_task_times_out = _override_test_main_writes_prompt_packet_only
RunWriterTests.test_main_syntax_first_prompt_references_sample = _override_test_main_writes_prompt_packet_only
RunWriterTests.test_main_runs_batch_fidelity_rewrite_only_when_needed = _override_test_main_writes_prompt_packet_only
RunWriterTests.test_main_includes_lint_feedback_when_present = _override_test_main_writes_prompt_packet_only

RunWriterTests.test_main_skips_backend_when_all_drafts_exist = _override_test_llm_execution_removed
RunWriterTests.test_main_fails_when_batch_brief_is_missing = _override_test_llm_execution_removed
RunWriterTests.test_resolve_llm_cli_respects_env_override = _override_test_llm_execution_removed
RunWriterTests.test_run_llm_command_with_retry_retries_transient_disconnects = _override_test_llm_execution_removed
RunWriterTests.test_run_llm_command_with_retry_returns_timeout_code = _override_test_llm_execution_removed
RunWriterTests.test_run_llm_command_with_retry_dumps_prompt_when_enabled = _override_test_llm_execution_removed
RunWriterTests.test_run_llm_command_with_retry_does_not_retry_non_transient_failures = _override_test_llm_execution_removed
RunWriterTests.test_single_episode_rewrite_uses_rewrite_timeout = _override_test_llm_execution_removed
RunWriterTests.test_run_writer_task_logs_rewrite_reasons = _override_test_llm_execution_removed
RunWriterTests.test_run_writer_task_logs_skip_reason_for_non_rewrite_episode = _override_test_llm_execution_removed

if __name__ == "__main__":
    unittest.main()
