import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "_ops" / "agent_backend.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("agent_backend_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AgentBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()

    def test_build_agent_command_prefers_claude_when_available(self) -> None:
        with mock.patch.object(
            self.module.shutil,
            "which",
            side_effect=lambda name: {
                "claude": "C:/bin/claude.exe",
                "codex": "C:/bin/codex.exe",
            }.get(name),
        ):
            backend_name, command = self.module.build_agent_command("PROMPT")

        self.assertEqual(backend_name, "Claude")
        self.assertEqual(command[:3], ["claude", "-p", "--dangerously-skip-permissions"])
        self.assertEqual(command[-1], "PROMPT")

    def test_build_agent_command_falls_back_to_codex_when_claude_missing(self) -> None:
        with mock.patch.object(
            self.module.shutil,
            "which",
            side_effect=lambda name: {
                "codex": "C:/bin/codex.exe",
            }.get(name),
        ):
            backend_name, command = self.module.build_agent_command("PROMPT")

        self.assertEqual(backend_name, "Codex")
        self.assertEqual(
            command[:3],
            ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox"],
        )
        self.assertEqual(command[-1], "PROMPT")

    def test_build_agent_command_errors_when_no_supported_backend_exists(self) -> None:
        with mock.patch.object(self.module.shutil, "which", return_value=None):
            with self.assertRaises(self.module.AgentBackendError):
                self.module.build_agent_command("PROMPT")


if __name__ == "__main__":
    unittest.main()
