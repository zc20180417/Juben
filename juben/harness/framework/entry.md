# Harness Entry

这是当前唯一有效的运行入口说明。

## 当前架构

- `controller`：编排 batch、生成 review packet、promote、record
- `writer`：只写 `drafts/episodes/*.md`
- `reviewer`：只审结果，不改稿
- `record`：只更新 `harness/project/state/*`

## Source Of Truth

- [G:\Juben\juben\harness\project\run.manifest.md](/G:/Juben/juben/harness/project/run.manifest.md)
- [G:\Juben\juben\harness\project\book.blueprint.md](/G:/Juben/juben/harness/project/book.blueprint.md)
- [G:\Juben\juben\harness\project\source.map.md](/G:/Juben/juben/harness/project/source.map.md)
- [G:\Juben\juben\harness\framework\write-contract.md](/G:/Juben/juben/harness/framework/write-contract.md)
- [G:\Juben\juben\harness\framework\writer-style.md](/G:/Juben/juben/harness/framework/writer-style.md)
- [G:\Juben\juben\harness\framework\review-standard.md](/G:/Juben/juben/harness/framework/review-standard.md)
- [G:\Juben\juben\_ops\controller.py](/G:/Juben/juben/_ops/controller.py)

## 主流程

1. `init`
2. `extract-book`
3. `map-book`
4. `start <batch_id>`
5. `start <batch_id> --write`
6. reviewer 阅读 review prompt，回填 `batch-review-done`
7. `run <batch_id>`
8. `record <batch_id>`

## Chat Command Aliases

| 聊天命令 | 对应命令 |
|---|---|
| `~init ...` | `python _ops/controller.py init ...` |
| `~extract-book` | `python _ops/controller.py extract-book` |
| `~map-book` | `python _ops/controller.py map-book` |
| `~start batch01` | `python _ops/controller.py start batch01` |
| `~start batch01 --write` | `python _ops/controller.py start batch01 --write` |
| `~check batch01` | `python _ops/controller.py check batch01`（仅重建 review packet） |
| `~run batch01` | `python _ops/controller.py run batch01` |
| `~record batch01` | `python _ops/controller.py record batch01` |
| `~clean` | `python _ops/controller.py clean` |

## 当前原则

- 不再使用旧的 lint/aligner gate 作为主流程门禁
- Python 只做结构校验和流程调度，不代替 reviewer 判断内容质量
- 上游只提供上下文合同，不给 writer 预写导演拆场
- review packet 由 `start --write` 自动生成，`check` 只是手动重生入口
