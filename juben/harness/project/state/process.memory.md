# Process Memory
_最后更新：2026-04-06 12:55_

## 活跃流程问题
- 2026-04-06：subagent 在主控验完后继续改正文，导致 PASS 结果被覆盖
  - 归类：发布通道缺失
  - 防复发：writer 只准写 `drafts/episodes/`，published lane 只准 controller promote
- 2026-04-06：`EP-03 -> EP-04` 出现假即时钩子，下一集没有兑现
  - 归类：连续性 gate 缺失
  - 防复发：即时动作钩子若不在下一集第一场兑现，verify 直接 FAIL
- 2026-04-06：`os` 曾出现语义悬空，读者需自行补主宾
  - 归类：主观窗口约束不足
  - 防复发：将 `os` 语义悬空纳入 verify warning/fail
- 2026-04-06：原著单点“被看见”场曾被扩成较热闹群像场
  - 归类：单点关系保护不足
  - 防复发：将单点关系稀释纳入 verify warning/fail

## 当前执行准则
- 先冻 batch，再写 draft
- 先 verify draft，再 promote
- 先 promote，再 record
