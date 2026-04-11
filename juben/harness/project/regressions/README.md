# Regressions

本目录用于存放项目级回归 pack。

规则：
- 只有存在活跃回归时，才需要新增具体 pack 文件
- 没有活跃回归时，本目录可只保留本说明文件
- 每个具体 pack 文件都必须包含：
  - `regression_id`
  - `scope`
  - `failure_mode`
  - `blocking_rule`
  - `severity`
  - `status`
