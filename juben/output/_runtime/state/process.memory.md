# Process Memory

## 活跃流程问题

- check 已降级为 review packet 重建入口，不再是主流程必经步骤。
- record 已收编为 controller 自动写入 state，不再依赖 script-recorder.md 手工执行。
- writer 外调命令已改为参数列表执行，避免 shell=True 带来的 Windows 不稳定。

## 当前执行准则
- start batchXX
- start batchXX --write
- batch-review-done batchXX PASS|FAIL --reviewer <name>
- run batchXX
- record batchXX

