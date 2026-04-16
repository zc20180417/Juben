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


class ControllerHandlerRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

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
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过离书被销毁\n\n"
                "**ending_type**: cliffhanger - 困局加深\n\n"
                "---\n\n"
                "### EP02: 白月光的假面 (2-3 分钟)\n\n"
                "**source_chapter_span**: 第2章后半至第3章\n\n"
                "**must-keep_beats**:\n"
                "- 柳清言登门\n"
                "- 海棠树下对峙\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过柳清言挑衅\n\n"
                "**ending_type**: plot_turn - 被抱入主院\n",
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
        self.assertIn("不能跳过离书被销毁", batches["batch01"]["episode_data"]["EP-01"]["must_not"])
        self.assertEqual(
            batches["batch01"]["episode_data"]["EP-02"]["ending_type"],
            "plot_turn - 被抱入主院",
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
                "**ending_type**: cliffhanger - 困局加深\n\n"
                "---\n\n"
                "### EP02: 白月光的假面 (2-3 分钟)\n\n"
                "**source_chapter_span**: 第2章后半至第3章\n\n"
                "**must-keep_beats**:\n"
                "- 柳清言登门\n\n"
                "**must-not-add / must-not-jump**:\n"
                "- 不能跳过柳清言挑衅\n\n"
                "**ending_type**: plot_turn - 被抱入主院\n",
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
             mock.patch.object(self.controller, "_run_lint_gate", return_value=(True, {"EP-01": {}})), \
             mock.patch.object(self.controller, "_compute_verify_tiers", return_value=(["EP-01"], [], [], [])):
            result = self.controller.cmd_check(args)

        self.assertEqual(result, 0)
        self.assertIn(
            "python _ops/controller.py verify-done EP-01 PASS --tier FULL --batch batch01",
            output.getvalue(),
        )

    def test_promote_uses_batch_id_for_manifest_and_log(self) -> None:
        args = argparse.Namespace(batch_id="batch01")

        with contextlib.redirect_stdout(io.StringIO()), \
             mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-01"])), \
             mock.patch.object(self.controller, "_run_lint_gate", return_value=(True, {"EP-01": {}})), \
             mock.patch.object(self.controller, "_run_verify_gate", return_value=True), \
             mock.patch.object(self.controller, "_is_locked", return_value=False), \
             mock.patch.object(self.controller, "_promote_batch", return_value=(0, {})) as mock_promote, \
             mock.patch.object(self.controller, "_set_batch_status") as mock_set_status, \
             mock.patch.object(self.controller, "_set_manifest_field") as mock_set_manifest, \
             mock.patch.object(self.controller, "_write_lock") as mock_write_lock, \
             mock.patch.object(self.controller, "_clear_retry_count") as mock_clear_retry, \
             mock.patch.object(self.controller, "_append_log") as mock_append_log:
            result = self.controller.cmd_promote(args)

        self.assertEqual(result, 0)
        mock_promote.assert_called_once_with("batch01", Path("brief.md"), ["EP-01"], {"EP-01": {}})
        mock_set_status.assert_called_once_with(Path("brief.md"), "promoted")
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
        self.assertIn("python _ops/controller.py run batch01", output.getvalue())


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
        verify_result = {"episode": "EP-11", "tier": "FULL", "status": "FAIL"}

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
        self.assertIn("verify FAIL", output.getvalue())
        mock_promote.assert_not_called()

    def test_run_stale_verify_hash_fails(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        output = io.StringIO()
        verify_result = {
            "episode": "EP-11",
            "tier": "FULL",
            "status": "PASS",
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
             mock.patch.object(self.controller, "_write_verify_result") as mock_write_verify, \
             mock.patch.object(self.controller, "_append_log") as mock_append_log, \
             mock.patch.object(self.controller, "_promote_batch", return_value=(0, {})) as mock_promote, \
             mock.patch.object(self.controller, "_is_locked", return_value=False), \
             mock.patch.object(self.controller, "_set_batch_status"), \
             mock.patch.object(self.controller, "_write_lock"), \
             mock.patch.object(self.controller, "_clear_retry_count"), \
             mock.patch.object(self.controller, "_set_manifest_field"), \
             mock.patch.object(self.controller, "_validate_state_file", return_value=[]), \
             mock.patch.object(self.controller.random, "sample", return_value=["EP-11"]), \
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

    def test_run_fails_on_lint_failure(self) -> None:
        args = argparse.Namespace(batch_id="batch03")
        with contextlib.redirect_stdout(io.StringIO()), \
             mock.patch.object(self.controller, "_resolve_batch",
                                return_value=(Path("brief.md"), {}, ["EP-11"])), \
             mock.patch.object(self.controller, "_run_lint_gate",
                                return_value=(False, {})):
            result = self.controller.cmd_run(args)
        self.assertEqual(result, 1)


class StartCommandTests(unittest.TestCase):
    """cmd_start: prepare-only escape hatch + writer-stage stop."""

    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_start_prepare_only_skips_writer_and_run(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=True, writer_command=None)
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
        self.assertIn("python _ops/controller.py check batch03", output.getvalue())
        self.assertIn("python _ops/controller.py run batch03", output.getvalue())

    def test_start_no_longer_auto_promotes(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, writer_command="writer --batch {batch_id}")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])) as mock_prepare, \
             mock.patch.object(self.controller, "_warn_unanchored_voice_assets"), \
             mock.patch.object(self.controller, "_run_smoke_lint_check", return_value=(True, {})) as mock_smoke, \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "cmd_run", return_value=0) as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        mock_prepare.assert_called_once_with("batch03")
        self.assertEqual(
            mock_writer.call_args_list,
            [
                mock.call("batch03", ["EP-11"], writer_command="writer --batch {batch_id}", parallelism=1),
                mock.call("batch03", ["EP-12"], writer_command="writer --batch {batch_id}", parallelism=3),
            ],
        )
        mock_smoke.assert_called_once_with("EP-11")
        mock_run.assert_not_called()
        text = output.getvalue()
        self.assertIn("=== Writer Stage Complete ===", text)
        self.assertIn("python _ops/controller.py check batch03", text)
        self.assertIn("python _ops/controller.py run batch03", text)

    def test_start_skips_verify_done_examples_for_unmapped_episodes(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, writer_command="writer --batch {batch_id}")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12"])), \
             mock.patch.object(self.controller, "_compute_verify_tiers",
                               return_value=(["EP-11"], [], [], ["EP-12"])), \
             mock.patch.object(self.controller, "_warn_unanchored_voice_assets"), \
             mock.patch.object(self.controller, "_run_smoke_lint_check", return_value=(True, {})), \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0):
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        text = output.getvalue()
        self.assertIn("python _ops/controller.py verify-done EP-11 PASS --tier FULL --batch batch03", text)
        self.assertNotIn("python _ops/controller.py verify-done EP-12", text)
        self.assertIn("⚠ Unmapped episodes: EP-12", text)

    def test_start_retries_smoke_once_in_syntax_first_mode(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, writer_command="writer --batch {batch_id}")
        shell_fail = {
            "checks": {"episode_failures": ["scene_count", "camera_count", "os_vo_count"]},
            "totals": {"scene_count": 0, "camera_count": 0, "os_count": 0, "vo_count": 0},
        }
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12", "EP-13"])), \
             mock.patch.object(self.controller, "_warn_unanchored_voice_assets"), \
             mock.patch.object(self.controller, "_run_smoke_lint_check", side_effect=[(False, shell_fail), (True, shell_fail)]) as mock_smoke, \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "cmd_run", return_value=0) as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 0)
        self.assertEqual(
            mock_writer.call_args_list,
            [
                mock.call("batch03", ["EP-11"], writer_command="writer --batch {batch_id}", parallelism=1),
                mock.call(
                    "batch03",
                    ["EP-11"],
                    writer_command="writer --batch {batch_id}",
                    parallelism=1,
                    syntax_first=True,
                    force_rewrite=True,
                ),
                mock.call("batch03", ["EP-12", "EP-13"], writer_command="writer --batch {batch_id}", parallelism=3),
            ],
        )
        self.assertEqual(mock_smoke.call_count, 2)
        mock_run.assert_not_called()
        self.assertIn("python _ops/controller.py check batch03", output.getvalue())

    def test_start_stops_after_second_smoke_failure(self) -> None:
        args = argparse.Namespace(batch_id="batch03", prepare_only=False, writer_command="writer --batch {batch_id}")
        shell_fail = {
            "checks": {"episode_failures": ["scene_count", "camera_count", "os_vo_count"]},
            "totals": {"scene_count": 0, "camera_count": 0, "os_count": 0, "vo_count": 0},
        }

        with mock.patch.object(self.controller, "_prepare_batch_start",
                               return_value=(Path("brief.md"), {}, ["EP-11", "EP-12", "EP-13"])), \
             mock.patch.object(self.controller, "_warn_unanchored_voice_assets"), \
             mock.patch.object(self.controller, "_run_smoke_lint_check", side_effect=[(False, shell_fail), (False, shell_fail)]), \
             mock.patch.object(self.controller, "_run_writer_stage", return_value=0) as mock_writer, \
             mock.patch.object(self.controller, "cmd_run") as mock_run:
            result = self.controller.cmd_start(args)

        self.assertEqual(result, 1)
        self.assertEqual(
            mock_writer.call_args_list,
            [
                mock.call("batch03", ["EP-11"], writer_command="writer --batch {batch_id}", parallelism=1),
                mock.call(
                    "batch03",
                    ["EP-11"],
                    writer_command="writer --batch {batch_id}",
                    parallelism=1,
                    syntax_first=True,
                    force_rewrite=True,
                ),
            ],
        )
        mock_run.assert_not_called()


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
                self.assertIn("--parallelism 3", command)
                self.assertIn("--syntax-first", command)
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
            self.assertIn("target_episode_minutes: 2", content)
            self.assertIn("episode_minutes_min: 1", content)
            self.assertIn("episode_minutes_max: 3", content)
            self.assertIn("writer_parallelism: 3", content)
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


class BookPipelineCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_extract_book_runs_backend_for_manifest_source_file(self) -> None:
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
                "- recommended_total_episodes: 48\n",
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
                 mock.patch.object(self.controller.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as mock_run:
                rc = self.controller.cmd_extract_book(argparse.Namespace())

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
                "- recommended_total_episodes: 48\n",
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

            with contextlib.redirect_stdout(io.StringIO()), \
                 mock.patch.object(self.controller, "ROOT", root), \
                 mock.patch.object(self.controller, "PROJECT", project), \
                 mock.patch.object(self.controller, "BOOK_BLUEPRINT", blueprint), \
                 mock.patch.object(self.controller, "RUN_MANIFEST", manifest), \
                 mock.patch.object(self.controller.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
                rc = self.controller.cmd_extract_book(argparse.Namespace())

            self.assertEqual(rc, 0)
            content = manifest.read_text(encoding="utf-8")
            self.assertIn("total_episodes: 48", content)
            self.assertIn("recommended_total_episodes: 48", content)
            self.assertIn("episode_count_source: model_recommended", content)

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
        self.assertEqual(parsed["batch01"]["episode_data"]["EP-02"]["ending_type"], "前推力")

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
            releases = project / "releases"
            run_manifest = project / "run.manifest.md"
            run_log = state / "run.log.md"
            source_map = project / "source.map.md"
            release_index = releases / "release.index.json"
            gold_set = releases / "gold-set.json"
            for path in [state, locks, drafts, episodes, batch_briefs, releases]:
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
                 mock.patch.object(self.controller, "RUN_MANIFEST", run_manifest), \
                 mock.patch.object(self.controller, "RUN_LOG", run_log), \
                 mock.patch.object(self.controller, "SOURCE_MAP", source_map), \
                 mock.patch.object(self.controller, "RELEASES", releases), \
                 mock.patch.object(self.controller, "RELEASE_INDEX", release_index), \
                 mock.patch.object(self.controller, "GOLD_SET", gold_set), \
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
                self.controller._write_verify_result("EP-99", "STANDARD", "PASS")
            self.assertIn("WARNING", output.getvalue())
            # Verify result should still be written
            vr_path = locks / "verify-EP-99.json"
            self.assertTrue(vr_path.exists())
            import json
            data = json.loads(vr_path.read_text(encoding="utf-8"))
            self.assertEqual(data["brief_sha256"], "")


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


class LintPayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

    def test_lint_payload_treats_warning_only_episode_as_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            drafts = Path(tmp) / "drafts" / "episodes"
            drafts.mkdir(parents=True)
            (drafts / "EP-11.md").write_text("draft", encoding="utf-8")
            payload = {
                "status": "warn",
                "checks": {
                    "episode_failures": [],
                    "scene_failures": [{"scene": 1, "title": "书房", "failures": []}],
                    "warnings": ["hookless_final_scene"],
                },
                "totals": {"scene_count": 2},
            }
            completed = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=json.dumps(payload, ensure_ascii=False),
                stderr="",
            )

            with mock.patch.object(self.controller, "DRAFTS", drafts), \
                 mock.patch.object(self.controller.subprocess, "run", return_value=completed):
                is_pass, data = self.controller._lint_episode_payload("EP-11")

        self.assertTrue(is_pass)
        self.assertEqual(data["status"], "warn")


if __name__ == "__main__":
    unittest.main()
