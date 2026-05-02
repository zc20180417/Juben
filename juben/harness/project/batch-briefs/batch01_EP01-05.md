# Batch Brief: EP-01 ~ EP-05

- owned episodes: EP-01, EP-02, EP-03, EP-04, EP-05
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第1章 首富从继承养猪场开始 ~ 第6章 配合饲料 至 第7章 砖厂的恐怖利润
- adjacent continuity: 【动作】段启荣催盖章，陆行川在印泥落下前按住陆振海的手。 -> 【动作】陆行川盯着融化的冰车，逼买方按缺货行情重新报价。 -> 【动作】陆行川把修机、加柜、人工、电费、押金写成一张周转表。 -> 【动作】陆行川当场重排值班表，把温控记录挂到冷库门口。 -> 【信息】陆行川说明冷库不能只出租，必须做可复制的速冻样品。
- draft output paths:
  - drafts/episodes/EP-01.md
  - drafts/episodes/EP-02.md
  - drafts/episodes/EP-03.md
  - drafts/episodes/EP-04.md
  - drafts/episodes/EP-05.md

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
- EP-01：第1章 首富从继承养猪场开始
  - transformative_adaptation:
    - source_function: 开局逼选；主角阻止家业被低价转走，用不能明说的未来认知改写家庭命运入口。
    - new_episode_event: 陆振海即将把旧冷库和制冰车间转给段启荣，陆行川赶到合同桌前按住印泥，要求给他七天用冷库挣出第一笔现钱。
    - setting_translation: 卖养猪场转译为转让旧冷库；卖猪行情转译为夏季冰块和果蔬预冷窗口；合同和印泥作为现场逼选道具。
    - must_keep_function: 保留“家业被卖前一秒抢回”“父亲不信”“外人催签”“主角不能说重生”的压力。
    - must_change_surface: 不得出现养猪场、猪价、建材转投、仔猪、饲料。
    - do_not_copy: 不得沿用原文卖场合同、猪价判断、建材风险表达或父子争执原句。
  - 【动作】段启荣催盖章，陆行川在印泥落下前按住陆振海的手。 -> 【对抗】陆振海当众骂他胡闹，段启荣用违约金和欠款逼陆家签字。 -> 【信息】陆行川只能用天气、菜站缺冰、冷库位置和七天现金流解释判断。 -> 【钩子】陆行川立下七天赌约：冷库若挣不出钱，他亲自签转让。
  - knowledge_boundary:
    - 陆振海不知道陆行川重生，只知道儿子突然强硬反对卖冷库。
    - 段启荣只知道交易被搅黄，不知道陆行川掌握未来窗口。
    - 陆行川不能说出后续全部产业布局。
- EP-02：第2章 卖猪
  - transformative_adaptation:
    - source_function: 用第一笔可见收益证明主角不是胡闹，让家人和市场第一次动摇。
    - new_episode_event: 陆行川临时接下菜站和鱼市的缺冰单，制冰车间却因老线路跳闸，第一车冰如果化掉就会赔上信誉。
    - setting_translation: 卖猪议价转译为冰块缺口订单；买方压价转译为菜站趁陆家急用钱压低冰价。
    - must_keep_function: 保留“现场交易压力”“父亲担心砸手里”“主角用供需判断谈价”“第一笔钱落桌”的爽点。
    - must_change_surface: 不得出现出栏车、猪贩、肉价、春节猪源。
    - do_not_copy: 不得近义改写原著卖猪谈价、供需解释和父亲动摇桥段。
  - 【动作】陆行川盯着融化的冰车，逼买方按缺货行情重新报价。 -> 【阻力】老线路跳闸，陆振海要求立刻低价卖掉，别一车冰化在手里。 -> 【信息】陆行川用县城三处停电、菜站明早开市和鱼市保鲜需求压住买方。 -> 【结果】第一车冰高价成交，陆振海第一次把账本推到陆行川面前。
  - knowledge_boundary:
    - 陆振海只看到这一笔订单，不知道后续冷链、速冻和渠道布局。
    - 买方不知道陆行川预判了连续缺冰，只知道眼前缺货。
