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
7. `run <batch_id>`（自动执行 review gate → FAIL? → 生成 revision prompt → 修稿 → 重审 → PASS → promote）
8. `record <batch_id>`

### 修稿→重审循环（`run` 内置）

当 `run` 检测到 review verdict 为 FAIL 时，自动触发修稿循环：

```
run batch01
  └─ review gate: FAIL（3 条 blocking reasons）
       └─ 自动生成 revision prompt packet（含定向修复指令）
            └─ Writer agent 执行修稿 → 写回 drafts/
                 └─ 操作者重新运行 review
                      └─ run batch01（再次进入 gate）
                           └─ review gate: PASS → promote → record
```

最大重试轮数可通过 `--max-retries` 配置（默认 3 轮）。超出上限后 `run` 会报错退出，需要人工介入。

也可以手动触发修稿：

```
.\~revise.cmd batch01   # 从 FAIL review 生成 revision prompt
```

## Chat Command Aliases

| 聊天命令 | 对应命令 |
|---|---|
| `.\~init.cmd ...` | 初始化项目 |
| `.\~extract.cmd` | 生成全书抽取 prompt packet |
| `.\~map.cmd` | 生成 source map prompt packet |
| `.\~start.cmd batch01` | 冻结批次 brief |
| `.\~start.cmd batch01 --write` | 生成/刷新写作与评审 prompt packet |
| `.\~check.cmd batch01` | 仅重建 review packet |
| `.\~review.cmd batch01 PASS --reviewer <name>` | 记录 PASS 评审结论 |
| `.\~review.cmd batch01 FAIL --reviewer <name> --reason "..."` | 记录 FAIL 评审结论 |
| `.\~revise.cmd batch01` | 从 FAIL review 生成定向修稿 prompt packet |
| `.\~run.cmd batch01` | 正式发布批次（含 review gate + 自动 revise→re-review 循环） |
| `.\~promote.cmd batch01` | 仅用于 promote 中断后的恢复 |
| `.\~record.cmd batch01` | 写入批次状态记忆 |
| `.\~export.cmd` | 刷新 output/ 交付包 |
| `.\~clean.cmd` | 清理运行态产物 |

## 当前原则

- 不再使用旧的 lint/aligner gate 作为主流程门禁
- Python 只做结构校验和流程调度，不代替 reviewer 判断内容质量
- 上游只提供上下文合同，不给 writer 预写导演拆场
- review packet 由 `start --write` 自动生成，`check` 只是手动重生入口
- `run` 内置 strict 评审质量检查：拒绝 smoke reviewer 和无 evidence/无 reason 的空 PASS
- FAIL 后自动生成 revision prompt packet，Writer 定向修稿后重新提交评审，默认最多 3 轮
