# Juben

面向“小说改编短剧剧本”的 agent-native 生产流水线。

当前只保留一套 reviewer-only workflow：
- `controller` 负责编排
- `writer` prompt packet 交给外部 agent 执行
- `reviewer` 独立审核
- `run` 负责正式发布

不再保留旧的 `episode-lint / script-aligner / verify-contract` 主链。

## V1 主流程

从仓库根目录运行：

```powershell
.\~init.cmd "被弃真千金：总裁不好惹.md" --episodes 25 --target-total-minutes 50
python .\juben\_ops\controller.py extract-book
python .\juben\_ops\controller.py map-book
.\~start.cmd batch01 --write
.\~review.cmd batch01 PASS --reviewer codex
.\~run.cmd batch01
.\~record.cmd batch01
.\~next.cmd
```

`extract-book / map-book / start --write` 会生成 prompt packet。把 packet 交给任意能读写本地文件的 agent 执行，不需要也不建议由 Python 嵌套调用模型 CLI。

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
- [G:\Juben\juben\output](/G:/Juben/juben/output)：可交付输出镜像，优先看这里

## 常用命令

```powershell
.\~next.cmd
.\~clean.cmd
python .\juben\_ops\controller.py status
python .\juben\_ops\controller.py export
```
