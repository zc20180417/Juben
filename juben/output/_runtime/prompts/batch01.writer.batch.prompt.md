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
  - beats：【动作】第一场第一拍直接写顾沉舟在街头拦住姜照眠，把她错认为温知澜，不能先铺生活日常。; 【信息】姜照眠手里有设计手稿和隐藏设计师身份线索，但本集只让观众看见她不慌、不是普通落魄女人。; 【动作】顾沉舟不顾姜照眠否认，把她带上车并带到温家，形成被迫入局。; 【关系】温正廷、梁淑仪、温绮罗看到姜照眠后不是拥抱，而是盘问、比较、嫌弃。; 【钩子】温正廷强压亲子鉴定，姜照眠当众声明“就算是你们女儿，也未必认这个家”。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：姜照眠开场只知道对方是陌生男人，顾沉舟自报或旁人介绍前，她不能称呼“顾先生”“顾沉舟”或顾氏身份。; 顾沉舟本集误认姜照眠为温知澜，他可以喊“知澜”，但不能已经把她当姜照眠本人追求。; 到温家后，温家人可从顾沉舟带人入场和外貌相似判断她可能有关联，但亲子鉴定前不能确认亲生关系。
- EP-02 -> drafts/episodes/EP-02.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-02.source.json
  - 场次：首场 `场2-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】亲子鉴定报告当场送达，温正廷确认姜照眠就是温家亲生女儿。; 【关系】梁淑仪要求姜照眠感恩懂事，并继续拿温绮罗的礼仪、才艺压她。; 【信息】顾沉舟旁观温家态度，第一次明确看出姜照眠的气场、穿戴和身份都不简单。; 【动作】姜照眠反问生而不养何以为父母，拒绝被规训成温家女儿。; 【钩子】姜照眠离开前与温家切断关系，顾沉舟低声判断温家会后悔。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：亲子鉴定送达后，温家人和姜照眠才可确认血缘事实；确认前的台词不能提前落成“亲生女儿”结论。; 顾沉舟只能基于现场态度、穿戴和气场判断姜照眠不简单，不能提前知道“眠光”身份。
- EP-03 -> drafts/episodes/EP-03.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-03.source.json
  - 场次：首场 `场3-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】开场直接进入温家晚宴，梁淑仪公开介绍温绮罗的设计天赋，把姜照眠排除在体面之外。; 【信息】主持人宣布顶级设计工作室“眠光”创始人登场，全场名流等待结交。; 【动作】姜照眠以“眠光”创始人身份登台，温家三人当众僵住。; 【关系】姜照眠公开点破自己就是被他们嫌弃的亲生女儿，让全场目光转向温家。; 【钩子】合作方和名流改向姜照眠示好，姜照眠留下“温家我高攀不起”的公开反击。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：主持人公开介绍前，宾客和温家不能知道姜照眠就是“眠光”创始人。; 姜照眠登台后，身份可公开；温家人的反应应从“不知道”转为“当众被打脸”。
- EP-04 -> drafts/episodes/EP-04.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-04.source.json
  - 场次：首场 `场4-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】顾沉舟在人群中走向姜照眠，把她从舞台边接下，现场注意力再次转向两人。; 【关系】姜照眠提醒顾沉舟自重，保留边界；顾沉舟公开承认自己要追求的是姜照眠本人。; 【动作】梁淑仪失控阻拦，顾沉舟当场打断，宣布谁为难姜照眠就是与他为敌。; 【信息】顾沉舟以傅氏合作作为筹码，切断温家对姜照眠的压迫空间。; 【钩子】姜照眠没有接受表白，只说自己的事自己能解决，让顾沉舟追在她身后离场。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：晚宴后众人已知道姜照眠的真千金和“眠光”身份，但不能把她写成已经接受温家或顾沉舟。; 顾沉舟可公开追求和护短，但姜照眠仍只承认边界，不承认恋爱关系。
- EP-05 -> drafts/episodes/EP-05.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-05.source.json
  - 场次：首场 `场5-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】温正廷、梁淑仪、温绮罗来到姜照眠顶层公寓，先被她真实生活条件震住。; 【关系】梁淑仪和温正廷放低姿态求她回家，温绮罗继续装委屈、试图把责任揽到自己身上引同情。; 【动作】姜照眠直接拆穿温家不是爱她，而是看中她的身份、钱和价值。; 【关系】梁淑仪伸手想拉她，姜照眠避开，明确不需要温家的家产、亲情和弥补。; 【钩子】姜照眠叫助理送客，门在温家三人面前关上，温绮罗的恨意压到下一轮反扑。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：温家已知道姜照眠身份和价值，但不能默认她愿意回家或接受弥补。; 温绮罗本集只能伪装委屈和暗藏怨恨，不能公开承认恶意反扑计划。

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
