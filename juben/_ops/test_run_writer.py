import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import types


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

    def test_main_skips_backend_when_all_drafts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            briefs = root / "harness" / "project" / "batch-briefs"
            drafts.mkdir(parents=True, exist_ok=True)
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")
            (drafts / "EP-11.md").write_text("existing", encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run") as mock_subprocess:
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])

        self.assertEqual(rc, 0)
        mock_subprocess.assert_not_called()

    def test_main_fails_when_batch_brief_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts" / "episodes").mkdir(parents=True, exist_ok=True)

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run") as mock_subprocess:
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11"])

        self.assertEqual(rc, 1)
        mock_subprocess.assert_not_called()

    def test_main_invokes_claude_for_missing_drafts_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            briefs = root / "harness" / "project" / "batch-briefs"
            drafts.mkdir(parents=True, exist_ok=True)
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")
            (drafts / "EP-11.md").write_text("existing", encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run") as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12"])

        self.assertEqual(rc, 0)
        mock_subprocess.assert_called_once()
        command = mock_subprocess.call_args.args[0]
        prompt = command[-1]
        self.assertEqual(command[:3], ["claude", "-p", "--dangerously-skip-permissions"])
        self.assertIn("EP-12", prompt)
        self.assertNotIn("EP-11.md", prompt)
        self.assertIn("drafts/episodes/EP-12.md", prompt)
        self.assertIn("不得 promote", prompt)
        self.assertIn("不得写 state", prompt)
        self.assertEqual(mock_subprocess.call_args.kwargs["cwd"], root)

    def test_main_uses_parallelism_and_runs_each_missing_episode_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            briefs = root / "harness" / "project" / "batch-briefs"
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")

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

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer, "ThreadPoolExecutor", FakeExecutor), \
                 mock.patch.object(self.run_writer.subprocess, "run") as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                rc = self.run_writer.main(
                    ["--batch", "batch03", "--episodes", "EP-11,EP-12", "--parallelism", "2"]
                )

        self.assertEqual(rc, 0)
        self.assertEqual(len(executor_instances), 1)
        self.assertEqual(executor_instances[0].max_workers, 2)
        self.assertEqual(mock_subprocess.call_count, 2)
        prompts = [call.args[0][-1] for call in mock_subprocess.call_args_list]
        self.assertTrue(any("EP-11" in prompt for prompt in prompts))
        self.assertTrue(any("EP-12" in prompt for prompt in prompts))

    def test_main_syntax_first_prompt_references_passing_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            briefs = root / "harness" / "project" / "batch-briefs"
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run") as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                rc = self.run_writer.main(
                    ["--batch", "batch03", "--episodes", "EP-11", "--syntax-first"]
                )

        self.assertEqual(rc, 0)
        prompt = mock_subprocess.call_args.args[0][-1]
        self.assertIn("场11-1", prompt)
        self.assertIn("整集最多 3 个场次标题", prompt)
        self.assertIn("当前集禁止出现 `场1-1 / 场1-2 / 场2-1`", prompt)
        self.assertIn("【镜头】", prompt)
        self.assertIn("角色（os）", prompt)
        self.assertIn("passing-episode.sample.md", prompt)
        self.assertIn("先把语法壳和排版写对", prompt)

    def test_main_splits_missing_episodes_into_parallel_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            briefs = root / "harness" / "project" / "batch-briefs"
            drafts.mkdir(parents=True, exist_ok=True)
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")
            calls: list[list[str]] = []

            def fake_run(command, **kwargs):
                calls.append(command)
                cp = mock.Mock()
                cp.returncode = 0
                return cp

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run", side_effect=fake_run):
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12", "--parallelism", "3"])

        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2)
        prompts = [command[-1] for command in calls]
        self.assertTrue(any("EP-11" in prompt and "EP-12" not in prompt for prompt in prompts))
        self.assertTrue(any("EP-12" in prompt and "EP-11" not in prompt for prompt in prompts))

    def test_main_includes_syntax_first_prompt_and_sample_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            briefs = root / "harness" / "project" / "batch-briefs"
            drafts.mkdir(parents=True, exist_ok=True)
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run") as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11", "--syntax-first"])

        self.assertEqual(rc, 0)
        prompt = mock_subprocess.call_args.args[0][-1]
        self.assertIn("场11-1", prompt)
        self.assertIn("整集最多 3 个场次标题", prompt)
        self.assertIn("【镜头】", prompt)
        self.assertIn("passing-episode.sample.md", prompt)
        self.assertIn("先对齐壳层和排版", prompt)

    def test_main_fails_if_any_parallel_worker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts" / "episodes"
            briefs = root / "harness" / "project" / "batch-briefs"
            drafts.mkdir(parents=True, exist_ok=True)
            briefs.mkdir(parents=True, exist_ok=True)
            (briefs / "batch03_EP11-15.md").write_text("# brief", encoding="utf-8")

            def fake_run(command, **kwargs):
                cp = mock.Mock()
                cp.returncode = 1 if "EP-12" in command[-1] else 0
                return cp

            with mock.patch.object(self.run_writer, "ROOT", root), \
                 mock.patch.object(self.run_writer.subprocess, "run", side_effect=fake_run):
                rc = self.run_writer.main(["--batch", "batch03", "--episodes", "EP-11,EP-12", "--parallelism", "3"])

        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
