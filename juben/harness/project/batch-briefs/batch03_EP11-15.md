# Batch Brief: EP-11 ~ EP-15

- owned episodes: EP-11, EP-12, EP-13, EP-14, EP-15
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第16章 早期管培生 至 第21章 刘玉芳加盟 ~ 第30章 资金到位 至 第31章 高伟良再次视察
- adjacent continuity: 【动作】梅知夏直接抽查账本、温控记录和赊账名单。 -> 【动作】梅知夏把现金缺口写在黑板上，工人就在门外等工资。 -> 【动作】陆行川打开车厢测温，发现货已经开始回温。 -> 【动作】陆行川把买门面的预算改成冷藏车和周转箱。 -> 【动作】梅知夏当场递出现金流表和坏损下降记录。
- draft output paths:
  - drafts/episodes/EP-11.md
  - drafts/episodes/EP-12.md
  - drafts/episodes/EP-13.md
  - drafts/episodes/EP-14.md
  - drafts/episodes/EP-15.md

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
- EP-11：第16章 早期管培生 至 第21章 刘玉芳加盟
  - transformative_adaptation:
    - source_function: 专业管理者入局，主角从个人判断转向组织能力。
    - new_episode_event: 梅知夏来旧冷库面试，第一件事不是谈工资，而是翻账本指出坏损、赊账和职责混乱。
    - setting_translation: 职业经理人加盟转译为冷链企业早期管理审计。
    - must_keep_function: 保留“专业人不被主角光环轻易打动”“加入前先设条件”的功能。
    - must_change_surface: 不得出现原著职业经理人姓名和养殖企业管理语境。
    - do_not_copy: 不得复制原著加盟谈判条件和台词。
  - 【动作】梅知夏直接抽查账本、温控记录和赊账名单。 -> 【对抗】陆振海觉得她还没入职就管太宽。 -> 【信息】陆行川给出授权边界：财务、人事、流程她都能改，但结果要落地。 -> 【钩子】梅知夏接过钥匙，说第一刀先砍熟人账。
  - knowledge_boundary:
    - 梅知夏知道陆行川有扩张野心，但不知道全部未来布局。
    - 陆振海不知道她会成为核心管理者。
- EP-12：第23章 资金问题 至 第24章 赚一笔快钱
  - transformative_adaptation:
    - source_function: 现金流压力逼出短期破局，主角必须证明不是靠空想扩张。
    - new_episode_event: 梅知夏发现账上现金只够三天电费和工资；陆行川决定接一笔高风险节庆冻品急单。
    - setting_translation: 资金问题和快钱方案转译为冷库电费、工资、押金和节庆订单。
    - must_keep_function: 保留“现金卡死”“必须用短期机会救局”“管理者质疑风险”的功能。
    - must_change_surface: 不得出现原著快钱渠道、养殖扩张资金细节。
    - do_not_copy: 不得复制原著资金危机解决路径。
  - 【动作】梅知夏把现金缺口写在黑板上，工人就在门外等工资。 -> 【阻力】急单赔付条款很重，陆振海反对用旧机器赌交付。 -> 【选择】陆行川接单，但要求沈砚山先划出停机预案。 -> 【钩子】急单货车提前到场，合同上的赔付数字压住所有人。
  - knowledge_boundary:
    - 工人只知道工资危险，不知道陆行川后续现金安排。
    - 梅知夏可以质疑，不可提前无条件信任。
- EP-13：第24章 赚一笔快钱 至 第26章 回到养猪场，准备扩张
  - transformative_adaptation:
    - source_function: 短期订单落地，主角把家庭资产重新推向扩张。
    - new_episode_event: 节庆冻品急单卡在运输车不到位，陆行川临时调民用货车加冰保温，保住订单后决定组建自有冷链车队。
    - setting_translation: 回到养殖场准备扩张转译为回到冷库后建立配送能力。
    - must_keep_function: 保留“危机现场解决”“赢得下一步扩张理由”的功能。
    - must_change_surface: 不得出现回养猪场、扩栏、仔猪。
    - do_not_copy: 不得复制原著回场扩张的结构。
  - 【动作】陆行川打开车厢测温，发现货已经开始回温。 -> 【阻力】司机拒绝担责，客户要求赔付。 -> 【结果】临时加冰和路线调整保住交付，急单回款入账。 -> 【钩子】陆行川当场说：没有自己的车，以后每笔钱都悬在路上。
  - knowledge_boundary:
    - 客户只知道这次交付险过，不知道陆行川要建车队。
    - 陆振海知道车队花钱，但未完全理解战略。
- EP-14：第27章 进军建筑领域的可能 至 第29章 贸易公司和物流公司
  - transformative_adaptation:
    - source_function: 主业之外的能力延伸成组织板块，产业链第一次显形。
    - new_episode_event: 陆行川放弃买更体面的门面，改买二手冷藏车和周转箱，成立配送班组。
    - setting_translation: 建筑、服装贸易和物流公司转译为包装材料、冷链配送和终端周转。
    - must_keep_function: 保留“跨出原资产边界”“父亲看不懂但必须选择”的功能。
    - must_change_surface: 不得出现建筑、鞋子、萝卜裤、原著贸易公司。
    - do_not_copy: 不得复用原著进军建筑/服装/物流的外壳。
  - 【动作】陆行川把买门面的预算改成冷藏车和周转箱。 -> 【对抗】陆振海认为车会折旧，段启荣趁机嘲笑陆家钱烧得快。 -> 【信息】陆行川用配送半径和货损率解释车队价值。 -> 【钩子】第一辆冷藏车挂上厂牌，竞品老板脸色变了。
  - knowledge_boundary:
    - 竞品只知道陆家有车，不知道后续连锁渠道。
    - 陆振海还不知道车队会承担跨区域订单。
- EP-15：第30章 资金到位 至 第31章 高伟良再次视察
  - transformative_adaptation:
    - source_function: 现金流和外部审视共同落地，主角获得下一阶段入场券。
    - new_episode_event: 信用社追加授信前，贺远桥再次来现场检查，梅知夏必须用账本、交付和用工证明陆家不是乱扩张。
    - setting_translation: 资金到位和领导再次视察转译为授信评估与县里复查。
    - must_keep_function: 保留“资金不是天降，是结果换来的”“干部二次确认”的功能。
    - must_change_surface: 不得出现原著对应领导姓名、养殖扩张贷款语境。
    - do_not_copy: 不得复制原著视察和资金到位台词。
  - 【动作】梅知夏当场递出现金流表和坏损下降记录。 -> 【阻力】信用社提出追加抵押，贺远桥追问安全责任。 -> 【结果】有限授信落地，陆行川获得小线试产资金。 -> 【钩子】陆行川把钱没有投进新冷库，而是投向速冻产品线。
  - knowledge_boundary:
    - 信用社只认可当前账面，不承诺长期贷款。
    - 贺远桥只给观察机会，不做全面背书。

## Hard Constraints
- 不能让梅知夏变成崇拜型秘书。
- 不能提前写食品品牌估值。
- 不能让钱凭空解决。
- 不能跳过合同风险和设备风险。
- 不能直接写完整物流公司成立。
- 不能提前出现边境贸易。
- 不能提前写便利店爆火。
- 不能写成现代大型物流公司。
- 不能跳到产业园。
- 不能把县里写成无条件站队。
