import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
OPENAI = ROOT / "OPENAI.md"
CLAUDE = ROOT / "CLAUDE.md"
ENTRY = ROOT / "harness" / "framework" / "entry.md"
INPUT_CONTRACT = ROOT / "harness" / "framework" / "input-contract.md"
WRITE_CONTRACT = ROOT / "harness" / "framework" / "write-contract.md"
VERIFY_CONTRACT = ROOT / "harness" / "framework" / "verify-contract.md"
PROMOTE_CONTRACT = ROOT / "harness" / "framework" / "promote-contract.md"
MEMORY_CONTRACT = ROOT / "harness" / "framework" / "memory-contract.md"
REGRESSION_CONTRACT = ROOT / "harness" / "framework" / "regression-contract.md"
PASSING_SAMPLE = ROOT / "harness" / "framework" / "passing-episode.sample.md"
RUN_MANIFEST = ROOT / "harness" / "project" / "run.manifest.md"
BOOK_BLUEPRINT = ROOT / "harness" / "project" / "book.blueprint.md"
SOURCE_MAP = ROOT / "harness" / "project" / "source.map.md"
BATCH_BRIEF = ROOT / "harness" / "project" / "batch-briefs" / "batch01_EP01-05.md"
REGRESSION_DIR = ROOT / "harness" / "project" / "regressions"
PROCESS_MEMORY = ROOT / "harness" / "project" / "state" / "process.memory.md"
SCRIPT_PROGRESS = ROOT / "harness" / "project" / "state" / "script.progress.md"
STORY_STATE = ROOT / "harness" / "project" / "state" / "story.state.md"
RELATIONSHIP = ROOT / "harness" / "project" / "state" / "relationship.board.md"
OPEN_LOOPS = ROOT / "harness" / "project" / "state" / "open_loops.md"
QUALITY = ROOT / "harness" / "project" / "state" / "quality.anchor.md"
RUN_LOG = ROOT / "harness" / "project" / "state" / "run.log.md"
ALIGNER = ROOT / "_ops" / "script-aligner.md"
RECORDER = ROOT / "_ops" / "script-recorder.md"
VOICE_ANCHOR = ROOT / "voice-anchor.md"
CHARACTER = ROOT / "character.md"
WRITER_STYLE = ROOT / "harness" / "framework" / "writer-style.md"
OPS_README = ROOT / "_ops" / "README.md"
ARCHIVE_README = ROOT / "docs" / "archive" / "README_v2_history.md"


# ---------------------------------------------------------------------------
# Layer 1: Structure Tests (contracts exist, routes wired)
# ---------------------------------------------------------------------------

