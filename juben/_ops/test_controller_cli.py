import argparse
import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_SCRIPT = ROOT / "_ops" / "controller.py"


def _load_controller_module():
    spec = importlib.util.spec_from_file_location("controller_under_test", CONTROLLER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ControllerCliSmokeTests(unittest.TestCase):
    def test_verify_plan_cli_prints_batch_header(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CONTROLLER_SCRIPT), "verify-plan", "batch01"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("=== Verify Plan: batch01 ===", result.stdout)

    def test_batch_review_cli_prints_batch_header(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CONTROLLER_SCRIPT), "batch-review", "batch01"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("=== Batch Review: batch01 ===", result.stdout)


class ControllerHandlerRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = _load_controller_module()

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

    def test_finish_uses_batch_id_for_manifest_log_and_next_steps(self) -> None:
        args = argparse.Namespace(batch_id="batch01")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), \
             mock.patch.object(self.controller, "_resolve_batch", return_value=(Path("brief.md"), {}, ["EP-01"])), \
             mock.patch.object(self.controller, "_run_lint_gate", return_value=(True, {"EP-01": {}})), \
             mock.patch.object(self.controller, "_run_verify_gate", return_value=True), \
             mock.patch.object(self.controller, "_is_locked", return_value=False), \
             mock.patch.object(self.controller, "_promote_batch", return_value=(0, {})) as mock_promote, \
             mock.patch.object(self.controller, "_set_batch_status") as mock_set_status, \
             mock.patch.object(self.controller, "_write_lock") as mock_write_lock, \
             mock.patch.object(self.controller, "_clear_retry_count") as mock_clear_retry, \
             mock.patch.object(self.controller, "_append_log") as mock_append_log, \
             mock.patch.object(self.controller, "_set_manifest_field") as mock_set_manifest, \
             mock.patch.object(self.controller, "_validate_state_file", return_value=[]), \
             mock.patch.object(self.controller.random, "sample", return_value=["EP-01"]), \
             mock.patch.object(
                 self.controller,
                 "_parse_source_map",
                 return_value={
                     "batch01": {"ep_start": "EP-01", "ep_end": "EP-01", "source_range": "ch1"},
                     "batch02": {"ep_start": "EP-02", "ep_end": "EP-02", "source_range": "ch2"},
                 },
             ):
            result = self.controller.cmd_finish(args)

        self.assertEqual(result, 0)
        mock_promote.assert_called_once_with("batch01", Path("brief.md"), ["EP-01"], {"EP-01": {}})
        mock_set_status.assert_called_once_with(Path("brief.md"), "promoted")
        mock_write_lock.assert_called_once_with("batch.lock", "unlocked")
        mock_clear_retry.assert_called_once_with("EP-01")
        self.assertEqual(mock_append_log.call_args.args[0], "batch01")
        mock_set_manifest.assert_called_once_with("active_batch", "batch01_promoted")
        self.assertIn("BATCH FINISHED: batch01", output.getvalue())
        self.assertIn("python _ops/controller.py record batch01", output.getvalue())


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


if __name__ == "__main__":
    unittest.main()
