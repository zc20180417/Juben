# Batch Brief: EP-06 ~ EP-10

- owned episodes: EP-06, EP-07, EP-08, EP-09, EP-10
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第7章 砖厂的恐怖利润 至 第8章 卖猪，惊人的收益 ~ 第15章 春节 至 第16章 早期管培生
- adjacent continuity: 【动作】陆行川把冷库、冰块、包装周转三本账摊在陆振海面前。 -> 【动作】陆行川把订单、用工、用电改造和消防清单交给贺远桥。 -> 【对抗】贺远桥当场验货，要求陆行川解释坏损率和赔付机制。 -> 【爽点】之前看笑话的人带礼上门，称陆家冷库翻身。 -> 【关系】亲戚饭桌上从劝卖冷库变成劝陆家带人发财。
- draft output paths:
  - drafts/episodes/EP-06.md
  - drafts/episodes/EP-07.md
  - drafts/episodes/EP-08.md
  - drafts/episodes/EP-09.md
  - drafts/episodes/EP-10.md

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
- EP-06：第7章 砖厂的恐怖利润 至 第8章 卖猪，惊人的收益
  - transformative_adaptation:
    - source_function: 第一阶段收益兑现，主角证明机会不止一个，并把现金流思路摆到家人面前。
    - new_episode_event: 陆行川帮包装小厂抢下冷藏运输和纸箱周转单，账本上的利润第一次超过冷库本身。
    - setting_translation: 砖厂暴利和卖猪收益转译为包装材料短缺、冷藏周转和订单结算。
    - must_keep_function: 保留“账本砸桌”“旁人改口”“父亲从反对转为追问风险”的功能。
    - must_change_surface: 不得出现砖厂、卖猪、猪价暴利。
    - do_not_copy: 不得复制原著阶段性首富和收益震动桥段的具体表达。
  - 【动作】陆行川把冷库、冰块、包装周转三本账摊在陆振海面前。 -> 【爽点】之前等着看笑话的人改口，开始问陆家还收不收人。 -> 【关系】陆振海不再骂他胡闹，只追问下一步怎么守住风险。 -> 【钩子】陆行川提出：冷库只是入口，真正要抓的是“从冷到卖”的整条路。
  - knowledge_boundary:
    - 外人只看到陆家赚钱，不知道后续食品和渠道布局。
    - 陆振海开始信任，但不完全放权。
- EP-07：第9章 养猪场扩张计划 至 第10章 镇长来访
  - transformative_adaptation:
    - source_function: 家庭项目升级为地方项目，政府审视从机会变成压力。
    - new_episode_event: 陆行川准备扩大冷链业务，贺远桥突然带人检查冷库安全、用电、消防和就业承诺。
    - setting_translation: 养殖扩张和镇长来访转译为冷链基础设施扩容与县里安全检查。
    - must_keep_function: 保留“干部不听空话，只问风险、就业、税收”的功能。
    - must_change_surface: 不得出现养猪扩栏、环保防疫、镇长支持养殖场。
    - do_not_copy: 不得复用原著镇长来访、养猪场扩张计划的事件组合。
  - 【动作】陆行川把订单、用工、用电改造和消防清单交给贺远桥。 -> 【阻力】贺远桥追问一旦断电、食品坏货、工人受伤谁负责。 -> 【信息】陆行川用冷链缺口和县里农产品外运难题回应。 -> 【钩子】贺远桥没有拍板，只留下一句：三天后看你现场交付。
  - knowledge_boundary:
    - 贺远桥只知道冷库近期活了，不知道陆行川后续集团化。
    - 陆行川不能提前许诺全国品牌。
