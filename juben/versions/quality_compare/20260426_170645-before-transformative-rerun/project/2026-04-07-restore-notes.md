# 2026-04-07 恢复说明

## 背景

上次对话中测试 `controller.py init` 时，意外覆盖了项目运行文件。本次从会话 transcript 中提取原始内容，逐一恢复。

## 恢复清单

| 文件 | 说明 |
|---|---|
| `harness/project/source.map.md` | 60集完整映射（beats/约束/ending type），410行 |
| `harness/project/state/` 全部7个文件 | script.progress、story.state、relationship.board、open_loops、quality.anchor、process.memory、run.log |
| `harness/project/batch-briefs/batch01_EP01-05.md` | batch01 brief，status=promoted |
| `episodes/EP-01..EP-60.md` | 从 git staging area 恢复60个剧集文件 |
| `harness/project/locks/*.lock` | 3个锁模板文件重建 |

## 测试修复

- `test_harness_v2.py` 中 `test_dual_lanes_exist` 移除了对 `drafts/episodes/EP-XX.md` 的断言 — batch01 已 promote，草稿通道为空是正确状态

## 验证结果

- `controller.py next` → batch01 promoted，下一步 `start batch02`
- `controller.py validate` → 7个 state 文件全部 PASS
- `controller.py status` → EP-01~05 正确归属 batch01
- 57 + 6 = 63 个测试全部通过
