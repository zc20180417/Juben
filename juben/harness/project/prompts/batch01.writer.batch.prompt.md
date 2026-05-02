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
2. source 功能顺序与边界 > 节奏性后拖或压场数；已发生的叙事功能不能后拖。
3. batch brief 当前集任务 > voice/style 借用；`voice-anchor` 只看气质与禁区，不抢任务优先级。
4. `角色（os）：` 只是壳；不得新增第一人称“我……”式旁白。
5. 原文句子只作含义参考；不得复用原句、近义改写原句或照搬标志性场面外壳。

目标文件：
- EP-01 -> drafts/episodes/EP-01.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-01.source.json
  - 场次：首场 `场1-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】段启荣催盖章，陆行川在印泥落下前按住陆振海的手。; 【对抗】陆振海当众骂他胡闹，段启荣用违约金和欠款逼陆家签字。; 【信息】陆行川只能用天气、菜站缺冰、冷库位置和七天现金流解释判断。; 【钩子】陆行川立下七天赌约：冷库若挣不出钱，他亲自签转让。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：陆振海不知道陆行川重生，只知道儿子突然强硬反对卖冷库。; 段启荣只知道交易被搅黄，不知道陆行川掌握未来窗口。; 陆行川不能说出后续全部产业布局。
- EP-02 -> drafts/episodes/EP-02.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-02.source.json
  - 场次：首场 `场2-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】陆行川盯着融化的冰车，逼买方按缺货行情重新报价。; 【阻力】老线路跳闸，陆振海要求立刻低价卖掉，别一车冰化在手里。; 【信息】陆行川用县城三处停电、菜站明早开市和鱼市保鲜需求压住买方。; 【结果】第一车冰高价成交，陆振海第一次把账本推到陆行川面前。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：陆振海只看到这一笔订单，不知道后续冷链、速冻和渠道布局。; 买方不知道陆行川预判了连续缺冰，只知道眼前缺货。
- EP-03 -> drafts/episodes/EP-03.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-03.source.json
  - 场次：首场 `场3-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】陆行川把修机、加柜、人工、电费、押金写成一张周转表。; 【对抗】陆振海要求见好就收，质问设备坏了、订单断了、债谁还。; 【现场阻力】信用社主任只认抵押物，不认年轻人的行情判断。; 【钩子】陆行川把旧冷库门牌放到柜台上，逼自己进入下一轮赌局。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：信用社只知道陆家有一笔冰块订单，不知道后续产业。; 陆振海可以动摇，但不能同意无条件放权。
- EP-04 -> drafts/episodes/EP-04.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-04.source.json
  - 场次：首场 `场4-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】陆行川当场重排值班表，把温控记录挂到冷库门口。; 【阻力】老工人怕担责，陆振海怕撕破熟人面子。; 【结果】陆行川用赔付条款逼众人接受新规矩，第一批果蔬才准入库。; 【钩子】预冷车倒进院子，旧冷库正式从保命变成主动接单。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：工人只知道陆家要接更多冷库活，不知道后续速冻食品。; 陆振海认可规矩有用，但仍担心儿子把熟人关系打碎。
- EP-05 -> drafts/episodes/EP-05.md
  - excerpt: harness/project/state/source-excerpts/batch01/EP-05.source.json
  - 场次：首场 `场5-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【信息】陆行川说明冷库不能只出租，必须做可复制的速冻样品。; 【对抗】沈砚山质疑旧机器冻速不稳，陆振海怕赔掉刚来的订单。; 【动作】陆行川用小批量试冻和损耗记录压住质疑。; 【钩子】包装厂老板求冰保货，陆行川发现包装材料短缺比冷库更急。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：众人只知道陆行川想做样品，不知道会做成区域品牌。; 包装机会只是刚露头，不能写成投资完成。

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
- 改名只是最低要求；每集必须用新设定下的场景、职业动作、道具/流程或现场阻力承载原作功能，不能把原事件换名搬运。
- 不得复用原文台词或近义改写原句；source excerpt 只用于理解功能、因果和信息顺序。
- 每集写入前必须确认：如果把剧名替回原名、把行业/场景替回原作后几乎仍是同一场戏，就必须重构场面外壳。
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
- `event_anchors` 定叙事功能顺序；`must_keep_names`、`forbidden_fill` 守边界；原文句子只作含义参考，不保原句。
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


