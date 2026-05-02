# Batch Brief: EP-16 ~ EP-20

- owned episodes: EP-16, EP-17, EP-18, EP-19, EP-20
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第32章 万家超市 至 第33章 火爆的开业 ~ 第39章 收购县食品厂 至 第41章 年终总结（上）
- adjacent continuity: 【动作】乔南枝亲自调整冷柜陈列，陆行川站在门口看客流。 -> 【动作】乔南枝发现冷柜被断电，坏货压在现场。 -> 【动作】沈砚山调出温控记录，秦峥封住出问题的车厢。 -> 【动作】检查组在货架前询问销量、坏损和就业人数。 -> 【动作】陆行川把欠薪名单分成保线、缓付、谈判三类。
- draft output paths:
  - drafts/episodes/EP-16.md
  - drafts/episodes/EP-17.md
  - drafts/episodes/EP-18.md
  - drafts/episodes/EP-19.md
  - drafts/episodes/EP-20.md

## Run Context
- adaptation_strategy: transformative_adaptation
- dialogue_adaptation_intensity: light
- generation_execution_mode: prompt_packet_external_agent
- generation_reset_mode: clean_rebuild

## Writer Authority
- 当前 batch brief：决定本批每集的任务、beats 与收尾上下文
- `harness/project/source.map.md`：决定 source 顺序、knowledge_boundary、must-not-add、must-not-jump 边界
- `harness/project/run.manifest.md`：只提供运行参数，不裁决内容冲突
- `voice-anchor.md` / `character.md`：仅作气质、禁区与称谓参考，不覆盖当前集任务

## Episode Mapping
- EP-16：第32章 万家超市 至 第33章 火爆的开业
  - transformative_adaptation:
    - source_function: 从生产端进入终端，市场验证带来第一轮渠道爽点。
    - new_episode_event: 陆行川和乔南枝在街口副食店放下第一只自有冷柜，速冻样品开卖当天被抢空。
    - setting_translation: 超市开业爆火转译为冷柜样板终端和速冻产品试卖。
    - must_keep_function: 保留“终端开张”“现场排队”“别人看见渠道价值”的功能。
    - must_change_surface: 不得出现万家超市名称和原著超市开业场景。
    - do_not_copy: 不得复用原著超市爆火的桥段组合。
  - 【动作】乔南枝亲自调整冷柜陈列，陆行川站在门口看客流。 -> 【阻力】店主担心冻品卖不动，占了柜位赔钱。 -> 【爽点】第一批样品被抢空，顾客追问明天还有没有。 -> 【钩子】竞品业务员当场要求店主撤柜。
  - knowledge_boundary:
    - 店主只知道样品好卖，不知道后续连锁计划。
    - 竞品只知道陆家开始抢终端。
- EP-17：第34章 超市扩张计划 至 第35章 疯狂扩张，存栏量突破两万
  - transformative_adaptation:
    - source_function: 成功后遭遇渠道阻力，主角用新机制扩张而不是靠单点爆发。
    - new_episode_event: 竞品联合几个店主锁掉陆家的冷柜电源，乔南枝提出用押金、换货和夜间补货机制反攻。
    - setting_translation: 超市扩张和存栏突破转译为冷柜点位扩张和配送机制升级。
    - must_keep_function: 保留“扩张计划”“现场阻力”“规模突破”的功能。
    - must_change_surface: 不得出现养殖存栏和超市连锁原名。
    - do_not_copy: 不得复制原著疯狂扩张的数字爽点。
  - 【动作】乔南枝发现冷柜被断电，坏货压在现场。 -> 【对抗】竞品业务员逼店主二选一。 -> 【选择】陆行川不吵架，改用换货承诺和夜配保证抢回店主。 -> 【钩子】十家店同时要柜，冷库产能被逼到极限。
  - knowledge_boundary:
    - 店主只知道陆家敢赔敢换，不知道内部现金压力。
    - 竞品不知道陆行川后续会做自有终端。
