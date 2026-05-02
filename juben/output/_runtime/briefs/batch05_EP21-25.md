# Batch Brief: EP-21 ~ EP-25

- owned episodes: EP-21, EP-22, EP-23, EP-24, EP-25
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第41章 年终总结（上）至 第44章 远丰的新架构 ~ 第52章 蔬菜加工厂 至 第56章 荷县新城和产业园
- adjacent continuity: 【动作】梅知夏撤掉熟人账，重画组织架构。 -> 【动作】叶承稷掰开失败样品，指出冻裂和复热口感问题。 -> 【动作】乔南枝把涨价后的成本单拍到桌上，爆款样品利润被吃掉。 -> 【动作】投资人要求看真实订单，陆行川带他们从冷库走到货架。 -> 【动作】银行现场查封存样、订单、冷柜点位和工资表。
- draft output paths:
  - drafts/episodes/EP-21.md
  - drafts/episodes/EP-22.md
  - drafts/episodes/EP-23.md
  - drafts/episodes/EP-24.md
  - drafts/episodes/EP-25.md

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
- EP-21：第41章 年终总结（上）至 第44章 远丰的新架构
  - transformative_adaptation:
    - source_function: 企业从单点赚钱升级为组织架构和品牌战略。
    - new_episode_event: 年终会上，陆行川把冷库、二厂、车队、终端拆成事业部，乔南枝要求给产品一个能被记住的新名字。
    - setting_translation: 年终总结和新架构转译为供应链集团早期事业部划分。
    - must_keep_function: 保留“人治到制度”“品牌意识浮出”的功能。
    - must_change_surface: 不得出现远丰架构名称。
    - do_not_copy: 不得复制原著架构升级会议表述。
  - 【动作】梅知夏撤掉熟人账，重画组织架构。 -> 【对抗】陆振海担心人分出去后心散，老员工怕被清退。 -> 【信息】乔南枝提出：终端要复购，必须有品牌而非散货。 -> 【钩子】陆行川把新品牌名写在黑板上，要求三个月铺满县城冷柜。
  - knowledge_boundary:
    - 员工只知道部门重排，不知道后续融资和产业园。
    - 乔南枝知道品牌方向，但未掌握全部资金安排。
- EP-22：第45章 偶遇海洋大学教授 至 第46章 面试
  - transformative_adaptation:
    - source_function: 专业外部资源入局，不被钱打动，先考主角是否尊重技术。
    - new_episode_event: 陆行川带着发裂的速冻样品去见食品工程教授叶承稷，叶承稷让他先解释失败原因。
    - setting_translation: 海洋大学教授和面试转译为食品工程专家考校工艺与加工适配人才。
    - must_keep_function: 保留“专家不轻易合作”“主角用长期投入打动对方”的功能。
    - must_change_surface: 不得出现海洋大学原设、大豆所、原著面试语境。
    - do_not_copy: 不得复制原著教授偶遇和面试桥段。
  - 【动作】叶承稷掰开失败样品，指出冻裂和复热口感问题。 -> 【阻力】陆行川承认产品没成熟，仍提出长期实验线投入。 -> 【关系】许望舒在一旁追问企业是否接受失败成本。 -> 【钩子】叶承稷给出一道题：三天内拿出能上货架的改良样。
  - knowledge_boundary:
    - 叶承稷不知道陆行川未来布局，只看是否懂长期科研。
    - 许望舒不能被高薪轻易打动。
- EP-23：第47章 1994，猪价开启狂飙模式 至 第48章 对饲料厂和食品厂的规划
  - transformative_adaptation:
    - source_function: 市场大行情开启，主角把价格窗口转为产能和原料策略。
    - new_episode_event: 白糖、油脂和淀粉原料突然涨价，乔南枝的新品成本失控；陆行川提出先锁原料再扩产。
    - setting_translation: 猪价狂飙和饲料/食品规划转译为速冻食品原料涨价和产能规划。
    - must_keep_function: 保留“大行情验证主角判断”“规划上游和产能”的功能。
    - must_change_surface: 不得出现猪价、饲料厂规划。
    - do_not_copy: 不得复制原著行情分析和规划会议。
  - 【动作】乔南枝把涨价后的成本单拍到桌上，爆款样品利润被吃掉。 -> 【阻力】团队有人要求立刻涨价，店主担心卖不动。 -> 【信息】陆行川拆出锁原料、稳价格、分批扩产的方案。 -> 【钩子】他提出建新厂区，梅知夏问第一笔钱从哪来。
  - knowledge_boundary:
    - 团队只知道原料涨价，不知道后续风控账户。
    - 店主只关心终端价格。
- EP-24：第49章 远丰产业园 至 第51章 拉投资，食品厂的估值
  - transformative_adaptation:
    - source_function: 产业园和估值线打开，主角必须把蓝图变成投资人能验的资产。
    - new_episode_event: 陆行川向县里和投资人展示旧二厂改造、新厂区、冷链车队和终端数据，争取第一轮扩产资金。
    - setting_translation: 产业园和食品厂估值转译为冷链食品新厂区和品牌估值。
    - must_keep_function: 保留“蓝图被外部审视”“估值来自真实订单和资产”的功能。
    - must_change_surface: 不得出现原著产业园名称、方便面估值。
    - do_not_copy: 不得复制原著拉投资谈判表达。
  - 【动作】投资人要求看真实订单，陆行川带他们从冷库走到货架。 -> 【阻力】县里担心新厂占地和安全，投资人压低估值。 -> 【信息】梅知夏用坏损率、回款周期和复购数据撑估值。 -> 【钩子】投资人同意谈，但要求陆行川先拿到千万授信。
  - knowledge_boundary:
    - 投资人知道企业增长快，但不知后续北方基地。
    - 县里只看当前项目可控性。
- EP-25：第52章 蔬菜加工厂 至 第56章 荷县新城和产业园
  - transformative_adaptation:
    - source_function: 深加工、贷款和新区项目推动企业从地方生意进入区域基础设施。
    - new_episode_event: 陆行川用果蔬深加工、冷链车队和新厂区就业计划，向银行争取千万授信。
    - setting_translation: 蔬菜加工、益农食品、千万贷款、新城产业园转译为果蔬深加工、冷链食品品牌和新厂区授信。
    - must_keep_function: 保留“贷款谈判高压”“产业项目和地方发展绑定”的功能。
    - must_change_surface: 不得出现益农、原著贷款细节、荷县新城原称。
    - do_not_copy: 不得复制原著银行谈判和产业园定位。
  - 【动作】银行现场查封存样、订单、冷柜点位和工资表。 -> 【阻力】一名副行长质疑陆行川增长太快，现金流扛不住。 -> 【结果】贺远桥只提供项目证明，不替陆行川担保。 -> 【钩子】授信批复有条件：食品安全再出一次事故，贷款立刻冻结。
  - knowledge_boundary:
    - 银行只认可可查资产和订单，不知道未来行情。
    - 贺远桥仍保持审慎。

## Hard Constraints
- 不能让组织升级无反弹。
- 不能提前写跨省布局。
- 不能让科研合作一口价成交。
- 不能提前写最终技术壁垒成型。
- 不能提前写期货风控部门。
- 不能用会议数字代替现场压力。
- 不能让投资无条件到账。
- 不能提前写集团富豪榜。
- 不能让政府替企业兜底。
- 不能跳过贷款附加条件。