- EP-03：第3章 扩大规模 至 第4章 招工和贷款
  - transformative_adaptation:
    - source_function: 第一笔收益后不落袋为安，而是继续加码，家庭内部冲突升级为外部融资压力。
    - new_episode_event: 陆行川提出修制冷机、加冷柜、接果蔬预冷长单，必须拿旧门牌和设备登记证去信用社抵押。
    - setting_translation: 扩栏和贷款转译为冷库设备升级、用电改造和周转融资。
    - must_keep_function: 保留“赚到钱后继续押注”“父亲担心风险”“把计划拆成设备、人手、贷款缺口”的功能。
    - must_change_surface: 不得出现猪舍、仔猪、疫病、防疫流程。
    - do_not_copy: 不得复制原著扩栏算账、招工贷款桥段或银行无阻力秒批结构。
  - 【动作】陆行川把修机、加柜、人工、电费、押金写成一张周转表。 -> 【对抗】陆振海要求见好就收，质问设备坏了、订单断了、债谁还。 -> 【现场阻力】信用社主任只认抵押物，不认年轻人的行情判断。 -> 【钩子】陆行川把旧冷库门牌放到柜台上，逼自己进入下一轮赌局。
  - knowledge_boundary:
    - 信用社只知道陆家有一笔冰块订单，不知道后续产业。
    - 陆振海可以动摇，但不能同意无条件放权。
- EP-04：第4章 招工和贷款 至 第5章 准备就绪，购买仔猪
  - transformative_adaptation:
    - source_function: 扩张落地前必须补齐现场能力；主角把风险从口头计划变成可执行清单。
    - new_episode_event: 陆行川一边招临时工、一边整理冷库温控记录，却发现夜里停电记录被老工人瞒下，第一批果蔬预冷单面临赔付。
    - setting_translation: 招工、猪舍、防疫和采购转译为招冷库工、查温控、修线路、建立交接班制度。
    - must_keep_function: 保留“扩张不是一句话，必须解决人手、流程、风险”的功能。
    - must_change_surface: 不得出现购买仔猪、猪舍准备、饲料采购。
    - do_not_copy: 不得沿用原著仔猪进场、村民观望的事件组合。
  - 【动作】陆行川当场重排值班表，把温控记录挂到冷库门口。 -> 【阻力】老工人怕担责，陆振海怕撕破熟人面子。 -> 【结果】陆行川用赔付条款逼众人接受新规矩，第一批果蔬才准入库。 -> 【钩子】预冷车倒进院子，旧冷库正式从保命变成主动接单。
  - knowledge_boundary:
    - 工人只知道陆家要接更多冷库活，不知道后续速冻食品。
    - 陆振海认可规矩有用，但仍担心儿子把熟人关系打碎。
- EP-05：第6章 配合饲料 至 第7章 砖厂的恐怖利润
  - transformative_adaptation:
    - source_function: 主角从等市场行情升级为控成本、控质量，同时发现下一笔快钱入口。
    - new_episode_event: 陆行川提出用旧冷库做小批量速冻样品，沈砚山临时帮他调冻速；同时包装小厂订单暴涨的消息让他看见下一个现金跳板。
    - setting_translation: 配合饲料控成本转译为速冻工艺和损耗控制；砖厂利润转译为包装材料短缺带来的短期机会。
    - must_keep_function: 保留“技术/流程破题”“身边人质疑新方法”“下一笔快钱被看见”的功能。
    - must_change_surface: 不得出现饲料配比、猪喂养、砖厂。
    - do_not_copy: 不得复制原著配合饲料小试和砖厂利润发现的桥段。
  - 【信息】陆行川说明冷库不能只出租，必须做可复制的速冻样品。 -> 【对抗】沈砚山质疑旧机器冻速不稳，陆振海怕赔掉刚来的订单。 -> 【动作】陆行川用小批量试冻和损耗记录压住质疑。 -> 【钩子】包装厂老板求冰保货，陆行川发现包装材料短缺比冷库更急。
  - knowledge_boundary:
    - 众人只知道陆行川想做样品，不知道会做成区域品牌。
    - 包装机会只是刚露头，不能写成投资完成。

## Hard Constraints
- 不能提前写银行贷款、县里支持、速冻食品线或集团成立。
- 不能让陆振海立刻完全相信陆行川。
- 不能提前写速冻产品试产。
- 不能把第一笔收益夸张成支撑全部扩张。
- 不能让贷款无阻力通过。
- 不能跳到县里领导支持。
- 不能提前写现代企业制度完全成型。
- 不能跳过用电、温控、人工这些现场阻力。
- 不能把速冻样品直接写成成熟品牌。
- 不能提前成立集团或便利店线。
