from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from v3_webui.runner import (
    DEFAULT_JUBEN_ROOT,
    ROOT,
    JobStore,
    RunnerError,
    build_codex_exec_command,
    build_juben_operation,
    resolve_under_root,
    save_novel_input,
    start_codex_job,
)
from v3_webui import pipeline_cli


class RunnerTests(unittest.TestCase):
    def test_builds_juben_whitelisted_command(self) -> None:
        command = build_juben_operation("start_write", batch_id="batch01")
        self.assertEqual(command[-3:], ["start", "batch01", "--write"])

    def test_rejects_unknown_juben_operation(self) -> None:
        with self.assertRaises(RunnerError):
            build_juben_operation("shell")

    def test_rejects_paths_outside_workspace(self) -> None:
        with self.assertRaises(RunnerError):
            resolve_under_root("..\\outside.md", root=ROOT)

    def test_codex_command_uses_exec_stdin_and_workspace(self) -> None:
        command = build_codex_exec_command(model="gpt-test", profile="", sandbox="workspace-write", approval="never")
        self.assertEqual(command[:4], ["codex", "exec", "-C", str(ROOT)])
        self.assertIn("gpt-test", command)
        self.assertEqual(command[-1], "-")

    def test_codex_dry_run_creates_job_without_process(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            prompt = Path(tmp) / "prompt.md"
            prompt.write_text("write nothing", encoding="utf-8")
            store = JobStore(Path(tmp) / "jobs")
            job = start_codex_job(
                store,
                prompt_path=str(prompt),
                dry_run=True,
            )
            self.assertEqual(job["status"], "dry_run")
            self.assertIn("codex exec", job["command_display"])

    def test_webui_novel_input_is_saved_where_juben_init_can_find_it(self) -> None:
        path = save_novel_input(filename="example.txt", novel_text="正文")
        try:
            self.assertEqual(path.parent, DEFAULT_JUBEN_ROOT)
            self.assertTrue(path.name.startswith("__webui_input_"))
            self.assertEqual(path.read_text(encoding="utf-8"), "正文")
        finally:
            path.unlink(missing_ok=True)

    def test_pipeline_rejects_pending_artifact_text(self) -> None:
        with self.assertRaises(SystemExit):
            pipeline_cli.ensure_no_pending_placeholders(
                Path("source.map.md"),
                "mapping_status: pending_book_extraction\n",
            )


if __name__ == "__main__":
    unittest.main()
