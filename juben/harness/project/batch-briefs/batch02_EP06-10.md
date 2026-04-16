# Batch Brief: EP-06 ~ EP-10

- batch status: promoted
- owned episodes: EP-06, EP-07, EP-08, EP-09, EP-10
- source excerpt range: 首辅白月光回京后，我主动让位，他却只要我.md 第9章（"第二天，我回到了沈家"）- 第10章开头 ~ 第18章（从"那天深夜"开始）至宗庙之前
- adjacent continuity: 沈回沈家，母亲关切，父亲欲言又止的尴尬 -> 沈带着恨意回府，裴砚亭在门口迎接（不知她已知真相） -> 沈着云青色宫装进宫，镜前梳妆的蜕变（从怯懦到冷静） -> 李氏恐惧驱动，开始通过寺庙上香暗递消息 -> 深夜裴砚亭换劲装，拿出纯金虎符放在沈的手心
- draft output paths:
  - drafts/episodes/EP-06.md
  - drafts/episodes/EP-07.md
  - drafts/episodes/EP-08.md
  - drafts/episodes/EP-09.md
  - drafts/episodes/EP-10.md

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
- EP-06：第9章（"第二天，我回到了沈家"）- 第10章开头
  - 沈回沈家，母亲关切，父亲欲言又止的尴尬 -> 沈潜入书房暗格，找到紫檀木盒、两封信 -> 裴砚亭的信：命格、死劫、新政、柳清言的保护欲 -> 父亲的拒绝信与背面的血字威胁："清言性命在你一念之间" -> 沈冲出，拿信质问父亲，父亲跪地哭诉真相
  - 集尾类型：emotional_climax - 真相大白，信任崩塌
- EP-07：第11章全部
  - 沈带着恨意回府，裴砚亭在门口迎接（不知她已知真相） -> 晚膳的压抑氛围，裴殷勤布菜，沈冷漠以对 -> 沈直问"你后悔过吗？"裴冷硬回答"不后悔，最正确的决定" -> 沈心中的讽刺：他把我三年当筹码，这笔买卖太划算了 -> 皇帝病重的消息传来，朝局大乱
  - 集尾类型：status_quo_shift - 从被动承受到主动参与（虽然带着恨）
- EP-08：第16章至第17章前半（赏花宴场景）
  - 沈着云青色宫装进宫，镜前梳妆的蜕变（从怯懦到冷静） -> 裴砚亭亲手簪金步摇，耳边低语："你是我的利刃" -> 御花园赏花宴，沈快速识别李氏 -> 小宫女撞翻糕点、佛珠断掉的"意外" -> 沈蹲身捡珠，速度与稳定令李氏震撼
  - 集尾类型：success_milestone - 第一步成功，进入权谋中心
- EP-09：第17章（李氏成为间谍之后）
  - 李氏恐惧驱动，开始通过寺庙上香暗递消息 -> 安国公密谋：见卫戍将领、城外藏兵器、病症加重 -> 裴砚亭书房彻夜灯亮，沈端参汤、他靠在她肩上说"累了" -> 沈首次听他倾诉柔弱，心中的恨意开始有裂纹 -> 第二天，太子也病了（天花），皇宫封锁
  - 集尾类型：tension_building - 局势逼仄，最后一步即将展开
- EP-10：第18章（从"那天深夜"开始）至宗庙之前
  - 深夜裴砚亭换劲装，拿出纯金虎符放在沈的手心 -> 沈惊骇，裴交代计划：去宗庙、阻止拥立新君 -> 用李氏的证据（账本、名单）作威胁 -> 裴的最关键信息：陛下和太子根本没生病 -> 沈提出"我怎么阻止"，裴凑耳边回答这个秘密
  - 集尾类型：commitment_point - 从被逼参与到主动誓约

## Hard Constraints
- 不能跳过两封信的完整揭示（整个命格欺骗的证物）
- 不能减弱父亲的无奈与痛苦（他也是受害者）
- 不能模糊沈对裴的态度转变：从困惑→愤恨
- 不能跳过沈对裴"最正确的决定"的内心反讽
- 不能减弱皇帝病重对朝局的冲击（为后续铺垫）
- 不能模糊沈的棋手身份初现（她开始替他做决策）
- 不能跳过梳妆时的心理蜕变场景（从复仇到超越复仇）
- 不能减弱裴那句"你是我的利刃"的意义（角色正式转换）
- 不能跳过花粉显字的具体演示（关键机关的核心）
- 不能跳过李氏从恐惧到被策反的心理过程
- 不能削弱裴砚亭的疲惫与脆弱时刻（为后续转折铺垫）
- 不能模糊安国公的野心升级（摄政王之心毕露）
- 不能跳过虎符交付的庄严仪式（权力与信任的象征）
- 不能减弱沈心中的复杂情感（既有恨，也有莫名的被信赖感）
- 不能模糊"陛下和太子根本没生病"这个核心反转

## verify checklist
- `_ops/episode-lint.py` on each draft: PASS
- `verify-contract.md` high-severity gates: PASS
- `harness/project/regressions/` active pack items: no active hit
- batch ready for promote: yes
