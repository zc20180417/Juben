# Process Memory

## 活跃流程问题
- 2026-04-15｜问题：`map-book` 生成的 `source.map.md` 新格式与 controller 旧解析器漂移，直接导致 `start batch01` 报 `batch01 not found in source.map`。｜归类：合同 / 解析兼容性漂移｜防复发规则：凡是改 `source.map.md` 模板或 `_ops/run_book_map.py`，必须同步跑 `_parse_source_map()` / `_compute_verify_tiers()` 回归测试，解析器保持双格式兼容直到旧格式彻底退场。
- 2026-04-15｜问题：writer 默认提示未把 Harness V2 硬语法讲清，首轮整批稿被写成 Markdown 场记，lint 出现整批 `scene_count=0`、`camera_count=0`。｜归类：writer 提示 / 工具契约不足｜防复发规则：writer 提示必须显式列出 `场 / △ / ♪ / 【镜头】 / 角色（os）` 壳，并附本仓库通过样例路径；批量重写前先拿 1 集跑 lint 验壳。
- 2026-04-15｜问题：整批 lint fail 时如果直接继续修内容，会浪费轮次；batch01 实际先要修格式壳和可拍性，再谈剧情细修。｜归类：调试流程失序｜防复发规则：当同一批次同时出现 `scene_count=0`、`camera_count=0`、`os_vo_count=0` 这类统一错误，先定位 parser / 语法 / 壳层问题，再进入逐场内容返修。
- 2026-04-15｜问题：`run_writer.py` 提示词和 `passing-episode.sample.md` 同时把场次壳写成模糊的 `场x-x` 样例，writer 在 batch02 smoke 集里把单集拆成 `场1-1 / 场1-2 / 场2-1` 式分幕，直接触发 `scene_count` 失败。｜归类：writer 提示 / 样例漂移｜防复发规则：writer prompt 必须显式写明“当前集号固定 + 整集最多 3 场”，样例文件也必须注明首位数字随集号变化；相关变更必须绑定 `_ops/test_run_writer.py` 回归。
- 2026-04-15｜问题：controller 早期把 lint `warn` 也视为 FAIL，但 batch01 的实际 promote 语义是“无 `episode_failures` / `scene_failures` 即可过 gate”，导致 batch02 的 smoke / run 门槛比合同更严。｜归类：lint gate 语义漂移｜防复发规则：`_lint_episode_payload()` 只以 `episode_failures` 与 `scene_failures` 判 fail，warnings 仅作告警；必须保留 warn-only episode 的回归测试。
- 2026-04-15｜问题：batch02 生成过程中 `claude` writer CLI 额度耗尽，主 writer backend 中断，只能切换到本地 `codex exec` 才补齐 EP-07~10。｜归类：外部 writer 依赖脆弱｜防复发规则：writer backend 必须具备降级链路；主 backend 不可用时先保住 smoke 集，再切到备用 writer，并对备用 writer 回稿逐集跑本地 lint 后才允许进入 `run`。
- 2026-04-15｜问题：非生产环境的测试 / 替代 CLI 运行把 `batch03` 和 `extract-book novel.md` 之类的噪声条目写进了真实 `run.log.md`，污染 production ledger。｜归类：日志隔离缺失｜防复发规则：tests、临时 CLI、fallback writer 的 controller 运行必须指向独立临时 workspace 或 mock `_append_log()`；真实 `run.log.md` 只允许生产批次写入。
- 2026-04-15｜问题：`start batch03` 在主 writer backend 失效后已经冻结 batch brief 并持有 `batch.lock`，但 controller 没有内建 fallback / resume handoff，只能人工接管写稿并再走 `run batch03`。｜归类：writer failover 断点缺失｜防复发规则：writer stage 一旦在锁已拿到后失败，controller 必须输出可恢复 checklist，并支持显式 resume / fallback writer 注入，而不是把恢复路径留给人工猜测。
- 2026-04-15｜问题：备用 `codex exec` writer 会自报“已按 lint 规则手工复核”，但其运行环境里没有权威 Python / `_ops/episode-lint.py`，这些自检结论并不可靠。｜归类：校验权威外泄 / 环境不一致｜防复发规则：任何备用 writer 的“已 lint / 已验证”声明都不计入正式 gate；权威 lint 只能在主 workspace 由 controller 或主控 agent 重新执行。

## 当前执行准则
- Story memory 只写剧情事实；流程失败模式与补强规则只写在本文件，不回灌到剧情 state。
- `source.map.md` 的输出格式变更必须和 controller 解析测试绑定提交，不能只改生成器。
- writer 批量返工时先做 syntax-first 诊断：一集过 `_ops/episode-lint.py` 之后再扩到整批。
- `warn` 但无 `episode_failures` / `scene_failures` 的 lint 结果视为可过 gate，只作为质量告警处理。
- 主 writer backend 不可用时，允许切备用 writer，但必须限定目标文件并逐集本地 lint 后再进入 `run`。
- 批次在 `batch.lock` 已拿到后若 writer stage 中断，恢复动作必须沿用同一个 frozen brief 和同一批 draft lane，禁止重新漂移输入。
- 备用 writer 的自带自检不具正式效力；所有 draft 必须回到主 workspace 重新跑权威 `_ops/episode-lint.py` 后，才能进入 controller `run`。
- tests、临时脚本和替代 CLI 不得写入真实 `run.log.md`；日志必须和生产 workspace 隔离。
- `character.md` 与 `voice-anchor.md` 仍未提取，后续批次如需保持声纹稳定，必须优先补这两份基础资料。
