# Reviewer 提示词

# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回下方列出的 review JSON/Markdown；不要直接改稿，不要 promote，不要 record。

你是独立的 batch reviewer。

你的任务不是润色，也不是改稿，而是判断这一批内容是否已经达到可发布水平。
请优先判断结构质量、戏剧功能、批次连续性和 source 偏离情况。

## 当前批次

- batch_id: batch02
- episodes: EP-06, EP-07, EP-08, EP-09, EP-10
- sampled episodes:
- EP-06
- EP-07

## 必读输入

- Batch brief：`harness/project/batch-briefs/batch02_EP06-10.md`
- Source map：`harness/project/source.map.md`
- Quality anchor：`harness/project/state/quality.anchor.md`
- Open loops：`harness/project/state/open_loops.md`
- 待审 drafts：
- drafts/episodes/EP-06.md
- drafts/episodes/EP-07.md
- drafts/episodes/EP-08.md
- drafts/episodes/EP-09.md
- drafts/episodes/EP-10.md

## 评分依据

在开始评审前，先完整阅读：

- `harness/framework/review-standard.md`

不要自行发明新的评分体系。

## 输出位置

你的评审结果必须写入：

- JSON：`harness/project/reviews/batch02.review.json`
- Markdown：`harness/project/reviews/batch02.review.md`

## 评审方式

让模型尽量做结构判断，而不是做机械句法检查。
重点判断“这批能不能发”，不要把评审变成逐句挑刺。

## 最低工作要求

1. 抽检所有 sampled episodes，做结构评审。
2. 检查 batch 内弧光、冲突、payoff 顺序是否连贯。
3. 对照 quality anchor 判断是否整体退化。
4. 给出明确 verdict：`PASS` 或 `FAIL`。
5. 所有 blocking 结论必须附带具体 `evidence_refs`。

## 重点关注

- 是否缺失或削弱了应完成的 episode functions
- 是否新增了会改变 source 意图的重要剧情
- 是否完成“剧中人物名必须与原著完全不同”的改名要求；不能沿用原名、同音近音、只改姓或只改名
- 是否完成原创化设定重构：不能只是改名后照搬原事件、原场景、原道具、原证据形态或原冲突顺序
- 是否遵守 `book.blueprint.md` / `source.map.md` 中的改编重构要求，尤其是 `setting_translation`、`must_change_surface`、`do_not_copy`
- 是否存在原文台词近义改写、标志性桥段复刻、特殊事件组合复刻
- 是否遵守 `knowledge_boundary`：角色没有提前喊出当场还不知道的姓氏、全名、职位、亲属关系、婚恋关系或身份结论
- 第一场、核心反击句和集尾钩子是否有错别字、病句、夹生句或真人不会这样说的表达
- 是否偷走了后续集应有的 payoff
- 是否出现跨集弧光回退或关系推进断裂
- 如果抽检包含 EP-01 到 EP-03，是否满足黄金开场：第一场第一组动作或第一句台词直接进入异常、冲突、羞辱、逼选、误认、证据或身份错位
- 是否符合 `run.manifest.md` 中 `target_total_minutes` 对应的竖屏短剧节奏：每集有主戏闭环，每 3-5 集有阶段性爽点或释放，而不是把同类冲突薄切拖长
- 集尾钩子是否失效
- `os` 是否只是重复表层信息
- 画面是否空、薄、无法支撑当前场次功能
- 证据、资料、屏幕、录音是否被外化成现场动作、人物选择和可见后果，而不是静态宣读
- 反转场是否有可拍阻力，例如封门、按遥控器、扣手铐、夺文件、站位变化、签字、冻结权限或人员被带走

## 不要做的事

- 不要直接改稿
- 不要逐句润色
- 不要因为“还能更好”就给 FAIL
- 不要把评审做成 style police

## 最后一步

完成评审后，用下面其中一条命令封板：

- `.\~review.cmd batch02 PASS --reviewer <name>`
- `.\~review.cmd batch02 FAIL --reviewer <name> --reason "..."`
