# Batch Brief: EP-01 ~ EP-05

- batch status: promoted
- owned episodes: EP-01, EP-02, EP-03, EP-04, EP-05
- source excerpt range: 首辅白月光回京后，我主动让位，他却只要我.md 第1-2章开头（第01章全部，第02章至"缓缓开口"前） ~ 第8章（从马场段落开始）至第9章"我骑着踏雪，回到了城外马场"
- adjacent continuity: 沈如月三年名义夫妻的现状：冷漠、画像、喊着柳清言的名字 -> 柳清言首次登门拜访的温柔伪装（白莲花人设完整展现） -> 搬入主院、第一次同床而眠的尴尬与战栗 -> 沈如月主动向春桃打听柳家三年前的风波 -> 裴砚亭突然提议学骑马（既解禁又是陷阱）
- draft output paths:
  - drafts/episodes/EP-01.md
  - drafts/episodes/EP-02.md
  - drafts/episodes/EP-03.md
  - drafts/episodes/EP-04.md
  - drafts/episodes/EP-05.md

## Run Context
- adaptation_strategy: original_fidelity
- dialogue_adaptation_intensity: light
- generation_execution_mode: orchestrated_subagents
- generation_reset_mode: clean_rebuild

## Source Priority
1. `harness/project/run.manifest.md`
2. `harness/project/source.map.md`
3. `harness/framework/write-contract.md`
4. 原著正文 `首辅白月光回京后，我主动让位，他却只要我.md`
5. `voice-anchor.md`
6. `character.md`

## Episode Mapping
- EP-01：第1-2章开头（第01章全部，第02章至"缓缓开口"前）
  - 沈如月三年名义夫妻的现状：冷漠、画像、喊着柳清言的名字 -> 白月光回京的消息与沈如月的喜悦转折 -> 主动起草离书、逐客令的细节与心理 -> 宫里听到"俸禄微薄，只够养一个夫人"的反问句 -> 和离书被销毁的关键转折
  - 集尾类型：cliffhanger - 离书被销毁，心理崩溃与困局加深
- EP-02：第2章（"缓缓开口"之后）- 第3章全部
  - 柳清言首次登门拜访的温柔伪装（白莲花人设完整展现） -> 沈如月与柳清言的对话博弈——"我很快就会还给你"的挑衅 -> 裴砚亭在海棠树下的出现与威胁警告 -> 沈如月的激烈反驳：权衡柳清言还是要我 -> 沈潜入书房摘画像、脚下一滑被抱住的身体接触
  - 集尾类型：plot_turn - 被抱入主院，局面反向，身心俱陷
- EP-03：第4章全部
  - 搬入主院、第一次同床而眠的尴尬与战栗 -> 柳清言送紫檀木匣（砚台、墨锭）的示威 -> 磨墨时被抓住手腕、被迫联笔书"沈"字的亲密 -> 砚台被扔进火盆的绝情毁弃 -> 沈如月的心理转折："他的每一件事，都和我认识的他完全不一样"
  - 集尾类型：emotional_pivot - 从被动承受到主动探寻真相
- EP-04：第6章全部
  - 沈如月主动向春桃打听柳家三年前的风波 -> 春桃揭露：科举舞弊大案，非贪墨小事 -> 沈推理出：裴砚亭暗中出手摆平，为了柳清言 -> 沈进一步推测：政敌借柳清言逼迫赐婚 -> 沈决定进宫查档、找表哥、查起居注
  - 集尾类型：action_escalation - 真相逼近，禁锢加深
- EP-05：第8章（从马场段落开始）至第9章"我骑着踏雪，回到了城外马场"
  - 裴砚亭突然提议学骑马（既解禁又是陷阱） -> 马场教骑马的温暖与缱绻（第一次看到他真心笑） -> 沈如月被信任放在"踏雪"上骑向京城的刹那抉择 -> 城门口与柳清言的相遇（对方以此示威） -> 沈冒死潜入静心堂、贿赂常公公的真相碎片
  - 集尾类型：revelation - 线索汇聚，父亲牵涉其中

## Hard Constraints
- 不能跳过沈如月的自嘲与绝望感
- 不能跳过裴砚亭销毁离书的冷酷姿态（"你是我的夫人，这辈子都是"）
- 不能改弱沈对裴的初期误解（完全不爱她）
- 不能跳过沈与柳的暗示较量（权力游戏的开始）
- 不能改弱裴砚亭摘画像时"如你所愿"的暧昧与危险
- 不能减弱沈对这一切的困惑与心理摇晃
- 不能跳过沈与裴初次的身体接近与心理涟漪
- 不能减弱裴对柳清言过往的彻底否定（不是爱，是决裂的信号）
- 不能模糊沈对真相需求的紧迫感
- 不能跳过春桃的警告与沈的坚持
- 不能减弱沈的推理过程（从表面事件到深层算计）
- 不能丢失软禁的象征意义（他知道了什么？）
- 不能跳过马场的温暖对比（让她有一瞬想放弃真相追求）
- 不能减弱沈背叛他信任的内疚（"对不起，裴砚亭，我骗了你"）
- 不能削弱常公公那句"您的父亲"的震撼

## verify checklist
- `_ops/episode-lint.py` on each draft: PASS
- `verify-contract.md` high-severity gates: PASS
- `harness/project/regressions/` active pack items: no active hit
- batch ready for promote: yes
