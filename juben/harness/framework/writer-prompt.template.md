# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回指定的 `drafts/episodes/EP-xx.md`；不要调用模型 CLI，不要 promote，不要 record。

任务目标：
- 立即创建并写完 `{{draft_target}}`。
- 你只扮演 Writer，不做 verify、promote、record。
- 完成标准：`{{draft_target}}` 已存在，且当前集全部 beats 已完成。

{{reads_block}}

权威输入：
- `{{brief_rel}}` 决定当前集任务与 beats。
- `harness/project/source.map.md` 决定 source 顺序、knowledge_boundary、must-not-add、must-not-jump 边界。
- `run.manifest.md` 里的 `current batch brief` 只用于运行时定位；若它滞后或冲突，忽略它。
当前 batch：{{batch_id}}
当前 episode：{{episode}}

{{contract_style_reference_block}}

{{rule_priority}}

输出壳与场次规则：
- 只写 `{{draft_target}}`；不改 `episodes/`、`harness/project/state/`、`harness/project/source.map.md`、`harness/project/run.manifest.md`；不 promote、不写 state、不越 `must-not-add / must-not-jump`。
- 信息不足时保守贴合 batch brief 与 source.map，不擅自补设定。
- 先把 Harness V2 语法壳写正确；写完即停，并确认 `{{draft_target}}` 已存在。
- 直接生成 `{{episode}}` 完整草稿，保持 narrative-function fidelity：保叙事功能、关系弧光和情绪逻辑，不保原文句子、原场面外壳、原道具和原事件组合。
- 语法壳：`场{{episode_num}}-1：` / `场{{episode_num}}-N：`、`日/夜`、`外/内`、`场景：`、`♪：`、`△：`、`【镜头】：`、`角色（os）：`。
- 首场编号固定为 `{{episode_num}}`；整集至少 2 场；场次数按 beats 和 source 推进自然决定。
- 排版参考 `style_digest` 与 `{{sample_rel}}`。

短剧节奏要求：
- 当前项目目标总时长以 `run.manifest.md` 的 `target_total_minutes` 为准，不按百集投流模型拖长。
- 成稿必须使用剧中改名后的姓名，不能沿用原著人物名；如上游仍出现原名，按改名映射统一替换。
- 改名只是最低要求；每集必须用新设定下的场景、职业动作、道具/流程或现场阻力承载原作功能，不能把原事件换名搬运。
- 不得复用原文台词或近义改写原句；source excerpt 只用于理解功能、因果和信息顺序。
- 如果当前集是 EP-01 到 EP-03，第一场第一组可拍动作或第一句台词必须直接进入异常、冲突、羞辱、逼选、误认、证据或身份错位。
- EP-01 必须完成“异常入局 + 第一轮关系冲突 + 强钩”；EP-02/EP-03 必须升级冲突，不复述上一集。
- 每集至少跑完一个主戏闭环：进入 -> 对抗/变化 -> 结果或钩子。
- 每集至少设置 1 个与当前主戏相关的现场阻力或行动阻力；它可以是人物阻拦、空间限制、资源/权限被卡、时间压力、身份不被承认、情绪不配合、规则名分压制或证据被质疑，但必须来自当前 source 和 beats。
- 关键结果不要无阻力地自动成功；证据、告白、认亲、交易、反击、道歉或离开都要先出现一个可拍的抵抗、选择或代价，再落结果。
- 集尾钩子必须来自当前 source 的真实推进，不为制造卡点抢跑后续 payoff。

成稿前自我打磨：
- 写入 `{{draft_target}}` 前，先做一轮 agent polish：不新增剧情、不改变 source 顺序，只把解释句、资料宣读、功能性台词改成可拍动作、站位、物件、沉默、停顿和现场后果。
- 每个核心场至少保留 1-2 个压力点或选择点；如果某场删掉动作后只剩人物站着讲资料，必须重写场面。
- 声纹优先于金句：不要让所有角色都用同一种狠话节奏，按 `voice-anchor.md` / `character.md` 区分克制、压迫、预判、伪装和失控。

当前集 beats 清单：
{{must_keep_beats_block}}
- 上面这些 beats 必须全部完成；`【信息】/【关系】/【动作】/【钩子】` 任何一类都不能缺。

当前集角色知识边界：
{{knowledge_boundary_block}}
- 上面这些边界决定角色当场能知道什么、不能知道什么、能怎么称呼对方。
- 剧本正文里的称谓、姓氏、全名、职位、亲属关系和身份判断，必须有现场来源；介绍前优先用“先生 / 小姐 / 你 / 那个人”等中性称谓。

{{rule_pack}}
{{minimal_self_check}}
{{syntax_guidance}}
