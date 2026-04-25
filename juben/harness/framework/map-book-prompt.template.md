# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回指定的 source map 目标文件；不要调用模型 CLI，不要 promote，不要 record。

你现在只做一件事：基于原著和 `book.blueprint.md`，返回一份完整可用的 `source.map.md`。

禁止事项：
- 不要解释 `source.map` 是什么
- 不要讲流程、架构、promote、state、draft 的概念
- 不要返回分析、摘要、注意事项、教程
- 不要返回代码块
- 不要返回半成品
- 如果你没有输出完整 `# Source Map` 文档，这次结果就会被判定为失败

必读文件：
- AGENTS.md
- {{entry_rel}}
- {{run_manifest_rel}}
- {{novel_rel}}
- {{blueprint_rel}}

你的任务：
- 读取原著和 `book.blueprint.md`
- 直接产出 `{{source_map_rel}}` 的完整正文

执行要求：
- 只输出完整 `source.map.md` 正文
- 不要输出任何解释性前言或后记
- 不要提 lock、state、promote、run.log
- 不要返回 JSON Schema 或示例解释
- 输出必须以 `# Source Map` 开头
- 输出里的 `mapping_status` 必须是 `complete`

分集原则：
- 你做的是“短剧分集编排”，不是“原著事件摘录”
- 当前项目目标总时长来自 `run.manifest.md`，本次为约 {{target_total_minutes}} 分钟；必须围绕这个总时长、单集时长和原著有效戏剧单元共同编排
- 不按 80-100 集付费长链条拖长，也不把必要主戏压成提纲切片
- source.map 必须使用剧中改名后的姓名，不能沿用原著人物名
- 剧中所有主要人物、反派、关键配角的姓名必须与原著姓名完全不同；不能只改姓或只改名，不能使用同音、近音、叠字变体
- 如 `book.blueprint.md` 已给出“剧名 -> 原著对应人物”映射，必须全程沿用；如未给出，先在 source.map 顶部补 `## Character Rename Map` 再统一使用剧名
- 每一集都应当是一个可以成立的短剧单元，不是只完成几个动作点就停
- 一集至少要形成一个完整主戏：进入 -> 对抗/变化 -> 结果或钩子
- 不要把分集切成“提纲式事件切片”
- 不要只因为一个事件发生了就立刻切集，必须看这一集的主戏是否已经跑完
- 如果当前 source span 只够“入局”而不够形成第一轮正面冲突，应自然吃进下一小段 source
- 首集尤其不能薄：首集至少应完成“异常入局 + 第一轮关系冲突 + 强钩”，不能只停在“刚到门口 / 风暴将起”
- EP-01 到 EP-03 必须按黄金开场设计：每集第一场第一组动作或第一句台词就进入异常、冲突、羞辱、逼选、误认、证据或身份错位
- EP-02 和 EP-03 必须在 EP-01 基础上升级，不得重复同一种误认、盘问或拉扯
- 每 3-5 集安排一个阶段性小爽点或释放，每 8-10 集安排一个大反转、大打脸或关系重排；这些应体现在 episode title、must-keep beats 或 ending_function 中
- 章节只用于定位，不作为平均切分单位
- 不能为了凑集数，把同一种羞辱、盘问、试探或拉扯拆成多个过薄小集

本次运行参数：
- total_episodes: {{episodes}}
- batch_size: {{batch_size}}
- adaptation_strategy: {{strategy}}
- dialogue_adaptation_intensity: {{intensity}}
- target_total_minutes: {{target_total_minutes}}
- target_episode_minutes: {{target_episode_minutes}}
- episode_minutes_min: {{episode_minutes_min}}
- episode_minutes_max: {{episode_minutes_max}}

每集必须包含的字段：
- `**source_chapter_span**:`
- `**must-keep_beats**:`
- `**knowledge_boundary**:`
- `**must-not-add / must-not-jump**:`
- `**ending_function**:` 只有在收尾目标非常明确时才填写

字段要求：
- `must-keep_beats` 保持 3-5 条
- 每条 beat 必须是“可执行的成集任务”，不是抽象标签
- beats 必须帮助 writer 写出完整主戏，不要只列动作摘要
- `knowledge_boundary` 必须写清本集关键角色“当场知道什么 / 还不知道什么 / 可以怎么称呼对方”
- `knowledge_boundary` 不是剧情摘要；它用于防止 writer 把编剧全知信息偷跑进角色台词
- 对误认、认亲、掉马、替身、隐瞒身份、陌生人初见类集数，必须明确称谓解锁顺序：介绍前只能用中性称谓，不能提前喊姓氏、全名、职位或关系词
- `source_chapter_span` 要能支撑这些 beats 真正写满这一集
- `must-not-add / must-not-jump` 只写 source 边界和不可抢跑内容，不要写风格建议

输出格式要求：
- 顶部必须包含：
  - `# Source Map`
  - `- mapping_status: complete`
  - `- total_episodes: ...`
  - `- batch_size: ...`
  - `- total_batches: ...`
  - `- target_total_minutes: ...`
  - `- target_episode_minutes: ...`
  - `- episode_minutes_min: ...`
  - `- episode_minutes_max: ...`
  - `- adaptation_strategy: ...`
  - `- dialogue_adaptation_intensity: ...`
- 若需要补充人物改名映射，放在顶部参数之后，标题为 `## Character Rename Map`
- 每个 batch 以 `## Batch 01 (EP01-05): ...` 表示
- 每个 episode 以 `### EP01: ...` 表示

唯一允许的输出内容，就是完整 `source.map.md` 正文。
