# Batch Brief: EP-36 ~ EP-40

- owned episodes: EP-36, EP-37, EP-38, EP-39, EP-40
- source excerpt range: 实业帝国：从继承养猪场开始.txt 第79章 东方沃尔顿家族 至 第81章 收购阿穆尔农机厂 ~ 第86章 远丰高层例会（下半）至全文收束
- adjacent continuity: 【动作】陆行川走进停产设备厂，机器蒙尘，工人守在门口。 -> 【动作】秦峥查封设备厂资料室，发现关键图纸缺页。 -> 【动作】叶承稷把样品复热后切开，让陆行川看失败截面。 -> 【动作】梅知夏要求先报问题，再报增长。 -> 【动作】陆振海摸着旧冷库门牌，想起当初差点盖下的转让章。
- draft output paths:
  - drafts/episodes/EP-36.md
  - drafts/episodes/EP-37.md
  - drafts/episodes/EP-38.md
  - drafts/episodes/EP-39.md
  - drafts/episodes/EP-40.md

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
- EP-36：第79章 东方沃尔顿家族 至 第81章 收购阿穆尔农机厂
  - transformative_adaptation:
    - source_function: 跨区域资产机会出现，主角从贸易收益转向长期设备能力。
    - new_episode_event: 陆行川获知北方一家食品设备厂濒临停产，旧速冻线和冷库改造技术正是棠源缺口，但债务和工人安置像雷。
    - setting_translation: 海外家族、投资州、收购农机厂转译为北方食品设备厂收购与冷链装备能力。
    - must_keep_function: 保留“资产机会”“不是倒货，是长期能力”的功能。
    - must_change_surface: 不得出现阿穆尔州、农机厂、原著海外投资外壳。
    - do_not_copy: 不得复制原著收购农机厂事件组合。
  - 【动作】陆行川走进停产设备厂，机器蒙尘，工人守在门口。 -> 【阻力】债务、欠薪、技术人员流失同时压上来。 -> 【信息】沈砚山看出设备改造能解决棠源主厂瓶颈。 -> 【钩子】老工程师说：你买得到厂，未必留得住图纸。
  - knowledge_boundary:
    - 设备厂工人只知道新买主要来谈，不知道棠源资金压力。
    - 沈砚山只看到技术价值，不掌握全部债务。
- EP-37：第82章 阿穆尔州的现状 至 第83章 致远贸易第一次交易
  - transformative_adaptation:
    - source_function: 资产尽调和首单交易同步考验，主角必须用规则拿回关键能力。
    - new_episode_event: 设备厂关键图纸被前负责人带走，边境订单回款也卡住；陆行川在两头压力下选择先稳合同责任。
    - setting_translation: 州现状和贸易首单转译为设备厂尽调风险与边境订单回款。
    - must_keep_function: 保留“资产背后有坑”“首单不是顺风局”的功能。
    - must_change_surface: 不得出现原著具体地名和贸易货物。
    - do_not_copy: 不得复制原著阿穆尔现状和首单交易桥段。
  - 【动作】秦峥查封设备厂资料室，发现关键图纸缺页。 -> 【阻力】边境客户拖延回款，韩策要求暂停下一单。 -> 【选择】陆行川不抢进度，先按合同追责、保住回款和图纸线索。 -> 【钩子】许望舒认出缺失图纸对应的正是速冻口感问题。
  - knowledge_boundary:
    - 许望舒只知道图纸可能有用，不知道最终科研合作。
    - 客户不知道棠源内部资金紧张。
