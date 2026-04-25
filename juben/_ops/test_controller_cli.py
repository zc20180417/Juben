import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_SCRIPT = ROOT / "_ops" / "controller.py"
FIXTURES = ROOT / "_ops" / "test_fixtures"


def _load_controller_module():
    spec = importlib.util.spec_from_file_location("controller_under_test", CONTROLLER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ControllerCliSmokeTests(unittest.TestCase):
    def _make_cli_workspace(self) -> Path:
        root = Path(tempfile.mkdtemp())
        ops = root / "_ops"
        ops.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CONTROLLER_SCRIPT, ops / "controller.py")
        framework = root / "harness" / "framework"
        framework.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "harness" / "framework" / "review-standard.md", framework / "review-standard.md")
        shutil.copy2(ROOT / "harness" / "framework" / "reviewer-prompt.template.md", framework / "reviewer-prompt.template.md")

        project = root / "harness" / "project"
        batch_briefs = project / "batch-briefs"
        batch_briefs.mkdir(parents=True, exist_ok=True)
        (batch_briefs / "batch01_EP01-02.md").write_text(
            "# Batch Brief\n"
            "- batch status: draft\n"
            "- owned episodes: EP-01, EP-02\n",
            encoding="utf-8",
        )
        (project / "run.manifest.md").write_text(
            "# Run Manifest\n"
            "- key_episodes: \n",
            encoding="utf-8",
        )
        (project / "source.map.md").write_text(
            "# Source Map\n\n"
            "## Batch 01：EP-01 ~ EP-02\n"
            "原著范围：ch1-ch2\n\n"
            "### EP-01\n"
            "source chapter span：ch1\n"
            "must-keep beats：起\n"
            "must-not-add / must-not-jump：无\n"
            "ending type：强闭环\n\n"
            "### EP-02\n"
            "source chapter span：ch2\n"
            "must-keep beats：承\n"
            "must-not-add / must-not-jump：无\n"
            "ending type：前推力\n",
            encoding="utf-8",
        )
        return root

    def _run_wrapper(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PATH"] = f"{ROOT}{os.pathsep}{env.get('PATH', '')}"
        return subprocess.run(
            ["cmd", "/c", name, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def test_verify_plan_cli_prints_batch_header(self) -> None:
        root = self._make_cli_workspace()
        result = subprocess.run(
            [sys.executable, str(root / "_ops" / "controller.py"), "verify-plan", "batch01"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("=== Verify Plan: batch01 ===", result.stdout)

    def test_batch_review_cli_prints_batch_header(self) -> None:
        root = self._make_cli_workspace()
        result = subprocess.run(
            [sys.executable, str(root / "_ops" / "controller.py"), "batch-review", "batch01"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("=== Batch Review: batch01 ===", result.stdout)
        self.assertTrue((root / "harness" / "project" / "reviews" / "batch01.review.json").exists())
        self.assertTrue((root / "harness" / "project" / "reviews" / "batch01.review.md").exists())
        self.assertTrue((root / "harness" / "project" / "reviews" / "batch01.review.prompt.md").exists())
        self.assertIn("Review Prompt:", result.stdout)
        self.assertIn("Review Standard:", result.stdout)

    def test_tilde_start_wrapper_routes_to_start_help(self) -> None:
        result = self._run_wrapper("~start", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)
        self.assertIn("prepare-only", result.stdout)

    def test_tilde_run_wrapper_routes_to_run_help(self) -> None:
        result = self._run_wrapper("~run", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py run", result.stdout)
        self.assertIn("batch_id", result.stdout)

    def test_tilde_clean_wrapper_routes_to_clean_help(self) -> None:
        result = self._run_wrapper("~clean", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py clean", result.stdout)
        self.assertNotIn("batch_id", result.stdout)

    def test_tilde_record_wrapper_routes_to_record_help(self) -> None:
        result = self._run_wrapper("~record", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py record", result.stdout)
        self.assertIn("batch_id", result.stdout)

    def test_tilde_next_wrapper_routes_to_next_help(self) -> None:
        result = self._run_wrapper("~next", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py next", result.stdout)

    def test_tilde_review_wrapper_routes_to_batch_review_done_help(self) -> None:
        result = self._run_wrapper("~review", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py batch-review-done", result.stdout)
        self.assertIn("--reviewer", result.stdout)

    def test_tilde_extract_wrapper_routes_to_extract_book_help(self) -> None:
        result = self._run_wrapper("~extract", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py extract-book", result.stdout)

    def test_tilde_map_wrapper_routes_to_map_book_help(self) -> None:
        result = self._run_wrapper("~map", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py map-book", result.stdout)

    def test_tilde_check_wrapper_routes_to_check_help(self) -> None:
        result = self._run_wrapper("~check", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py check", result.stdout)
        self.assertIn("batch_id", result.stdout)

    def test_tilde_status_wrapper_routes_to_status_help(self) -> None:
        result = self._run_wrapper("~status", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py status", result.stdout)

    def test_tilde_export_wrapper_routes_to_export_help(self) -> None:
        result = self._run_wrapper("~export", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py export", result.stdout)

    def test_tilde_promote_wrapper_routes_to_promote_help(self) -> None:
        result = self._run_wrapper("~promote", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: controller.py promote", result.stdout)


class ControllerHandlerRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_book_blueprint_quality_gate_accepts_minimal_episode_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blueprint = Path(tmp) / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n\n"
                "- extraction_status: extracted\n"
                "- recommended_total_episodes: 40\n\n"
                "## 集数建议\n\n"
                "- recommended_total_episodes: 40\n"
                "- 推荐区间：30-40集\n"
                "- 最终采用：40集\n"
                "- 可独立成集戏剧节点：很多关键情节\n"
                "- 应合并压缩的内容：可压缩\n"
                "- 为什么不是更短/更长：因为节奏合适\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint):
                issues = self.controller._book_blueprint_quality_issues()
                is_complete = self.controller._book_blueprint_is_complete()

        self.assertEqual(issues, [])
        self.assertTrue(is_complete)

    def test_book_blueprint_quality_gate_accepts_loose_final_count_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blueprint = Path(tmp) / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n\n"
                "- extraction_status: extracted\n\n"
                "## 集数建议\n\n"
                "- 最终采用：约16（建议）\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint):
                issues = self.controller._book_blueprint_quality_issues()
                is_complete = self.controller._book_blueprint_is_complete()
                recommended = self.controller._recommended_total_episodes_from_blueprint()

        self.assertEqual(issues, [])
        self.assertTrue(is_complete)
        self.assertEqual(recommended, 16)

    def test_sync_state_from_blueprint_populates_blank_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            blueprint = root / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n\n"
                "## 主线\n\n- 误认入局；认亲寒心；身份反打\n\n"
                "## 集数建议\n\n"
                "- 推荐区间：30-35集\n"
                "- 最终采用：32集\n"
                "- 可独立成集戏剧节点：误认入局、真千金确认、身份反打\n"
                "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                "- 为什么不是更短/更长：短了会挤压反转，长了会注水\n\n"
                "## 角色弧光\n\n- 时鸢从防御到允许被爱\n\n"
                "## 关系变化\n\n- 时鸢 vs 苏家：从失望到切割\n\n"
                "## 关键反转\n\n- 鉴定确认；身份掉马；旧案翻面\n",
                encoding="utf-8",
            )
            templates = self.controller._state_templates()
            for name in ("story.state.md", "relationship.board.md", "quality.anchor.md"):
                (state_dir / name).write_text(templates[name], encoding="utf-8")

            with mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "STATE", state_dir):
                updated = self.controller._sync_state_from_blueprint()

            self.assertIn("story.state.md", updated)
            self.assertIn("relationship.board.md", updated)
            self.assertIn("quality.anchor.md", updated)
            self.assertIn("误认入局", (state_dir / "story.state.md").read_text(encoding="utf-8"))
            self.assertIn("时鸢 vs 苏家", (state_dir / "relationship.board.md").read_text(encoding="utf-8"))
            self.assertIn("短句服务情境", (state_dir / "quality.anchor.md").read_text(encoding="utf-8"))

    def test_source_map_quality_gate_accepts_single_structured_beat_when_structure_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_map = Path(tmp) / "source.map.md"
            source_map.write_text(
                "# Source Map\n\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-05): 测试批次\n\n"
                "### EP01: 测试集\n\n"
                "**source_chapter_span**: 第1章前半\n\n"
                "**must-keep_beats**:\n"
                "- 【关系】冷静拒认，拒绝回苏家\n\n"
                "**knowledge_boundary**:\n"
                "- 女主只知道对方在逼认亲，不能提前知道后续鉴定结果\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 无\n\n"
                "**ending_function**: confrontation_pending\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "SOURCE_MAP", source_map):
                issues = self.controller._source_map_quality_issues()
                is_complete = self.controller._source_map_is_complete()

        self.assertEqual(issues, [])
        self.assertTrue(is_complete)

    def test_source_map_quality_gate_rejects_single_overly_abstract_beat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_map = Path(tmp) / "source.map.md"
            source_map.write_text(
                "# Source Map\n\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-05): 测试批次\n\n"
                "### EP01: 测试集\n\n"
                "**source_chapter_span**: 第1章前半\n\n"
                "**must-keep_beats**:\n"
                "- 冷静拒认\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 无\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "SOURCE_MAP", source_map):
                issues = self.controller._source_map_quality_issues()

        self.assertIn("must-keep beats are too abstract", issues[0])

    def test_generate_batch_brief_no_longer_embeds_fake_ready_state(self) -> None:
        batch_info = {
            "episodes": ["EP-01", "EP-02"],
            "ep_start": "EP-01",
            "ep_end": "EP-02",
            "source_range": "ch1 ~ ch2",
            "episode_data": {
                "EP-01": {"source_span": "ch1", "must_keep": "【信息】误认", "knowledge_boundary": "女主不知道男主姓名", "must_not": "不能抢跑", "ending_function": "confrontation_pending"},
                "EP-02": {"source_span": "ch2", "must_keep": "【动作】入局", "knowledge_boundary": "双方已互知姓名", "must_not": "", "ending_function": "confrontation_pending"},
            },
        }

        with mock.patch.object(self.controller, "_read_manifest", return_value={}):
            brief = self.controller._generate_batch_brief("batch01", batch_info)

        self.assertNotIn("verify checklist", brief)
        self.assertNotIn("ready for promote", brief)
        self.assertNotIn("batch ready for promote: yes", brief)
        self.assertNotIn("batch status:", brief)
        self.assertIn("knowledge_boundary", brief)
        self.assertIn("女主不知道男主姓名", brief)

    def test_prepare_batch_start_reads_generated_brief_before_status_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_briefs = root / "batch-briefs"
            source_map = root / "source.map.md"
            batch_briefs.mkdir(parents=True, exist_ok=True)
            source_map.write_text("# Source Map\n", encoding="utf-8")

            batch_info = {
                "episodes": ["EP-01", "EP-02"],
                "ep_start": "EP-01",
                "ep_end": "EP-02",
                "batch_num": "01",
                "source_range": "ch1 ~ ch2",
                "episode_data": {
                    "EP-01": {"source_span": "ch1", "must_keep": "【信息】误认", "must_not": "", "ending_function": "confrontation_pending"},
                    "EP-02": {"source_span": "ch2", "must_keep": "【动作】入局", "must_not": "", "ending_function": "confrontation_pending"},
                },
            }
            status_updates: list[dict[str, object]] = []

            with mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "_book_blueprint_quality_issues", return_value=[]), \
                 mock.patch.object(self.controller, "_source_map_quality_issues", return_value=[]), \
                 mock.patch.object(self.controller, "_parse_source_map", return_value={"batch01": batch_info}), \
                 mock.patch.object(self.controller, "_is_locked", return_value=False), \
                 mock.patch.object(self.controller, "_find_batch_brief", return_value=None), \
                 mock.patch.object(self.controller, "_generate_batch_brief", return_value="# Batch Brief\n- owned episodes: EP-01, EP-02\n"), \
                 mock.patch.object(self.controller, "_read_batch_brief", return_value={"episodes": ["EP-01", "EP-02"]}), \
                 mock.patch.object(self.controller, "_set_batch_status"), \
                 mock.patch.object(self.controller, "_write_lock"), \
                 mock.patch.object(self.controller, "_set_manifest_field"), \
                 mock.patch.object(self.controller, "_append_log"), \
                 mock.patch.object(self.controller, "_clear_retry_count"), \
                 mock.patch.object(self.controller, "_clear_verify_result"), \
                 mock.patch.object(self.controller, "_compute_verify_tiers", return_value=([], [], [], [])), \
                 mock.patch.object(
                     self.controller,
                     "_upsert_batch_status",
                     side_effect=lambda batch_id, **kwargs: status_updates.append({"batch_id": batch_id, **kwargs}),
                 ):
                prepared = self.controller._prepare_batch_start("batch01")
                self.assertIsNotNone(prepared)
                brief_path, _, episodes = prepared
                self.assertTrue(brief_path.exists())
                self.assertEqual(episodes, ["EP-01", "EP-02"])
                self.assertGreaterEqual(len(status_updates), 2)
                self.assertEqual(status_updates[0]["episodes"], ["EP-01", "EP-02"])
                self.assertEqual(status_updates[1]["episodes"], ["EP-01", "EP-02"])

    def test_resolve_batch_require_frozen_prefers_runtime_phase_over_missing_brief_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_briefs = root / "batch-briefs"
            state = root / "state"
            batch_status_dir = state / "batch-status"
            batch_briefs.mkdir(parents=True, exist_ok=True)
            batch_status_dir.mkdir(parents=True, exist_ok=True)
            brief_path = batch_briefs / "batch01_EP01-02.md"
            brief_path.write_text(
                "# Batch Brief\n"
                "- owned episodes: EP-01, EP-02\n",
                encoding="utf-8",
            )
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "review_pending",
                        "status": "BLOCKED",
                        "episodes": ["EP-01", "EP-02"],
                        "brief_path": "batch-briefs/batch01_EP01-02.md",
                        "batch_review_status": "MISSING",
                        "updated_at": "2026-04-19 00:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir):
                resolved = self.controller._resolve_batch("batch01", require_frozen=True)

        self.assertIsNotNone(resolved)

    def test_batch_review_done_writes_verdict_and_syncs_runtime_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reviews = root / "harness" / "project" / "reviews"
            state = root / "harness" / "project" / "state"
            batch_status_dir = state / "batch-status"
            reviews.mkdir(parents=True, exist_ok=True)
            batch_status_dir.mkdir(parents=True, exist_ok=True)
            review_json = reviews / "batch01.review.json"
            review_json.write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "status": "PENDING",
                        "reviewer": "",
                        "timestamp": "2026-04-19 00:00",
                        "episodes": ["EP-01", "EP-02"],
                        "sampled_episodes": ["EP-01", "EP-02"],
                        "blocking_reasons": [],
                        "warning_families": [],
                        "arc_regressions": [],
                        "function_theft_findings": [],
                        "quality_anchor_findings": [],
                        "evidence_refs": [],
                        "reason": "",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (reviews / "batch01.review.md").write_text("# Batch Review\n", encoding="utf-8")

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", root / "harness" / "project"), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir):
                rc = self.controller.cmd_batch_review_done(
                    argparse.Namespace(batch_id="batch01", status="FAIL", reviewer="codex", reason="unsupported additions")
                )

            self.assertEqual(rc, 0)
            review = json.loads(review_json.read_text(encoding="utf-8"))
            runtime = json.loads((batch_status_dir / "batch01.status.json").read_text(encoding="utf-8"))
            self.assertEqual(review["status"], "FAIL")
            self.assertEqual(review["reviewer"], "codex")
            self.assertEqual(review["reason"], "unsupported additions")
            self.assertEqual(runtime["batch_review_status"], "FAIL")
            self.assertEqual(runtime["phase"], "review_pending")

    def test_next_prefers_runtime_batch_status_over_brief_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_map = root / "source.map.md"
            batch_briefs = root / "batch-briefs"
            state = root / "state"
            batch_status_dir = state / "batch-status"
            batch_briefs.mkdir(parents=True, exist_ok=True)
            batch_status_dir.mkdir(parents=True, exist_ok=True)
            source_map.write_text(
                "# Source Map\n\n"
                "## Batch 01 (EP01-02): demo\n\n"
                "### EP01: a\n"
                "**source_chapter_span**: ch1\n"
                "**must-keep_beats**:\n- 【信息】a\n- 【动作】b\n- 【钩子】c\n"
                "**must-not-add / must-not-jump**:\n- none\n"
                "**ending_function**: confrontation_pending\n\n"
                "### EP02: b\n"
                "**source_chapter_span**: ch2\n"
                "**must-keep_beats**:\n- 【信息】a\n- 【动作】b\n- 【钩子】c\n"
                "**must-not-add / must-not-jump**:\n- none\n"
                "**ending_function**: confrontation_pending\n\n"
                "## Batch 02 (EP03-04): demo\n\n"
                "### EP03: c\n"
                "**source_chapter_span**: ch3\n"
                "**must-keep_beats**:\n- 【信息】a\n- 【动作】b\n- 【钩子】c\n"
                "**must-not-add / must-not-jump**:\n- none\n"
                "**ending_function**: confrontation_pending\n\n"
                "### EP04: d\n"
                "**source_chapter_span**: ch4\n"
                "**must-keep_beats**:\n- 【信息】a\n- 【动作】b\n- 【钩子】c\n"
                "**must-not-add / must-not-jump**:\n- none\n"
                "**ending_function**: confrontation_pending\n",
                encoding="utf-8",
            )
            (batch_briefs / "batch01_EP01-02.md").write_text(
                "# Batch Brief\n- batch status: frozen\n- owned episodes: EP-01, EP-02\n",
                encoding="utf-8",
            )
            (batch_briefs / "batch02_EP03-04.md").write_text(
                "# Batch Brief\n- batch status: promoted\n- owned episodes: EP-03, EP-04\n",
                encoding="utf-8",
            )
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "promoted",
                        "status": "ACTIVE",
                        "episodes": ["EP-01", "EP-02"],
                        "brief_path": "harness/project/batch-briefs/batch01_EP01-02.md",
                        "batch_review_status": "PASS",
                        "updated_at": "2026-04-19 00:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={"active_batch": "(none)"}), \
                 mock.patch.object(self.controller, "_is_locked", return_value=False):
                rc = self.controller.cmd_next(argparse.Namespace())

            self.assertEqual(rc, 0)
            text = output.getvalue()
            self.assertIn("Promoted: batch01, batch02", text)
            self.assertNotIn("Pending:  batch01", text)

    def test_export_outputs_writes_summary_and_machine_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            state = project / "state"
            batch_status_dir = state / "batch-status"
            episodes = root / "episodes"
            drafts = root / "drafts" / "episodes"
            output = root / "output"
            reviews = project / "reviews"
            prompts = project / "prompts"
            briefs = project / "batch-briefs"
            locks = project / "locks"
            for path in (batch_status_dir, episodes, drafts, reviews, prompts, briefs, locks):
                path.mkdir(parents=True, exist_ok=True)

            (episodes / "EP-01.md").write_text("# 第1集\n", encoding="utf-8")
            (drafts / "EP-02.md").write_text("# 第2集\n", encoding="utf-8")
            (prompts / "batch01.prompt.md").write_text("# Prompt\n", encoding="utf-8")
            (briefs / "batch01_EP01-02.md").write_text(
                "# Batch Brief\n- owned episodes: EP-01, EP-02\n",
                encoding="utf-8",
            )
            run_manifest = project / "run.manifest.md"
            run_manifest.write_text(
                "# Run Manifest\n\n"
                "- source_file: sample.md\n"
                "- total_episodes: 2\n"
                "- batch_size: 2\n"
                "- target_total_minutes: 4\n"
                "- target_episode_minutes: 2\n"
                "- run_status: active\n"
                "- active_batch: batch01\n",
                encoding="utf-8",
            )
            source_map = project / "source.map.md"
            source_map.write_text(
                "# Source Map\n\n"
                "## Batch 01 (EP01-02): demo\n\n"
                "### EP01: a\n"
                "**source_chapter_span**: ch1\n"
                "**must-keep_beats**:\n- 【信息】a\n"
                "**must-not-add / must-not-jump**:\n- none\n"
                "**ending_function**: confrontation_pending\n\n"
                "### EP02: b\n"
                "**source_chapter_span**: ch2\n"
                "**must-keep_beats**:\n- 【动作】b\n"
                "**must-not-add / must-not-jump**:\n- none\n"
                "**ending_function**: locked_in\n",
                encoding="utf-8",
            )
            book_blueprint = project / "book.blueprint.md"
            book_blueprint.write_text("# Book Blueprint\n", encoding="utf-8")
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "review_pending",
                        "status": "BLOCKED",
                        "episodes": ["EP-01", "EP-02"],
                        "batch_review_status": "PENDING",
                        "updated_at": "2026-04-24 00:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (reviews / "batch01.review.json").write_text(
                json.dumps(
                    {"batch_id": "batch01", "status": "PENDING", "episodes": ["EP-01", "EP-02"]},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "OUTPUT", output), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "PROMPTS", prompts), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", briefs), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", book_blueprint), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest):
                stats = self.controller._export_outputs()

            self.assertEqual(stats["episodes"], 1)
            self.assertTrue((output / "SUMMARY.md").exists())
            self.assertTrue((output / "manifest.json").exists())
            summary = (output / "SUMMARY.md").read_text(encoding="utf-8")
            payload = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("Juben V1 Output Summary", summary)
            self.assertIn(".\\~review.cmd batch01 PASS", summary)
            self.assertEqual(payload["schema_version"], "juben-output/v1")
            self.assertEqual(payload["published_episodes"][0]["episode"], "EP-01")
            self.assertEqual(payload["batches"][0]["review_status"], "PENDING")

    def test_voice_anchor_quality_gate_rejects_common_expression_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            voice_anchor = Path(tmp) / "voice-anchor.md"
            voice_anchor.write_text(
                "# Voice Anchor\n\n"
                "### 时鸢\n"
                "- 说话气质：冷静\n"
                "- 常用表达：\n"
                "  - 不必。\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "ROOT", Path(tmp)):
                issues = self.controller._voice_anchor_quality_issues()

        self.assertTrue(any("常用表达" in issue for issue in issues))

    def test_append_log_bootstraps_missing_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            run_log = state_dir / "run.log.md"

            with mock.patch.object(self.controller, "STATE", state_dir), \
                 mock.patch.object(self.controller, "RUN_LOG", run_log):
                self.controller._append_log("batch01", "EP-01", "plan_inputs", "boot", "✓", "smoke")

            self.assertTrue(run_log.exists())
            content = run_log.read_text(encoding="utf-8")
            self.assertIn("# Run Log", content)
            self.assertIn("| batch01 | EP-01 | plan_inputs | boot | ✓ | smoke |", content)

    def test_detect_chapters_supports_plain_numeric_headings(self) -> None:
        novel_text = "\n".join([
            "书名：示例",
            "",
            "　　01",
            "",
            "第一段内容",
            "",
            "　　02",
            "",
            "第二段内容",
        ])

        chapters = self.controller._detect_chapters(novel_text)

        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0]["start_line"], 2)
        self.assertEqual(chapters[1]["start_line"], 6)

    def test_detect_chapters_supports_plain_chinese_chapter_headings(self) -> None:
        novel_text = "\n".join([
            "青萝引",
            "第一章 山雨夜归人",
            "第一章内容",
            "",
            "第二章 旧事如刀",
            "第二章内容",
        ])

        chapters = self.controller._detect_chapters(novel_text)

        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0]["title"], "第一章 山雨夜归人")
        self.assertEqual(chapters[0]["start_line"], 1)
        self.assertEqual(chapters[1]["title"], "第二章 旧事如刀")
        self.assertEqual(chapters[1]["start_line"], 4)

    def test_init_creates_missing_project_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            novel = root / "sample.md"
            novel.write_text("第一章\n误认入局。\n", encoding="utf-8")
            harness = root / "harness"
            project = harness / "project"
            state = project / "state"
            batch_status_dir = state / "batch-status"
            locks = project / "locks"
            drafts = root / "drafts" / "episodes"
            episodes = root / "episodes"
            batch_briefs = project / "batch-briefs"
            reviews = project / "reviews"
            prompts = project / "prompts"
            releases = project / "releases"
            release_journals = releases / "journals"
            run_manifest = project / "run.manifest.md"
            book_blueprint = project / "book.blueprint.md"
            source_map = project / "source.map.md"
            output = root / "output"
            run_log = state / "run.log.md"

            args = argparse.Namespace(
                novel_file="sample.md",
                episodes=4,
                batch_size=5,
                target_total_minutes=8,
                strategy="original_fidelity",
                intensity="light",
                key_episodes="",
                force=True,
            )
            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "PROMPTS", prompts), \
                 mock.patch.object(self.controller, "RELEASES", releases), \
                 mock.patch.object(self.controller, "RELEASE_JOURNALS", release_journals), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", book_blueprint), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "RUN_LOG", run_log), \
                 mock.patch.object(self.controller, "OUTPUT", output):
                result = self.controller.cmd_init(args)

            self.assertEqual(result, 0)
            self.assertTrue(run_manifest.exists())
            self.assertTrue(book_blueprint.exists())
            self.assertTrue(source_map.exists())
            self.assertTrue(batch_status_dir.exists())
            self.assertTrue(prompts.exists())
            self.assertTrue(release_journals.exists())

    def test_parse_source_map_supports_generated_markdown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_map = Path(tmp) / "source.map.md"
            source_map.write_text(
                "# Source Map\n\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-02): 觉醒破冰 - 试运行\n\n"
                "### EP01: 开局困局 (1-2 分钟)\n\n"
                "**source_chapter_span**: 第1章至第2章前半\n\n"
                "**must-keep_beats**:\n"
                "- 和离书被销毁\n"
                "- 沈如月误以为裴砚亭不爱她\n\n"
                "**knowledge_boundary**:\n"
                "- 沈如月不知道裴砚亭真实计划\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过离书被销毁\n\n"
                "**ending_function**: confrontation_pending\n\n"
                "---\n\n"
                "### EP02: 白月光的假面 (2-3 分钟)\n\n"
                "**source_chapter_span**: 第2章后半至第3章\n\n"
                "**must-keep_beats**:\n"
                "- 柳清言登门\n"
                "- 海棠树下对峙\n\n"
                "**knowledge_boundary**:\n"
                "- 柳清言出现前不能提前叫出她的真实目的\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过柳清言挑衅\n\n"
                "**ending_function**: reversal_triggered\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "SOURCE_MAP", source_map):
                batches = self.controller._parse_source_map()

        self.assertIn("batch01", batches)
        self.assertEqual(batches["batch01"]["ep_start"], "EP-01")
        self.assertEqual(batches["batch01"]["ep_end"], "EP-02")
        self.assertEqual(batches["batch01"]["episodes"], ["EP-01", "EP-02"])
        self.assertEqual(
            batches["batch01"]["episode_data"]["EP-01"]["source_span"],
            "第1章至第2章前半",
        )
        self.assertIn("和离书被销毁", batches["batch01"]["episode_data"]["EP-01"]["must_keep"])
        self.assertIn("沈如月不知道裴砚亭真实计划", batches["batch01"]["episode_data"]["EP-01"]["knowledge_boundary"])
        self.assertIn("不能跳过离书被销毁", batches["batch01"]["episode_data"]["EP-01"]["must_not"])
        self.assertEqual(
            batches["batch01"]["episode_data"]["EP-02"]["ending_function"],
            "reversal_triggered",
        )

    def test_compute_verify_tiers_supports_generated_markdown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_map = Path(tmp) / "source.map.md"
            source_map.write_text(
                "# Source Map\n\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-02): 觉醒破冰 - 试运行\n\n"
                "### EP01: 开局困局 (1-2 分钟)\n\n"
                "**source_chapter_span**: 第1章至第2章前半\n\n"
                "**must-keep_beats**:\n"
                "- 和离书被销毁\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过离书被销毁\n\n"
                "**ending_function**: confrontation_pending\n\n"
                "---\n\n"
                "### EP02: 白月光的假面 (2-3 分钟)\n\n"
                "**source_chapter_span**: 第2章后半至第3章\n\n"
                "**must-keep_beats**:\n"
                "- 柳清言登门\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过柳清言挑衅\n\n"
                "**ending_function**: reversal_triggered\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={"key_episodes": ""}):
                full, standard, light, unmapped = self.controller._compute_verify_tiers(["EP-01", "EP-02"])

        self.assertEqual(full, ["EP-01"])
        self.assertEqual(standard, ["EP-02"])
        self.assertEqual(light, [])
        self.assertEqual(unmapped, [])

    def test_check_uses_batch_id_in_verify_done_instructions(self) -> None:
        args = argparse.Namespace(batch_id="batch01")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-01"])), \
             mock.patch.object(self.controller, "_ensure_batch_review_artifacts", return_value={"status": "PENDING"}):
            result = self.controller.cmd_check(args)

        self.assertEqual(result, 0)
        self.assertIn(".\\~review.cmd batch01 PASS --reviewer <name>", output.getvalue())

    def test_promote_uses_batch_id_for_manifest_and_log(self) -> None:
        args = argparse.Namespace(batch_id="batch01")

        with contextlib.redirect_stdout(io.StringIO()), \
             mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-01"])), \
             mock.patch.object(self.controller, "_run_lint_gate", return_value=(True, {"EP-01": {}})), \
             mock.patch.object(self.controller, "_run_verify_gate", return_value=True), \
             mock.patch.object(self.controller, "_require_batch_review_pass", return_value=(True, "")), \
             mock.patch.object(self.controller, "_is_locked", return_value=False), \
             mock.patch.object(self.controller, "_promote_batch", return_value=(0, {})) as mock_promote, \
             mock.patch.object(self.controller, "_set_batch_status") as mock_set_status, \
             mock.patch.object(self.controller, "_upsert_batch_status") as mock_upsert_status, \
             mock.patch.object(self.controller, "_set_manifest_field") as mock_set_manifest, \
             mock.patch.object(self.controller, "_write_lock") as mock_write_lock, \
             mock.patch.object(self.controller, "_clear_retry_count") as mock_clear_retry, \
             mock.patch.object(self.controller, "_append_log") as mock_append_log:
            result = self.controller.cmd_promote(args)

        self.assertEqual(result, 0)
        mock_promote.assert_called_once_with("batch01", Path("brief.md"), ["EP-01"], {"EP-01": {}})
        mock_set_status.assert_called_once_with(Path("brief.md"), "promoted")
        mock_upsert_status.assert_called_once()
        mock_set_manifest.assert_called_once_with("active_batch", "batch01_promoted")
        mock_write_lock.assert_called_once_with("batch.lock", "unlocked")
        mock_clear_retry.assert_called_once_with("EP-01")
        self.assertEqual(mock_append_log.call_args.args[0], "batch01")

    def test_finish_aliases_run(self) -> None:
        args = argparse.Namespace(batch_id="batch01")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "cmd_run", return_value=0) as mock_run:
            result = self.controller.cmd_finish(args)

        self.assertEqual(result, 0)
        mock_run.assert_called_once_with(args)
        self.assertIn("deprecated", output.getvalue().lower())
        self.assertIn(".\\~run.cmd batch01", output.getvalue())


class RunCommandTests(unittest.TestCase):
    """cmd_run: strict release path with lint + verify gates."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_run_missing_verify_fails(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                                return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                                return_value=(True, {"EP-11": {"status": "pass"}, "EP-12": {"status": "pass"}})), \
             mock.patch.object(self.controller, "_compute_verify_tiers",
                                return_value=(["EP-11"], ["EP-12"], [], [])), \
             mock.patch.object(self.controller, "_read_verify_result", return_value=None), \
             mock.patch.object(self.controller, "_promote_batch") as mock_promote:
            result = self.controller.cmd_run(args)

        self.assertEqual(result, 1)
        text = output.getvalue()
        self.assertIn("no verify result", text)
        mock_promote.assert_not_called()

    def test_run_verify_fail_fails(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()
        verify_result = {
            "episode": "EP-11",
            "tier": "FULL",
            "status": "FAIL",
            "aligner_status": "FAIL",
            "source_compare_status": "PASS",
        }

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                               return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                               return_value=(True, {"EP-11": {}})), \
             mock.patch.object(self.controller, "_compute_verify_tiers",
                               return_value=(["EP-11"], [], [], [])), \
             mock.patch.object(self.controller, "_read_verify_result", return_value=verify_result), \
             mock.patch.object(self.controller, "_promote_batch") as mock_promote:
            result = self.controller.cmd_run(args)

        self.assertEqual(result, 1)
        self.assertIn("aligner verify FAIL", output.getvalue())
        mock_promote.assert_not_called()

    def test_run_source_compare_fail_fails(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()
        verify_result = {
            "episode": "EP-11",
            "tier": "FULL",
            "status": "FAIL",
            "aligner_status": "PASS",
            "source_compare_status": "FAIL",
        }

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                               return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                               return_value=(True, {"EP-11": {}})), \
             mock.patch.object(self.controller, "_compute_verify_tiers",
                               return_value=(["EP-11"], [], [], [])), \
             mock.patch.object(self.controller, "_read_verify_result", return_value=verify_result), \
             mock.patch.object(self.controller, "_promote_batch") as mock_promote:
            result = self.controller.cmd_run(args)

        self.assertEqual(result, 1)
        self.assertIn("source-compare verify FAIL", output.getvalue())
        mock_promote.assert_not_called()

    def test_run_stale_verify_hash_fails(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()
        verify_result = {
            "episode": "EP-11",
            "tier": "FULL",
            "status": "PASS",
            "aligner_status": "PASS",
            "source_compare_status": "PASS",
            "draft_sha256": "stale",
        }

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                               return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                               return_value=(True, {"EP-11": {}})), \
             mock.patch.object(self.controller, "_compute_verify_tiers",
                               return_value=(["EP-11"], [], [], [])), \
             mock.patch.object(self.controller, "_read_verify_result", return_value=verify_result), \
             mock.patch.object(
                 self.controller,
                 "_verify_draft_integrity",
                 return_value="EP-11 draft modified after verify",
             ), \
             mock.patch.object(self.controller, "_promote_batch") as mock_promote:
            result = self.controller.cmd_run(args)

        self.assertEqual(result, 1)
        self.assertIn("must re-verify", output.getvalue())
        mock_promote.assert_not_called()

    def test_run_does_not_write_verify_pass(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                               return_value=(True, {"EP-11": {}, "EP-12": {}})), \
             mock.patch.object(self.controller, "_run_verify_gate", return_value=True), \
             mock.patch.object(self.controller, "_require_batch_review_pass", return_value=(True, "")), \
             mock.patch.object(self.controller, "_write_verify_result") as mock_write_verify, \
             mock.patch.object(self.controller, "_append_log") as mock_append_log, \
             mock.patch.object(self.controller, "_promote_batch", return_value=(0, {})) as mock_promote, \
             mock.patch.object(self.controller, "_is_locked", return_value=False), \
             mock.patch.object(self.controller, "_set_batch_status"), \
             mock.patch.object(self.controller, "_upsert_batch_status"), \
             mock.patch.object(self.controller, "_write_lock"), \
             mock.patch.object(self.controller, "_clear_retry_count"), \
             mock.patch.object(self.controller, "_set_manifest_field"), \
             mock.patch.object(self.controller, "_validate_state_file", return_value=[]), \
             mock.patch.object(self.controller, "_parse_source_map", return_value={
                 "batch03": {"ep_start": "EP-11", "ep_end": "EP-12", "source_range": "ch9"},
             }):
            result = self.controller.cmd_run(args)

        self.assertEqual(result, 0)
        mock_promote.assert_called_once()
        mock_write_verify.assert_not_called()
        self.assertFalse(
            any(call.args[2] == "verify" and call.args[5] == "PASS" for call in mock_append_log.call_args_list)
        )
        self.assertNotIn("auto-verify", output.getvalue())

    def test_verify_done_records_aligner_only_until_source_compare_arrives(self) -> None:
        args = argparse.Namespace(batch="batch01", episode="EP-01", status="PASS", tier="FULL")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "LOCKS", Path(tempfile.mkdtemp())), \
             mock.patch.object(self.controller, "DRAFTS", Path(tempfile.mkdtemp())), \
             mock.patch.object(self.controller, "_find_brief_for_episode", return_value=""), \
             mock.patch.object(self.controller, "_append_log"):
            result = self.controller.cmd_verify_done(args)
            payload = self.controller._read_verify_result("EP-01")

        self.assertEqual(result, 0)
        self.assertEqual(payload["aligner_status"], "PASS")
        self.assertEqual(payload["source_compare_status"], "MISSING")
        self.assertEqual(payload["status"], "PENDING")

    def test_source_compare_done_completes_overall_verify_status(self) -> None:
        args_aligner = argparse.Namespace(batch="batch01", episode="EP-01", status="PASS", tier="FULL")
        args_source = argparse.Namespace(batch="batch01", episode="EP-01", status="PASS", tier="FULL")
        lock_dir = Path(tempfile.mkdtemp())
        drafts_dir = Path(tempfile.mkdtemp())
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "LOCKS", lock_dir), \
             mock.patch.object(self.controller, "DRAFTS", drafts_dir), \
             mock.patch.object(self.controller, "_find_brief_for_episode", return_value=""), \
             mock.patch.object(self.controller, "_append_log"):
            self.controller.cmd_verify_done(args_aligner)
            result = self.controller.cmd_source_compare_done(args_source)
            payload = self.controller._read_verify_result("EP-01")

        self.assertEqual(result, 0)
        self.assertEqual(payload["aligner_status"], "PASS")
        self.assertEqual(payload["source_compare_status"], "PASS")
        self.assertEqual(payload["status"], "PASS")

    def test_verify_done_persists_note_and_evidence_refs(self) -> None:
        args = argparse.Namespace(
            batch="batch01",
            episode="EP-01",
            status="PASS",
            tier="FULL",
            note="kept original long sentence",
            evidence_refs=["novel:ch1:l10-l18", "draft:EP-01:scene2"],
        )
        lock_dir = Path(tempfile.mkdtemp())
        drafts_dir = Path(tempfile.mkdtemp())

        with mock.patch.object(self.controller, "LOCKS", lock_dir), \
             mock.patch.object(self.controller, "DRAFTS", drafts_dir), \
             mock.patch.object(self.controller, "_find_brief_for_episode", return_value=""), \
             mock.patch.object(self.controller, "_append_log"):
            self.controller.cmd_verify_done(args)
            payload = self.controller._read_verify_result("EP-01")

        reviewer = payload["reviewers"]["aligner"]
        self.assertEqual(reviewer["note"], "kept original long sentence")
        self.assertEqual(reviewer["evidence_refs"], ["novel:ch1:l10-l18", "draft:EP-01:scene2"])

    def test_run_fails_on_lint_failure(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        with contextlib.redirect_stdout(io.StringIO()), \
             mock.patch.object(self.controller, "_resolve_batch",
                                return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                                return_value=(False, {})):
            result = self.controller.cmd_run(args)
        self.assertEqual(result, 1)

    def test_run_fails_when_batch_review_missing(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                               return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                               return_value=(True, {"EP-11": {}})), \
             mock.patch.object(self.controller, "_run_verify_gate", return_value=True), \
             mock.patch.object(self.controller, "_require_batch_review_pass",
                               return_value=(False, "ERROR: batch review artifact missing for 'batch03'")), \
             mock.patch.object(self.controller, "_promote_batch") as mock_promote:
            result = self.controller.cmd_run(args)

        self.assertEqual(result, 1)
        self.assertIn("batch review artifact missing", output.getvalue())
        mock_promote.assert_not_called()

    def test_promote_fails_when_batch_review_is_not_pass(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch",
                               return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                               return_value=(True, {"EP-11": {}})), \
             mock.patch.object(self.controller, "_run_verify_gate", return_value=True), \
             mock.patch.object(self.controller, "_require_batch_review_pass",
                               return_value=(False, "ERROR: batch review verdict is FAIL for 'batch03'")), \
             mock.patch.object(self.controller, "_promote_batch") as mock_promote:
            result = self.controller.cmd_promote(args)

        self.assertEqual(result, 1)
        self.assertIn("batch review verdict is FAIL", output.getvalue())
        mock_promote.assert_not_called()


class StartCommandTests(unittest.TestCase):
    """cmd_start: prepare-only escape hatch + writer-stage stop."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_start_prepare_only_skips_writer_and_run(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=True, write=False, writer_command=None)
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])) as mock_prepare, \
             mock.patch.object(self.controller, "_run_writer_stage") as mock_writer, \
             mock.patch.object(self.controller, "cmd_run") as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        mock_prepare.assert_called_once_with("batch03")
        mock_writer.assert_not_called()
        mock_run.assert_not_called()
        self.assertIn("prepare-only", output.getvalue())
        self.assertIn(".\\~review.cmd batch03 PASS --reviewer <name>", output.getvalue())
        self.assertIn(".\\~run.cmd batch03", output.getvalue())

    def test_start_defaults_to_prepare_mode_without_write_flag(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=False, writer_command="writer --batch {batch_id}")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])) as mock_prepare, \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "cmd_run", return_value=0) as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        mock_prepare.assert_called_once_with("batch03")
        mock_writer.assert_not_called()
        mock_run.assert_not_called()
        text = output.getvalue()
        self.assertIn("default prepare mode", text)
        self.assertIn(".\\~review.cmd batch03 PASS --reviewer <name>", text)
        self.assertIn(".\\~run.cmd batch03", text)

    def test_start_runs_writer_only_with_write_flag(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=True, writer_command="writer --batch {batch_id}")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])) as mock_prepare, \
             mock.patch.object(self.controller, "_guard_quality_anchors", return_value=True), \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "_ensure_batch_review_artifacts", return_value={"status": "PENDING"}) as mock_review, \
             mock.patch.object(self.controller, "cmd_run", return_value=0) as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        mock_prepare.assert_called_once_with("batch03")
        self.assertEqual(
            mock_writer.call_args_list,
            [mock.call("batch03", ["EP-11", "EP-12"], writer_command="writer --batch {batch_id}", parallelism=1)],
        )
        mock_review.assert_called_once_with("batch03", ["EP-11", "EP-12"], brief_path=Path("brief.md"))
        mock_run.assert_not_called()
        text = output.getvalue()
        self.assertIn("=== Writer Stage Complete ===", text)
        self.assertIn("=== Review Packet Ready ===", text)


class BatchReviewVerdictTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_batch_review_done_persists_structured_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            reviews = project / "reviews"
            state = project / "state"
            batch_status_dir = state / "batch-status"
            reviews.mkdir(parents=True, exist_ok=True)
            batch_status_dir.mkdir(parents=True, exist_ok=True)

            review_payload = self.controller._empty_batch_review("batch01", ["EP-01", "EP-02"], ["EP-01"])
            (reviews / "batch01.review.json").write_text(
                json.dumps(review_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            args = argparse.Namespace(
                batch_id="batch01",
                status="FAIL",
                reviewer="codex",
                reason="source drift",
                blocking_reasons=["unsupported additions in EP-05"],
                warning_families=["unsupported_addition"],
                arc_regressions=["EP-03 repeats EP-02 humiliation beat"],
                function_theft_findings=["EP-05 consumes EP-06 reconciliation payoff"],
                quality_anchor_findings=["weaker than anchor in reveal scene"],
                evidence_refs=["draft:EP-05:23-33", "source:ch3:14-17"],
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir):
                result = self.controller.cmd_batch_review_done(args)

            self.assertEqual(result, 0)
            saved = json.loads((reviews / "batch01.review.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "FAIL")
            self.assertEqual(saved["reviewer"], "codex")
            self.assertEqual(saved["blocking_reasons"], ["source drift", "unsupported additions in EP-05"])
            self.assertEqual(saved["warning_families"], ["unsupported_addition"])
            self.assertEqual(saved["arc_regressions"], ["EP-03 repeats EP-02 humiliation beat"])
            self.assertEqual(saved["function_theft_findings"], ["EP-05 consumes EP-06 reconciliation payoff"])
            self.assertEqual(saved["quality_anchor_findings"], ["weaker than anchor in reveal scene"])
            self.assertEqual(saved["evidence_refs"], ["draft:EP-05:23-33", "source:ch3:14-17"])

            runtime = json.loads((batch_status_dir / "batch01.status.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime["batch_review_status"], "FAIL")
            self.assertEqual(runtime["phase"], "review_pending")
            self.assertIn("blocking_reasons: 2", output.getvalue())
            self.assertIn("evidence_refs: 2", output.getvalue())

    def test_batch_review_done_pass_can_store_evidence_without_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            reviews = project / "reviews"
            state = project / "state"
            batch_status_dir = state / "batch-status"
            reviews.mkdir(parents=True, exist_ok=True)
            batch_status_dir.mkdir(parents=True, exist_ok=True)

            review_payload = self.controller._empty_batch_review("batch02", ["EP-06"], ["EP-06"])
            (reviews / "batch02.review.json").write_text(
                json.dumps(review_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            args = argparse.Namespace(
                batch_id="batch02",
                status="PASS",
                reviewer="codex",
                reason="",
                blocking_reasons=[],
                warning_families=["imagery_dense"],
                arc_regressions=[],
                function_theft_findings=[],
                quality_anchor_findings=[],
                evidence_refs=["draft:EP-06:12-19"],
            )

            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir):
                result = self.controller.cmd_batch_review_done(args)

            self.assertEqual(result, 0)
            saved = json.loads((reviews / "batch02.review.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "PASS")
            self.assertEqual(saved["blocking_reasons"], [])
            self.assertEqual(saved["warning_families"], ["imagery_dense"])
            self.assertEqual(saved["evidence_refs"], ["draft:EP-06:12-19"])
            runtime = json.loads((batch_status_dir / "batch02.status.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime["batch_review_status"], "PASS")
            self.assertEqual(runtime["phase"], "review_passed")


class PromoteJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_promote_batch_writes_completed_journal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            releases = project / "releases"
            journals = releases / "journals"
            staging = releases / "staging"
            drafts = root / "drafts" / "episodes"
            published = root / "episodes"
            brief = project / "batch-briefs" / "batch01_EP01-05.md"
            for path in [journals, staging, drafts, published, brief.parent]:
                path.mkdir(parents=True, exist_ok=True)

            (drafts / "EP-01.md").write_text("draft one", encoding="utf-8")
            brief.write_text("# brief", encoding="utf-8")

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "RELEASES", releases), \
                 mock.patch.object(self.controller, "RELEASE_JOURNALS", journals), \
                 mock.patch.object(self.controller, "RELEASE_INDEX", releases / "release.index.json"), \
                 mock.patch.object(self.controller, "GOLD_SET", releases / "gold-set.json"), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "EPISODES", published), \
                 mock.patch.object(self.controller, "NOW", "2026-04-19 20:10"), \
                 mock.patch.object(
                     self.controller,
                     "_read_verify_result",
                     return_value={"episode": "EP-01", "tier": "FULL", "status": "PASS"},
                 ):
                rc, _ = self.controller._promote_batch(
                    "batch01",
                    brief,
                    ["EP-01"],
                    {"EP-01": {"status": "pass", "checks": {}}},
                )

            self.assertEqual(rc, 0)
            self.assertTrue((published / "EP-01.md").exists())
            self.assertTrue((published / "EP-01.meta.json").exists())
            journal = json.loads((journals / "batch01.promote.json").read_text(encoding="utf-8"))
            self.assertTrue(journal["completed"])
            self.assertEqual(journal["phase"], "completed")
            self.assertEqual(journal["published_episodes"], ["EP-01"])
            stage_root = root / journal["stage_root"]
            self.assertFalse(stage_root.exists())

    def test_promote_batch_resumes_from_partial_journal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            releases = project / "releases"
            journals = releases / "journals"
            stage_root = releases / "staging" / "batch01-resume"
            drafts = root / "drafts" / "episodes"
            published = root / "episodes"
            brief = project / "batch-briefs" / "batch01_EP01-05.md"
            for path in [journals, stage_root, drafts, published, brief.parent]:
                path.mkdir(parents=True, exist_ok=True)

            brief.write_text("# brief", encoding="utf-8")
            (drafts / "EP-01.md").write_text("draft one", encoding="utf-8")
            (drafts / "EP-02.md").write_text("draft two", encoding="utf-8")
            (published / "EP-01.md").write_text("published one", encoding="utf-8")
            (published / "EP-01.meta.json").write_text("{}", encoding="utf-8")
            (stage_root / "EP-02.md").write_text("draft two", encoding="utf-8")
            (stage_root / "EP-02.meta.json").write_text("{}", encoding="utf-8")
            (stage_root / "release.index.json").write_text(
                json.dumps({"episodes": {"EP-01": {"release_status": "gold"}, "EP-02": {"release_status": "gold"}}}),
                encoding="utf-8",
            )
            (stage_root / "gold-set.json").write_text(
                json.dumps({"episodes": ["EP-01", "EP-02"]}),
                encoding="utf-8",
            )
            (journals / "batch01.promote.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "episodes": ["EP-01", "EP-02"],
                        "phase": "publishing",
                        "completed": False,
                        "stage_root": "harness/project/releases/staging/batch01-resume",
                        "staged_episode_files": {
                            "EP-01": "harness/project/releases/staging/batch01-resume/EP-01.md",
                            "EP-02": "harness/project/releases/staging/batch01-resume/EP-02.md",
                        },
                        "staged_meta_files": {
                            "EP-01": "harness/project/releases/staging/batch01-resume/EP-01.meta.json",
                            "EP-02": "harness/project/releases/staging/batch01-resume/EP-02.meta.json",
                        },
                        "staged_release_index": "harness/project/releases/staging/batch01-resume/release.index.json",
                        "staged_gold_set": "harness/project/releases/staging/batch01-resume/gold-set.json",
                        "published_episodes": ["EP-01"],
                        "release_files_written": False,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "RELEASES", releases), \
                 mock.patch.object(self.controller, "RELEASE_JOURNALS", journals), \
                 mock.patch.object(self.controller, "RELEASE_INDEX", releases / "release.index.json"), \
                 mock.patch.object(self.controller, "GOLD_SET", releases / "gold-set.json"), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "EPISODES", published), \
                 mock.patch.object(self.controller, "NOW", "2026-04-19 20:11"):
                rc, _ = self.controller._promote_batch(
                    "batch01",
                    brief,
                    ["EP-01", "EP-02"],
                    {"EP-01": {"status": "pass", "checks": {}}, "EP-02": {"status": "pass", "checks": {}}},
                )

            self.assertEqual(rc, 0)
            self.assertTrue((published / "EP-02.md").exists())
            self.assertTrue((releases / "release.index.json").exists())
            self.assertTrue((releases / "gold-set.json").exists())
            journal = json.loads((journals / "batch01.promote.json").read_text(encoding="utf-8"))
            self.assertTrue(journal["completed"])
            self.assertEqual(journal["published_episodes"], ["EP-01", "EP-02"])

    def test_start_write_mode_runs_writer_once_without_smoke_retry(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=True, writer_command="writer --batch {batch_id}")

        with mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12", "EP-13"])), \
             mock.patch.object(self.controller, "_guard_quality_anchors", return_value=True), \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "cmd_run") as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        mock_writer.assert_called_once_with(
            "batch03",
            ["EP-11", "EP-12", "EP-13"],
            writer_command="writer --batch {batch_id}",
            parallelism=1,
        )
        mock_run.assert_not_called()

    def test_start_write_mode_updates_status_to_review_pending(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=True, writer_command="writer --batch {batch_id}")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12", "EP-13"])), \
             mock.patch.object(self.controller, "_guard_quality_anchors", return_value=True), \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "_ensure_batch_review_artifacts", return_value={"status": "PENDING"}), \
             mock.patch.object(self.controller, "_upsert_batch_status") as mock_status, \
             mock.patch.object(self.controller, "cmd_run", return_value=0) as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        mock_writer.assert_called_once()
        self.assertEqual(mock_status.call_args.kwargs["phase"], "review_pending")
        mock_run.assert_not_called()
        self.assertIn("=== Writer Stage Complete ===", output.getvalue())

    def test_start_stops_when_quality_anchors_are_pending(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=True, writer_command="writer --batch {batch_id}")

        with mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])), \
             mock.patch.object(self.controller, "_guard_quality_anchors", return_value=False), \
             mock.patch.object(self.controller, "_run_writer_stage") as mock_writer:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 1)
        mock_writer.assert_not_called()

    def test_repairable_smoke_content_failure_only_allows_hookless_scenes(self) -> None:
        self.assertEqual(self.controller.RULESET_VERSION, "reviewer-gate/v1")


class WriterStageTests(unittest.TestCase):
    """writer stage hook: use existing drafts or invoke configured command."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_writer_stage_uses_existing_drafts_without_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            drafts = Path(tmp) / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            (drafts / "EP-11.md").write_text("draft", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller.subprocess, "run") as mock_subprocess:
                result = self.controller._run_writer_stage("batch03", ["EP-11"], writer_command=None)

        self.assertEqual(result, 0)
        mock_subprocess.assert_not_called()
        self.assertIn("existing drafts", output.getvalue())

    def test_writer_stage_fails_without_command_or_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            drafts = Path(tmp) / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.dict(os.environ, {}, clear=False), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={}):
                result = self.controller._run_writer_stage("batch03", ["EP-11"], writer_command=None)

        self.assertEqual(result, 1)
        self.assertIn("writer stage is not configured", output.getvalue())

    def test_writer_stage_runs_configured_command_and_requires_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            output = io.StringIO()

            def fake_run(command, **kwargs):
                self.assertEqual(kwargs.get("cwd"), root)
                self.assertNotIn("shell", kwargs)
                self.assertIn("batch03", command)
                (drafts / "EP-11.md").write_text("generated", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="writer ok\n", stderr="")

            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller.subprocess, "run", side_effect=fake_run) as mock_subprocess:
                result = self.controller._run_writer_stage(
                    "batch03", ["EP-11"], writer_command="writer --batch {batch_id}"
                )

        self.assertEqual(result, 0)
        mock_subprocess.assert_called_once()
        self.assertIn("writer ok", output.getvalue())

    def test_writer_stage_formats_parallelism_and_syntax_first_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            output = io.StringIO()

            def fake_run(command, **kwargs):
                command_text = " ".join(command)
                self.assertIn("--parallelism 3", command_text)
                self.assertIn("--syntax-first", command_text)
                (drafts / "EP-11.md").write_text("generated", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller.subprocess, "run", side_effect=fake_run):
                result = self.controller._run_writer_stage(
                    "batch03",
                    ["EP-11"],
                    writer_command="writer --batch {batch_id} --parallelism {parallelism} {syntax_first_flag}",
                    parallelism=3,
                    syntax_first=True,
                )

        self.assertEqual(result, 0)

    def test_writer_stage_force_rewrite_removes_existing_draft_before_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            existing = drafts / "EP-11.md"
            existing.write_text("old", encoding="utf-8")

            def fake_run(command, **kwargs):
                self.assertFalse(existing.exists())
                self.assertIsInstance(command, list)
                existing.write_text("new", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller.subprocess, "run", side_effect=fake_run):
                result = self.controller._run_writer_stage(
                    "batch03",
                    ["EP-11"],
                    writer_command="writer {syntax_first_flag}",
                    syntax_first=True,
                    force_rewrite=True,
                )
                self.assertTrue(existing.exists())
                self.assertEqual(existing.read_text(encoding="utf-8"), "new")

        self.assertEqual(result, 0)

    def test_writer_stage_rejects_shell_metacharacters_in_command_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller.subprocess, "run") as mock_run:
                result = self.controller._run_writer_stage(
                    "batch03",
                    ["EP-11"],
                    writer_command="writer --batch {batch_id} && echo hi",
                )

        self.assertEqual(result, 1)
        mock_run.assert_not_called()
        self.assertIn("shell metacharacters", output.getvalue())


class RecordStageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_record_auto_updates_state_and_marks_batch_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            locks = root / "locks"
            batch_briefs = root / "batch-briefs"
            batch_status_dir = root / "batch-status"
            reviews = root / "reviews"
            state.mkdir(parents=True)
            locks.mkdir(parents=True)
            batch_briefs.mkdir(parents=True)
            batch_status_dir.mkdir(parents=True)
            reviews.mkdir(parents=True)

            brief_path = batch_briefs / "batch01_EP01-02.md"
            brief_path.write_text(
                "# Batch Brief: EP-01 ~ EP-02\n\n"
                "- batch status: promoted\n"
                "- owned episodes: EP-01, EP-02\n",
                encoding="utf-8",
            )
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps({"batch_id": "batch01", "phase": "promoted", "status": "ACTIVE"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (reviews / "batch01.review.json").write_text(
                json.dumps({"status": "PASS", "warning_families": ["opening_density"]}, ensure_ascii=False),
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "RUN_LOG", state / "run.log.md"), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", root / "book.blueprint.md"), \
                 mock.patch.object(self.controller, "SOURCE_MAP", root / "source.map.md"), \
                 mock.patch.object(self.controller, "EPISODES", root / "episodes"), \
                 mock.patch.object(self.controller, "_export_outputs", return_value={"episodes": 2}), \
                 mock.patch.object(self.controller, "_parse_source_map", return_value={
                     "batch01": {
                         "episodes": ["EP-01", "EP-02"],
                         "ep_start": "EP-01",
                         "ep_end": "EP-02",
                         "source_range": "ch1~ch2",
                         "episode_data": {
                             "EP-01": {
                                 "source_span": "ch1",
                                 "must_keep": "【动作】误认带回苏家；【关系】冷静拒认，切断期待",
                                 "ending_function": "locked_in",
                             },
                             "EP-02": {
                                 "source_span": "ch2",
                                 "must_keep": "【动作】亲子鉴定坐实；【关系】说出不认这个家",
                                 "ending_function": "confrontation_pending",
                             },
                         },
                     },
                     "batch02": {
                         "episodes": ["EP-03"],
                         "ep_start": "EP-03",
                         "ep_end": "EP-03",
                         "source_range": "ch3",
                         "episode_data": {
                             "EP-03": {"source_span": "ch3", "must_keep": "【钩子】公开掉马"}
                         },
                     },
                 }), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={
                     "source_file": "novel.md",
                     "total_episodes": "20",
                     "batch_size": "5",
                 }):
                rc = self.controller.cmd_record(argparse.Namespace(batch_id="batch01"))

            self.assertEqual(rc, 0)
            self.assertIn("batch01", (state / "script.progress.md").read_text(encoding="utf-8"))
            self.assertIn("EP-01", (state / "story.state.md").read_text(encoding="utf-8"))
            runtime = json.loads((batch_status_dir / "batch01.status.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime["phase"], "recorded")
            self.assertEqual(runtime["status"], "DONE")

    def test_record_done_accepts_already_recorded_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            locks = root / "locks"
            batch_briefs = root / "batch-briefs"
            batch_status_dir = root / "batch-status"
            state.mkdir(parents=True)
            locks.mkdir(parents=True)
            batch_briefs.mkdir(parents=True)
            batch_status_dir.mkdir(parents=True)

            for name, content in self.controller._state_templates().items():
                (state / name).write_text(content, encoding="utf-8")
            brief_path = batch_briefs / "batch01_EP01-02.md"
            brief_path.write_text("# Batch Brief\n- owned episodes: EP-01, EP-02\n", encoding="utf-8")
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps({"batch_id": "batch01", "phase": "recorded", "status": "DONE"}, ensure_ascii=False),
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir):
                rc = self.controller.cmd_record_done(argparse.Namespace(batch_id="batch01"))

            self.assertEqual(rc, 0)
            self.assertIn("Record already complete", output.getvalue())


class OutputExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_export_outputs_builds_human_facing_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            episodes = root / "episodes"
            drafts = root / "drafts" / "episodes"
            reviews = root / "harness" / "project" / "reviews"
            prompts = root / "harness" / "project" / "prompts"
            briefs = root / "harness" / "project" / "batch-briefs"
            state = root / "harness" / "project" / "state"
            project = root / "harness" / "project"
            framework = root / "harness" / "framework"
            output = root / "output"
            for path in (episodes, drafts, reviews, prompts, briefs, state, project, framework):
                path.mkdir(parents=True, exist_ok=True)

            (episodes / "EP-01.md").write_text("# EP-01\n", encoding="utf-8")
            (episodes / "EP-01.meta.json").write_text("{}", encoding="utf-8")
            (drafts / "EP-02.md").write_text("# EP-02\n", encoding="utf-8")
            (reviews / "batch01.review.md").write_text("# review\n", encoding="utf-8")
            (reviews / "batch01.review.json").write_text("{}", encoding="utf-8")
            (reviews / "batch01.review.prompt.md").write_text("# review prompt\n", encoding="utf-8")
            (prompts / "batch01.writer.batch.prompt.md").write_text("# writer prompt\n", encoding="utf-8")
            (briefs / "batch01_EP01-05.md").write_text("# brief\n", encoding="utf-8")
            (project / "book.blueprint.md").write_text("# blueprint\n", encoding="utf-8")
            (project / "source.map.md").write_text("# source\n", encoding="utf-8")
            (project / "run.manifest.md").write_text("# manifest\n", encoding="utf-8")
            (state / "story.state.md").write_text("# story\n", encoding="utf-8")
            (framework / "prompt-packet-protocol.md").write_text("# protocol\n", encoding="utf-8")
            (root / "character.md").write_text("# character\n", encoding="utf-8")
            (root / "voice-anchor.md").write_text("# voice\n", encoding="utf-8")

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "OUTPUT", output), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "PROMPTS", prompts), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", briefs), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "PROMPT_PACKET_PROTOCOL", framework / "prompt-packet-protocol.md"), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", project / "book.blueprint.md"), \
                 mock.patch.object(self.controller, "SOURCE_MAP", project / "source.map.md"), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", project / "run.manifest.md"):
                stats = self.controller._export_outputs()

            self.assertEqual(stats["episodes"], 1)
            self.assertTrue((output / "episodes" / "EP-01.md").exists())
            self.assertFalse((output / "episodes" / "EP-01.meta.json").exists())
            self.assertTrue((output / "_runtime" / "drafts" / "EP-02.md").exists())
            self.assertFalse((output / "drafts").exists())
            self.assertTrue((output / "_runtime" / "prompts" / "batch01.writer.batch.prompt.md").exists())
            self.assertTrue((output / "_runtime" / "prompts" / "batch01.review.prompt.md").exists())
            self.assertTrue((output / "_runtime" / "protocols" / "prompt-packet-protocol.md").exists())
            self.assertTrue((output / "anchors" / "character.md").exists())
            self.assertIn("_runtime/", (output / "README.md").read_text(encoding="utf-8"))
            self.assertIn(".\\~export.cmd", (output / "README.md").read_text(encoding="utf-8"))

    def test_export_marks_manifest_complete_when_all_batches_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            episodes = root / "episodes"
            drafts = root / "drafts" / "episodes"
            reviews = project / "reviews"
            prompts = project / "prompts"
            briefs = project / "batch-briefs"
            state = project / "state"
            locks = project / "locks"
            batch_status = project / "batch-status"
            framework = root / "harness" / "framework"
            output = root / "output"
            for path in (project, episodes, drafts, reviews, prompts, briefs, state, locks, batch_status, framework):
                path.mkdir(parents=True, exist_ok=True)

            (episodes / "EP-01.md").write_text("# EP-01\n", encoding="utf-8")
            (drafts / "EP-01.md").write_text("# EP-01\n", encoding="utf-8")
            (project / "book.blueprint.md").write_text("# blueprint\n", encoding="utf-8")
            (project / "source.map.md").write_text(
                "# Source Map\n\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-01): 示例\n\n"
                "### EP01: 开局\n\n"
                "**source_chapter_span**: 第1章\n\n"
                "**must_keep_beats**:\n"
                "- 【动作】开局冲突\n\n",
                encoding="utf-8",
            )
            run_manifest = project / "run.manifest.md"
            run_manifest.write_text(
                "# Run Manifest\n\n"
                "- source_file: novel.md\n"
                "- total_episodes: 1\n"
                "- target_total_minutes: 2\n"
                "- target_episode_minutes: 2\n"
                "- batch_size: 1\n"
                "- run_status: active\n"
                "- active_batch: batch01_promoted\n",
                encoding="utf-8",
            )
            (batch_status / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "recorded",
                        "status": "DONE",
                        "episodes": ["EP-01"],
                        "batch_review_status": "PASS",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (reviews / "batch01.review.json").write_text(
                json.dumps({"batch_id": "batch01", "status": "PASS", "reviewer": "codex"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (framework / "prompt-packet-protocol.md").write_text("# protocol\n", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "OUTPUT", output), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "PROMPTS", prompts), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", briefs), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status), \
                 mock.patch.object(self.controller, "PROMPT_PACKET_PROTOCOL", framework / "prompt-packet-protocol.md"), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", project / "book.blueprint.md"), \
                 mock.patch.object(self.controller, "SOURCE_MAP", project / "source.map.md"), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest):
                result = self.controller.cmd_export(argparse.Namespace())

            self.assertEqual(result, 0)
            manifest_text = run_manifest.read_text(encoding="utf-8")
            self.assertIn("- run_status: complete", manifest_text)
            self.assertIn("- active_batch: (none)", manifest_text)
            payload = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["run_status"], "complete")
            self.assertEqual(payload["active_batch"], "(none)")
            self.assertEqual(payload["paths"]["drafts"], "_runtime/drafts/")
            self.assertEqual(payload["paths"]["protocols"], "_runtime/protocols/")
            self.assertEqual(payload["draft_episodes"][0]["path"], "_runtime/drafts/EP-01.md")


class WriterCommandConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_resolve_writer_command_prefers_argument_over_manifest_and_env(self) -> None:
        with mock.patch.object(self.controller, "_read_manifest", return_value={"writer_command": "manifest-cmd"}), \
             mock.patch.dict(os.environ, {self.controller.WRITER_COMMAND_ENV: "env-cmd"}, clear=False):
            result = self.controller._resolve_writer_command("arg-cmd")
        self.assertEqual(result, "arg-cmd")

    def test_init_writes_default_writer_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            novel = root / "novel.md"
            novel.write_text("# 第1章 初见\n内容\n# 第2章 交锋\n内容\n", encoding="utf-8")
            harness = root / "harness"
            project = harness / "project"
            state = project / "state"
            locks = project / "locks"
            drafts = root / "drafts" / "episodes"
            episodes = root / "episodes"
            batch_briefs = project / "batch-briefs"
            book_blueprint = project / "book.blueprint.md"
            run_manifest = project / "run.manifest.md"
            run_log = state / "run.log.md"
            source_map = project / "source.map.md"
            for path in [state, locks, drafts, episodes, batch_briefs]:
                path.mkdir(parents=True, exist_ok=True)

            args = argparse.Namespace(
                novel_file="novel.md",
                episodes=None,
                batch_size=2,
                target_total_minutes=50,
                strategy="original_fidelity",
                intensity="light",
                key_episodes="",
                force=False,
            )
            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "HARNESS", harness), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", book_blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.controller, "RUN_LOG", run_log), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "_has_existing_project", return_value=False), \
                 mock.patch.object(self.controller, "_backup_project", return_value=None), \
                 mock.patch.object(self.controller, "_append_log"):
                result = self.controller.cmd_init(args)

            self.assertEqual(result, 0)
            content = run_manifest.read_text(encoding="utf-8")
            self.assertIn("writer_command", content)
            self.assertIn("_ops/run_writer.py", content)
            self.assertIn("book.blueprint.md", content)
            self.assertIn("total_episodes: pending_model_recommendation", content)
            self.assertIn("recommended_total_episodes: pending_book_extraction", content)
            self.assertIn("episode_count_source: model_recommended", content)
            self.assertIn("target_total_minutes: 50", content)
            self.assertIn("target_episode_minutes: 2", content)
            self.assertIn("episode_minutes_min: 1", content)
            self.assertIn("episode_minutes_max: 3", content)
            self.assertIn("writer_parallelism: 1", content)
            self.assertIn("--parallelism {parallelism}", content)
            self.assertIn("{syntax_first_flag}", content)
            blueprint = book_blueprint.read_text(encoding="utf-8")
            self.assertIn("recommended_total_episodes: pending_extraction", blueprint)
            self.assertIn("## 集数建议", blueprint)
            self.assertIn("## 主线", blueprint)
            self.assertIn("## 角色弧光", blueprint)
            self.assertIn("## 章节索引（仅定位）", blueprint)
            source_map_content = source_map.read_text(encoding="utf-8")
            self.assertIn("mapping_status: pending_book_extraction", source_map_content)
            self.assertIn("total_episodes: pending_model_recommendation", source_map_content)
            self.assertIn("total_batches: pending_total_episodes", source_map_content)
            self.assertIn("target_total_minutes: 50", source_map_content)

    def test_init_prompts_for_episode_count_on_interactive_terminal(self) -> None:
        class TtyInput(io.StringIO):
            def isatty(self) -> bool:
                return True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            novel = root / "novel.md"
            novel.write_text("# 第1章 初见\n内容\n", encoding="utf-8")
            harness = root / "harness"
            project = harness / "project"
            state = project / "state"
            locks = project / "locks"
            drafts = root / "drafts" / "episodes"
            episodes = root / "episodes"
            batch_briefs = project / "batch-briefs"
            book_blueprint = project / "book.blueprint.md"
            run_manifest = project / "run.manifest.md"
            run_log = state / "run.log.md"
            source_map = project / "source.map.md"
            for path in [state, locks, drafts, episodes, batch_briefs]:
                path.mkdir(parents=True, exist_ok=True)

            args = argparse.Namespace(
                novel_file="novel.md",
                episodes=None,
                batch_size=5,
                target_total_minutes=60,
                strategy="original_fidelity",
                intensity="light",
                key_episodes="",
                force=False,
            )
            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller.sys, "stdin", TtyInput("30集\n")), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "HARNESS", harness), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", book_blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.controller, "RUN_LOG", run_log), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "_has_existing_project", return_value=False), \
                 mock.patch.object(self.controller, "_backup_project", return_value=None), \
                 mock.patch.object(self.controller, "_append_log"):
                result = self.controller.cmd_init(args)

            self.assertEqual(result, 0)
            content = run_manifest.read_text(encoding="utf-8")
            self.assertIn("total_episodes: 30", content)
            self.assertIn("episode_count_source: manual_override", content)
            self.assertIn("target_total_minutes: 60", content)


class BookPipelineCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_extract_book_runs_backend_for_manifest_source_file_when_forced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n"
                "- source_file: novel.md\n"
                "- extraction_status: extracted\n"
                "- recommended_total_episodes: 48\n\n"
                "## 集数建议\n\n"
                "- 推荐区间：32-48集\n"
                "- 最终采用：48集\n"
                "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n",
                encoding="utf-8",
            )
            manifest = project / "run.manifest.md"
            manifest.write_text(
                "# Run Manifest\n"
                "- source_file: novel.md\n"
                "- total_episodes: pending_model_recommendation\n"
                "- recommended_total_episodes: pending_book_extraction\n"
                "- episode_count_source: model_recommended\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            def _fake_extract(*_args, **_kwargs):
                blueprint.write_text(
                    "# Book Blueprint\n"
                    "- source_file: novel.md\n"
                    "- extraction_status: extracted\n"
                    "- recommended_total_episodes: 48\n\n"
                    "## 集数建议\n\n"
                    "- 推荐区间：32-48集\n"
                    "- 最终采用：48集\n"
                    "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                    "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                    "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n\n"
                    "## 主线\n\n完整主线\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess([], 0)
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest), \
                 mock.patch.object(self.controller.subprocess, "run", side_effect=_fake_extract) as mock_run:
                rc = self.controller.cmd_extract_book(argparse.Namespace(force=True))

            self.assertEqual(rc, 0)
            command = mock_run.call_args.args[0]
            self.assertIn(str(root / "_ops" / "run_book_extract.py"), command)
            self.assertIn("--novel-file", command)
            self.assertIn("novel.md", command)
            self.assertIn("extract-book", output.getvalue())

    def test_extract_book_auto_applies_recommended_total_episodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n"
                "- source_file: novel.md\n"
                "- extraction_status: extracted\n"
                "- recommended_total_episodes: 48\n\n"
                "## 集数建议\n\n"
                "- 推荐区间：32-48集\n"
                "- 最终采用：48集\n"
                "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n",
                encoding="utf-8",
            )
            manifest = project / "run.manifest.md"
            manifest.write_text(
                "# Run Manifest\n"
                "- source_file: novel.md\n"
                "- total_episodes: pending_model_recommendation\n"
                "- recommended_total_episodes: pending_book_extraction\n"
                "- episode_count_source: model_recommended\n",
                encoding="utf-8",
            )

            def _fake_extract(*_args, **_kwargs):
                blueprint.write_text(
                    "# Book Blueprint\n"
                    "- source_file: novel.md\n"
                    "- extraction_status: extracted\n"
                    "- recommended_total_episodes: 48\n\n"
                    "## 集数建议\n\n"
                    "- 推荐区间：32-48集\n"
                    "- 最终采用：48集\n"
                    "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                    "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                    "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n\n"
                    "## 主线\n\n完整主线\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess([], 0)
            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest), \
                 mock.patch.object(self.controller.subprocess, "run", side_effect=_fake_extract):
                rc = self.controller.cmd_extract_book(argparse.Namespace())

            self.assertEqual(rc, 0)
            content = manifest.read_text(encoding="utf-8")
            self.assertIn("total_episodes: 48", content)
            self.assertIn("recommended_total_episodes: 48", content)
            self.assertIn("episode_count_source: model_recommended", content)

    def test_extract_book_sync_accepts_final_count_without_top_level_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blueprint = root / "book.blueprint.md"
            manifest = root / "run.manifest.md"
            blueprint.write_text(
                "# Book Blueprint\n"
                "- extraction_status: extracted\n"
                "\n## 集数建议\n"
                "- 最终采用：约20（建议）\n",
                encoding="utf-8",
            )
            manifest.write_text(
                "- total_episodes: pending_model_recommendation\n"
                "- recommended_total_episodes: pending_book_extraction\n"
                "- episode_count_source: model_recommended\n",
                encoding="utf-8",
            )

            with mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest):
                recommended = self.controller._sync_recommended_episode_count_from_blueprint()

            self.assertEqual(recommended, 20)
            content = manifest.read_text(encoding="utf-8")
            self.assertIn("total_episodes: 20", content)
            self.assertIn("recommended_total_episodes: 20", content)

    def test_extract_book_skips_when_blueprint_already_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n"
                "- source_file: novel.md\n"
                "- extraction_status: extracted\n"
                "- recommended_total_episodes: 48\n"
                "\n## 集数建议\n"
                "- 推荐区间：32-48集\n"
                "- 最终采用：48集\n"
                "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n"
                "\n## 主线\n已填写\n",
                encoding="utf-8",
            )
            manifest = project / "run.manifest.md"
            manifest.write_text(
                "# Run Manifest\n"
                "- source_file: novel.md\n"
                "- total_episodes: pending_model_recommendation\n"
                "- recommended_total_episodes: pending_book_extraction\n"
                "- episode_count_source: model_recommended\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest), \
                 mock.patch.object(self.controller, "_append_log") as mock_log, \
                 mock.patch.object(self.controller.subprocess, "run") as mock_run:
                rc = self.controller.cmd_extract_book(argparse.Namespace(force=False))

            self.assertEqual(rc, 0)
            mock_run.assert_not_called()
            self.assertIn("Skip: existing book.blueprint.md is already complete", output.getvalue())
            self.assertIn("total_episodes: 48", manifest.read_text(encoding="utf-8"))
            self.assertEqual(mock_log.call_args.args[3], "extract-book")
            self.assertEqual(mock_log.call_args.args[4], "↷")

    def test_map_book_requires_non_placeholder_blueprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            blueprint = project / "book.blueprint.md"
            blueprint.write_text("# Book Blueprint\n\n（AGENT_EXTRACT_REQUIRED）\n", encoding="utf-8")
            source_map = project / "source.map.md"
            source_map.write_text("# Source Map\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={"source_file": "novel.md"}), \
                 mock.patch.object(self.controller.subprocess, "run") as mock_run:
                rc = self.controller.cmd_map_book(argparse.Namespace())

            self.assertEqual(rc, 1)
            mock_run.assert_not_called()
            self.assertIn("extract-book", output.getvalue())

    def test_map_book_requires_resolved_total_episode_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            blueprint = project / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n"
                "- extraction_status: extracted\n"
                "- recommended_total_episodes: 48\n"
                "\n## 集数建议\n"
                "- 推荐区间：32-48集\n"
                "- 最终采用：48集\n"
                "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n"
                "\n## 主线\n已填写\n",
                encoding="utf-8",
            )
            source_map = project / "source.map.md"
            source_map.write_text("# Source Map\n", encoding="utf-8")
            manifest = project / "run.manifest.md"
            manifest.write_text(
                "# Run Manifest\n"
                "- source_file: novel.md\n"
                "- total_episodes: pending_model_recommendation\n"
                "- batch_size: 5\n"
                "- adaptation_strategy: original_fidelity\n"
                "- dialogue_adaptation_intensity: light\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest), \
                 mock.patch.object(self.controller.subprocess, "run") as mock_run:
                rc = self.controller.cmd_map_book(argparse.Namespace())

            self.assertEqual(rc, 1)
            mock_run.assert_not_called()
            self.assertIn("total_episodes is still pending", output.getvalue())

    def test_map_book_skips_when_source_map_already_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            project.mkdir(parents=True, exist_ok=True)
            novel = root / "novel.md"
            novel.write_text("正文", encoding="utf-8")
            blueprint = project / "book.blueprint.md"
            blueprint.write_text(
                "# Book Blueprint\n"
                "- extraction_status: extracted\n"
                "- recommended_total_episodes: 48\n"
                "\n## 集数建议\n"
                "- 推荐区间：32-48集\n"
                "- 最终采用：48集\n"
                "- 可独立成集戏剧节点：误认入局、真千金确认、身份掉马、总裁站队\n"
                "- 应合并压缩的内容：重复羞辱、重复试探、重复求和\n"
                "- 为什么不是更短/更长：过短会挤压反转，过长会导致同型情绪注水\n"
                "\n## 主线\n已填写\n",
                encoding="utf-8",
            )
            source_map = project / "source.map.md"
            source_map.write_text(
                "# Source Map\n"
                "- mapping_status: complete\n\n"
                "## Batch 01 (EP01-05): 示例\n",
                encoding="utf-8",
            )
            manifest = project / "run.manifest.md"
            manifest.write_text(
                "# Run Manifest\n"
                "- source_file: novel.md\n"
                "- total_episodes: 48\n"
                "- batch_size: 5\n"
                "- adaptation_strategy: original_fidelity\n"
                "- dialogue_adaptation_intensity: light\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest), \
                 mock.patch.object(self.controller, "_append_log") as mock_log, \
                 mock.patch.object(self.controller.subprocess, "run") as mock_run:
                rc = self.controller.cmd_map_book(argparse.Namespace(force=False))

            self.assertEqual(rc, 0)
            mock_run.assert_not_called()
            self.assertIn("Skip: existing source.map.md is already complete", output.getvalue())
            self.assertEqual(mock_log.call_args.args[3], "map-book")
            self.assertEqual(mock_log.call_args.args[4], "↷")


class SourceMapParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_parse_source_map_supports_current_fixture_format(self) -> None:
        fixture = FIXTURES / "source_map.current.md"
        with mock.patch.object(self.controller, "SOURCE_MAP", fixture):
            parsed = self.controller._parse_source_map()

        self.assertIn("batch01", parsed)
        self.assertEqual(parsed["batch01"]["episodes"], ["EP-01", "EP-02"])
        self.assertEqual(parsed["batch01"]["episode_data"]["EP-01"]["source_span"], "第1章")

    def test_parse_source_map_supports_legacy_fixture_format(self) -> None:
        fixture = FIXTURES / "source_map.legacy.md"
        with mock.patch.object(self.controller, "SOURCE_MAP", fixture):
            parsed = self.controller._parse_source_map()

        self.assertIn("batch01", parsed)
        self.assertEqual(parsed["batch01"]["episodes"], ["EP-01", "EP-02"])
        self.assertEqual(parsed["batch01"]["episode_data"]["EP-02"]["ending_function"], "")

    def test_compute_verify_tiers_supports_current_fixture_format(self) -> None:
        fixture = FIXTURES / "source_map.current.md"
        with mock.patch.object(self.controller, "SOURCE_MAP", fixture), \
             mock.patch.object(self.controller, "_read_manifest", return_value={"key_episodes": ""}):
            full, standard, light, unmapped = self.controller._compute_verify_tiers(["EP-01", "EP-02"])

        self.assertEqual(full, ["EP-01"])
        self.assertEqual(standard, ["EP-02"])
        self.assertEqual(light, [])
        self.assertEqual(unmapped, [])

    def test_compute_verify_tiers_supports_legacy_fixture_format(self) -> None:
        fixture = FIXTURES / "source_map.legacy.md"
        with mock.patch.object(self.controller, "SOURCE_MAP", fixture), \
             mock.patch.object(self.controller, "_read_manifest", return_value={"key_episodes": ""}):
            full, standard, light, unmapped = self.controller._compute_verify_tiers(["EP-01", "EP-02"])

        self.assertEqual(full, ["EP-01"])
        self.assertEqual(standard, ["EP-02"])
        self.assertEqual(light, [])
        self.assertEqual(unmapped, [])


class CleanCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_clean_resets_runtime_data_but_preserves_source_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness = root / "harness"
            project = harness / "project"
            state = project / "state"
            locks = project / "locks"
            drafts = root / "drafts" / "episodes"
            episodes = root / "episodes"
            batch_briefs = project / "batch-briefs"
            reviews = project / "reviews"
            prompts = project / "prompts"
            releases = project / "releases"
            release_journals = releases / "journals"
            output_dir = root / "output"
            run_manifest = project / "run.manifest.md"
            run_log = state / "run.log.md"
            source_map = project / "source.map.md"
            release_index = releases / "release.index.json"
            gold_set = releases / "gold-set.json"
            for path in [state, locks, drafts, episodes, batch_briefs, reviews, prompts, releases, output_dir]:
                path.mkdir(parents=True, exist_ok=True)

            (drafts / "EP-01.md").write_text("draft", encoding="utf-8")
            (episodes / "EP-01.md").write_text("published", encoding="utf-8")
            (batch_briefs / "batch01_EP01-05.md").write_text("brief", encoding="utf-8")
            (locks / "verify-EP-01.json").write_text("{}", encoding="utf-8")
            (locks / "retry-EP-01.count").write_text("2", encoding="utf-8")
            (locks / "batch.lock").write_text("status: locked\nowner: controller:batch01\n", encoding="utf-8")
            (releases / "staging").mkdir(exist_ok=True)
            release_index.write_text('{"episodes": {"EP-01": {"release_status": "gold"}}}', encoding="utf-8")
            gold_set.write_text('{"episodes": ["EP-01"]}', encoding="utf-8")
            run_manifest.write_text(
                "# Run Manifest\n\n"
                "- run_status: active\n"
                "- active_batch: batch03_promoted\n\n"
                "## Current Runtime\n"
                "- current batch brief: harness/project/batch-briefs/batch03_EP11-15.md\n",
                encoding="utf-8",
            )
            source_map.write_text("# Source Map\n\nKEEP ME\n", encoding="utf-8")
            for name in [
                "script.progress.md",
                "story.state.md",
                "relationship.board.md",
                "open_loops.md",
                "quality.anchor.md",
                "process.memory.md",
            ]:
                (state / name).write_text(f"# stale {name}\n\nold content\n", encoding="utf-8")
            run_log.write_text("# stale log\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "HARNESS", harness), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "EPISODES", episodes), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "PROMPTS", prompts), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.controller, "RUN_LOG", run_log), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "RELEASES", releases), \
                 mock.patch.object(self.controller, "RELEASE_JOURNALS", release_journals), \
                 mock.patch.object(self.controller, "RELEASE_INDEX", release_index), \
                 mock.patch.object(self.controller, "GOLD_SET", gold_set), \
                 mock.patch.object(self.controller, "OUTPUT", output_dir), \
                 mock.patch.object(self.controller, "NOW", "2026-04-15 14:30"):
                result = self.controller.cmd_clean(argparse.Namespace())

            self.assertEqual(result, 0)
            self.assertFalse((drafts / "EP-01.md").exists())
            self.assertFalse((episodes / "EP-01.md").exists())
            self.assertFalse((batch_briefs / "batch01_EP01-05.md").exists())
            self.assertFalse((locks / "verify-EP-01.json").exists())
            self.assertFalse((locks / "retry-EP-01.count").exists())
            self.assertIn("status: unlocked", (locks / "batch.lock").read_text(encoding="utf-8"))
            self.assertIn("status: unlocked", (locks / "episode-XX.lock").read_text(encoding="utf-8"))
            self.assertIn("status: unlocked", (locks / "state.lock").read_text(encoding="utf-8"))
            self.assertFalse(release_index.exists())
            self.assertFalse(gold_set.exists())
            self.assertEqual(source_map.read_text(encoding="utf-8"), "# Source Map\n\nKEEP ME\n")

            manifest = run_manifest.read_text(encoding="utf-8")
            self.assertIn("- active_batch: (none)", manifest)
            self.assertIn("- current batch brief: (none)", manifest)

            self.assertIn("## 项目信息", (state / "script.progress.md").read_text(encoding="utf-8"))
            self.assertIn("## 当前阶段", (state / "story.state.md").read_text(encoding="utf-8"))
            self.assertIn("## Log Entries", run_log.read_text(encoding="utf-8"))
            self.assertTrue((root / "versions" / "rebuild_snapshots").exists())
            self.assertIn("Runtime project data cleared", output.getvalue())


class VerifyIntegrityTests(unittest.TestCase):
    """P1: _verify_draft_integrity must check brief and source_map, not just draft."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()
        self.tmp = tempfile.mkdtemp()
        self.drafts = Path(self.tmp) / "drafts" / "episodes"
        self.drafts.mkdir(parents=True)
        self.briefs = Path(self.tmp) / "batch-briefs"
        self.briefs.mkdir()
        self.smap = Path(self.tmp) / "source.map.md"
        # Write fixtures
        (self.drafts / "EP-01.md").write_text("draft v1", encoding="utf-8")
        (self.briefs / "batch01_EP01-05.md").write_text("episodes: EP-01", encoding="utf-8")
        self.smap.write_text("### EP-01\nsome data", encoding="utf-8")

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sha(self, path: Path) -> str:
        return self.controller._file_sha256(path)

    def _make_verify_result(self) -> dict:
        return {
            "draft_sha256": self._sha(self.drafts / "EP-01.md"),
            "brief_sha256": self._sha(self.briefs / "batch01_EP01-05.md"),
            "source_map_sha256": self._sha(self.smap),
        }

    def test_brief_change_invalidates_verify(self) -> None:
        vr = self._make_verify_result()
        # Modify brief after verify
        (self.briefs / "batch01_EP01-05.md").write_text("episodes: EP-01\nchanged", encoding="utf-8")
        with mock.patch.object(self.controller, "DRAFTS", self.drafts), \
             mock.patch.object(self.controller, "BATCH_BRIEFS", self.briefs), \
             mock.patch.object(self.controller, "SOURCE_MAP", self.smap):
            err = self.controller._verify_draft_integrity("EP-01", vr)
        self.assertIsNotNone(err)
        self.assertIn("batch brief modified", err)

    def test_source_map_change_invalidates_verify(self) -> None:
        vr = self._make_verify_result()
        # Modify source map after verify
        self.smap.write_text("### EP-01\nchanged data", encoding="utf-8")
        with mock.patch.object(self.controller, "DRAFTS", self.drafts), \
             mock.patch.object(self.controller, "BATCH_BRIEFS", self.briefs), \
             mock.patch.object(self.controller, "SOURCE_MAP", self.smap):
            err = self.controller._verify_draft_integrity("EP-01", vr)
        self.assertIsNotNone(err)
        self.assertIn("source.map.md modified", err)

    def test_unchanged_passes(self) -> None:
        vr = self._make_verify_result()
        with mock.patch.object(self.controller, "DRAFTS", self.drafts), \
             mock.patch.object(self.controller, "BATCH_BRIEFS", self.briefs), \
             mock.patch.object(self.controller, "SOURCE_MAP", self.smap):
            err = self.controller._verify_draft_integrity("EP-01", vr)
        self.assertIsNone(err)


class VerifyDoneBriefFailureTests(unittest.TestCase):
    """P1: _write_verify_result must not crash when no brief is found."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_write_verify_result_no_brief_no_crash(self) -> None:
        """When _find_brief_for_episode returns '', should warn, not PermissionError."""
        with tempfile.TemporaryDirectory() as tmp:
            drafts = Path(tmp) / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            (drafts / "EP-99.md").write_text("test", encoding="utf-8")
            locks = Path(tmp) / "locks"
            locks.mkdir()
            briefs = Path(tmp) / "batch-briefs"
            briefs.mkdir()
            smap = Path(tmp) / "source.map.md"
            smap.write_text("", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "LOCKS", locks), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", briefs), \
                 mock.patch.object(self.controller, "SOURCE_MAP", smap):
                # Should not raise PermissionError
                self.controller._write_verify_result("EP-99", "STANDARD", "PASS", reviewer="aligner")
            self.assertIn("WARNING", output.getvalue())
            # Verify result should still be written
            vr_path = locks / "verify-EP-99.json"
            self.assertTrue(vr_path.exists())
            import json
            data = json.loads(vr_path.read_text(encoding="utf-8"))
            self.assertEqual(data["brief_sha256"], "")
            self.assertEqual(data["aligner_status"], "PASS")
            self.assertEqual(data["source_compare_status"], "MISSING")


class MetadataLintFieldTests(unittest.TestCase):
    """P2: _build_episode_metadata must read actual lint output structure."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_metadata_reads_checks_subkeys(self) -> None:
        lint_payload = {
            "status": "fail",
            "checks": {
                "episode_failures": ["too_few_scenes"],
                "scene_failures": [{"scene": 1, "rule": "x"}],
                "warnings": ["metaphor_density_high"],
            },
        }
        verify_result = {"tier": "FULL", "status": "PASS"}
        meta = self.controller._build_episode_metadata(
            episode="EP-01",
            batch_id="batch01",
            brief_path=Path("brief.md"),
            lint_payload=lint_payload,
            verify_result=verify_result,
        )
        self.assertEqual(meta["episode_failures"], ["too_few_scenes"])
        self.assertEqual(meta["scene_failures"], [{"scene": 1, "rule": "x"}])
        self.assertEqual(meta["warnings"], ["metaphor_density_high"])
        # Old wrong keys should not be present
        self.assertNotIn("contract_failures", meta)
        self.assertNotIn("craft_flags", meta)
        self.assertNotIn("style_warnings", meta)

    def test_metadata_handles_empty_lint(self) -> None:
        meta = self.controller._build_episode_metadata(
            episode="EP-01",
            batch_id="batch01",
            brief_path=Path("brief.md"),
            lint_payload={},
            verify_result={},
        )
        self.assertEqual(meta["episode_failures"], [])
        self.assertEqual(meta["scene_failures"], [])
        self.assertEqual(meta["warnings"], [])


class StatusGoldDisplayTests(unittest.TestCase):
    """P2: cmd_status must read release.index.json and gold-set.json."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_status_shows_gold_and_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            episodes_dir = tmp_path / "episodes"
            episodes_dir.mkdir()
            (episodes_dir / "EP-01.md").write_text("gold ep", encoding="utf-8")
            (episodes_dir / "EP-11.md").write_text("legacy ep", encoding="utf-8")
            releases_dir = tmp_path / "releases"
            releases_dir.mkdir()
            locks_dir = tmp_path / "locks"
            locks_dir.mkdir()
            retries_dir = tmp_path / "retries"
            retries_dir.mkdir()

            import json
            release_index = {
                "episodes": {
                    "EP-01": {
                        "release_status": "gold",
                        "source_batch": "batch01",
                    },
                    "EP-11": {
                        "release_status": "legacy",
                    },
                },
            }
            gold_set = {"episodes": ["EP-01"]}
            (releases_dir / "release.index.json").write_text(
                json.dumps(release_index), encoding="utf-8",
            )
            (releases_dir / "gold-set.json").write_text(
                json.dumps(gold_set), encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "EPISODES", episodes_dir), \
                 mock.patch.object(self.controller, "RELEASE_INDEX", releases_dir / "release.index.json"), \
                 mock.patch.object(self.controller, "GOLD_SET", releases_dir / "gold-set.json"), \
                 mock.patch.object(self.controller, "LOCKS", locks_dir), \
                 mock.patch.object(self.controller, "RETRY_DIR", retries_dir), \
                 mock.patch.object(self.controller, "DRAFTS", tmp_path / "drafts"), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={}):
                result = self.controller.cmd_status(argparse.Namespace())

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("EP-01.md", text)
            self.assertIn("gold", text)
            self.assertIn("batch=batch01", text)
            self.assertIn("EP-11.md", text)
            self.assertIn("legacy", text)
            self.assertIn("Gold set: EP-01", text)
            # Must NOT show old "UNTRACKED" label for tracked episodes
            self.assertNotIn("UNTRACKED", text)

    def test_status_shows_batch_overview_with_runtime_authority_and_review_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "harness" / "project"
            state = project / "state"
            batch_status_dir = state / "batch-status"
            reviews = project / "reviews"
            release_journals = project / "releases" / "journals"
            batch_briefs = project / "batch-briefs"
            episodes_dir = tmp_path / "episodes"
            locks_dir = tmp_path / "locks"
            retries_dir = tmp_path / "retries"
            for path in [batch_status_dir, reviews, release_journals, batch_briefs, episodes_dir, locks_dir, retries_dir]:
                path.mkdir(parents=True, exist_ok=True)

            (batch_briefs / "batch01_EP01-02.md").write_text(
                "# Batch Brief\n- owned episodes: EP-01, EP-02\n",
                encoding="utf-8",
            )
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "review_pending",
                        "status": "BLOCKED",
                        "episodes": ["EP-01", "EP-02"],
                        "brief_path": "harness/project/batch-briefs/batch01_EP01-02.md",
                        "batch_review_status": "PENDING",
                        "updated_at": "2026-04-19 00:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (reviews / "batch01.review.json").write_text(
                json.dumps({"batch_id": "batch01", "status": "PENDING"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (release_journals / "batch01.promote.json").write_text(
                json.dumps({"batch_id": "batch01", "phase": "publishing", "completed": False}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "RELEASE_JOURNALS", release_journals), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "EPISODES", episodes_dir), \
                 mock.patch.object(self.controller, "LOCKS", locks_dir), \
                 mock.patch.object(self.controller, "RETRY_DIR", retries_dir), \
                 mock.patch.object(self.controller, "DRAFTS", tmp_path / "drafts"), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={}):
                result = self.controller.cmd_status(argparse.Namespace())

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("=== Batch Overview ===", text)
            self.assertIn("batch01: phase=review_pending, status=BLOCKED, batch_review=PENDING", text)
            self.assertIn("review_artifact=present", text)
            self.assertIn("promote_journal=incomplete:publishing", text)
            self.assertIn("authority=runtime", text)

    def test_status_surfaces_batch_review_reason_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "harness" / "project"
            state = project / "state"
            batch_status_dir = state / "batch-status"
            reviews = project / "reviews"
            batch_briefs = project / "batch-briefs"
            episodes_dir = tmp_path / "episodes"
            locks_dir = tmp_path / "locks"
            retries_dir = tmp_path / "retries"
            for path in [batch_status_dir, reviews, batch_briefs, episodes_dir, locks_dir, retries_dir]:
                path.mkdir(parents=True, exist_ok=True)

            (batch_briefs / "batch02_EP06-10.md").write_text(
                "# Batch Brief\n- owned episodes: EP-06\n",
                encoding="utf-8",
            )
            (batch_status_dir / "batch02.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch02",
                        "phase": "review_pending",
                        "status": "BLOCKED",
                        "episodes": ["EP-06"],
                        "brief_path": "harness/project/batch-briefs/batch02_EP06-10.md",
                        "batch_review_status": "FAIL",
                        "updated_at": "2026-04-19 00:00",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (reviews / "batch02.review.json").write_text(
                json.dumps(
                    {"batch_id": "batch02", "status": "FAIL", "reason": "source drift in reveal scene"},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
                 mock.patch.object(self.controller, "EPISODES", episodes_dir), \
                 mock.patch.object(self.controller, "LOCKS", locks_dir), \
                 mock.patch.object(self.controller, "RETRY_DIR", retries_dir), \
                 mock.patch.object(self.controller, "DRAFTS", tmp_path / "drafts"), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={}):
                result = self.controller.cmd_status(argparse.Namespace())

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("batch02: phase=review_pending, status=BLOCKED, batch_review=FAIL", text)
            self.assertIn("review_reason=source drift in reveal scene", text)

    def test_next_prioritizes_incomplete_promote_journal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = tmp_path / "state"
            batch_status_dir = state / "batch-status"
            journals = tmp_path / "releases" / "journals"
            batch_status_dir.mkdir(parents=True, exist_ok=True)
            journals.mkdir(parents=True, exist_ok=True)
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "review_passed",
                        "status": "ACTIVE",
                        "episodes": ["EP-01", "EP-02"],
                        "batch_review_status": "PASS",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (journals / "batch01.promote.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "publishing",
                        "completed": False,
                        "published_episodes": ["EP-01"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "RELEASE_JOURNALS", journals), \
                 mock.patch.object(
                     self.controller,
                     "_parse_source_map",
                     return_value={"batch01": {"episodes": ["EP-01", "EP-02"], "source_range": "ch1"}},
                 ), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={"active_batch": "batch01"}), \
                 mock.patch.object(self.controller, "_is_locked", return_value=False):
                rc = self.controller.cmd_next(argparse.Namespace())

            self.assertEqual(rc, 0)
            text = output.getvalue()
            self.assertIn("=== Promote Recovery Required: batch01 ===", text)
            self.assertIn("Journal phase: publishing", text)
            self.assertIn("To resume: .\\~promote.cmd batch01", text)

    def test_next_prioritizes_batch_review_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = tmp_path / "state"
            batch_status_dir = state / "batch-status"
            reviews = tmp_path / "reviews"
            batch_status_dir.mkdir(parents=True, exist_ok=True)
            reviews.mkdir(parents=True, exist_ok=True)
            (batch_status_dir / "batch01.status.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch01",
                        "phase": "review_pending",
                        "status": "BLOCKED",
                        "episodes": ["EP-01", "EP-02"],
                        "batch_review_status": "MISSING",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output), \
                 mock.patch.object(self.controller, "STATE", state), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status_dir), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(
                     self.controller,
                     "_parse_source_map",
                     return_value={"batch01": {"episodes": ["EP-01", "EP-02"], "source_range": "ch1"}},
                 ), \
                 mock.patch.object(self.controller, "_read_manifest", return_value={"active_batch": "batch01"}), \
                 mock.patch.object(self.controller, "_is_locked", return_value=False):
                rc = self.controller.cmd_next(argparse.Namespace())

            self.assertEqual(rc, 0)
            text = output.getvalue()
            self.assertIn("=== Current Blocker: batch01 ===", text)
            self.assertIn("batch review artifact missing", text)
            self.assertIn(".\\~check.cmd batch01", text)


class BatchBriefAuthoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_generate_batch_brief_uses_writer_authority_instead_of_source_priority(self) -> None:
        batch_info = {
            "episodes": ["EP-01"],
            "ep_start": "EP-01",
            "ep_end": "EP-01",
            "source_range": "ch1",
            "episode_data": {
                "EP-01": {
                    "source_span": "ch1",
                    "must_keep": "【信息】误认 -> 【关系】拒认 -> 【动作】带走 -> 【钩子】卷入",
                    "must_not": "不能提前认亲",
                    "ending_function": "reveal_pending",
                }
            },
        }

        with mock.patch.object(self.controller, "_read_manifest", return_value={}):
            brief = self.controller._generate_batch_brief("batch01", batch_info)

        self.assertIn("## Writer Authority", brief)
        self.assertIn("收尾上下文", brief)
        self.assertIn("`harness/project/source.map.md`：决定 source 顺序、knowledge_boundary、must-not-add、must-not-jump 边界", brief)
        self.assertNotIn("## Source Priority", brief)
        self.assertNotIn("## Function Policy", brief)
        self.assertNotIn("功能目标", brief)


def _override_test_verify_plan_cli_removed(self) -> None:
    root = self._make_cli_workspace()
    result = subprocess.run(
        [sys.executable, str(root / "_ops" / "controller.py"), "verify-plan", "batch01"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("invalid choice", result.stderr)


def _override_test_compute_review_focus_generated_markdown(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_map = Path(tmp) / "source.map.md"
        source_map.write_text(
            "# Source Map\n\n"
            "### EP-01\n"
            "**source_chapter_span**: ch1\n"
            "**must_keep_beats**:\n- 【信息】误认\n- 【动作】带走\n- 【钩子】卷入\n\n"
            "### EP-02\n"
            "**source_chapter_span**: ch2\n"
            "**must_keep_beats**:\n- 【信息】入局\n- 【动作】对抗\n- 【钩子】升级\n",
            encoding="utf-8",
        )
        with mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
             mock.patch.object(self.controller, "_read_manifest", return_value={"key_episodes": "EP-01"}):
            focus = self.controller._compute_review_focus(["EP-01", "EP-02"])
    self.assertEqual(focus["deep"], ["EP-01"])
    self.assertEqual(focus["standard"], ["EP-02"])
    self.assertEqual(focus["light"], [])
    self.assertEqual(focus["unmapped"], [])


def _override_test_prepare_batch_start_reads_generated_brief_before_status_sync(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        batch_briefs = root / "batch-briefs"
        source_map = root / "source.map.md"
        batch_briefs.mkdir(parents=True, exist_ok=True)
        source_map.write_text("# Source Map\n", encoding="utf-8")
        batch_info = {
            "episodes": ["EP-01", "EP-02"],
            "ep_start": "EP-01",
            "ep_end": "EP-02",
            "batch_num": "01",
            "source_range": "ch1 ~ ch2",
            "episode_data": {
                "EP-01": {"source_span": "ch1", "must_keep": "【信息】误认", "must_not": "", "ending_function": "confrontation_pending"},
                "EP-02": {"source_span": "ch2", "must_keep": "【动作】入局", "must_not": "", "ending_function": "confrontation_pending"},
            },
        }
        status_updates: list[dict[str, object]] = []
        with mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
             mock.patch.object(self.controller, "BATCH_BRIEFS", batch_briefs), \
             mock.patch.object(self.controller, "_book_blueprint_quality_issues", return_value=[]), \
             mock.patch.object(self.controller, "_source_map_quality_issues", return_value=[]), \
             mock.patch.object(self.controller, "_parse_source_map", return_value={"batch01": batch_info}), \
             mock.patch.object(self.controller, "_is_locked", return_value=False), \
             mock.patch.object(self.controller, "_find_batch_brief", return_value=None), \
             mock.patch.object(self.controller, "_generate_batch_brief", return_value="# Batch Brief\n- owned episodes: EP-01, EP-02\n"), \
             mock.patch.object(self.controller, "_read_batch_brief", return_value={"episodes": ["EP-01", "EP-02"]}), \
             mock.patch.object(self.controller, "_set_batch_status"), \
             mock.patch.object(self.controller, "_write_lock"), \
             mock.patch.object(self.controller, "_set_manifest_field"), \
             mock.patch.object(self.controller, "_append_log"), \
             mock.patch.object(self.controller, "_clear_retry_count"), \
             mock.patch.object(self.controller, "_compute_review_focus", return_value={"deep": ["EP-01"], "standard": ["EP-02"], "light": [], "unmapped": []}), \
             mock.patch.object(
                 self.controller,
                 "_upsert_batch_status",
                 side_effect=lambda batch_id, **kwargs: status_updates.append({"batch_id": batch_id, **kwargs}),
             ):
            prepared = self.controller._prepare_batch_start("batch01")
            self.assertIsNotNone(prepared)
            brief_path, _, episodes = prepared
            self.assertTrue(brief_path.exists())
            self.assertEqual(episodes, ["EP-01", "EP-02"])
            self.assertGreaterEqual(len(status_updates), 2)
            self.assertEqual(status_updates[0]["episodes"], ["EP-01", "EP-02"])
            self.assertEqual(status_updates[1]["episodes"], ["EP-01", "EP-02"])


def _override_test_check_uses_batch_review_cli(self) -> None:
    args = argparse.Namespace(batch_id="batch01")
    with mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-01"])), \
         mock.patch.object(self.controller, "_upsert_batch_status") as mock_status, \
         mock.patch.object(self.controller, "cmd_batch_review", return_value=0) as mock_review:
        result = self.controller.cmd_check(args)
    self.assertEqual(result, 0)
    mock_review.assert_called_once_with(args)
    mock_status.assert_called_once()
    self.assertEqual(mock_status.call_args.kwargs["phase"], "review_pending")
    self.assertEqual(mock_status.call_args.kwargs["batch_review_status"], "PENDING")


def _override_test_promote_uses_batch_id_for_manifest_and_log(self) -> None:
    args = argparse.Namespace(batch_id="batch01")
    with mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-01"])), \
         mock.patch.object(self.controller, "_require_batch_review_pass", return_value=(True, "")), \
         mock.patch.object(self.controller, "_is_locked", return_value=False), \
         mock.patch.object(self.controller, "_promote_batch", return_value=(0, {})) as mock_promote, \
         mock.patch.object(self.controller, "_set_batch_status"), \
         mock.patch.object(self.controller, "_upsert_batch_status"), \
         mock.patch.object(self.controller, "_set_manifest_field") as mock_manifest, \
         mock.patch.object(self.controller, "_write_lock"), \
         mock.patch.object(self.controller, "_append_log") as mock_log, \
         mock.patch.object(self.controller, "_clear_retry_count"), \
         mock.patch.object(self.controller, "_export_outputs", return_value={"episodes": 1}):
        result = self.controller.cmd_promote(args)
    self.assertEqual(result, 0)
    mock_promote.assert_called_once_with("batch01", Path("brief.md"), ["EP-01"])
    mock_manifest.assert_called_once_with("active_batch", "batch01_promoted")
    self.assertEqual(mock_log.call_args.args[0], "batch01")


def _override_test_metadata_reads_review_fields(self) -> None:
    with mock.patch.object(self.controller, "_read_batch_review", return_value={"status": "PASS", "reviewer": "codex", "warning_families": ["imagery_dense"]}):
        meta = self.controller._build_episode_metadata(
            episode="EP-01",
            batch_id="batch01",
            brief_path=Path("brief.md"),
        )
    self.assertEqual(meta["review_status"], "PASS")
    self.assertEqual(meta["reviewer"], "codex")
    self.assertEqual(meta["warnings"], ["imagery_dense"])


def _override_test_metadata_handles_empty_review(self) -> None:
    with mock.patch.object(self.controller, "_read_batch_review", return_value=None):
        meta = self.controller._build_episode_metadata(
            episode="EP-01",
            batch_id="batch01",
            brief_path=Path("brief.md"),
        )
    self.assertEqual(meta["review_status"], "MISSING")
    self.assertEqual(meta["reviewer"], "")
    self.assertEqual(meta["warnings"], [])


def _override_test_promote_batch_writes_completed_journal(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        project = root / "harness" / "project"
        releases = project / "releases"
        journals = releases / "journals"
        staging = releases / "staging"
        drafts = root / "drafts" / "episodes"
        published = root / "episodes"
        brief = project / "batch-briefs" / "batch01_EP01-05.md"
        for path in [journals, staging, drafts, published, brief.parent]:
            path.mkdir(parents=True, exist_ok=True)
        (drafts / "EP-01.md").write_text("draft one", encoding="utf-8")
        brief.write_text("# brief", encoding="utf-8")
        with mock.patch.object(self.controller, "ROOT", root), \
             mock.patch.object(self.controller, "PROJECT", project), \
             mock.patch.object(self.controller, "RELEASES", releases), \
             mock.patch.object(self.controller, "RELEASE_JOURNALS", journals), \
             mock.patch.object(self.controller, "RELEASE_INDEX", releases / "release.index.json"), \
             mock.patch.object(self.controller, "GOLD_SET", releases / "gold-set.json"), \
             mock.patch.object(self.controller, "DRAFTS", drafts), \
             mock.patch.object(self.controller, "EPISODES", published), \
             mock.patch.object(self.controller, "NOW", "2026-04-19 20:10"), \
             mock.patch.object(self.controller, "_read_batch_review", return_value={"status": "PASS", "reviewer": "codex", "warning_families": []}):
            rc, _ = self.controller._promote_batch("batch01", brief, ["EP-01"])
        self.assertEqual(rc, 0)
        self.assertTrue((published / "EP-01.md").exists())
        self.assertTrue((published / "EP-01.meta.json").exists())
        journal = json.loads((journals / "batch01.promote.json").read_text(encoding="utf-8"))
        self.assertTrue(journal["completed"])
        self.assertEqual(journal["phase"], "completed")
        self.assertEqual(journal["published_episodes"], ["EP-01"])


def _override_test_promote_batch_resumes_from_partial_journal(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        project = root / "harness" / "project"
        releases = project / "releases"
        journals = releases / "journals"
        stage_root = releases / "staging" / "batch01-resume"
        drafts = root / "drafts" / "episodes"
        published = root / "episodes"
        brief = project / "batch-briefs" / "batch01_EP01-05.md"
        for path in [journals, stage_root, drafts, published, brief.parent]:
            path.mkdir(parents=True, exist_ok=True)
        brief.write_text("# brief", encoding="utf-8")
        (drafts / "EP-01.md").write_text("draft one", encoding="utf-8")
        (drafts / "EP-02.md").write_text("draft two", encoding="utf-8")
        (published / "EP-01.md").write_text("published one", encoding="utf-8")
        (published / "EP-01.meta.json").write_text("{}", encoding="utf-8")
        (stage_root / "EP-02.md").write_text("draft two", encoding="utf-8")
        (stage_root / "EP-02.meta.json").write_text("{}", encoding="utf-8")
        (stage_root / "release.index.json").write_text(
            json.dumps({"episodes": {"EP-01": {"release_status": "gold"}, "EP-02": {"release_status": "gold"}}}),
            encoding="utf-8",
        )
        (stage_root / "gold-set.json").write_text(json.dumps({"episodes": ["EP-01", "EP-02"]}), encoding="utf-8")
        (journals / "batch01.promote.json").write_text(
            json.dumps(
                {
                    "batch_id": "batch01",
                    "episodes": ["EP-01", "EP-02"],
                    "phase": "publishing",
                    "completed": False,
                    "stage_root": "harness/project/releases/staging/batch01-resume",
                    "staged_episode_files": {
                        "EP-01": "harness/project/releases/staging/batch01-resume/EP-01.md",
                        "EP-02": "harness/project/releases/staging/batch01-resume/EP-02.md",
                    },
                    "staged_meta_files": {
                        "EP-01": "harness/project/releases/staging/batch01-resume/EP-01.meta.json",
                        "EP-02": "harness/project/releases/staging/batch01-resume/EP-02.meta.json",
                    },
                    "staged_release_index": "harness/project/releases/staging/batch01-resume/release.index.json",
                    "staged_gold_set": "harness/project/releases/staging/batch01-resume/gold-set.json",
                    "published_episodes": ["EP-01"],
                    "release_files_written": False,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        with mock.patch.object(self.controller, "ROOT", root), \
             mock.patch.object(self.controller, "PROJECT", project), \
             mock.patch.object(self.controller, "RELEASES", releases), \
             mock.patch.object(self.controller, "RELEASE_JOURNALS", journals), \
             mock.patch.object(self.controller, "RELEASE_INDEX", releases / "release.index.json"), \
             mock.patch.object(self.controller, "GOLD_SET", releases / "gold-set.json"), \
             mock.patch.object(self.controller, "DRAFTS", drafts), \
             mock.patch.object(self.controller, "EPISODES", published), \
             mock.patch.object(self.controller, "NOW", "2026-04-19 20:11"):
            rc, _ = self.controller._promote_batch("batch01", brief, ["EP-01", "EP-02"])
        self.assertEqual(rc, 0)
        self.assertTrue((published / "EP-02.md").exists())
        journal = json.loads((journals / "batch01.promote.json").read_text(encoding="utf-8"))
        self.assertTrue(journal["completed"])
        self.assertEqual(journal["published_episodes"], ["EP-01", "EP-02"])


def _override_test_start_review_only(self) -> None:
    args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=True, writer_command="writer --batch {batch_id}")
    output = io.StringIO()
    with contextlib.redirect_stdout(output), \
         mock.patch.object(self.controller, "_prepare_batch_start", return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])), \
         mock.patch.object(self.controller, "_sync_state_from_blueprint", return_value=[]), \
         mock.patch.object(self.controller, "_compute_review_focus", return_value={"deep": ["EP-11"], "standard": ["EP-12"], "light": [], "unmapped": []}), \
         mock.patch.object(self.controller, "_guard_quality_anchors", return_value=True), \
         mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
         mock.patch.object(self.controller, "_ensure_batch_review_artifacts", return_value={"status": "PENDING"}) as mock_review, \
         mock.patch.object(self.controller, "_upsert_batch_status") as mock_status:
        result = self.controller.cmd_start(args)
    self.assertEqual(result, 0)
    mock_writer.assert_called_once_with("batch03", ["EP-11", "EP-12"], writer_command="writer --batch {batch_id}", parallelism=1)
    mock_review.assert_called_once_with("batch03", ["EP-11", "EP-12"], brief_path=Path("brief.md"))
    self.assertEqual(mock_status.call_args.kwargs["phase"], "review_pending")
    text = output.getvalue()
    self.assertIn(".\\~review.cmd batch03 PASS --reviewer <name>", text)
    self.assertNotIn("verify-done", text)
    self.assertNotIn("smoke", text.lower())


def _override_test_run_review_gate_only(self) -> None:
    args = argparse.Namespace(batch_id="batch03")
    with mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-11"])), \
         mock.patch.object(self.controller, "_require_batch_review_pass", return_value=(True, "")), \
         mock.patch.object(self.controller, "_do_promote_and_report", return_value=0) as mock_promote:
        result = self.controller.cmd_run(args)
    self.assertEqual(result, 0)
    mock_promote.assert_called_once_with("batch03", Path("brief.md"), ["EP-11"])


def _override_test_run_batch_review_missing(self) -> None:
    args = argparse.Namespace(batch_id="batch03")
    with mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-11"])), \
         mock.patch.object(self.controller, "_require_batch_review_pass", return_value=(False, "ERROR: batch review artifact missing")):
        result = self.controller.cmd_run(args)
    self.assertEqual(result, 1)


def _override_test_legacy_verify_helpers_removed(self) -> None:
    for attr in [
        "_run_lint_gate",
        "_run_verify_gate",
        "_run_smoke_lint_check",
        "_read_verify_result",
        "_write_verify_result",
        "_verify_draft_integrity",
        "_compute_verify_tiers",
        "_verify_tier_for_episode",
        "cmd_verify_done",
        "cmd_source_compare_done",
        "cmd_lint",
        "cmd_gate",
        "cmd_retry",
        "cmd_verify_plan",
    ]:
        self.assertFalse(hasattr(self.controller, attr), attr)


def _override_test_function_metadata_normalization_defaults_without_text_guessing(self) -> None:
    normalized = self.controller._normalize_episode_function_metadata(
        "EP-01",
        {
            "must_keep": "【信息】误认；【动作】强行带走；【钩子】卷入漩涡",
        },
    )
    self.assertEqual(normalized["ending_function"], "")
    self.assertNotIn("irreversibility_level", normalized)
    self.assertNotIn("function_signals", normalized)
    source = Path(self.controller.__file__).read_text(encoding="utf-8")
    self.assertNotIn("def _infer_function_name_from_text", source)
    self.assertNotIn("误认\", \"错认\", \"闯\"", source)


ControllerCliSmokeTests.test_verify_plan_cli_prints_batch_header = _override_test_verify_plan_cli_removed

ControllerHandlerRegressionTests.test_compute_verify_tiers_supports_generated_markdown_format = _override_test_compute_review_focus_generated_markdown
ControllerHandlerRegressionTests.test_prepare_batch_start_reads_generated_brief_before_status_sync = _override_test_prepare_batch_start_reads_generated_brief_before_status_sync
ControllerHandlerRegressionTests.test_check_uses_batch_id_in_verify_done_instructions = _override_test_check_uses_batch_review_cli
ControllerHandlerRegressionTests.test_promote_uses_batch_id_for_manifest_and_log = _override_test_promote_uses_batch_id_for_manifest_and_log

PromoteJournalTests.test_promote_batch_writes_completed_journal = _override_test_promote_batch_writes_completed_journal
PromoteJournalTests.test_promote_batch_resumes_from_partial_journal = _override_test_promote_batch_resumes_from_partial_journal
PromoteJournalTests.test_start_skips_verify_done_examples_for_unmapped_episodes = _override_test_start_review_only
PromoteJournalTests.test_start_retries_smoke_once_in_syntax_first_mode = _override_test_start_review_only
PromoteJournalTests.test_start_stops_after_second_smoke_failure = _override_test_start_review_only
PromoteJournalTests.test_start_retries_smoke_once_for_repairable_hookless_failures = _override_test_start_review_only

RunCommandTests.test_run_missing_verify_fails = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_run_verify_fail_fails = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_run_source_compare_fail_fails = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_run_stale_verify_hash_fails = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_run_does_not_write_verify_pass = _override_test_run_review_gate_only
RunCommandTests.test_verify_done_records_aligner_only_until_source_compare_arrives = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_source_compare_done_completes_overall_verify_status = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_verify_done_persists_note_and_evidence_refs = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_run_fails_on_lint_failure = _override_test_legacy_verify_helpers_removed
RunCommandTests.test_run_fails_when_batch_review_missing = _override_test_run_batch_review_missing
RunCommandTests.test_promote_fails_when_batch_review_is_not_pass = _override_test_run_batch_review_missing

StartCommandTests.test_start_no_longer_auto_promotes = _override_test_start_review_only

SourceMapParsingTests.test_compute_verify_tiers_supports_current_fixture_format = _override_test_compute_review_focus_generated_markdown
SourceMapParsingTests.test_compute_verify_tiers_supports_legacy_fixture_format = _override_test_compute_review_focus_generated_markdown

VerifyIntegrityTests.test_brief_change_invalidates_verify = _override_test_legacy_verify_helpers_removed
VerifyIntegrityTests.test_source_map_change_invalidates_verify = _override_test_legacy_verify_helpers_removed
VerifyIntegrityTests.test_unchanged_passes = _override_test_legacy_verify_helpers_removed
VerifyDoneBriefFailureTests.test_write_verify_result_no_brief_no_crash = _override_test_legacy_verify_helpers_removed

MetadataLintFieldTests.test_metadata_reads_checks_subkeys = _override_test_metadata_reads_review_fields
MetadataLintFieldTests.test_metadata_handles_empty_lint = _override_test_metadata_handles_empty_review
ControllerHandlerRegressionTests.test_function_metadata_normalization_defaults_without_text_guessing = _override_test_function_metadata_normalization_defaults_without_text_guessing


def _override_test_model_cli_execution_removed_from_controller(self) -> None:
    source = Path(self.controller.__file__).read_text(encoding="utf-8")
    self.assertFalse(hasattr(self.controller, "subprocess"))
    self.assertNotIn("writer_command", source)
    self.assertNotIn("JUBEN_WRITER_COMMAND", source)
    self.assertNotIn("subprocess.run", source)


def _override_test_start_review_only_prompt_packet(self) -> None:
    args = argparse.Namespace(batch_id="batch03", prepare_only=False, write=True)
    output = io.StringIO()
    with contextlib.redirect_stdout(output), \
         mock.patch.object(self.controller, "_prepare_batch_start", return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])), \
         mock.patch.object(self.controller, "_sync_state_from_blueprint", return_value=[]), \
         mock.patch.object(self.controller, "_compute_review_focus", return_value={"deep": ["EP-11"], "standard": ["EP-12"], "light": [], "unmapped": []}), \
         mock.patch.object(self.controller, "_guard_quality_anchors", return_value=True), \
         mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
         mock.patch.object(self.controller, "_ensure_batch_review_artifacts", return_value={"status": "PENDING"}) as mock_review, \
         mock.patch.object(self.controller, "_upsert_batch_status") as mock_status:
        result = self.controller.cmd_start(args)
    self.assertEqual(result, 0)
    mock_writer.assert_called_once_with("batch03", ["EP-11", "EP-12"], parallelism=1)
    mock_review.assert_called_once_with("batch03", ["EP-11", "EP-12"], brief_path=Path("brief.md"))
    self.assertEqual(mock_status.call_args.kwargs["phase"], "review_pending")
    self.assertIn("~review.cmd batch03 PASS", output.getvalue())


def _override_test_writer_stage_uses_existing_drafts_without_command(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        drafts = Path(tmp) / "drafts"
        drafts.mkdir()
        (drafts / "EP-11.md").write_text("draft", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "DRAFTS", drafts), \
             mock.patch.object(self.controller, "_upsert_batch_status"):
            result = self.controller._run_writer_stage("batch03", ["EP-11"])
    self.assertEqual(result, 0)
    self.assertIn("existing drafts", output.getvalue())


def _override_test_writer_stage_creates_prompt_packet_when_drafts_missing(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        drafts = root / "drafts" / "episodes"
        prompts = root / "harness" / "project" / "prompts"
        brief_dir = root / "harness" / "project" / "batch-briefs"
        state = root / "harness" / "project" / "state"
        framework = root / "harness" / "framework"
        for path in [drafts, prompts, brief_dir, state, framework]:
            path.mkdir(parents=True, exist_ok=True)
        (root / "novel.md").write_text("第1章\n误认。", encoding="utf-8")
        (root / "harness" / "project" / "source.map.md").write_text(
            "# Source Map\n\n## Batch 03\n### EP11\n**source_chapter_span**: 第1章\n**must-keep_beats**:\n- 【信息】误认\n",
            encoding="utf-8",
        )
        (brief_dir / "batch03_EP11-11.md").write_text("# Batch Brief\n- owned episodes: EP-11\n", encoding="utf-8")
        (framework / "writer-prompt.template.md").write_text(
            "{{reads_block}}\n{{current_episode_beats}}\n", encoding="utf-8"
        )
        (framework / "writer-batch-prompt.template.md").write_text(
            "{{reads_block}}\n{{targets_block}}\n", encoding="utf-8"
        )
        (framework / "write-contract.md").write_text("# contract\n", encoding="utf-8")
        (framework / "writer-style.md").write_text("# style\n", encoding="utf-8")
        (framework / "passing-episode.sample.md").write_text("# sample\n", encoding="utf-8")
        with mock.patch.object(self.controller, "ROOT", root), \
             mock.patch.object(self.controller, "DRAFTS", drafts), \
             mock.patch.object(self.controller, "PROMPTS", prompts), \
             mock.patch.object(self.controller, "_upsert_batch_status"):
            result = self.controller._run_writer_stage("batch03", ["EP-11"])
            self.assertEqual(result, self.controller.WRITER_STAGE_PROMPTS_READY)
            self.assertTrue((prompts / "batch03.EP-11.writer.prompt.md").exists())


BookPipelineCommandTests.test_extract_book_runs_backend_for_manifest_source_file_when_forced = _override_test_model_cli_execution_removed_from_controller
BookPipelineCommandTests.test_extract_book_auto_applies_recommended_total_episodes = _override_test_model_cli_execution_removed_from_controller
BookPipelineCommandTests.test_extract_book_skips_when_blueprint_already_complete = _override_test_model_cli_execution_removed_from_controller
BookPipelineCommandTests.test_map_book_requires_non_placeholder_blueprint = _override_test_model_cli_execution_removed_from_controller
BookPipelineCommandTests.test_map_book_requires_resolved_total_episode_count = _override_test_model_cli_execution_removed_from_controller
BookPipelineCommandTests.test_map_book_skips_when_source_map_already_complete = _override_test_model_cli_execution_removed_from_controller

WriterCommandConfigTests.test_resolve_writer_command_prefers_argument_over_manifest_and_env = _override_test_model_cli_execution_removed_from_controller
WriterCommandConfigTests.test_init_writes_default_writer_command = _override_test_model_cli_execution_removed_from_controller

WriterStageTests.test_writer_stage_uses_existing_drafts_without_command = _override_test_writer_stage_uses_existing_drafts_without_command
WriterStageTests.test_writer_stage_fails_without_command_or_drafts = _override_test_writer_stage_creates_prompt_packet_when_drafts_missing
WriterStageTests.test_writer_stage_runs_configured_command_and_requires_drafts = _override_test_writer_stage_creates_prompt_packet_when_drafts_missing
WriterStageTests.test_writer_stage_formats_parallelism_and_syntax_first_placeholders = _override_test_writer_stage_creates_prompt_packet_when_drafts_missing
WriterStageTests.test_writer_stage_force_rewrite_removes_existing_draft_before_running = _override_test_writer_stage_creates_prompt_packet_when_drafts_missing
WriterStageTests.test_writer_stage_rejects_shell_metacharacters_in_command_template = _override_test_model_cli_execution_removed_from_controller

PromoteJournalTests.test_start_skips_verify_done_examples_for_unmapped_episodes = _override_test_start_review_only_prompt_packet
PromoteJournalTests.test_start_retries_smoke_once_in_syntax_first_mode = _override_test_start_review_only_prompt_packet
PromoteJournalTests.test_start_stops_after_second_smoke_failure = _override_test_start_review_only_prompt_packet
PromoteJournalTests.test_start_retries_smoke_once_for_repairable_hookless_failures = _override_test_start_review_only_prompt_packet
PromoteJournalTests.test_start_write_mode_runs_writer_once_without_smoke_retry = _override_test_start_review_only_prompt_packet

StartCommandTests.test_start_no_longer_auto_promotes = _override_test_start_review_only_prompt_packet
StartCommandTests.test_start_runs_writer_only_with_write_flag = _override_test_start_review_only_prompt_packet


class PolishCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_polish_creates_prompt_packet_without_model_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "harness" / "project"
            framework = root / "harness" / "framework"
            drafts = root / "drafts" / "episodes"
            prompts = project / "prompts"
            reviews = project / "reviews"
            briefs = project / "batch-briefs"
            state = project / "state"
            batch_status = state / "batch-status"
            for path in (framework, drafts, prompts, reviews, briefs, batch_status):
                path.mkdir(parents=True, exist_ok=True)

            (root / "character.md").write_text("# Character\n", encoding="utf-8")
            (root / "voice-anchor.md").write_text("# Voice\n", encoding="utf-8")
            (project / "source.map.md").write_text("# Source Map\n", encoding="utf-8")
            (project / "run.manifest.md").write_text(
                "# Run Manifest\n\n- quality_mode: premium\n",
                encoding="utf-8",
            )
            (framework / "polish-prompt.template.md").write_text(
                "{{batch_id}}\n{{quality_mode}}\n{{draft_paths}}\n{{polish_report_path}}\n",
                encoding="utf-8",
            )
            (framework / "writer-style.md").write_text("# style\n", encoding="utf-8")
            (framework / "write-contract.md").write_text("# contract\n", encoding="utf-8")
            (briefs / "batch03_EP11-12.md").write_text(
                "# Batch Brief\n- owned episodes: EP-11, EP-12\n",
                encoding="utf-8",
            )
            (drafts / "EP-11.md").write_text("draft 11", encoding="utf-8")
            (drafts / "EP-12.md").write_text("draft 12", encoding="utf-8")

            with mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "FRAMEWORK", framework), \
                 mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller, "PROMPTS", prompts), \
                 mock.patch.object(self.controller, "REVIEWS", reviews), \
                 mock.patch.object(self.controller, "BATCH_BRIEFS", briefs), \
                 mock.patch.object(self.controller, "BATCH_STATUS_DIR", batch_status), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", project / "run.manifest.md"), \
                 mock.patch.object(self.controller, "SOURCE_MAP", project / "source.map.md"), \
                 mock.patch.object(self.controller, "POLISH_PROMPT_TEMPLATE", framework / "polish-prompt.template.md"):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    rc = self.controller.cmd_polish(argparse.Namespace(batch_id="batch03"))

            prompt = prompts / "batch03.polish.prompt.md"
            self.assertEqual(rc, self.controller.WRITER_STAGE_PROMPTS_READY)
            self.assertTrue(prompt.exists())
            text = prompt.read_text(encoding="utf-8")
            self.assertIn("premium", text)
            self.assertIn("drafts/episodes/EP-11.md", text)
            self.assertIn("harness/project/reviews/batch03.polish.md", text)
            self.assertIn("Prompt packet ready", output.getvalue())


if __name__ == "__main__":
    unittest.main()
