# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回下方列出的 `drafts/episodes/EP-xx.md`；不要调用模型 CLI，不要 promote，不要 record。

任务：立即在当前工作区按顺序创建并写完以下草稿文件。完成条件：下面列出的每个目标文件都存在，且每集的全部 beats 已完成。不要输出角色确认，不要索要更多输入，不要只总结规则；在所有目标文件真正写出来之前，不得停止。
你现在只扮演 Harness V2 的 Writer 角色，不扮演 Controller、Verifier 或 Recorder。

必读输入：
- harness/project/state/batch-context/batch01.writer-context.json

权威输入：
- `harness/project/batch-briefs/batch01_EP01-05.md` 决定每集任务与 beats。
- `harness/project/source.map.md` 决定 source 顺序、knowledge_boundary、must-not-add、must-not-jump 边界。
- `harness/project/run.manifest.md` 的 `current batch brief` 只用于运行时定位；若冲突则忽略。
本次只处理 batch：batch01

契约引用：
- 遵循 `harness/framework/write-contract.md` [SECTION:MARKER_FORMAT] [SECTION:OS_RULES] [SECTION:SCENE_RULES] [SECTION:CHARACTER_KNOWLEDGE] [SECTION:PRE_SUBMIT_CHECK]
- 遵循 `harness/framework/writer-style.md` [SECTION:NARRATIVE_POSTURE] [SECTION:SCENE_CRAFT] [SECTION:DIALOGUE_CRAFT] [SECTION:AGENT_POLISH] [SECTION:STYLE_RED_LINES]

冲突优先级：
1. 完成当前集全部 beats > 其他一切；`【信息】/【关系】/【动作】/【钩子】` 任何一类都不能缺失。
2. source 顺序与边界 > 节奏性后拖或压场数；已发生硬事件不能后拖。
3. batch brief 当前集任务 > voice/style 借用；`voice-anchor` 只看气质与禁区，不抢任务优先级。
4. `角色（os）：` 只是壳；不得新增第一人称“我……”式旁白。
5. `must_keep_long_lines` 只有在不违反 `forbidden_fill`、must-not-add、must-not-jump 时才保。

目标文件：
- EP-01 -> drafts/episodes/EP-01.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-01.source.json
  - 场次：首场 `场1-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：开场必须直接进入异常冲突：陌生男人在街头错认姜照眠，现场拦人，不能先铺背景。; 姜照眠不认识顾砚舟，介绍前只能称他为“先生”“这位先生”或“你”，不能提前喊顾先生或全名。; 顾砚舟因她酷似沈知微而失控，坚持带她回沈家确认，姜照眠明确拒绝被当成替身。; 姜照眠用行动争取离开，但被车门、中控、保镖或路线形成现实阻力。; 结尾必须形成强钩：车门锁死或车已驶向沈家，姜照眠被迫卷入一个她尚不知道的豪门漩涡。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：按当场已公开信息保守处理，称谓不抢跑
- EP-02 -> drafts/episodes/EP-02.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-02.source.json
  - 场次：首场 `场2-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：开场直接升级：姜照眠被带到沈家，不是被欢迎，而是被审视、盘问或质疑来历。; 沈怀章与许兰因在亲子鉴定和现实压力间摇摆，确认血缘后也没有真正给出亲情。; 沈雨棠第一次以“沈家女儿”的姿态占位，表面委屈，实际引导父母防备姜照眠。; 姜照眠从期待最低限度解释，转为看清沈家只想控制她、补偿她、安置她。; 结尾落在姜照眠第一次明确划线：她不是回来争宠的人，也不会跪着认亲。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：按当场已公开信息保守处理，称谓不抢跑
- EP-03 -> drafts/episodes/EP-03.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-03.source.json
  - 场次：首场 `场3-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：开场用宴会现场羞辱或服装事件切入，姜照眠被当作上不了台面的“外来者”。; 沈雨棠借宾客、礼服、身份差距制造难堪，逼姜照眠在公众面前出丑。; 姜照眠不靠解释求饶，而是用专业细节或作品归属反制。; 顶级设计师“眠”的身份被现场关键人物或证据逼近公开，沈家和宾客态度反转。; 结尾卡在身份刚被认出或即将被完全确认，沈雨棠第一次真正慌乱。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：按当场已公开信息保守处理，称谓不抢跑
- EP-04 -> drafts/episodes/EP-04.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-04.source.json
  - 场次：首场 `场4-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：开场从宴会余波继续：沈雨棠试图把翻车解释成误会，沈家想大事化小。; 顾砚舟第一次公开站到姜照眠一侧，但姜照眠指出他最初也是错认和强迫的一部分。; 沈怀章、许兰因用补偿、房间、股份或名分试图安抚，暴露他们仍在用利益处理亲情。; 姜照眠拒绝被“补偿”收买，要求的是边界、尊重和真相。; 结尾形成新压力：顾砚舟意识到想靠权势靠近她无效，沈雨棠转向更隐蔽的反扑。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：按当场已公开信息保守处理，称谓不抢跑
