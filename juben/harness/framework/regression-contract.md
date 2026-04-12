# Regression Contract

## Regression Pack
项目层回归包定义在：
- `harness/project/regressions/`
- `active.md` 不是必需文件；只有存在活跃回归时才需要具体 pack 文件

## Required Fields
- `regression_id`
- `scope`
- `failure_mode`
- `blocking_rule`
- `severity`
- `status`

## Required Regression Classes
- 对白触发链断裂
- 自然事件被改成设计局
- 概述性信息被改成具体事故
- 单点关系稀释
- `os` 语义悬空
- 即时钩子未兑现

## Enforcement
- `severity: P1` 且 `status: active` 的条目必须阻断 promote
- `severity: P2` 可 warning，但同批累计 2 条及以上必须阻断 promote
