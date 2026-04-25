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
6. reviewer 阅读 review prompt，通过 `.\~review.cmd` 回填结论
7. `run <batch_id>`
8. `record <batch_id>`

## Chat Command Aliases

| 聊天命令 | 对应命令 |
|---|---|
| `.\~init.cmd ...` | 初始化项目 |
| `.\~extract.cmd` | 生成全书抽取 prompt packet |
| `.\~map.cmd` | 生成 source map prompt packet |
| `.\~start.cmd batch01` | 冻结批次 brief |
| `.\~start.cmd batch01 --write` | 生成/刷新写作与评审 prompt packet |
| `.\~check.cmd batch01` | 仅重建 review packet |
| `.\~review.cmd batch01 PASS --reviewer <name>` | 记录评审结论 |
| `.\~run.cmd batch01` | 正式发布批次 |
| `.\~promote.cmd batch01` | 仅用于 promote 中断后的恢复 |
| `.\~record.cmd batch01` | 写入批次状态记忆 |
| `.\~export.cmd` | 刷新 output/ 交付包 |
| `.\~clean.cmd` | 清理运行态产物 |

## 当前原则

- 不再使用旧的 lint/aligner gate 作为主流程门禁
- Python 只做结构校验和流程调度，不代替 reviewer 判断内容质量
- 上游只提供上下文合同，不给 writer 预写导演拆场
- review packet 由 `start --write` 自动生成，`check` 只是手动重生入口
