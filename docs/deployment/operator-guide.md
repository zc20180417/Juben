# Juben 操作手册

本手册写给负责跑流程的人。目标是从一份小说 Markdown 生成 50 分钟左右竖屏短剧，并把结果交付到 `juben/output/`。

## 1. 初始化

把小说 Markdown 放在仓库根目录，然后运行：

```powershell
.\~init.cmd "小说文件.md" --episodes 25 --target-total-minutes 50
```

非 Windows 环境使用：

```powershell
python -m juben init "小说文件.md" --episodes 25 --target-total-minutes 50
```

如果只是重新测试工程能力，先清理运行态：

```powershell
.\~clean.cmd
```

等价 Python 入口：

```powershell
python -m juben clean
```

再重新 init。

## 2. 全书抽取

```powershell
.\~extract.cmd
```

等价 Python 入口：

```powershell
python -m juben extract
```

命令会生成 prompt packet。把终端显示的 prompt 文件交给 agent 执行，agent 必须写回：

- `juben/harness/project/book.blueprint.md`
- `juben/character.md`
- `juben/voice-anchor.md`

不要让 Python 调模型 CLI。

## 3. 分集映射

```powershell
.\~map.cmd
```

等价 Python 入口：

```powershell
python -m juben map
```

把生成的 map prompt packet 交给 agent 执行，agent 必须写回：

- `juben/harness/project/source.map.md`

分集质量重点：

- 总集数和目标总时长一致。
- 前几集有黄金三秒冲突。
- 每集信息密度足够支撑 1-3 分钟。
- 每集结尾有明确付费钩子或推进钩子。
- 人名必须与原著不同。

## 4. 写批次

从第一批开始：

```powershell
.\~start.cmd batch01 --write
```

等价 Python 入口：

```powershell
python -m juben start batch01 --write
```

如果草稿还不存在，命令会生成 writer prompt packet。把 packet 交给 agent 执行，agent 必须写回：

- `juben/drafts/episodes/EP-xx.md`

agent 写完后，再运行同一条命令刷新 review packet：

```powershell
.\~start.cmd batch01 --write
```

## 5. 评审

读取 review prompt，让 reviewer agent 按 `review-standard.md` 评审。

通过：

```powershell
.\~review.cmd batch01 PASS --reviewer <name>
```

等价 Python 入口：

```powershell
python -m juben review batch01 PASS --reviewer <name>
```

不通过：

```powershell
.\~review.cmd batch01 FAIL --reviewer <name> --reason "具体阻塞原因"
```

等价 Python 入口：

```powershell
python -m juben review batch01 FAIL --reviewer <name> --reason "具体阻塞原因"
```

评审不改稿。若 FAIL，回到 writer 或 polish，再重跑 `.\~start.cmd batch01 --write`。

## 6. 发布与记录

评审通过后发布：

```powershell
.\~run.cmd batch01
```

写入批次状态：

```powershell
.\~record.cmd batch01
```

查看下一步：

```powershell
.\~next.cmd
```

等价 Python 入口：

```powershell
python -m juben run batch01
python -m juben record batch01
python -m juben next
```

## 7. 交付

随时刷新交付包：

```powershell
.\~export.cmd
```

等价 Python 入口：

```powershell
python -m juben export
```

优先查看：

- `juben/output/SUMMARY.md`
- `juben/output/episodes/`
- `juben/output/anchors/`
- `juben/output/manifest.json`

普通交付不要让对方去 `harness/project/` 里找文件。

## 8. 换模型执行

换模型时不要改 Python。只需要把当前 prompt packet 和 `juben/AGENT-RUNBOOK.md` 交给新 agent，并确认它能读写本地文件。

如果新 agent 只会聊天、不能写文件，不适合直接执行本流程。

## 9. 跨平台入口边界

`python -m juben ...` 适合在仓库根目录直接运行，作用是替代 Windows `.cmd` 包装脚本。它不是正式 pip 安装包入口。不要把当前仓库安装到全局 Python 后再运行，否则项目文件写入位置会变得不直观。
