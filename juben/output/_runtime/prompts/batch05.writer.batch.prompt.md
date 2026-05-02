# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回下方列出的 `drafts/episodes/EP-xx.md`；不要调用模型 CLI，不要 promote，不要 record。

任务：立即在当前工作区按顺序创建并写完以下草稿文件。完成条件：下面列出的每个目标文件都存在，且每集的全部 beats 已完成。不要输出角色确认，不要索要更多输入，不要只总结规则；在所有目标文件真正写出来之前，不得停止。
你现在只扮演 Harness V2 的 Writer 角色，不扮演 Controller、Verifier 或 Recorder。

必读输入：
- harness/project/state/batch-context/batch05.writer-context.json
- drafts/episodes/EP-20.md

权威输入：
- `harness/project/batch-briefs/batch05_EP21-25.md` 决定每集任务与 beats。
- `harness/project/source.map.md` 决定 source 顺序、knowledge_boundary、must-not-add、must-not-jump 边界。
- `harness/project/run.manifest.md` 的 `current batch brief` 只用于运行时定位；若冲突则忽略。
本次只处理 batch：batch05

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
- EP-21 -> drafts/episodes/EP-21.md
  - excerpt: harness/project/state/source-excerpts/batch05/EP-21.source.json
  - 场次：首场 `场21-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】梅知夏撤掉熟人账，重画组织架构。; 【对抗】陆振海担心人分出去后心散，老员工怕被清退。; 【信息】乔南枝提出：终端要复购，必须有品牌而非散货。; 【钩子】陆行川把新品牌名写在黑板上，要求三个月铺满县城冷柜。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：员工只知道部门重排，不知道后续融资和产业园。; 乔南枝知道品牌方向，但未掌握全部资金安排。
- EP-22 -> drafts/episodes/EP-22.md
  - excerpt: harness/project/state/source-excerpts/batch05/EP-22.source.json
  - 场次：首场 `场22-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】叶承稷掰开失败样品，指出冻裂和复热口感问题。; 【阻力】陆行川承认产品没成熟，仍提出长期实验线投入。; 【关系】许望舒在一旁追问企业是否接受失败成本。; 【钩子】叶承稷给出一道题：三天内拿出能上货架的改良样。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：叶承稷不知道陆行川未来布局，只看是否懂长期科研。; 许望舒不能被高薪轻易打动。
- EP-23 -> drafts/episodes/EP-23.md
  - excerpt: harness/project/state/source-excerpts/batch05/EP-23.source.json
  - 场次：首场 `场23-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】乔南枝把涨价后的成本单拍到桌上，爆款样品利润被吃掉。; 【阻力】团队有人要求立刻涨价，店主担心卖不动。; 【信息】陆行川拆出锁原料、稳价格、分批扩产的方案。; 【钩子】他提出建新厂区，梅知夏问第一笔钱从哪来。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：团队只知道原料涨价，不知道后续风控账户。; 店主只关心终端价格。
- EP-24 -> drafts/episodes/EP-24.md
  - excerpt: harness/project/state/source-excerpts/batch05/EP-24.source.json
  - 场次：首场 `场24-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】投资人要求看真实订单，陆行川带他们从冷库走到货架。; 【阻力】县里担心新厂占地和安全，投资人压低估值。; 【信息】梅知夏用坏损率、回款周期和复购数据撑估值。; 【钩子】投资人同意谈，但要求陆行川先拿到千万授信。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：投资人知道企业增长快，但不知后续北方基地。; 县里只看当前项目可控性。
- EP-25 -> drafts/episodes/EP-25.md
  - excerpt: harness/project/state/source-excerpts/batch05/EP-25.source.json
  - 场次：首场 `场25-1`；整集至少 2 场；按 beats 与 source 推进自然拆场
  - beats：【动作】银行现场查封存样、订单、冷柜点位和工资表。; 【阻力】一名副行长质疑陆行川增长太快，现金流扛不住。; 【结果】贺远桥只提供项目证明，不替陆行川担保。; 【钩子】授信批复有条件：食品安全再出一次事故，贷款立刻冻结。；`【信息】/【关系】/【动作】/【钩子】` 不能缺
  - knowledge_boundary：银行只认可可查资产和订单，不知道未来行情。; 贺远桥仍保持审慎。

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


