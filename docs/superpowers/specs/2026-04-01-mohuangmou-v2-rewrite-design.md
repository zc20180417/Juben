# 《墨凰谋：庶女上位录》v2 重构与批次对比设计

## 背景
现有项目 [juben](/H:/BaiduNetdiskDownload/juben/juben) 已完成《墨凰谋：庶女上位录》60 集正文初版，但在实测中暴露出三类持续性问题：

- 中后期存在自然变薄，前期质量明显高于后期
- 角色台词逐渐同质化，关键人物声纹不稳定
- 后半程更偏“事件推进”，棋局变化与权力位移不够清晰

本次工作不是在旧稿上局部修补，而是基于已优化的剧本 skill 体系，对同一项目做一次并行保留式整季重构，并输出旧版与新版的批次对比。

## 目标
- 产出一套与旧版并行存在的新版 60 集项目资产
- 保留《墨凰谋：庶女上位录》的核心 premise、题材气质和大里程碑
- 允许按每 5 集一批重排小高潮、反派压力和权力位移
- 为每 5 集生成一份“旧版 vs 新版”对比文档
- 让新版具备后续持续迭代所需的状态文件，而不是只有一套正文

## 非目标
- 不覆盖或删除现有旧版文件
- 不把新版写成完全不同的故事
- 不以“补丁修稿”方式直接在旧版 `episodes/` 上改写
- 不在本设计阶段直接进入正文生产

## 现状与基线

### 旧版资产位置
- 基础文档位于 [juben](/H:/BaiduNetdiskDownload/juben/juben)
- 旧版正文位于 [episodes](/H:/BaiduNetdiskDownload/juben/juben/episodes)
- 已存在 `outline.md`、`character.md`、`episode_index.md`、`script.progress.md`

### 旧版已确认保留的核心骨架
- premise：沈青鸾目睹生母惨死，替姐入宫，借帝权复仇，一路登后并掌权
- 题材：古装宫斗 / 复仇爽文 / 大女主上位 / 权谋反转
- 体量：60 集
- 终局：沈青鸾赢尽天下，情感上成为孤家寡人

## 新版落盘方案
新版采用并行保留策略，落盘到新目录 [v2_rewrite](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite)。

### 新版目录结构
- [outline.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/outline.md)
- [character.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/character.md)
- [episode_index.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/episode_index.md)
- [quality.anchor.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/quality.anchor.md)
- [story.state.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/story.state.md)
- [relationship.board.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/relationship.board.md)
- [open_loops.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/open_loops.md)
- [script.progress.md](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/script.progress.md)
- [episodes](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/episodes)
- [comparisons](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/comparisons)

## 重构边界

### 锁定不变的内容
- 核心 premise 不变
- 60 集体量不变
- 大阶段路径不变：家仇原点 -> 替姐入宫 -> 前期立威 -> 翠竹之死 -> 家仇清算 -> 登后 -> 废储 -> 帝崩 -> 垂帘 -> 废帝 -> 终局
- 核心人物功能不变：
  - 沈青鸾：复仇与上位双线驱动的核心行动者
  - 萧景珩：帝王之刀与情感线核心
  - 沈夫人、沈明珠、皇后：三条不同性质的女性压迫链
  - 翠竹、云太医、太子、阿碧：结构性关键配角

### 允许重排和强化的内容
- 每 5 集的内部事件编排
- 小高潮位置与表达方式
- 反派压力的分布与上场顺序
- 权力位移的呈现方式
- 萧景珩与沈青鸾的情感埋线节奏
- 沈明珠、皇后、太子等中后段角色的戏份分配
- 关键角色的语音指纹与“狠法”差异化表达

### 重构原则
- 故事不换，打法重做
- 大里程碑不换，5 集批次内部结构重排
- 新版要显著强化“棋局推进”，不能只堆事件
- 任何新增变化都必须服务于权力上升线、复仇线或感情线之一

## 新版内容策略

### 1. 基础三件套先行
正文重写前，必须先稳定新版基础三件套：
- 新版整季大纲
- 新版人物小传与语音指纹
- 新版 60 集目录

这三份文件用于锁定：
- 整季节奏和阶段目标
- 角色声纹与关系位移
- 每 5 集批次的小弧光和批次结尾钩子

### 2. 批次推进
正文按 5 集一批推进，共 12 批：

1. EP01-EP05
2. EP06-EP10
3. EP11-EP15
4. EP16-EP20
5. EP21-EP25
6. EP26-EP30
7. EP31-EP35
8. EP36-EP40
9. EP41-EP45
10. EP46-EP50
11. EP51-EP55
12. EP56-EP60