- EP-18：第36章 建立仔猪繁育体系 至 第38章 市长视察（下）
  - transformative_adaptation:
    - source_function: 规模化后必须建立可追溯体系，并接受更高层级审视。
    - new_episode_event: 一批速冻品被投诉发酸，陆行川用批次码、温控记录和配送封条追出责任点，贺远桥带上级现场复查。
    - setting_translation: 仔猪繁育体系和市长视察转译为食品追溯体系和上级安全复查。
    - must_keep_function: 保留“体系化能力”“危机现场”“上级审视”的功能。
    - must_change_surface: 不得出现繁育体系、市长视察养殖。
    - do_not_copy: 不得照搬原著建立仔猪体系和领导视察组合。
  - 【动作】沈砚山调出温控记录，秦峥封住出问题的车厢。 -> 【阻力】店主要求赔偿，竞品借机散播坏货。 -> 【结果】陆行川追到配送环节漏洞，现场赔付并立新封条制度。 -> 【钩子】上级检查组到门口，贺远桥要求陆行川当场解释。
  - knowledge_boundary:
    - 顾客只知道买到坏货，不知道内部责任链。
    - 检查组只看证据，不预设支持。
- EP-19：第37章 市长视察（上）至 第39章 收购县食品厂
  - transformative_adaptation:
    - source_function: 外部审视转化为扩张机会，主角从小线走向旧厂改造。
    - new_episode_event: 检查组从冷库追到终端货架，看见就业和销售结果；陆行川趁机提出接手濒临停产的县食品二厂。
    - setting_translation: 市长视察和收购食品厂转译为检查组认可后推动旧食品厂改造。
    - must_keep_function: 保留“检查现场变成背书”“收购/接手新产能”的功能。
    - must_change_surface: 不得出现原著食品厂收购的名称和具体条件。
    - do_not_copy: 不得复制原著视察后的收购触发方式。
  - 【动作】检查组在货架前询问销量、坏损和就业人数。 -> 【阻力】老食品二厂债务重、设备旧，没人愿意接。 -> 【信息】陆行川提出不买壳子，先租线改造、保工人、保品控。 -> 【钩子】二厂工人堵门：你要接厂，先把欠薪说清楚。
  - knowledge_boundary:
    - 检查组只认可阶段成果，不知道陆行川长期布局。
    - 二厂工人只关心欠薪和饭碗。
- EP-20：第39章 收购县食品厂 至 第41章 年终总结（上）
  - transformative_adaptation:
    - source_function: 新产能带来旧债和组织压力，阶段成果进入复盘。
    - new_episode_event: 陆行川面对二厂欠薪名单，决定先保关键工人和生产线，再在年终复盘上宣布组织重排。
    - setting_translation: 收购食品厂和年终总结转译为旧厂接管、欠薪处理和组织升级。
    - must_keep_function: 保留“扩张不是白捡资产”“年终复盘确立新阶段”的功能。
    - must_change_surface: 不得沿用原著食品厂财务口径和年终总结内容。
    - do_not_copy: 不得复制原著会议汇报句式。
  - 【动作】陆行川把欠薪名单分成保线、缓付、谈判三类。 -> 【阻力】老工人不信新老板，梅知夏要求先设财务红线。 -> 【结果】第一批关键工人留住，二厂改造进入倒计时。 -> 【钩子】陆行川宣布下一年不是守冷库，而是打区域品牌。
  - knowledge_boundary:
    - 二厂工人不知道陆行川后续资金来源。
    - 团队只知道要升级组织，不知道全部后段布局。

## Hard Constraints
- 不能直接写全国品牌。
- 不能跳到大规模连锁完成。
- 不能让渠道战无成本胜利。
- 不能提前写食品安全事故。
- 不能靠一句解释解决食品安全问题。
- 不能提前写产业园落地。
- 不能让二厂无阻力交接。
- 不能提前写完整产业园。
- 不能一集解决全部欠薪历史。
- 不能提前写富豪榜。
