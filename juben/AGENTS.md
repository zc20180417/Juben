<!-- BEGIN COMPOUND CODEX TOOL MAP -->
## Compound Codex Tool Mapping (Claude Compatibility)

This section maps Claude Code plugin tool references to Codex behavior.
Only this block is managed automatically.

Tool mapping:
- Read: use shell reads (cat/sed) or rg
- Write: create files via shell redirection or apply_patch
- Edit/MultiEdit: use apply_patch
- Bash: use shell_command
- Grep: use rg (fallback: grep)
- Glob: use rg --files or find
- LS: use ls via shell_command
- WebFetch/WebSearch: use curl or Context7 for library docs
- AskUserQuestion/Question: present choices as a numbered list in chat and wait for a reply number. For multi-select (multiSelect: true), accept comma-separated numbers. Never skip or auto-configure — always wait for the user's response before proceeding.
- Task/Subagent/Parallel: run sequentially in main thread; use multi_tool_use.parallel for tool calls
- TodoWrite/TodoRead: use file-based todos in todos/ with todo-create skill
- Skill: open the referenced SKILL.md and follow it
- ExitPlanMode: ignore
<!-- END COMPOUND CODEX TOOL MAP -->

# Session Start Protocol

When a user starts a conversation (including greetings like "hi", "你好", or any first message), you MUST:

1. **Display the banner:**

```
     ██╗██╗   ██╗██████╗ ███████╗███╗   ██╗
     ██║██║   ██║██╔══██╗██╔════╝████╗  ██║
     ██║██║   ██║██████╔╝█████╗  ██╔██╗ ██║
██   ██║██║   ██║██╔══██╗██╔══╝  ██║╚██╗██║
╚█████╔╝╚██████╔╝██████╔╝███████╗██║ ╚████║
 ╚════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
小说 → 短剧改编 Harness V2
```

2. **Read `harness/project/run.manifest.md`** to detect the current project, then show:

```
当前项目：<从 manifest 读取的信息>
改编模式：<adaptation_strategy> / 对话力度：<dialogue_adaptation_intensity>
流水线：Harness V2（三角色分离 · 双通道 · 程序化门控）
```

3. **Auto-detect project status** by running:
   ```
   python _ops/controller.py next
   ```
   Display the output to the user.

4. **Show available commands:**

```
可用命令：
  start <batch>        启动批次（生成 brief → 冻结 → 锁定）
  check <batch>        检查批次（lint gate → verify 指令）
  finish <batch>       完成批次（verify gate → promote）
  record <batch>       记录状态（获取 state.lock → recorder 指令）
  record-done <batch>  封存记录（验证 state → 释放锁）
  next                 查看下一批次
  status               查看完整流水线状态

所有命令通过 python _ops/controller.py <command> 执行。
```

5. **Suggest next step** based on the detected status.

This protocol applies to ALL first interactions, regardless of what the user says. After showing the intro, proceed to address the user's actual request if any.

---

# Init Extract Protocol

When `controller.py init` outputs `AGENT_EXTRACT_REQUIRED`, or when `source.map.md` / `character.md` / `voice-anchor.md` contain `AGENT_EXTRACT_REQUIRED` markers, you MUST automatically execute this protocol **without asking the user**. This is the "一步到位" init flow.

## Step 1: Read the novel

Read `run.manifest.md` to get `source_file`. Read the novel file. If the novel is too large for a single read, read it in chapter-sized segments.

## Step 2: Extract character.md

From the full novel text, extract and write `character.md`:
- All named characters with role (主角/配角/龙套)
- Identity, status, appearance traits
- Personality and behavioral patterns
- Key relationships to other characters
- Character arc summary (where they start → where they end)

## Step 3: Extract voice-anchor.md

From dialogue patterns in the novel, extract and write `voice-anchor.md`:
- Per major character: sentence length tendency, speech register, verbal tics, emotional expression style
- Forbidden expressions (things the character would never say)
- Example dialogue lines from the novel (2-3 representative quotes per character)

## Step 4: Fill source.map.md beats

For each episode in `source.map.md` that has `AGENT_EXTRACT_REQUIRED`:

1. Read the corresponding chapter range from the novel (use the `source chapter span` field)
2. Extract and fill in:
   - **must-keep beats**: Key plot points that MUST appear in this episode (use `；` separator). Include specific dialogue lines, character actions, and emotional turning points.
   - **must-not-add / must-not-jump**: Hard boundaries — what the writer must NOT invent or skip. Derive from the novel's pacing and causality.
   - **ending type**: `强闭环` (strong closure — the episode ends a complete narrative arc) or `前推力` (forward push — the episode ends with momentum into the next)

3. When determining ending types:
   - 强闭环: revenge completed, enemy defeated, major revelation, death scene, status change ceremony
   - 前推力: setup planted, danger approaching, plan in motion, cliffhanger

## Step 5: Determine key_episodes

After filling all episodes, identify key episodes (付费节点 / 大高潮) and update `run.manifest.md`:
- Major turning points, climactic confrontations, death scenes, status changes
- Update the `key_episodes` field with comma-separated EP IDs

## Step 6: Verify and report

After all files are filled:
1. Confirm no `AGENT_EXTRACT_REQUIRED` markers remain in any file
2. Run `python _ops/controller.py validate` to check state files
3. Report completion to the user with a summary:
   - Number of chapters detected
   - Number of episodes mapped
   - Number of characters extracted
   - Key episodes identified

The project is then ready for `python _ops/controller.py start batch01`.

---

# Harness V2 Entry

## Source Of Truth
- Runtime entry: [harness/framework/entry.md](./harness/framework/entry.md)
- Runtime manifest: [harness/project/run.manifest.md](./harness/project/run.manifest.md)

## Default Routing
- Before any writing, verifying, or recording, resolve the current run from `harness/project/run.manifest.md`.
- Writer only follows:
  - `harness/framework/entry.md`
  - `harness/framework/input-contract.md`
  - `harness/framework/write-contract.md`
  - `harness/project/run.manifest.md`
  - `harness/project/source.map.md`
  - active `harness/project/batch-briefs/batchNN_*.md`
  - `voice-anchor.md`（优先）→ 回退 `character.md`（声纹锚）
- Verify only follows:
  - `harness/framework/verify-contract.md`
  - `harness/framework/regression-contract.md`
  - optional regression packs under `harness/project/regressions/`
  - `_ops/episode-lint.py`
  - `_ops/script-aligner.md`
- Record only follows:
  - `harness/framework/memory-contract.md`
  - `_ops/script-recorder.md`
  - `harness/project/state/*`

## Hard Gates
- Writer must write candidate files only to `drafts/episodes/`.
- Published files in `episodes/` are controller-promoted outputs only.
- Verify reads draft lane only.
- Record writes `harness/project/state/*` only.
- Legacy v1 files under `harness/legacy/v1/` are not runtime authority.

