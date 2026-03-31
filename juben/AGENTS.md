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

- Follow this `AGENTS.md` first. For short-drama creation and novel adaptation tasks, this file delegates workflow details to `OPENAI.md`.
- `OPENAI.md` is the authoritative runtime spec for this repository.
- If `OPENAI.md` conflicts with `README.md`, `CLAUDE.md`, `script-aligner.md`, `script-recorder.md`, or any older notes in the repo, `OPENAI.md` wins.
- `CLAUDE.md` is the historical baseline that `OPENAI.md` was derived from. Use it only as background when `OPENAI.md` is silent.
- Treat older Kimi-specific or experimental workflow notes as legacy reference, not active runtime instructions.

## Startup Behavior

- For creative writing, short-drama planning, and novel adaptation requests in this repo, read `OPENAI.md` before responding in depth.
- If the user provides novel text, chapter summaries, or adaptation requirements without an explicit command, assume novel-adaptation mode and start from `/adapt`, then continue into `/outline` unless the user says otherwise.
- Keep all creative outputs and user-facing communication in Chinese unless the user explicitly requests another language.

## Workflow Rules

- Enforce the gated flow defined in `OPENAI.md`:
  - create or revise content
  - run aligner check
  - only on PASS treat it as writable
  - update recorder/progress
  - guide the user to the next step
- If the runtime has no separate aligner or recorder tools, simulate them explicitly in the reply using the structure required by `OPENAI.md`.
- Write project artifacts to the standard paths defined in `OPENAI.md`, including:
  - `outline.md`
  - `character.md`
  - `episode_index.md`
  - `episodes/EP-XX.md`
  - `script.progress.md`
  - `versions/`

## File Priority

1. `OPENAI.md`
2. `README.md`
3. `CLAUDE.md`
4. `script-aligner.md`
5. `script-recorder.md`
6. `short-drama-cn.md`

## Codex CLI Guidance

- In Codex CLI sessions, prefer explicitly grounding on `OPENAI.md` before starting long creative work.
- When instructions appear ambiguous, say that you are following `OPENAI.md` and proceed with the least-surprising workflow.
- If the repository is opened outside Git, it is acceptable to run with `--skip-git-repo-check`.

