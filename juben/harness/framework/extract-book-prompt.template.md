# Prompt Packet 协议

执行本提示词前，先遵守 `harness/framework/prompt-packet-protocol.md`。本任务只允许写回指定的全书蓝图目标文件；不要调用模型 CLI，不要 promote，不要 record。

你现在只做全书级抽取。

你的唯一任务：
- 基于下面给你的小说正文和 blueprint 骨架
- 返回一份完整可用的 `book.blueprint.md` 正文

输出约束：
- 最终输出必须满足外部 JSON Schema
- 把完整正文放进 `book_blueprint` 字段
- `book_blueprint` 必须以 `# Book Blueprint` 开头
- 严格沿用下面给出的 `{{blueprint_rel}}` 骨架和标题顺序，只填内容，不新增结构
- 删除所有 `AGENT_EXTRACT_REQUIRED`
- 把 `extraction_status` 改成 `extracted`
- 把 `recommended_total_episodes` 改成纯整数
- 全文用中文写
- 不要返回解释、状态汇报、代码块或额外说明

必须完整填充：
- `## 主线`
- `## 集数建议`
- `## 角色弧光`
- `## 关系变化`
- `## 关键反转`
- `## 结局闭环`

人物改名规则：
- 剧中所有主要人物、反派、关键配角的姓名必须与原著姓名完全不同
- 不能只改姓或只改名，不能使用同音、近音、叠字变体或明显可互换的名字
- 在 `## 角色弧光` 中必须先给出“剧名 -> 原著对应人物”的映射，后续蓝图统一使用剧名
- 保留人物功能、关系和弧光，不保留原著姓名

集数估算规则：
- 当前项目目标总时长来自 `run.manifest.md`，本次为约 {{target_total_minutes}} 分钟
- 单集按 {{episode_minutes_min}}-{{episode_minutes_max}} 分钟动态浮动，中心值按 {{target_episode_minutes}} 分钟/集理解
- 先以 {{episode_range_center}} 集为中心估算，合理区间约 {{episode_range_low}}-{{episode_range_high}} 集；最终集数必须由原著有效戏剧单元校正
- 不要按 80-100 集投流长链条拖长；也不要为了贴合中心估算而压掉必要的高价值戏剧节点
- 按“去重后的有效戏剧单元”估总集数，不按“能拆多少小节点”估
- 同类型内容必须合并压缩，不能拆成多集卖点：
  - 重复羞辱
  - 重复试探/试探失败
  - 重复盘问
  - 重复求和
  - 重复追妻日常
  - 同一种冲突只是换说法，但没有新结果
- `可独立成集戏剧节点` 只列高价值、结果不同的节点
- 章节只用于 source 定位，不作为平均切分单位{{explicit_cap_line}}
- 前 3 集必须具备黄金开场改编价值：EP-01 快速进入核心异常/冲突，EP-02/EP-03 逐集升级，而不是重复同一种误认或盘问
- 每 3-5 集应有一个阶段性爽点或释放，每 8-10 集应有一个大反转、大打脸或关系重排；这些节奏点应在 `可独立成集戏剧节点` 中体现

在 `## 集数建议` 中必须明确写出：
- 推荐区间
- 最终采用
- 可独立成集戏剧节点
- 应合并压缩的内容
- 为什么不是更短/更长
- 前 3 集黄金开场应如何处理
- 阶段性爽点/大高潮大致落点

下面是 blueprint 骨架：
<<<BLUEPRINT_TEMPLATE
{{blueprint_template}}
BLUEPRINT_TEMPLATE

下面是小说正文：
<<<NOVEL_TEXT
{{novel_text}}
NOVEL_TEXT

写完后立刻停止。
