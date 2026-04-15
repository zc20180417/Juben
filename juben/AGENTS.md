# Agent Runtime Entry

- Read [harness/framework/entry.md](./harness/framework/entry.md)
- Read [harness/project/run.manifest.md](./harness/project/run.manifest.md)
- 如果用户输入以 `~` 开头（如 `~init`、`~extract-book`、`~map-book`、`~start`、`~run`），按 `entry.md` 的 Chat Command Aliases 解释，不在本文件定义并行命令集
- Resolve writer / verifier / recorder inputs from `entry.md`; do not define a parallel workflow here
- Treat Harness V2 as the only workflow source of truth
- Workflow authority lives only in `harness/framework/*`, `harness/project/*`, `_ops/controller.py`, `_ops/episode-lint.py`, `_ops/script-aligner.md`, and `_ops/script-recorder.md`
