const state = {
  prompts: [],
  guide: null,
  activeJobId: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { error: await response.text() };
  if (!response.ok) {
    if (response.status === 404 && path === "/api/project/start") {
      throw new Error("后端不是最新版：没有 /api/project/start。请停止 WebUI，重新运行 python -m v3_webui.server，然后浏览器 Ctrl+F5。");
    }
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function setOutput(text) {
  $("commandOutput").textContent = text || "(no output)";
}

function renderCommandResult(result) {
  const parts = [
    `> ${result.command_display || ""}`,
    `exit: ${result.returncode}`,
    "",
    result.stdout || "",
  ];
  if (result.stderr) {
    parts.push("", "[stderr]", result.stderr);
  }
  setOutput(parts.join("\n"));
}

async function refreshHealth() {
  const health = await api("/api/health");
  const codex = health.codex || {};
  $("connectionState").textContent = codex.available ? `Codex 已连接 · ${codex.version}` : "Codex 未连接";
  $("connectionState").classList.toggle("ok", Boolean(codex.available));
  state.prompts = health.prompts || [];
  renderPrompts();
  await refreshGuide().catch((error) => renderGuideError(error));
  await refreshJobs();
}

async function refreshGuide() {
  const guide = await api("/api/guide");
  state.guide = guide;
  renderGuide(guide);
}

function renderGuideError(error) {
  const stateEl = $("guideState");
  stateEl.className = "guide-state error";
  stateEl.innerHTML = `
    <strong>状态读取失败</strong>
    <span>不是你的问题，是 WebUI 没拿到向导结果。</span>
    <em>${error.message || error}</em>
  `;
  $("guidePaths").innerHTML = "";
  $("quickActions").innerHTML = "";
  document.querySelector(".runner-panel").classList.add("hidden-panel");
}

function renderGuide(guide) {
  const stateEl = $("guideState");
  stateEl.className = `guide-state ${guide.state || "unknown"}`;
  stateEl.innerHTML = `
    <strong>${guide.title}</strong>
    <span>${guide.summary}</span>
    <em>${guide.primary_action}</em>
  `;

  const paths = guide.paths || {};
  const counts = guide.counts || {};
  $("guidePaths").innerHTML = `
    <div><span>成品剧集</span><strong>${counts.episodes || 0} 集</strong><code>${paths.episodes || ""}</code></div>
    <div><span>Prompt</span><strong>${counts.prompts || 0} 个</strong><code>${paths.prompts || ""}</code></div>
  `;

  const actions = $("quickActions");
  actions.innerHTML = "";
  for (const op of guide.recommended_buttons || []) {
    const button = document.createElement("button");
    button.textContent = labelForOperation(op);
    button.addEventListener("click", () => runJubenOperation(op).catch((error) => setOutput(error.message)));
    actions.appendChild(button);
  }

  const runnerPanel = document.querySelector(".runner-panel");
  runnerPanel.classList.toggle("disabled-panel", !guide.can_run_codex);
  $("runnerHint").textContent = guide.can_run_codex
    ? "当前状态允许执行 prompt。先预览；确认后取消 Dry run 才会真正调用 Codex。"
    : "当前状态不需要执行 prompt。除非你在做对比实验，否则不要启动 Codex job。";
  updateCodexButtonText();

  runnerPanel.classList.toggle("hidden-panel", guide.state === "complete");
}

function labelForOperation(operation) {
  const labels = {
    status: "查看状态",
    next: "查看下一步",
    extract: "生成抽取 prompt",
    map: "生成分集 prompt",
    export: "刷新交付目录",
    start_prepare: "准备 batch",
    start_write: "生成写作 prompt",
    check: "生成审稿 prompt",
    run: "通过后发布",
    record: "记录状态",
  };
  return labels[operation] || operation;
}

function renderPrompts() {
  const select = $("promptSelect");
  select.innerHTML = "";
  if (!state.prompts.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "未找到 prompt packet";
    select.appendChild(option);
    return;
  }
  for (const prompt of state.prompts) {
    const option = document.createElement("option");
    option.value = prompt.path;
    option.textContent = `${prompt.name} · ${prompt.size} bytes`;
    select.appendChild(option);
  }
}

async function runJubenOperation(operation) {
  setOutput("执行中...");
  const payload = {
    operation,
    batch_id: $("batchId").value,
  };
  const result = await api("/api/juben", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  renderCommandResult(result);
  await refreshHealth();
}

async function previewPrompt() {
  const path = $("promptSelect").value;
  if (!path) return;
  const data = await api(`/api/prompt?path=${encodeURIComponent(path)}`);
  $("promptPreview").textContent = data.content || "(empty)";
}

async function runCodex() {
  const promptPath = $("promptSelect").value;
  if (!promptPath) {
    $("promptPreview").textContent = "没有可执行的 prompt packet。";
    return;
  }
  const job = await api("/api/codex/run", {
    method: "POST",
    body: JSON.stringify({
      prompt_path: promptPath,
      model: $("modelInput").value,
      profile: $("profileInput").value,
      sandbox: $("sandboxSelect").value,
      approval: "never",
      dry_run: $("dryRun").checked,
      timeout_seconds: 1800,
    }),
  });
  $("promptPreview").textContent = `job ${job.id} 已创建：${job.status}\n${job.command_display}`;
  await refreshJobs();
}

async function loadNovelFile(file) {
  if (!file) return;
  $("novelFilename").value = file.name || "novel.md";
  const buffer = await file.arrayBuffer();
  const decoders = ["utf-8", "gb18030", "gbk"];
  let text = "";
  let usedEncoding = "";
  for (const encoding of decoders) {
    try {
      text = new TextDecoder(encoding, { fatal: true }).decode(buffer);
      usedEncoding = encoding;
      break;
    } catch (_error) {
      // Try the next common Chinese novel encoding.
    }
  }
  if (!text) {
    text = new TextDecoder("utf-8", { fatal: false }).decode(buffer);
    usedEncoding = "utf-8-with-replacement";
  }
  $("novelText").value = text;
  $("liveTerminal").textContent = `已读取文件：${file.name}\n编码：${usedEncoding}\n字数：${text.length}\n现在可以点击“开始新项目”。`;
}

async function startProject() {
  const novelText = $("novelText").value;
  if (!novelText.trim()) {
    $("liveTerminal").textContent = "请先上传文件，或粘贴小说原文。";
    return;
  }
  $("liveTerminal").textContent = "正在启动新项目...\n";
  let job;
  try {
    job = await api("/api/project/start", {
      method: "POST",
      body: JSON.stringify({
        filename: $("novelFilename").value || "novel.md",
        novel_text: novelText,
        episodes: Number($("episodesInput").value || 25),
        target_total_minutes: Number($("totalMinutesInput").value || 50),
        auto_codex: $("autoCodex").checked,
      }),
    });
  } catch (error) {
    $("liveTerminal").textContent = `启动失败：${error.message || error}`;
    throw error;
  }
  state.activeJobId = job.id;
  renderLiveJob(job);
  await refreshJobs();
}

function renderLiveJob(job) {
  const lines = [
    `任务：${job.id}`,
    `状态：${job.status}`,
    `命令：${job.command_display || ""}`,
  ];
  if (job.auto_codex_disabled_reason) {
    lines.push(`提示：自动 Codex CLI 已禁用。${job.auto_codex_disabled_reason}`);
  }
  lines.push("", job.stdout_tail || job.error || "等待输出...");
  $("liveTerminal").textContent = lines.join("\n");
  $("liveTerminal").scrollTop = $("liveTerminal").scrollHeight;
}

async function pollActiveJob() {
  if (!state.activeJobId) return;
  try {
    const job = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}`);
    renderLiveJob(job);
    if (!["queued", "running"].includes(job.status)) {
      state.activeJobId = null;
      await refreshHealth();
    }
  } catch (error) {
    $("liveTerminal").textContent = error.message || String(error);
  }
}

async function sendTerminalInput() {
  if (!state.activeJobId) {
    $("liveTerminal").textContent += "\n没有正在运行的任务，无法发送输入。";
    return;
  }
  const text = $("terminalInput").value;
  if (!text.trim()) return;
  await api("/api/jobs/input", {
    method: "POST",
    body: JSON.stringify({ job_id: state.activeJobId, text }),
  });
  $("terminalInput").value = "";
  $("liveTerminal").textContent += `\n> ${text}\n`;
}

async function cancelActiveJob() {
  if (!state.activeJobId) {
    $("liveTerminal").textContent += "\n没有正在运行的任务可停止。";
    return;
  }
  const jobId = state.activeJobId;
  $("liveTerminal").textContent += "\n正在停止当前任务...\n";
  await api("/api/jobs/cancel", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId }),
  });
  state.activeJobId = null;
  $("liveTerminal").textContent += "\n任务已停止。";
  await refreshJobs();
}

function updateCodexButtonText() {
  $("runCodexBtn").textContent = $("dryRun").checked ? "测试执行命令" : "真正调用 Codex 生成";
}

async function refreshJobs() {
  const jobs = await api("/api/jobs");
  const list = $("jobsList");
  list.innerHTML = "";
  if (!jobs.length) {
    list.innerHTML = `<div class="empty">暂无 Codex job。</div>`;
    return;
  }
  for (const job of jobs.slice(0, 12)) {
    const item = document.createElement("article");
    item.className = "job";
    item.innerHTML = `
      <div class="job-top">
        <strong>${job.id}</strong>
        <span class="job-status ${job.status}">${job.status}</span>
      </div>
      <div class="job-path">${job.prompt_path || ""}</div>
      <code>${job.command_display || ""}</code>
      <pre>${job.stdout_tail || job.error || ""}${job.stderr_tail ? `\n[stderr]\n${job.stderr_tail}` : ""}</pre>
    `;
    list.appendChild(item);
  }
}

function bindEvents() {
  $("refreshBtn").addEventListener("click", () => refreshHealth().catch((error) => setOutput(error.message)));
  $("refreshGuideBtn").addEventListener("click", () => refreshGuide().catch((error) => setOutput(error.message)));
  document.querySelectorAll("[data-op]").forEach((button) => {
    button.addEventListener("click", () => runJubenOperation(button.dataset.op).catch((error) => setOutput(error.message)));
  });
  $("previewPromptBtn").addEventListener("click", () => previewPrompt().catch((error) => ($("promptPreview").textContent = error.message)));
  $("runCodexBtn").addEventListener("click", () => runCodex().catch((error) => ($("promptPreview").textContent = error.message)));
  $("dryRun").addEventListener("change", updateCodexButtonText);
  $("novelFile").addEventListener("change", (event) => loadNovelFile(event.target.files[0]).catch((error) => ($("liveTerminal").textContent = error.message)));
  $("startProjectBtn").addEventListener("click", () => startProject().catch((error) => ($("liveTerminal").textContent = error.message)));
  $("sendInputBtn").addEventListener("click", () => sendTerminalInput().catch((error) => ($("liveTerminal").textContent += `\n发送失败：${error.message}`)));
  $("cancelJobBtn").addEventListener("click", () => cancelActiveJob().catch((error) => ($("liveTerminal").textContent += `\n停止失败：${error.message}`)));
  $("terminalInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendTerminalInput().catch((error) => ($("liveTerminal").textContent += `\n发送失败：${error.message}`));
    }
  });
}

bindEvents();
refreshHealth().catch((error) => setOutput(error.message));
setInterval(refreshJobs, 5000);
setInterval(pollActiveJob, 1000);