class StructureTests(unittest.TestCase):
    def test_root_entries_are_thin_routes(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")
        openai = OPENAI.read_text(encoding="utf-8")
        claude = CLAUDE.read_text(encoding="utf-8")
        self.assertIn("harness/framework/entry.md", agents)
        self.assertIn("harness/project/run.manifest.md", agents)
        self.assertIn("Treat Harness V2 as the only workflow source of truth", agents)
        self.assertIn("harness/framework/entry.md", openai)
        self.assertIn("harness/project/run.manifest.md", openai)
        self.assertIn("Resolve workflow inputs from `entry.md`", openai)
        self.assertIn("Treat Harness V2 as the only workflow source of truth", openai)
        self.assertIn("harness/framework/entry.md", claude)
        self.assertIn("harness/project/run.manifest.md", claude)
        self.assertIn("Resolve workflow inputs from `entry.md`", claude)
        self.assertIn("Treat Harness V2 as the only workflow source of truth", claude)

    def test_agents_and_claude_route_tilde_commands_via_entry(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")
        claude = CLAUDE.read_text(encoding="utf-8")
        self.assertIn("`~` 开头", agents)
        self.assertIn("entry.md", agents)
        self.assertIn("`~` 开头", claude)
        self.assertIn("entry.md", claude)

    def test_agents_doc_is_not_an_operations_manual(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")
        for marker in [
            "Session Start Protocol",
            "Init Extract Protocol",
            "AGENT_EXTRACT_REQUIRED",
            "python _ops/controller.py next",
            "可用命令：",
        ]:
            self.assertNotIn(marker, agents)

    def test_openai_and_claude_do_not_reference_missing_protocols(self) -> None:
        for path in [OPENAI, CLAUDE]:
            content = path.read_text(encoding="utf-8")
            for marker in ["Session Start Protocol", "Init Extract Protocol", "AGENT_EXTRACT_REQUIRED"]:
                self.assertNotIn(marker, content, f"{path.name} should not reference {marker}")

    def test_framework_contracts_exist(self) -> None:
        for path in [
            ENTRY,
            INPUT_CONTRACT,
            WRITE_CONTRACT,
            WRITER_STYLE,
            PASSING_SAMPLE,
            VERIFY_CONTRACT,
            PROMOTE_CONTRACT,
            MEMORY_CONTRACT,
            REGRESSION_CONTRACT,
        ]:
            self.assertTrue(path.exists(), path)

    def test_book_blueprint_file_exists(self) -> None:
        self.assertTrue(BOOK_BLUEPRINT.exists(), BOOK_BLUEPRINT)
        content = BOOK_BLUEPRINT.read_text(encoding="utf-8")
        self.assertIn("recommended_total_episodes", content)
        self.assertIn("## 集数建议", content)

    def test_run_manifest_fields_exist(self) -> None:
        content = RUN_MANIFEST.read_text(encoding="utf-8")
        for field in [
            "total_episodes",
            "recommended_total_episodes",
            "episode_count_source",
            "target_episode_minutes",
            "episode_minutes_min",
            "episode_minutes_max",
            "adaptation_mode",
            "adaptation_strategy",
            "dialogue_adaptation_intensity",
            "generation_execution_mode",
            "writer_parallelism",
            "writer_command",
            "generation_reset_mode",
            "run_status",
            "active_batch",
            "source_authority",
            "draft_lane",
            "publish_lane",
            "promotion_policy",
        ]:
            self.assertIn(field, content)

    def test_source_map_has_required_episode_fields(self) -> None:
        content = SOURCE_MAP.read_text(encoding="utf-8")
        self.assertIn("source chapter span", content)
        self.assertIn("must-keep beats", content)
        self.assertIn("must-not-add", content)
        self.assertIn("must-not-jump", content)
        self.assertIn("ending type", content)

    def test_batch_brief_has_required_fields(self) -> None:
        content = BATCH_BRIEF.read_text(encoding="utf-8")
        for field in [
            "batch status",
            "owned episodes",
            "source excerpt range",
            "adjacent continuity",
            "draft output paths",
            "verify checklist",
        ]:
            self.assertIn(field, content)

    def test_regression_directory_exists_and_optional_pack_shape_is_valid(self) -> None:
        self.assertTrue(REGRESSION_DIR.exists())
        for path in REGRESSION_DIR.glob("*.md"):
            if path.name.lower() == "readme.md":
                continue
            content = path.read_text(encoding="utf-8")
            for field in [
                "regression_id",
                "scope",
                "failure_mode",
                "blocking_rule",
                "severity",
                "status",
            ]:
                self.assertIn(field, content)

    def test_project_state_files_exist_under_harness(self) -> None:
        for path in [SCRIPT_PROGRESS, STORY_STATE, RELATIONSHIP, OPEN_LOOPS, QUALITY, PROCESS_MEMORY, RUN_LOG]:
            self.assertTrue(path.exists(), path)

    def test_dual_lanes_exist(self) -> None:
        publish_dir = ROOT / "episodes"
        draft_dir = ROOT / "drafts" / "episodes"
        self.assertTrue(publish_dir.exists())
        self.assertTrue(draft_dir.exists())
        for i in range(1, 6):
            self.assertTrue((publish_dir / f"EP-{i:02d}.md").exists())

    def test_locks_exist(self) -> None:
        lock_dir = ROOT / "harness" / "project" / "locks"
        for name in ["batch.lock", "episode-XX.lock", "state.lock"]:
            self.assertTrue((lock_dir / name).exists())

    def test_legacy_v1_and_root_workflow_files_are_removed(self) -> None:
        self.assertFalse((ROOT / "harness" / "legacy" / "v1").exists())
        for removed in [
            ROOT / "runtime-core.md",
            ROOT / "adaptation-core.md",
            ROOT / "project.profile.md",
            ROOT / "script.progress.md",
            ROOT / "story.state.md",
            ROOT / "relationship.board.md",
            ROOT / "open_loops.md",
            ROOT / "quality.anchor.md",
        ]:
            self.assertFalse(removed.exists(), removed)

    def test_ops_history_readme_is_archived_out_of_ops(self) -> None:
        self.assertFalse(OPS_README.exists(), OPS_README)
        self.assertTrue(ARCHIVE_README.exists(), ARCHIVE_README)

    def test_root_docs_only_describe_harness_v2_as_current_workflow(self) -> None:
        banned_phrases = [
            "主Agent",
            "v2.0–v2.3.3",
            "v2.0",
            "v2.1",
            "v2.2",
            "v2.3",
            "legacy/v1",
            "runtime-core.md",
        ]
        for path in [README, AGENTS, OPENAI, CLAUDE]:
            content = path.read_text(encoding="utf-8")
            for phrase in banned_phrases:
                self.assertNotIn(phrase, content, f"{path.name} should not mention {phrase} as active workflow context")

    def test_harness_v2_authority_files_are_explicit(self) -> None:
        readme = README.read_text(encoding="utf-8")
        for path_text in [
            "harness/framework/*",
            "harness/project/*",
            "_ops/controller.py",
            "_ops/episode-lint.py",
            "_ops/script-aligner.md",
            "_ops/script-recorder.md",
        ]:
            self.assertIn(path_text, readme)

    def test_entry_defines_chat_command_aliases(self) -> None:
        entry = ENTRY.read_text(encoding="utf-8")
        self.assertIn("Chat Command Aliases", entry)
        for alias in ["~init", "~extract-book", "~map-book", "~start", "~run", "~check", "~finish", "~record", "~clean", "~clear", "~status"]:
            self.assertIn(alias, entry)
        self.assertIn("--episodes", entry)
        self.assertIn("--batch-size", entry)
        self.assertIn("可选人工覆盖", entry)
        self.assertIn("smoke", entry)
        self.assertIn("不是清空聊天记录", entry)

    def test_passing_episode_sample_contains_required_shell_markers(self) -> None:
        content = PASSING_SAMPLE.read_text(encoding="utf-8")
        for marker in ["场1-1：", "日/夜", "外/内", "场景：", "♪：", "△：", "【镜头】：", "（os）"]:
            self.assertIn(marker, content)


# ---------------------------------------------------------------------------
# Layer 2: Execution Coverage Tests (specs consume contracts)
# ---------------------------------------------------------------------------

class AlignerExecutionTests(unittest.TestCase):
    """Verify that script-aligner.md execution steps cover all verify-contract checklist items."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.aligner = ALIGNER.read_text(encoding="utf-8")
        cls.verify = VERIFY_CONTRACT.read_text(encoding="utf-8")

    def test_aligner_is_execution_spec_not_stub(self) -> None:
        self.assertIn("Execution Steps", self.aligner)
        self.assertIn("Step 1", self.aligner)
        # Must have at least 7 steps
        self.assertIn("Step 7", self.aligner)

    def test_aligner_consumes_lint_gate(self) -> None:
        self.assertIn("episode-lint.py", self.aligner)
        self.assertIn("scene_failures", self.aligner)
        self.assertIn("episode_failures", self.aligner)

    def test_aligner_covers_fail_closed_items(self) -> None:
        for item in [
            "触发语义",
            "设计局",
            "具体事故",
            "强闭环",
            "即时动作钩子",
            "第一人称",
            "publish lane",
        ]:
            self.assertIn(item, self.aligner, f"Fail Closed item missing from aligner: {item}")

    def test_aligner_covers_adversarial_checks(self) -> None:
        for check in [
            "角色替换测试",
            "删除测试",
            "逻辑反推测试",
            "钩子有效性测试",
            "画面感测试",
            "表里不一测试",
        ]:
            self.assertIn(check, self.aligner, f"Adversarial check missing from aligner: {check}")

    def test_aligner_covers_voice_fingerprint(self) -> None:
        for item in [
            "voice-anchor.md",
            "character.md",
            "句长分布",
            "角色区分度",
            "禁用表达",
        ]:
            self.assertIn(item, self.aligner, f"Voice fingerprint item missing from aligner: {item}")

    def test_aligner_covers_quality_anchor_benchmark(self) -> None:
        self.assertIn("quality.anchor.md", self.aligner)
        self.assertIn("质量锚对标", self.aligner)
        self.assertIn("场景厚度", self.aligner)

    def test_aligner_covers_expression_density(self) -> None:
        for item in ["表情", "微表情", "冲突", "反转", "情绪层次"]:
            self.assertIn(item, self.aligner, f"Density check missing from aligner: {item}")

    def test_aligner_covers_dialogue_drift(self) -> None:
        self.assertIn("对白语义漂移", self.aligner)
        for drift_type in ["态度增强", "机锋增强", "关系温度偏移", "说明化"]:
            self.assertIn(drift_type, self.aligner, f"Drift type missing from aligner: {drift_type}")

    def test_aligner_covers_warning_escalation(self) -> None:
        self.assertIn("WARNING 累计", self.aligner)
        self.assertIn("回归", self.aligner)
        self.assertIn("regressions/", self.aligner)

    def test_aligner_has_output_format(self) -> None:
        self.assertIn("Output Format", self.aligner)
        self.assertIn("PASS", self.aligner)
        self.assertIn("FAIL", self.aligner)

    def test_aligner_references_source_map(self) -> None:
        self.assertIn("source.map.md", self.aligner)
        self.assertIn("must-keep beats", self.aligner)
        self.assertIn("must-not-add", self.aligner)

    def test_aligner_references_recovery_protocol(self) -> None:
        self.assertIn("Recovery Protocol", self.aligner)
        self.assertIn("context reset", self.aligner)
        self.assertIn("run.log.md", self.aligner)


class RecorderExecutionTests(unittest.TestCase):
    """Verify that script-recorder.md execution steps cover all memory-contract template sections."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.recorder = RECORDER.read_text(encoding="utf-8")
        cls.memory = MEMORY_CONTRACT.read_text(encoding="utf-8")

    def test_recorder_is_execution_spec_not_stub(self) -> None:
        self.assertIn("Execution Steps", self.recorder)
        self.assertIn("Step 1", self.recorder)
        self.assertIn("Step 10", self.recorder)

    def test_recorder_has_preconditions(self) -> None:
        self.assertIn("Preconditions", self.recorder)
        self.assertIn("controller", self.recorder)
        self.assertIn("promote", self.recorder)
        self.assertIn("state.lock", self.recorder)

    def test_recorder_covers_all_write_targets(self) -> None:
        for target in [
            "script.progress.md",
            "story.state.md",
            "relationship.board.md",
            "open_loops.md",
            "quality.anchor.md",
            "process.memory.md",
            "run.log.md",
        ]:
            self.assertIn(target, self.recorder, f"Write target missing from recorder: {target}")

    def test_recorder_covers_script_progress_sections(self) -> None:
        for section in ["项目信息", "基础文档", "当前整季状态", "分集记录", "全局记录", "质量统计", "版本记录"]:
            self.assertIn(section, self.recorder, f"script.progress section missing from recorder: {section}")

    def test_recorder_covers_story_state_sections(self) -> None:
        for section in ["当前阶段", "权力格局", "主要角色位置", "最近关键转折", "下一批关键预期"]:
            self.assertIn(section, self.recorder, f"story.state section missing from recorder: {section}")

    def test_recorder_covers_relationship_board_sections(self) -> None:
        for section in ["核心关系网", "最近关系变动", "待爆关系线"]:
            self.assertIn(section, self.recorder, f"relationship.board section missing from recorder: {section}")

    def test_recorder_covers_open_loops_sections(self) -> None:
        for section in ["未回收伏笔", "未爆真相", "待解冲突", "已超期伏笔"]:
            self.assertIn(section, self.recorder, f"open_loops section missing from recorder: {section}")

    def test_recorder_covers_quality_anchor_sections(self) -> None:
        for section in ["场景厚度", "对话节奏", "os 使用方式", "表情", "代表性打法"]:
            self.assertIn(section, self.recorder, f"quality.anchor section missing from recorder: {section}")

    def test_recorder_covers_weakness_label_mapping(self) -> None:
        for label in ["对话不足", "描写空洞", "成片感缺失", "情绪单一", "标记缺失", "比喻过密", "意象单一", "角色同腔"]:
            self.assertIn(label, self.recorder, f"Weakness label missing from recorder: {label}")

    def test_recorder_has_validate_and_unlock(self) -> None:
        self.assertIn("Validate", self.recorder)
        self.assertIn("Unlock", self.recorder)
        self.assertIn("必备 section", self.recorder)

    def test_recorder_has_output_format(self) -> None:
        self.assertIn("Output Format", self.recorder)
        self.assertIn("RECORD COMPLETE", self.recorder)


# ---------------------------------------------------------------------------
# Layer 3: Voice Anchor Routing Tests
# ---------------------------------------------------------------------------

class VoiceAnchorRoutingTests(unittest.TestCase):
    """Verify voice-anchor -> character fallback chain is wired across all layers."""

    def test_writer_routing_includes_voice_anchor(self) -> None:
        entry = ENTRY.read_text(encoding="utf-8")
        self.assertIn("voice-anchor.md", entry)
        self.assertIn("character.md", entry)

    def test_write_contract_includes_voice_anchor(self) -> None:
        wc = WRITE_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Voice Anchor", wc)
        self.assertIn("voice-anchor.md", wc)
        self.assertIn("character.md", wc)
        self.assertIn("writer-style.md", wc)

    def test_verify_contract_includes_voice_anchor(self) -> None:
        vc = VERIFY_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("voice-anchor.md", vc)
        self.assertIn("character.md", vc)

    def test_aligner_includes_voice_anchor(self) -> None:
        aligner = ALIGNER.read_text(encoding="utf-8")
        self.assertIn("voice-anchor.md", aligner)
        self.assertIn("character.md", aligner)

    def test_voice_anchor_file_exists(self) -> None:
        self.assertTrue(VOICE_ANCHOR.exists() or CHARACTER.exists(),
                        "At least one voice source must exist")


# ---------------------------------------------------------------------------
# Layer 4: State Template Compliance Tests
# ---------------------------------------------------------------------------

class StateTemplateComplianceTests(unittest.TestCase):
    """Verify that existing state files comply with memory-contract templates."""

    def _read(self, path: Path) -> str:
        self.assertTrue(path.exists(), path)
        return path.read_text(encoding="utf-8")

    def _assert_sections(self, content: str, sections: list[str], file_name: str) -> None:
        for section in sections:
            self.assertTrue(
                re.search(rf"^#+\s.*{re.escape(section)}", content, re.MULTILINE),
                f"Section '{section}' missing from {file_name}",
            )

    def test_script_progress_has_required_sections(self) -> None:
        content = self._read(SCRIPT_PROGRESS)
        self._assert_sections(content, ["项目信息", "基础文档", "当前整季状态", "分集记录", "全局记录", "质量统计", "版本记录"], "script.progress.md")

    def test_story_state_has_required_sections(self) -> None:
        content = self._read(STORY_STATE)
        self._assert_sections(content, ["当前阶段", "权力格局", "主要角色位置", "最近关键转折", "下一批关键预期"], "story.state.md")

    def test_relationship_board_has_required_sections(self) -> None:
        content = self._read(RELATIONSHIP)
        self._assert_sections(content, ["核心关系网", "最近关系变动", "待爆关系线"], "relationship.board.md")

    def test_open_loops_has_required_sections(self) -> None:
        content = self._read(OPEN_LOOPS)
        self._assert_sections(content, ["未回收伏笔", "未爆真相", "待解冲突", "已超期伏笔"], "open_loops.md")

    def test_quality_anchor_has_required_sections(self) -> None:
        content = self._read(QUALITY)
        self._assert_sections(content, ["场景厚度", "对话节奏", "os 使用方式", "代表性打法"], "quality.anchor.md")

    def test_process_memory_has_required_sections(self) -> None:
        content = self._read(PROCESS_MEMORY)
        self._assert_sections(content, ["活跃流程问题", "当前执行准则"], "process.memory.md")


# ---------------------------------------------------------------------------
# Layer 5: Role Architecture & Context Reset Tests
# ---------------------------------------------------------------------------

class RoleArchitectureTests(unittest.TestCase):
    """Verify three-role separation is explicitly defined in entry.md."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entry = ENTRY.read_text(encoding="utf-8")

    def test_entry_defines_role_architecture(self) -> None:
        self.assertIn("Role Architecture", self.entry)

    def test_entry_defines_three_roles(self) -> None:
        for role in ["Controller", "Writer", "Verifier"]:
            self.assertIn(role, self.entry, f"Role '{role}' missing from entry.md")

    def test_entry_defines_context_reset_protocol(self) -> None:
        self.assertIn("Context Reset Protocol", self.entry)
        self.assertIn("batch 边界", self.entry)
        self.assertIn("不跨 batch 累积正文上下文", self.entry)
        self.assertIn("context reset 触发条件", self.entry)


# ---------------------------------------------------------------------------
# Layer 6: Recovery Protocol & Run Log Tests
# ---------------------------------------------------------------------------

class RecoveryProtocolTests(unittest.TestCase):
    """Verify recovery protocol is defined and wired into execution specs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entry = ENTRY.read_text(encoding="utf-8")
        cls.aligner = ALIGNER.read_text(encoding="utf-8")
        cls.memory = MEMORY_CONTRACT.read_text(encoding="utf-8")

    def test_entry_defines_recovery_protocol(self) -> None:
        self.assertIn("Recovery Protocol", self.entry)

    def test_recovery_has_retry_limits(self) -> None:
        for marker in ["第 1 次 FAIL", "第 2 次 FAIL", "第 3 次 FAIL", "第 4 次 FAIL"]:
            self.assertIn(marker, self.entry, f"Retry stage missing: {marker}")

    def test_recovery_has_context_reset_trigger(self) -> None:
        self.assertIn("context reset", self.entry)

    def test_recovery_has_human_escalation(self) -> None:
        self.assertIn("人工介入", self.entry)

    def test_recovery_has_batch_level_escalation(self) -> None:
        self.assertIn("batch 暂停", self.entry)

    def test_recovery_has_rollback_strategy(self) -> None:
        self.assertIn("回滚", self.entry)

    def test_memory_contract_defines_run_log(self) -> None:
        self.assertIn("Run Log Contract", self.memory)
        self.assertIn("run.log.md", self.memory)

    def test_run_log_records_all_phases(self) -> None:
        for phase in ["plan_inputs", "draft_write", "verify", "promote", "record", "recovery"]:
            self.assertIn(phase, self.memory, f"Phase '{phase}' missing from run log contract")

    def test_run_log_file_exists_and_has_entries(self) -> None:
        self.assertTrue(RUN_LOG.exists())
        content = RUN_LOG.read_text(encoding="utf-8")
        self.assertIn("Log Entries", content)
        # Must have at least one real log entry (not just header)
        self.assertIn("batch01", content)

    def test_recorder_writes_run_log(self) -> None:
        recorder = RECORDER.read_text(encoding="utf-8")
        self.assertIn("run.log.md", recorder)
        self.assertIn("追加", recorder)


if __name__ == "__main__":
    unittest.main()
