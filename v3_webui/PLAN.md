# V3 WebUI 旁路实验计划

## 目标

在不破坏现有 `python -m juben` 工作流的前提下，验证本地 WebUI 能否稳定控制 Codex CLI，并产出与 Codex App 手工执行同一 prompt packet 接近的结果。

## 当前 V1 范围

- 新增独立目录 `v3_webui/`。
- 本地 HTTP 服务只绑定 `127.0.0.1`。
- 后端只调用白名单 Juben 命令和 `codex exec`。
- WebUI 读取现有 prompt packet，不自行拼写作 prompt。
- Codex job 日志写入 `v3_webui/runtime/jobs/`。
- 默认 dry run，用户明确取消后才真正执行 Codex CLI。

## 不做

- 不改 `juben/_ops/controller.py` 主流程。
- 不改 writer/map/extract prompt 生成逻辑。
- 不控制 Codex App 窗口。
- 不开放公网访问。
- 不做多用户并发。

## 验收

- `python -m v3_webui.server` 能启动本地 WebUI。
- `/api/health` 能检测 Codex CLI 和 prompt packet。
- WebUI 能执行 `status`、`next` 等白名单命令。
- WebUI 能创建 Codex dry-run job。
- 用户可以选择同一个 prompt packet，在 Codex App 和 WebUI/Codex CLI 下分别执行并对比产物。