- EP-05 -> drafts/episodes/EP-05.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-05.source.json
  - 场次：首场 `场5-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：开场必须是沈家主动求和或安排“家庭修复”场面，但现场仍把沈雨棠放在姜照眠前面。; 沈雨棠用示弱、旧情、父母愧疚继续占据道德高位，逼姜照眠显得“不懂事”。; 姜照眠逐条拆穿所谓亲情的条件：需要她让、忍、退，却无人要求沈雨棠付出代价。; 姜照眠明确断开对沈家亲情幻想，选择自己离开或只保留必要法律关系。; 结尾给出阶段钩：沈雨棠发现软招无效，开始盯上姜照眠的事业或设计资料。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：按当场已公开信息保守处理，称谓不抢跑

顺序写作要求：
1. 严格按上面列出的 episode 顺序逐个完成，禁止跳集、并集或提前写后面的 episode。
2. 每完成一集后，先确认对应草稿文件已写入磁盘，再开始下一集。
3. 写每一集前，先重新读取该集对应的 `source excerpt`，并从中建立当前集的内部 `must_keep` 清单。
4. 写每一集前，先读取该集的 `knowledge_boundary`，确认角色当场知道什么、还不知道什么、能怎么称呼对方。
5. 写下一集之前，只重新读取刚写完的上一集草稿和必要的相邻集上下文，再决定承接边界。
6. 整个批次里优先保护相邻集之间的信息增量和关系渐进，不要为了提速把多集写成同一种试探节奏。

短剧节奏要求：
- 当前项目目标总时长以 `run.manifest.md` 的 `target_total_minutes` 为准，不按百集投流模型拖长。
- 成稿必须使用剧中改名后的姓名，不能沿用原著人物名；如上游仍出现原名，按改名映射统一替换。
- EP-01 到 EP-03 必须按黄金开场执行：第一场第一组可拍动作或第一句台词直接进入异常、冲突、羞辱、逼选、误认、证据或身份错位。
- EP-01 必须完成“异常入局 + 第一轮关系冲突 + 强钩”；EP-02/EP-03 必须升级冲突，不复述上一集。
- 每一集至少跑完一个主戏闭环：进入 -> 对抗/变化 -> 结果或钩子。
- 每一集至少设置 1 个与当前主戏相关的现场阻力或行动阻力；它可以是人物阻拦、空间限制、资源/权限被卡、时间压力、身份不被承认、情绪不配合、规则名分压制或证据被质疑，但必须来自当前 source 和 beats。
- 关键结果不要无阻力地自动成功；证据、告白、认亲、交易、反击、道歉或离开都要先出现一个可拍的抵抗、选择或代价，再落结果。
- 集尾钩子必须来自当前 source 的真实推进，不为制造卡点抢跑后续 payoff。

成稿前自我打磨：
- 每集写入文件前，先做一轮 agent polish：不新增剧情、不改变 source 顺序，只把解释句、资料宣读、功能性台词改成可拍动作、站位、物件、沉默、停顿和现场后果。
- 每个核心场至少保留 1-2 个压力点或选择点；如果某场删掉动作后只剩人物站着讲资料，必须重写场面。
- 声纹优先于金句：不要让所有角色都用同一种狠话节奏，按 `voice-anchor.md` / `character.md` 区分克制、压迫、预判、伪装和失控。

批次顺序写作最小规则：
- 每集只读自己的 excerpt，并完成自己在 batch brief / batch_facts 里的全部 beats；压场数不能成为缺 beat 的理由。
- `event_anchors` 定顺序；`must_keep_names`、`forbidden_fill` 守边界；有 `reusable_source_lines` 就先保原句。
- 整集至少 2 场；按当前戏的推进自然拆场，不为凑格式硬拆或硬并。
- 非终场最后一个 `△` 必须带服务 beats 的新增推进，别停在静态结果。
- 禁新增第一人称叙述；`角色（os）：` 也不能写成“我……”式内心旁白。
- 上一集只给边界；承接最多 1-2 个镜头。模型知道不等于角色知道；身份、关系、真名只按当场已公开信息和 `knowledge_boundary` 写。
- 称谓必须有现场来源；介绍前不提前喊姓氏、全名、职位或关系词。
- `voice-anchor` 只看气质与禁区，优先级低于当前集 beats 和 source 边界。

硬约束：
- 只能写 `drafts/episodes/EP-XX.md`
- 不得 promote
- 不得写 state
- 不得修改 `episodes/`
- 不得修改 `harness/project/run.manifest.md`
- 不得修改 `harness/project/source.map.md`
- 不得修改 `harness/project/state/`
- 不得修改 locks、tests、docs 或其他无关文件
- 不得跨越 source.map 里的 must-not-add / must-not-jump
- 全部目标草稿都写完后立刻停止，不要继续做 verify、promote、record

批次级最小自检：
- 每一集单独成稿，不得把两集合并到同一个文件。
- 每一集的 `【信息】/【关系】/【动作】/【钩子】` beats 都要完成，不能为了压场数缺项。
- 若 source excerpt 已发生硬事件，而正文还停在“等待 / 前夜 / 即将揭晓”，说明你把事件往后拖了。
- 每集至少 2 场，非终场结尾必须留下服务 beats 的新增推进。
- 每集写入前必须完成自我打磨：删解释、压台词、补动作/站位/沉默/现场后果，但不得新增 source 外剧情。
- `角色（os）：` 不得写成新增第一人称“我……”旁白。
- 称谓、姓氏、全名、职位、亲属关系和身份判断必须有现场来源；介绍前不得抢跑称谓。


