# Project Profile

本文件是当前项目的运行时配置单一事实源。

- adaptation_mode: novel_to_short_drama
- genre_profile: revenge_palace
- distribution_mode: cn_paid_microdrama
- relation_layer: enabled
- dialogue_adaptation_intensity: light

## 说明
- `adaptation_mode`：声明当前项目以“小说改编成短剧”的方式工作
- `genre_profile`：声明当前项目使用的题材打法
- `distribution_mode`：声明当前项目采用的平台/分发节奏假设
- `relation_layer`：声明是否启用关系态说话规则
- `dialogue_adaptation_intensity`：声明当前轮生成对原著对话的保留力度
  - `preserve`：只允许清理叙述标签、并句、去口水词，不改态度、不改关系温度
  - `light`：允许顺句和影视化整理，但不允许新增原著没有的挑衅、机锋、判断、嘲讽或反击升级
  - `adaptive`：才允许为了成片效果做明显改写，但仍需保住关键关系走向
