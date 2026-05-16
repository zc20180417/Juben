# Juben V3 WebUI 实验台

这个目录是旁路实验，不改变现有 `python -m juben` 工作流。

目标是验证：用本地 WebUI 调用 Codex CLI 执行同一份 prompt packet，产出是否能和 Codex App 手工执行保持一致。

## 启动

推荐在仓库根目录 `G:\Juben` 运行：

```powershell
python -m v3_webui.server
```

如果你已经进入 `G:\Juben\v3_webui`，运行：

```powershell
python start.py
```

打开：

```text
http://127.0.0.1:8765
```

## 设计边界

- WebUI 只绑定本机 `127.0.0.1`。
- WebUI 不拼写作 prompt，只读取现有 `juben/harness/project/prompts/` 和 review prompt。
- WebUI 不替代现有流程，只调用白名单命令。
- Codex 执行默认使用 `codex exec`，不是控制 Codex App。
- 默认勾选 `Dry run`，只验证命令和 prompt packet，不实际消耗模型。
- 执行日志写入 `v3_webui/runtime/jobs/`，该目录应视为本地运行产物。

## 推荐对比方式

1. 在 Codex App 中手工执行某个 prompt packet，保存输出。
2. 在 WebUI 中选择同一个 prompt packet。
3. 先 dry run，确认命令、模型、sandbox、cwd 一致。
4. 取消 dry run 后启动 Codex job。
5. 对比生成文件、job 日志和 Codex App 产物。

## 页面怎么读

普通用户优先使用页面最上方的“新建短剧项目”：

1. 上传 `.md/.txt` 小说文件，或把小说全文粘贴到文本框。
2. 填目标集数和目标总时长。
3. 点“开始新项目”。
4. 看“实时 CLI 输出”。
5. 如果 CLI 明确等待输入，再在下面的输入框发送文本。

默认不会自动调用 Codex。勾选“自动调用 Codex”后，后台会尝试执行抽取/分集 prompt，会消耗模型额度，且 `codex exec` 本身不是严格交互式终端。

上传/粘贴的原文会临时保存为 `juben/__webui_input_*.md|txt`，这些文件已加入 `.gitignore`，不会污染仓库。

高级用户再看“你现在该做什么”。

- 如果显示“剧本已经生成完成”，说明当前项目已经有成品，不需要启动 Codex。
- 如果显示“可以开始下一批生成”，先点“准备 batch”或“生成写作 prompt”。
- 如果显示“已有 prompt packet 等待执行”，再去下面的 Codex CLI Runner。
- 黑色日志只是调试信息，普通使用可以忽略。
- `Dry run` 勾选时只是测试命令，不会调用模型，也不会生成剧本。
- 取消 `Dry run` 后点击“真正调用 Codex 生成”，才会消耗模型并写文件。

## 安全说明

这个 WebUI 是本机开发工具，不是公网服务。

不要把端口暴露到局域网或公网。Codex CLI 具备读写项目文件和执行命令的能力，必须只在可信本机使用。