每批都必须明确：
- 本批主反派是谁
- 本批女主核心目标是什么
- 本批主要爽点打法是什么
- 本批关系位移是什么
- 本批结尾钩子是什么

### 3. 批次完成后的同步产物
每一批完成时，必须同步产出：
- 5 集新版正文
- 1 份批次对比文档
- 1 次 `story.state.md` 更新
- 1 次 `relationship.board.md` 更新
- 1 次 `open_loops.md` 更新
- 1 次 `script.progress.md` 更新

## 批次对比文档规范
对比文档存放在 [comparisons](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite/comparisons)，采用以下命名：

- `batch-01-compare.md`
- `batch-02-compare.md`
- ...
- `batch-12-compare.md`

每份对比文档固定包含以下部分：

### 旧版本批问题
总结旧版这 5 集最明显的结构缺陷，例如：
- 集与集之间只是在接事件
- 反派压力不足或过早塌陷
- 角色台词同质化
- 情绪虽强但权力位移不明显

### 新版本批策略
说明新版如何应对旧问题，包括：
- 小弧光重排
- 反派权重调整
- 声纹强化方式
- 钩子与记忆唤醒强化方式

### 剧情重排表
列出旧版与新版在本批的关键差异：
- 旧版的主要事件分布
- 新版对应事件如何重新组合
- 哪些关键节点提前、延后或换表达方式

### 角色声纹变化
指出本批关键人物说话方式与狠法如何稳定下来，重点覆盖：
- 沈青鸾
- 萧景珩
- 皇后
- 沈明珠
- 其他本批核心反派

### 权力位移变化
总结新版是否成功把本批从“事件推进”改成“棋局推进”，包括：
- 身份变化
- 宠爱变化
- 盟友关系变化
- 后宫站位变化
- 朝堂或储位变化

### 本批结论
直接回答：
- 新版这一批比旧版强在哪
- 哪些旧问题被直接修掉
- 哪些问题只是缓解，仍需下一批继续处理

## 质量与验收

### 单集验收线
每集必须满足新版剧本规范的底线：
- 场景数 1-3
- 场景要素完整
- 对话不过长
- 有动作、表情、os、镜头、音效
- 有明确冲突或反转
- 有集尾钩子
- 关键场景有记忆唤醒手段

### 批次验收线
每 5 集必须形成完整小弧光：
- 主反派清晰
- 女主目标清晰
- 至少 1 个明显爽点
- 至少 1 次可感知的关系或权力位移
- 结尾能将观众推入下一批

### 整季验收线
整季必须明显优于旧版，至少解决三类核心问题：
- 后期自然变薄
- 角色说话越来越像同一个人
- 后半段只有事件没有棋局变化

### 对比验收线
每份批次对比必须能清楚回答：
- 新版为什么比旧版更强
- 强在丰满度、声纹、钩子还是权力推进
- 旧版哪个具体问题被修掉
- 是否还有未完全解决的风险

## 实施顺序
1. 创建 `v2_rewrite` 目录及子目录
2. 写新版 `outline.md`
3. 写新版 `character.md`
4. 写新版 `episode_index.md`
5. 生成新版 `quality.anchor.md`
6. 进入 12 个批次的正文重写与对比产出
7. 每批同步更新状态文件
8. 在整季完成后回看 12 份对比，验证新版是否形成稳定升级

## 风险与控制

### 风险 1：新版变成“另一个故事”
控制方式：
- 锁定 premise、大里程碑和终局
- 仅重排每 5 集内部结构，不推翻整季主线

### 风险 2：中后段再次塌成事件流水账
控制方式：
- 每批都强制写出权力位移
- 对比文档中单列“权力位移变化”

### 风险 3：角色声纹二次同质化
控制方式：
- `character.md` 中为关键角色写明语速、句式、口头习惯、禁用表达、狠的方式
- 每批对比文档单列声纹变化

### 风险 4：新版产物散乱，后续难以维护
控制方式：
- 新版独立目录
- 每批固定同步状态文件
- 对比文档统一命名和统一结构

## 决策结论
本次采用“并行保留 + 结构重制 + 每 5 集对比”的方案：

- 旧版保留在现有目录，不覆盖
- 新版落在 [v2_rewrite](/H:/BaiduNetdiskDownload/juben/juben/v2_rewrite)
- 重写对象是整季 60 集，而不是局部补丁
- 对比粒度为每 5 集一批
- 质量判断以单集、批次、整季、对比四条验收线共同决定
