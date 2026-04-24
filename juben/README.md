# Juben

面向“小说改编短剧剧本”的专用生产流水线。

当前只保留一套 reviewer-only workflow：
- `controller` 负责编排
- `writer` 只负责生成草稿
- `reviewer` 独立审核
- `run` 负责正式发布

不再保留旧的 `episode-lint / script-aligner / verify-contract` 主链。

## 当前主流程

1. `init`
2. `extract-book`
3. `map-book`
4. `start batchXX`
5. `start batchXX --write`
6. reviewer 审核并回填 `batch-review-done`
7. `run batchXX`
8. `record batchXX`

## Source Of Truth

- [G:\Juben\juben\harness\framework\entry.md](/G:/Juben/juben/harness/framework/entry.md)
- [G:\Juben\juben\harness\project\run.manifest.md](/G:/Juben/juben/harness/project/run.manifest.md)
- [G:\Juben\juben\_ops\controller.py](/G:/Juben/juben/_ops/controller.py)

## 关键目录

- [G:\Juben\juben\_ops](/G:/Juben/juben/_ops)：控制器、writer、extract/map 脚本与测试
- [G:\Juben\juben\harness\framework](/G:/Juben/juben/harness/framework)：合同、风格、prompt 模板、review 标准
- [G:\Juben\juben\harness\project](/G:/Juben/juben/harness/project)：当前项目的 blueprint、source.map、brief、state、releases、reviews
- [G:\Juben\juben\drafts\episodes](/G:/Juben/juben/drafts/episodes)：writer 草稿
- [G:\Juben\juben\episodes](/G:/Juben/juben/episodes)：已发布剧本

## 常用命令

```powershell
python _ops/controller.py init "被弃真千金：总裁不好惹.md" --batch-size 5 --strategy original_fidelity --intensity light --force
python _ops/controller.py extract-book
python _ops/controller.py map-book
python _ops/controller.py start batch01
python _ops/controller.py start batch01 --write
python _ops/controller.py batch-review-done batch01 PASS --reviewer codex
python _ops/controller.py run batch01
python _ops/controller.py record batch01
```
