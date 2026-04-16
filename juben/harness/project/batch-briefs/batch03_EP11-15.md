# Batch Brief: EP-11 ~ EP-15

- batch status: promoted
- owned episodes: EP-11, EP-12, EP-13, EP-14, EP-15
- source excerpt range: 首辅白月光回京后，我主动让位，他却只要我.md 第18章（"宗庙大殿，庄严肃穆"）至"裴砚亭走到我的面前"前 ~ 第18章全部结尾（"朝阳照耀整个京城"之后）
- adjacent continuity: 沈从梁柱后走出，举起虎符，全场瞬间静默 -> 天边鱼肚白，沈与裴砚亭站在宫墙之上，手相握 -> 宗庙事件后，朝局的正式宣布与权力重组 -> 沈回首辅府，下人的态度与言行的转变（从暗讽到敬畏） -> 春日清晨，沈在花园中梳妆，裴砚亭在后相伴
- draft output paths:
  - drafts/episodes/EP-11.md
  - drafts/episodes/EP-12.md
  - drafts/episodes/EP-13.md
  - drafts/episodes/EP-14.md
  - drafts/episodes/EP-15.md

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
- EP-11：第18章（"宗庙大殿，庄严肃穆"）至"裴砚亭走到我的面前"前
  - 沈从梁柱后走出，举起虎符，全场瞬间静默 -> "我奉陛下之命而来"，沈递呈李氏的账本与信件 -> 宗亲长老们脸色变化（白→青→黑），罪证铁板钉钉 -> 沈宣读真相：天花之说子虚乌有，引蛇出洞之局 -> 话音刚落，宗庙殿门轰然大开
  - 集尾类型：victory_moment - 阴谋破灭，权力转手
- EP-12：第18章（"漫长的一夜，终于过去了"）至末尾
  - 天边鱼肚白，沈与裴砚亭站在宫墙之上，手相握 -> 沈问"为什么要绕这么大一个圈子" -> 裴澄清：命格之说是真的、相士预言也是真的，但不是全部理由 -> 裴拿出泛黄童年画：小沈递糖人给小裴 -> 裴讲述：父亲被害、妹妹被杀、他的复仇、对沈的三十年记忆
  - 集尾类型：emotional_resolution - 恨消融为爱，真爱的共同誓约
- EP-13：第18章（"新政开始推行"之后 / 补充完整故事线）
  - 宗庙事件后，朝局的正式宣布与权力重组 -> 沈对自己在权谋中所做选择的理解与反思 -> 裴砚亭在皇帝与陛下面前对沈的公开确认与褒奖 -> 沈从"隐形参与者"变成"被官方承认的贡献者" -> 新旧派的权力平衡，国家秩序的初步稳定
  - 集尾类型：status_consolidation - 权力的转移确认，沈的新身份定格
- EP-14：第18章（"大事已毕，沈如月回到首辅府"及后续原文扩展场景）
  - 沈回首辅府，下人的态度与言行的转变（从暗讽到敬畏） -> 沈进入主院书房，裴砚亭在等她，第一次名正言顺的拥抱 -> 沈看到书房的柳清言画像已被撤下，取而代之的是她与裴砚亭的合绘画 -> 沈在裴的怀中，既感受到胜利的满足，也感受到失去"被保护者身份"的失落感 -> 两人探讨新政的执行、权力的维护、以及他们共同的未来
  - 集尾类型：domestic_transition - 从权力中心回到家庭中心，新的"首辅夫人"定义
- EP-15：第18章全部结尾（"朝阳照耀整个京城"之后）
  - 春日清晨，沈在花园中梳妆，裴砚亭在后相伴 -> 沈回顾整个觉醒之路：从"摆设"到"棋手"再到"皇后"，每一步都是血泪 -> 沈与裴在花厅晨光中的对话：不是权力的讨论，而是生活与未来的规划 -> 沈的最后独白：我曾想逃离，现在我选择留下，不是因为被困，而是因为爱 -> 镜头拉开，京城在新朝的秩序中展开新的一天，沈与裴的身影消失在晨光中
  - 集尾类型：narrative_closure - 完整的故事闭环，个人与时代的新生

## Hard Constraints
- 不能跳过虎符的视觉冲击与权力象征
- 不能减弱宗亲长老们从怀疑到确信的转变过程
- 不能削弱裴砚亭出现时的"神将"气质（映照沈的"神女"角色）
- 不能跳过童年画的出现与讲述（整个逻辑闭环的钥匙）
- 不能削弱裴对妹妹与复仇的情感记忆（解释他的执念）
- 不能模糊沈的最终选择：不是被逼，而是主动拥吻、主动承诺
- 不能跳过官方层面对沈的认可（身份的正式转变）
- 不能减弱沈对自己行动道德性的思考（她是否做对了？）
- 不能跳过新朝秩序对"女性参政"的微妙态度转变
- 不能跳过下人态度的转变（体现沈新身份的社会确认）
- 不能削弱画像更换的象征意义（过去的执念被现在的爱所取代）
- 不能模糊沈对新身份的复杂情感（胜利与失落并存）
- 不能跳过沈的回顾与反思（整个觉醒之路的确认）
- 不能削弱"选择"与"爱"的最终确认（不是被迫，而是心甘情愿）
- 不能丢失整部故事的最终主题：女性的觉醒与蜕变

## verify checklist
- `_ops/episode-lint.py` on each draft: PASS
- `verify-contract.md` high-severity gates: PASS
- `harness/project/regressions/` active pack items: no active hit
- batch ready for promote: yes
