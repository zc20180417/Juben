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

# Current Project Instructions

## Source Of Truth

- Follow this `AGENTS.md` first.
- [runtime-core.md](./runtime-core.md) is the canonical writing-stance spec — only describes how to write, no file routing.
- [OPENAI.md](./OPENAI.md) and [CLAUDE.md](./CLAUDE.md) are thin runtime entry files that point to `runtime-core.md`.
- Operational docs live under [_ops/](./_ops/) and are not default Writer context.

## Startup Behavior

- For short-drama creation and novel adaptation, read [runtime-core.md](./runtime-core.md) before responding in depth.
- If the task is Writer-phase generation, do not read `_ops/` docs by default.
- If the task is explicit checking or recording, then read:
  - [_ops/script-aligner.md](./_ops/script-aligner.md)
  - [_ops/script-recorder.md](./_ops/script-recorder.md)

## Workflow Rules

- Writer phase:
  - create or revise content
  - self-check against `runtime-core.md`
  - only then continue
- Check phase:
  - run `_ops/episode-lint.py`
  - run `_ops/script-aligner.md`
  - only on PASS treat content as writable
- Record phase:
  - pass lint JSON + aligner result into `_ops/script-recorder.md`
  - update progress via `_ops/script-recorder.md`

## Writer Default Context

**单一事实源**：Writer 读取范围仅由本节定义。`runtime-core.md` 不含文件白名单。

- Allowed by default:
  - `runtime-core.md`
  - `voice-anchor.md`（如已填写）
  - `character.md`
  - `outline.md`
  - `episode_index.md`
  - `quality.anchor.md` if present
  - `story.state.md` / `relationship.board.md` / `open_loops.md` if present
  - `script.progress.md`
  - current episode brief and adjacent episode context
- Not allowed by default:
  - `_ops/script-aligner.md`
  - `_ops/script-recorder.md`
  - `_ops/README.md`
  - `_ops/comparisons/`
  - design specs, review notes, rationale docs

## Phase-Specific Loading Order

- **Writer phase**: `runtime-core.md` → `voice-anchor.md`（如已填写）→ `character.md` → 素材文件（见 Writer Default Context）
- **Check phase**: `_ops/script-aligner.md` → `runtime-core.md`（aligner 引用写法基准）
- **Record phase**: `_ops/script-recorder.md`
- **Platform entry**: `OPENAI.md` / `CLAUDE.md`（仅启动时读取，指向 `runtime-core.md`）
