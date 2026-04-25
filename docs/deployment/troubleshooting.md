# Juben 排障手册

## 终端出现乱码

优先确认文件本身是否是 UTF-8。PowerShell 显示乱码不一定代表文件坏了。

可用 Python 检查：

```powershell
python - <<'PY'
from pathlib import Path
print(Path("juben/README.md").read_text(encoding="utf-8")[:200])
PY
```

如果 Python 读取正常，通常是终端 code page 问题，不要为显示问题重写文件。

## prompt packet 生成了，但没有剧本

这是正常边界：Python 只生成 prompt packet，不调用模型。

下一步是让 agent 读取终端显示的 prompt 文件，并写回目标文件。写完后再运行：

```powershell
.\~start.cmd batchXX --write
```

非 Windows 环境：

```powershell
python -m juben start batchXX --write
```

## review 一直 pending

说明 reviewer 还没有回填结论。通过时运行：

```powershell
.\~review.cmd batchXX PASS --reviewer <name>
```

非 Windows 环境：

```powershell
python -m juben review batchXX PASS --reviewer <name>
```

失败时运行：

```powershell
.\~review.cmd batchXX FAIL --reviewer <name> --reason "具体阻塞原因"
```

非 Windows 环境：

```powershell
python -m juben review batchXX FAIL --reviewer <name> --reason "具体阻塞原因"
```

## run 被 gate 拦住

`.\~run.cmd batchXX` 只接受已 PASS 的批次。先检查：

```powershell
.\~status.cmd
.\~next.cmd
```

如果缺 review artifact，运行：

```powershell
.\~check.cmd batchXX
```

非 Windows 环境：

```powershell
python -m juben check batchXX
```

## output 没更新

手动刷新：

```powershell
.\~export.cmd
```

非 Windows 环境：

```powershell
python -m juben export
```

如果还是没有目标文件，说明上游 drafts、episodes 或 reviews 本身没有生成，先回到对应批次处理。

## batch.lock 卡住

先运行：

```powershell
.\~status.cmd
.\~next.cmd
```

非 Windows 环境：

```powershell
python -m juben status
python -m juben next
```

如果确认为历史中断，不要直接删除文件。优先完成当前批次的 review/run/record。只有确认没有并行任务时，才手工处理 lock。

## promote 中断

如果 `.\~next.cmd` 提示 promote recovery，按提示运行：

```powershell
.\~promote.cmd batchXX
```

非 Windows 环境：

```powershell
python -m juben promote batchXX
```

恢复后继续：

```powershell
.\~record.cmd batchXX
```

非 Windows 环境：

```powershell
python -m juben record batchXX
```

## agent 没有写文件，只在聊天里回复

这次执行视为未完成。把 `juben/AGENT-RUNBOOK.md` 和当前 prompt packet 一起交给 agent，明确要求它写入目标文件。

## 想换 Claude / Qwen / DeepSeek

不要改 controller。流程只要求 agent 具备三项能力：

- 能读取 prompt packet 和必读上下文文件。
- 能写入 prompt packet 指定的目标文件。
- 能遵守 `harness/framework/prompt-packet-protocol.md`。

如果模型环境不支持本地文件写入，只能用于人工辅助，不适合作为执行 agent。
