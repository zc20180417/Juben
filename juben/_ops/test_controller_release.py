import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_PATH = ROOT / "_ops" / "controller.py"


def load_controller():
    spec = importlib.util.spec_from_file_location("controller_under_test", CONTROLLER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ControllerReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = load_controller()
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.project = self.root / "harness" / "project"
        self.state = self.project / "state"
        self.locks = self.project / "locks"
        self.batch_briefs = self.project / "batch-briefs"
        self.releases = self.project / "releases"
        self.drafts = self.root / "drafts" / "episodes"
        self.episodes = self.root / "episodes"
        self.ops = self.root / "_ops"
        self.manifest_md = self.project / "run.manifest.md"
        self.manifest_json = self.project / "run.manifest.json"
        self.source_map_md = self.project / "source.map.md"
        self.source_map_json = self.project / "source.map.json"
        self.run_log = self.state / "run.log.md"
        self.lint_script = self.ops / "episode-lint.py"

        self._patch_paths()
        self._seed_common_files()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _patch_paths(self) -> None:
        c = self.controller
        c.ROOT = self.root
        c.HARNESS = self.root / "harness"
        c.PROJECT = self.project
        c.STATE = self.state
        c.LOCKS = self.locks
        c.DRAFTS = self.drafts
        c.EPISODES = self.episodes
        c.LINT_SCRIPT = self.lint_script
        c.BATCH_BRIEFS = self.batch_briefs
        c.RUN_MANIFEST = self.manifest_md
        c.RUN_MANIFEST_JSON = self.manifest_json
        c.RUN_LOG = self.run_log
        c.SOURCE_MAP = self.source_map_md
        c.SOURCE_MAP_JSON = self.source_map_json
        c.RELEASES = self.releases
        c.RELEASE_INDEX = self.releases / "release.index.json"
        c.GOLD_SET = self.releases / "gold-set.json"
        c.NOW = "2026-04-13 22:30"

    def _seed_common_files(self) -> None:
        for path in [
            self.state / "script.progress.md",
            self.state / "story.state.md",
            self.state / "relationship.board.md",
            self.state / "open_loops.md",
            self.state / "quality.anchor.md",
            self.state / "process.memory.md",
        ]:
            write(path, "# placeholder\n")
        write(
            self.run_log,
            "# Run Log\n\n_最后更新：2026-04-13 22:00_\n\n## Log Entries\n| time | batch | episode | phase | event | result | note |\n",
        )
        write(self.locks / "batch.lock", "status: locked\nowner: controller:batch01\nupdated_at: 2026-04-13 22:00\n")
        write(self.locks / "state.lock", "status: unlocked\nowner: none\nupdated_at: 2026-04-13 22:00\n")
        write(self.locks / "episode-XX.lock", "")
        write(
            self.lint_script,
            """#!/usr/bin/env python3
import json
import sys

print(json.dumps({
    "status": "warn",
    "contract_failures": [],
    "craft_flags": ["hookless_final_scene"],
    "style_warnings": [],
    "metrics": {"file": sys.argv[1]},
}, ensure_ascii=False))
""",
        )
        write(
            self.batch_briefs / "batch01_EP01-02.md",
            """# Batch Brief: EP-01 ~ EP-02

- batch status: frozen
- owned episodes: EP-01, EP-02
- source excerpt range: novel 第1章 ~ 第2章
""",
        )
        write(self.drafts / "EP-01.md", "第1集：测试\n")
        write(self.drafts / "EP-02.md", "第2集：测试\n")
        write(self.episodes / "EP-03.md", "legacy payload\n")
        write(self.locks / "verify-EP-01.json", json.dumps({"episode": "EP-01", "tier": "FULL", "status": "PASS"}, ensure_ascii=False, indent=2))
        write(self.locks / "verify-EP-02.json", json.dumps({"episode": "EP-02", "tier": "STANDARD", "status": "PASS"}, ensure_ascii=False, indent=2))
        write(
            self.manifest_md,
            """# Run Manifest

- source_file: novel.md
- total_episodes: 60
- batch_size: 5
- key_episodes: EP-01
- adaptation_mode: novel_to_short_drama
- adaptation_strategy: original_fidelity
- dialogue_adaptation_intensity: light
- generation_execution_mode: orchestrated_subagents
- generation_reset_mode: clean_rebuild
- run_status: active
- active_batch: stale_md
- source_authority: original novel manuscript + harness/project/source.map.md
- draft_lane: drafts/episodes
- publish_lane: episodes
- promotion_policy: controller_only_after_full_batch_verify

## Current Runtime
- framework entry: harness/framework/entry.md
- source map: harness/project/source.map.md
- current batch brief: harness/project/batch-briefs/stale.md
- regression packs: optional under harness/project/regressions/
- state directory: harness/project/state/
""",
        )
        write(
            self.manifest_json,
            json.dumps(
                {
                    "source_file": "novel.md",
                    "total_episodes": "60",
                    "batch_size": "5",
                    "key_episodes": "EP-01",
                    "adaptation_mode": "novel_to_short_drama",
                    "adaptation_strategy": "original_fidelity",
                    "dialogue_adaptation_intensity": "light",
                    "generation_execution_mode": "orchestrated_subagents",
                    "generation_reset_mode": "clean_rebuild",
                    "run_status": "active",
                    "active_batch": "batch00_seeded",
                    "current_batch_brief": "harness/project/batch-briefs/seeded.md",
                    "source_authority": "original novel manuscript + harness/project/source.map.md",
                    "draft_lane": "drafts/episodes",
                    "publish_lane": "episodes",
                    "promotion_policy": "controller_only_after_full_batch_verify",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        write(
            self.source_map_md,
            """# Source Map Mirror

## Batch 01：EP-91 ~ EP-92
原著范围：第91章 ~ 第92章

### EP-91
- source chapter span：第91章
- must-keep beats：旧数据
- must-not-add / must-not-jump：旧数据
- ending type：前推力
""",
        )
        write(
            self.source_map_json,
            json.dumps(
                {
                    "batch01": {
                        "batch_num": "01",
                        "ep_start": "EP-01",
                        "ep_end": "EP-02",
                        "episodes": ["EP-01", "EP-02"],
                        "source_range": "第1章 ~ 第2章",
                        "episode_data": {
                            "EP-01": {
                                "source_span": "第1章",
                                "must_keep": "母坟立誓；后山埋母",
                                "must_not": "不得漏父亲冷反应",
                                "ending_type": "强闭环",
                            },
                            "EP-02": {
                                "source_span": "第2章",
                                "must_keep": "选秀旨意压府；替姐入宫",
                                "must_not": "不得跳过求生姿态",
                                "ending_type": "前推力",
                            },
                        },
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

    def test_read_manifest_prefers_json_sidecar(self) -> None:
        data = self.controller._read_manifest()
        self.assertEqual(data["active_batch"], "batch00_seeded")
        self.assertEqual(data["current_batch_brief"], "harness/project/batch-briefs/seeded.md")

    def test_parse_source_map_prefers_json_sidecar(self) -> None:
        data = self.controller._parse_source_map()
        self.assertEqual(data["batch01"]["episodes"], ["EP-01", "EP-02"])
        self.assertEqual(data["batch01"]["ep_start"], "EP-01")

    def test_promote_allows_craft_flags_and_updates_release_tracking(self) -> None:
        result = self.controller.cmd_promote(argparse.Namespace(batch_id="batch01"))
        self.assertEqual(result, 0)

        meta = json.loads((self.episodes / "EP-01.meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["episode"], "EP-01")
        self.assertEqual(meta["source_batch"], "batch01")
        self.assertEqual(meta["runtime_authority"], "rebuild-2026-04")
        self.assertIn(meta["release_status"], {"gold", "provisional"})
        self.assertEqual(meta["lint_status"], "warn")
        self.assertEqual(meta["verify_tier"], "FULL")
        self.assertEqual(meta["verify_status"], "PASS")

        release_index = json.loads((self.releases / "release.index.json").read_text(encoding="utf-8"))
        self.assertEqual(release_index["episodes"]["EP-03"]["release_status"], "legacy")
        self.assertTrue((self.releases / "gold-set.json").exists())

        manifest = json.loads(self.manifest_json.read_text(encoding="utf-8"))
        self.assertEqual(manifest["active_batch"], "batch01_promoted")
        self.assertEqual(manifest["current_batch_brief"], "harness/project/batch-briefs/batch01_EP01-02.md")
        self.assertIn("current batch brief: harness/project/batch-briefs/batch01_EP01-02.md", self.manifest_md.read_text(encoding="utf-8"))

    def test_audit_detects_missing_meta_for_gold_episode(self) -> None:
        self.controller.cmd_promote(argparse.Namespace(batch_id="batch01"))
        (self.episodes / "EP-01.meta.json").unlink()
        result = self.controller.cmd_audit(argparse.Namespace())
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
