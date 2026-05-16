# Batch Brief: EP-31 ~ EP-35

- owned episodes: EP-31, EP-32, EP-33, EP-34, EP-35
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第67章 固定仓位浮盈加仓 至 第68章 边境贸易 ~ 第76章 “三角贸易” 至 第78章 对未来期货价格的分析
- adjacent continuity: 【动作】韩策把浮盈表翻过去，先亮风险线。 -> 【动作】牵线人递合同，秦峥发现运输条款被改。 -> 【动作】陆行川看北方仓库，发现纸面产能和现场条件不一致。 -> 【动作】韩策把三条线的现金占用叠在一张表上。 -> 【动作】陆行川用三张订单把原料、运输、终端铺货连成闭环。
- draft output paths:
  - drafts/episodes/EP-31.md
  - drafts/episodes/EP-32.md
  - drafts/episodes/EP-33.md
  - drafts/episodes/EP-34.md
  - drafts/episodes/EP-35.md

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
- EP-31：第67章 固定仓位浮盈加仓 至 第68章 边境贸易
  - transformative_adaptation:
    - source_function: 初次浮盈考验纪律，并引出跨区域订单机会。
    - new_episode_event: 风控账户出现浮盈，团队有人要求加仓；同一天，边境冷链订单找上门，要求低价长约。
    - setting_translation: 固定仓位浮盈和边境贸易转译为原料风控浮盈与边境冻品/冷链订单。
    - must_keep_function: 保留“赚钱诱惑”“纪律约束”“新贸易机会”的功能。
    - must_change_surface: 不得出现原著期货品种和边境贸易货物。
    - do_not_copy: 不得复制原著浮盈加仓和边贸组局细节。
  - 【动作】韩策把浮盈表翻过去，先亮风险线。 -> 【阻力】有人要求趁行情加仓，陆振海担心赔光。 -> 【信息】边境客户要求长约，价格诱人但运输和汇率风险很重。 -> 【钩子】陆行川只接样单，并要求先验路、验车、验回款。
  - knowledge_boundary:
    - 团队只知道浮盈，不知道后续退出点。
    - 边境客户不知道棠源内部风控纪律。
- EP-32：第69章 再次组局，致远贸易 至 第70章 时代的限制
  - transformative_adaptation:
    - source_function: 贸易平台搭建时暴露时代规则限制，主角必须先验人再验货。
    - new_episode_event: 陆行川重组外贸小组，发现牵线人隐瞒运输扣费和口岸延迟，秦峥当场扣下合同。
    - setting_translation: 贸易公司组局和时代限制转译为边境冷链贸易团队和口岸规则限制。
    - must_keep_function: 保留“组局”“规则限制”“不能只靠关系做生意”的功能。
    - must_change_surface: 不得出现致远贸易原名和原著三角贸易准备细节。
    - do_not_copy: 不得复制原著组局谈判结构。
  - 【动作】牵线人递合同，秦峥发现运输条款被改。 -> 【阻力】对方用“这个年代都这么办”逼陆行川接受灰色规则。 -> 【选择】陆行川宁可放慢订单，也要求回款、验货、冷链责任写清。 -> 【钩子】口岸传来消息：下一批货窗口只剩四十八小时。
  - knowledge_boundary:
    - 牵线人不知道陆行川底线。
    - 团队只知道订单急，不知道后续北方基地安排。
- EP-33：第71章 布局大豆 至 第73章 真主角林建军限时返场
  - transformative_adaptation:
    - source_function: 原料布局从采购转向基地，父亲返场用现实经验压住风险。
    - new_episode_event: 陆行川决定在北方布局马铃薯和玉米淀粉原料基地，陆振海赶到现场，指出仓储、冻害和农户违约风险。
    - setting_translation: 布局大豆、远东分公司和父亲返场转译为北方淀粉作物基地和父亲现场校正。
    - must_keep_function: 保留“上游布局”“父亲用老经验提供现实锚点”的功能。
    - must_change_surface: 不得出现大豆布局、远东分公司、原著父亲限时返场外壳。
    - do_not_copy: 不得复制原著大豆/农场/父亲返场组合。
  - 【动作】陆行川看北方仓库，发现纸面产能和现场条件不一致。 -> 【阻力】当地合作方只报好消息，陆振海当场追问冻害和回款。 -> 【关系】父子第一次在外地项目上形成互补。 -> 【钩子】北方负责人递来设备清单：没有改造设备，基地就是空话。
  - knowledge_boundary:
    - 北方合作方只知道棠源要锁原料，不知道科研线。
    - 陆振海不知道后续设备收购计划。
- EP-34：第74章 见梁永辉，期货市场的隐患 至 第75章 期货部门规划
  - transformative_adaptation:
    - source_function: 风险负责人正式立权，主角接受被制度约束。
    - new_episode_event: 韩策指出边境订单、原料锁价和新厂扩产叠加后，公司现金流会被拉断，要求风控部门有否决权。
    - setting_translation: 见期货负责人和部门规划转译为大宗原料风控负责人立规矩。
    - must_keep_function: 保留“专业风险提醒”“部门制度化”“主角被约束”的功能。
    - must_change_surface: 不得出现期货部门原设和原著人物姓名。
    - do_not_copy: 不得复制原著期货隐患和部门规划台词。
  - 【动作】韩策把三条线的现金占用叠在一张表上。 -> 【阻力】团队认为他太保守，乔南枝担心错过铺货窗口。 -> 【选择】陆行川同意风控对超线项目有一票暂停权。 -> 【钩子】韩策第一张暂停单，签的就是陆行川刚拍板的订单。
  - knowledge_boundary:
    - 团队只知道风控部门有权，不知道后续收益。
    - 韩策不知道陆行川是否真能接受被否决。
- EP-35：第76章 “三角贸易” 至 第78章 对未来期货价格的分析
  - transformative_adaptation:
    - source_function: 组合交易方案成型，同时明确收益和退出边界。
    - new_episode_event: 陆行川设计“北方原料、边境订单、终端铺货”三单联动，韩策要求先写退出条件，秦峥负责验车验仓。
    - setting_translation: 三角贸易、收益和行情分析转译为原料-贸易-终端的组合订单和风控退出。
    - must_keep_function: 保留“复杂交易联动”“收益可见但风险被写清”的功能。
    - must_change_surface: 不得出现原著三角贸易货物和期货价格分析品种。
    - do_not_copy: 不得复制原著三角贸易结构细节。
  - 【动作】陆行川用三张订单把原料、运输、终端铺货连成闭环。 -> 【阻力】任一环延误都会拖垮现金，韩策要求先砍掉超线部分。 -> 【结果】团队按风控版方案执行，收益不最大但活得下来。 -> 【钩子】第一批货刚过口岸，北方设备厂的消息传来。
  - knowledge_boundary:
    - 各合作方只知道自己那一单，不知道整体组合。
    - 团队知道收益变小，但不知道下一步设备布局。

## Hard Constraints
- 不能让浮盈直接变成企业利润。
- 不能让边境贸易无风险成交。
- 不能让灰色规则轻松绕过。
- 不能提前写海外设备厂收购。
- 不能把北方基地写成马上成功。
- 不能提前写科研合作完成。
- 不能让风控只是摆设。
- 不能提前写高层例会收口。
- 不能把复杂交易写成主角一句话全赢。
- 不能提前写设备收购完成。