- EP-08：第11章（地方支持节点）至 第12章 投资砖厂的想法
  - transformative_adaptation:
    - source_function: 主角用现场结果换来有限政策口子，并把短期现金机会纳入主线。
    - new_episode_event: 陆行川在三天内完成冷藏交付，贺远桥给出临时通行和用电协调；陆行川同时盯上即将断供的包装材料厂。
    - setting_translation: 镇里给支持和投资砖厂转译为县里给冷链通行口子与包装材料现金跳板。
    - must_keep_function: 保留“支持不是白给，是现场交付换来的”“下一条现金线进入视野”的功能。
    - must_change_surface: 不得出现砖厂作为建材投资。
    - do_not_copy: 不得照搬原著政府背书与砖厂机会的顺序台词。
  - 【对抗】贺远桥当场验货，要求陆行川解释坏损率和赔付机制。 -> 【结果】县里给出有限口子，不是全面背书。 -> 【信息】陆行川把包装材料短缺纳入周转计划，而不是盲目跨行。 -> 【钩子】陆振海发现儿子已经在同时盘冷库、包装和食品样品三条账。
  - knowledge_boundary:
    - 贺远桥知道陆行川有产业想法，但不清楚后续渠道和风控。
    - 陆振海知道包装能赚钱，不知道它会变成供应链一环。
- EP-09：第13章 首富 至 第14章 招兵买马
  - transformative_adaptation:
    - source_function: 阶段性赚钱带来面子和新风险，主角意识到必须招人和建组织。
    - new_episode_event: 陆家被称为“冷库翻身户”，亲戚和熟人都来求岗位，陆行川却先公布岗位责任和赔付制度。
    - setting_translation: 本地首富和招兵买马转译为县城冷链生意出名后的熟人求职与制度化招聘。
    - must_keep_function: 保留“赚钱后外部态度变化”“主角找能管事的人而非只找劳力”的功能。
    - must_change_surface: 不得出现养猪户首富、猪场招工。
    - do_not_copy: 不得复用原著首富称呼和招工桥段的具体场面。
  - 【爽点】之前看笑话的人带礼上门，称陆家冷库翻身。 -> 【动作】陆行川当众贴出岗位责任、温控记录和赔付制度。 -> 【阻力】熟人觉得他不讲情面，陆振海也担心得罪乡里。 -> 【钩子】陆行川提出要找能管账、管人、管货的人。
  - knowledge_boundary:
    - 外人只知道陆家赚钱，不知道后续组织架构。
    - 新人只能知道当前岗位。
- EP-10：第15章 春节 至 第16章 早期管培生
  - transformative_adaptation:
    - source_function: 家庭作坊进入组织化早期，年轻人培养和第一条产品线同步启动。
    - new_episode_event: 春节饭桌上亲戚态度转变，陆行川却把第一批学徒和速冻小线值班表摆上桌。
    - setting_translation: 春节和管培生转译为熟人社会压力下的学徒制、车间值班和小线试产。
    - must_keep_function: 保留“亲戚态度变化”“组织化开始”“老工人与新人冲突”的功能。
    - must_change_surface: 不得出现养殖管培生或猪场岗位。
    - do_not_copy: 不得复制原著春节亲戚与管培生入局的表达。
  - 【关系】亲戚饭桌上从劝卖冷库变成劝陆家带人发财。 -> 【动作】陆行川公布第一批学徒名单，要求从温控、包装、配送轮岗。 -> 【阻力】老工人怕新人抢饭碗，陆振海担心年轻人不稳。 -> 【钩子】速冻小线第一次开机，所有人盯着第一盘样品出霜。
  - knowledge_boundary:
    - 亲戚只知道陆家变有钱，不知道后续集团化。
    - 学徒只进入早期培养，不具备高管能力。

## Hard Constraints
- 不要把收益写成无限资金。
- 不要提前出现职业经理人团队。
- 不能让政府支持无条件落地。
- 不能提前写市级领导。
- 不能把包装厂写成主业替代冷链。
- 不能提前写全县产业园落地。
- 不能提前让梅知夏入职。
- 不能把陆家写成全国性财富。
- 不能把学徒立刻写成成熟管理层。
- 不能跳到便利店开业。