- EP-38：第84章 吉省大豆所 至 第85章 杂交种和常规种
  - transformative_adaptation:
    - source_function: 科研合作成为长期壁垒，专家要求企业尊重规律而非短期收益。
    - new_episode_event: 陆行川带设备图纸和失败样品再次见叶承稷、许望舒，提出共建加工适配实验线；叶承稷要求先签科研边界。
    - setting_translation: 大豆所、种子合作转译为食品工程、速冻工艺、设备改造和原料适配。
    - must_keep_function: 保留“科研不是采购”“长期壁垒浮出”的功能。
    - must_change_surface: 不得出现大豆所、杂交种、常规种、种子袋。
    - do_not_copy: 不得复制原著大豆科研谈判和人物劝说。
  - 【动作】叶承稷把样品复热后切开，让陆行川看失败截面。 -> 【阻力】许望舒要求研发失败不能算个人责任，梅知夏追问预算边界。 -> 【选择】陆行川接受实验线周期和失败成本。 -> 【钩子】叶承稷同意合作，但要求第一批数据公开给团队看。
  - knowledge_boundary:
    - 科研人员知道棠源有诚意，不知道商业扩张全貌。
    - 团队不知道科研投入多久见效。
- EP-39：第86章 远丰高层例会（上半）
  - transformative_adaptation:
    - source_function: 全线业务汇总前先暴露压力，让最终闭环不是无脑报喜。
    - new_episode_event: 高层例会前，乔南枝报告渠道增长，韩策报告风控收益，沈砚山却带来主厂设备瓶颈和一次质量返工。
    - setting_translation: 高层例会的多线汇报转译为供应链集团业务线汇总和问题暴露。
    - must_keep_function: 保留“多板块成型”“同时仍有风险”的功能。
    - must_change_surface: 不得出现饲料厂、方便面、远东农场、大豆所原汇报口径。
    - do_not_copy: 不得复制原著高层例会数据和汇报句式。
  - 【动作】梅知夏要求先报问题，再报增长。 -> 【信息】渠道、车队、风控、设备、科研各线都有结果，但没有一条完全轻松。 -> 【阻力】设备瓶颈导致返工，乔南枝担心货架断供。 -> 【钩子】陆行川准备定下一阶段方向时，外面有人送来一份榜单传真。
  - knowledge_boundary:
    - 各负责人只掌握自己板块。
    - 富豪榜消息还未公开解释。
- EP-40：第86章 远丰高层例会（下半）至全文收束
  - transformative_adaptation:
    - source_function: 阶段闭环；外界用富豪榜确认主角已从家庭资产守护者成为实业集团掌舵人。
    - new_episode_event: 富豪榜传真显示陆行川进入民营企业家名单，陆振海想起第一集差点卖掉冷库；陆行川没有庆功，而是定下设备升级、科研投入、风控收手和区域扩张边界。
    - setting_translation: 富豪榜和高层例会收口转译为供应链集团阶段成型和下一牌桌开启。
    - must_keep_function: 保留“首尾合同闭环”“父亲认可”“事业阶段成型”“进入更大竞争”的功能。
    - must_change_surface: 不得出现原著远丰、猪场、饲料、农场、大豆所收口。
    - do_not_copy: 不得复制原著富豪榜收口语句和产业线清单。
  - 【动作】陆振海摸着旧冷库门牌，想起当初差点盖下的转让章。 -> 【情绪】团队短暂沉默，不是炫富，而是意识到棠源被更大市场看见。 -> 【结果】陆行川定下下一阶段：设备升级、科研实验线、区域渠道、风控退出线。 -> 【钩子】传真另一页显示全国品牌已注意到棠源，新的竞争刚开始。
  - knowledge_boundary:
    - 团队知道棠源进入更大牌桌，但不知道后续全国竞争细节。
    - 陆振海终于理解儿子保住的不是冷库，而是方向盘。

## Hard Constraints
- 不能让收购轻松完成。
- 不能提前写富豪榜。
- 不能用暴力或关系直接拿回图纸。
- 不能提前写科研线全面成功。
- 不能把科研合作写成高薪挖人。
- 不能提前写技术壁垒完全成型。
- 不能把例会写成纯报喜。
- 不能提前完成最终情绪收束。
- 不能写成终局无敌。
- 不能引入与本阶段无关的新主线。
