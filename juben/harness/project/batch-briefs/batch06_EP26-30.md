# Batch Brief: EP-26 ~ EP-30

- owned episodes: EP-26, EP-27, EP-28, EP-29, EP-30
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第57章 饲料厂估值 至 第58章 新版方便面 ~ 第65章 期货对冲 至 第66章 开户
- adjacent continuity: 【动作】乔南枝当场拆开新版包装，展示冷柜陈列和复购表。 -> 【动作】主厂开机，第一批产品还没出线，外面装卸队先乱了。 -> 【动作】乔南枝在邻县货架前看到竞品贴出降价牌。 -> 【动作】旧冷库门头摘下，新集团牌子挂上。 -> 【动作】韩策把原料涨价曲线和采购缺口摆到会议桌上。
- draft output paths:
  - drafts/episodes/EP-26.md
  - drafts/episodes/EP-27.md
  - drafts/episodes/EP-28.md
  - drafts/episodes/EP-29.md
  - drafts/episodes/EP-30.md

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
- EP-26：第57章 饲料厂估值 至 第58章 新版方便面
  - transformative_adaptation:
    - source_function: 估值和产品升级并行，品牌从能卖变成能复制。
    - new_episode_event: 投资人再次压估值，乔南枝把新版包装和冷柜复购数据摆上桌，证明品牌不是散货。
    - setting_translation: 饲料厂估值和新版方便面转译为冷链食品品牌估值和新版速冻产品。
    - must_keep_function: 保留“估值争夺”“新品升级”“渠道数据反打”的功能。
    - must_change_surface: 不得出现饲料厂、方便面。
    - do_not_copy: 不得复制原著估值和新品会议。
  - 【动作】乔南枝当场拆开新版包装，展示冷柜陈列和复购表。 -> 【阻力】投资人认为县城品牌没有溢价，只愿按设备估值。 -> 【反击】陆行川要求按冷柜网络和配送能力重新估。 -> 【钩子】竞品宣布降价封柜，估值谈判被渠道战打断。
  - knowledge_boundary:
    - 投资人只看到当前数据，不知道后续区域扩张。
    - 竞品不知道陆行川已准备新厂投产。
- EP-27：第59章 饲料厂投产与开业 至 第60章 战斗英雄刘浩
  - transformative_adaptation:
    - source_function: 新产能投产，同时引入硬执行人才补齐秩序。
    - new_episode_event: 新速冻主厂开机当天，装卸队与竞品人员冲突，退伍军人秦峥出手稳住现场。
    - setting_translation: 饲料厂开业和战斗英雄入场转译为速冻主厂投产与车队/仓储纪律负责人加入。
    - must_keep_function: 保留“开业大节点”“硬执行人才入场”的功能。
    - must_change_surface: 不得出现饲料厂开业、战斗英雄原身份细节照搬。
    - do_not_copy: 不得复制原著刘浩入场桥段。
  - 【动作】主厂开机，第一批产品还没出线，外面装卸队先乱了。 -> 【阻力】竞品人员故意堵车，司机要求加钱。 -> 【结果】秦峥用封条、排班和现场纪律压住混乱。 -> 【钩子】陆行川让秦峥接车队和仓库，第一条规矩是“货比人情大”。
  - knowledge_boundary:
    - 秦峥只知道企业缺纪律，不知道后续边境订单。
    - 工人不知道他会成为核心执行负责人。
- EP-28：第61章 远乡方便面 至 第62章 远丰的家底
  - transformative_adaptation:
    - source_function: 品牌正式走向区域市场，家底公开带来新目标。
    - new_episode_event: 新品牌进入邻县货架，竞品用低价和退货威胁围堵；梅知夏在会上亮出真实家底，要求陆行川选主攻方向。
    - setting_translation: 方便面品牌和企业家底转译为速冻食品区域铺货和供应链资产盘点。
    - must_keep_function: 保留“品牌起势”“资产盘点”“选择下一阶段主攻”的功能。
    - must_change_surface: 不得出现方便面、远乡、远丰家底。
    - do_not_copy: 不得复制原著品牌和家底汇报。
  - 【动作】乔南枝在邻县货架前看到竞品贴出降价牌。 -> 【阻力】店主要求陆行川跟降，否则撤柜。 -> 【信息】梅知夏摊出家底：现金、车队、产能都不够全面开战。 -> 【钩子】陆行川决定不跟低价，先拿下学校和单位食堂冷柜。
  - knowledge_boundary:
    - 店主只看眼前利润。
    - 团队知道家底紧，不知道后续集团改组。
- EP-29：第63章 远丰实业 至 第64章 远东农场负责人
  - transformative_adaptation:
    - source_function: 公司集团化，并安排外地资源负责人，为后续跨区域布局铺路。
    - new_episode_event: 陆行川把冷库、食品、车队、终端整合为“棠源供应链”，并面试北方原料基地负责人。
    - setting_translation: 远丰实业和远东农场负责人转译为供应链集团改组和北方原料基地负责人。
    - must_keep_function: 保留“集团牌子立起来”“外地基地负责人确定”的功能。
    - must_change_surface: 不得出现远丰、远东农场。
    - do_not_copy: 不得复制原著集团成立和农场负责人场面。
  - 【动作】旧冷库门头摘下，新集团牌子挂上。 -> 【阻力】陆振海担心牌子太大，实际根基不稳。 -> 【信息】陆行川说明北方基地不是囤地，是保原料和加工适配。 -> 【钩子】北方负责人带来消息：原料价格要变，必须提前锁。
  - knowledge_boundary:
    - 员工知道集团改组，不知道远期资本牌桌。
    - 北方负责人只负责原料基地，不知道全集团风控。
- EP-30：第65章 期货对冲 至 第66章 开户
  - transformative_adaptation:
    - source_function: 风控线打开，主角把市场投机转化为企业采购保护。
    - new_episode_event: 韩策提出开设大宗原料风控账户，陆行川明确只能围绕白糖、油脂、淀粉采购需求做锁价，不许赌方向。
    - setting_translation: 期货对冲和开户转译为食品原料采购风控账户。
    - must_keep_function: 保留“金融工具入场”“必须绑定风险纪律”的功能。
    - must_change_surface: 不得出现玉米/大豆期货和原著开户细节。
    - do_not_copy: 不得复制原著期货操作台词和品种组合。
  - 【动作】韩策把原料涨价曲线和采购缺口摆到会议桌上。 -> 【阻力】陆振海听到开户就以为赌博，要求陆行川停手。 -> 【规则】陆行川定下仓位、止损、退出和采购对应关系。 -> 【钩子】账户开通，韩策提醒：第一笔浮盈最容易让人失控。
  - knowledge_boundary:
    - 陆振海不知道风控机制，只听见“账户”和“行情”。
    - 韩策知道规则，但还未被完全信任。

## Hard Constraints
- 不能让估值瞬间翻倍无依据。
- 不能提前写富豪榜。
- 不能写成打架爽戏解决全部问题。
- 不能跳到跨境贸易。
- 不能靠降价一句话赢渠道战。
- 不能提前写北方基地。
- 不能把集团成立写成全国巨头。
- 不能提前写大规模海外收购。
- 不能写成暴富投机。
- 不能提前写边境订单盈利。
