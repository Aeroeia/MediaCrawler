(function () {
  "use strict";

  if (window.__mediaCrawlerTaskManagerLoaded) {
    return;
  }
  window.__mediaCrawlerTaskManagerLoaded = true;
  // Helps diagnose HTML/JS cache mismatch quickly.
  console.info("[TaskManager] sidecar init v20260313c");

  const MAX_HISTORY = 100;
  const REFRESH_INTERVAL = 10000;
  const LOG_POLL_INTERVAL = 2000;
  const PAGE_MODE = document.body && document.body.dataset.tmMode === "page";

  const state = {
    tasks: [],
    platforms: [],
    options: {
      login_types: [],
      crawler_types: [],
      save_options: [],
    },
    panelOpen: false,
    editingTask: null,
    loading: false,
    viewingLogsTaskId: 0,
    logsPollTimer: null,
    consoleTaskId: 0,
    consoleLevel: "info",
    consoleAutoScroll: true,
    consolePollTimer: null,
  };

  const els = {};

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function setPanelOpen(open) {
    state.panelOpen = !!open;
    if (els.panel) {
      els.panel.classList.toggle("open", state.panelOpen);
    }
    if (els.mask) {
      els.mask.classList.toggle("show", state.panelOpen);
    }
  }

  function showToast(message, type) {
    if (!els.toastWrap) {
      return;
    }
    const node = document.createElement("div");
    node.className = "tm-toast " + (type || "error");
    node.textContent = message;
    els.toastWrap.appendChild(node);
    window.setTimeout(function () {
      node.remove();
    }, 3600);
  }

  async function fetchJson(url, options) {
    const response = await fetch(url, options || {});
    const text = await response.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (error) {
      throw new Error("接口返回非 JSON：" + url);
    }
    if (!response.ok) {
      const message = data.message || data.detail || ("HTTP " + response.status);
      throw new Error(message);
    }
    return data;
  }

  async function fetchEnvelope(url, options) {
    const data = await fetchJson(url, options);
    if (data && data.success === false) {
      throw new Error(data.message || "请求失败");
    }
    return data.data;
  }

  function createLayout() {
    const root = document.createElement("div");
    root.id = "tm-root";
    root.innerHTML = [
      '<div class="tm-entry">',
      '  <button id="tm-open-btn" class="tm-pill" type="button">任务管理</button>',
      "</div>",
      '<div id="tm-mask" class="tm-mask"></div>',
      '<aside id="tm-panel" class="tm-panel" aria-label="任务管理">',
      '  <div class="tm-header">',
      '    <div class="tm-title-wrap">',
      "      <h3>任务管理</h3>",
      '      <div class="tm-subtitle">Cron-only 调度 / 同平台互斥 / MySQL 持久化</div>',
      "    </div>",
      '    <div class="tm-actions">',
      '      <button class="tm-btn" id="tm-refresh-btn" type="button">刷新</button>',
      '      <button class="tm-btn primary" id="tm-create-btn" type="button">新建任务</button>',
      '      <button class="tm-btn ghost" id="tm-close-btn" type="button">关闭</button>',
      "    </div>",
      "  </div>",
      '  <div class="tm-toolbar">',
      '    <div id="tm-meta" class="tm-meta">加载中...</div>',
      '    <div class="tm-chip">同平台最多一个运行实例</div>',
      "  </div>",
      '  <div class="tm-table-wrap">',
      '    <div id="tm-table-target"></div>',
      "  </div>",
      '  <section id="tm-console" class="tm-console" aria-label="实时控制台">',
      '    <div class="tm-console-head">',
      '      <div class="tm-console-title">实时控制台</div>',
      '      <div class="tm-console-controls">',
      '        <label class="tm-console-label" for="tm-console-task">任务</label>',
      '        <select id="tm-console-task" class="tm-console-select"></select>',
      '        <label class="tm-console-label" for="tm-console-level">级别</label>',
      '        <select id="tm-console-level" class="tm-console-select">',
      '          <option value="all">全部</option>',
      '          <option value="info" selected>INFO</option>',
      '          <option value="warning">WARNING</option>',
      '          <option value="error">ERROR</option>',
      "        </select>",
      '        <label class="tm-console-check">',
      '          <input id="tm-console-autoscroll" type="checkbox" checked> 自动滚动',
      "        </label>",
      "      </div>",
      "    </div>",
      '    <div id="tm-console-meta" class="tm-run-meta">未选择任务</div>',
      '    <pre id="tm-console-output" class="tm-log-pre tm-console-pre"></pre>',
      "  </section>",
      "</aside>",
      '<div id="tm-task-modal" class="tm-modal" role="dialog" aria-modal="true">',
      '  <div class="tm-dialog">',
      '    <div class="tm-dialog-header">',
      '      <div id="tm-task-modal-title" class="tm-dialog-title">新建任务</div>',
      '      <button class="tm-btn ghost" id="tm-task-modal-close" type="button">关闭</button>',
      "    </div>",
      '    <form id="tm-task-form" class="tm-form">',
      '      <div class="tm-field"><label>任务名称 *</label><input class="tm-input" name="name" required maxlength="255"></div>',
      '      <div class="tm-field"><label>平台 *</label><select class="tm-select" name="platform"></select></div>',
      '      <div class="tm-field full"><label>任务描述</label><input class="tm-input" name="description"></div>',
      '      <div class="tm-field"><label>Cron 表达式 *</label><input class="tm-input" name="cron_expr" placeholder="*/10 * * * *" required></div>',
      '      <div class="tm-field"><label>启用状态</label><select class="tm-select" name="is_enabled"><option value="true">启用</option><option value="false">暂停</option></select></div>',
      '      <div class="tm-field"><label>优先级</label><select class="tm-select" name="priority"><option value="medium">medium</option><option value="high">high</option><option value="low">low</option></select></div>',
      '      <div class="tm-field"><label>超时（秒）</label><input class="tm-input" name="timeout_seconds" type="number" min="5" max="3600" value="30"></div>',
      '      <div class="tm-field"><label>爬取模式</label><select class="tm-select" name="crawler_type"></select></div>',
      '      <div class="tm-field"><label>登录方式</label><select class="tm-select" name="login_type"></select></div>',
      '      <div class="tm-field"><label>存储方式</label><select class="tm-select" name="save_option"></select></div>',
      '      <div class="tm-field"><label>起始页</label><input class="tm-input" name="start_page" type="number" min="1" value="1"></div>',
      '      <div class="tm-field full" id="tm-field-keywords"><label>关键词（search）</label><textarea class="tm-textarea" name="keywords" placeholder="多个关键词可逗号分隔"></textarea></div>',
      '      <div class="tm-field full" id="tm-field-specified"><label>详情ID（detail）</label><textarea class="tm-textarea" name="specified_ids" placeholder="多个 ID 逗号分隔"></textarea></div>',
      '      <div class="tm-field full" id="tm-field-creator"><label>创作者ID（creator）</label><textarea class="tm-textarea" name="creator_ids" placeholder="多个 ID 逗号分隔"></textarea></div>',
      '      <div class="tm-field full"><label>Cookies（可选）</label><textarea class="tm-textarea" name="cookies"></textarea></div>',
      '      <div class="tm-field full">',
      '        <label>抓取选项</label>',
      '        <div class="tm-checkline">',
      '          <label><input type="checkbox" name="enable_comments" checked> 抓取评论</label>',
      '          <label><input type="checkbox" name="enable_sub_comments"> 抓取子评论</label>',
      '          <label><input type="checkbox" name="headless"> 无头模式</label>',
      '          <label><input type="checkbox" name="run_now_after_save"> 保存后立即执行</label>',
      "        </div>",
      "      </div>",
      '      <div class="tm-form-foot">',
      '        <button class="tm-btn" type="button" id="tm-cancel-submit">取消</button>',
      '        <button class="tm-btn primary" type="submit" id="tm-submit-btn">保存任务</button>',
      "      </div>",
      "    </form>",
      "  </div>",
      "</div>",
      '<div id="tm-runs-modal" class="tm-modal" role="dialog" aria-modal="true">',
      '  <div class="tm-dialog">',
      '    <div class="tm-dialog-header">',
      '      <div id="tm-runs-title" class="tm-dialog-title">运行历史</div>',
      '      <button class="tm-btn ghost" id="tm-runs-close" type="button">关闭</button>',
      "    </div>",
      '    <div id="tm-runs-target" class="tm-runs"></div>',
      "  </div>",
      "</div>",
      '<div id="tm-logs-modal" class="tm-modal" role="dialog" aria-modal="true">',
      '  <div class="tm-dialog">',
      '    <div class="tm-dialog-header">',
      '      <div id="tm-logs-title" class="tm-dialog-title">运行日志</div>',
      '      <button class="tm-btn ghost" id="tm-logs-close" type="button">关闭</button>',
      "    </div>",
      '    <div class="tm-runs">',
      '      <div id="tm-logs-meta" class="tm-run-meta">加载中...</div>',
      '      <pre id="tm-logs-target" class="tm-log-pre"></pre>',
      "    </div>",
      "  </div>",
      "</div>",
      '<div id="tm-toast-wrap" class="tm-toast-wrap"></div>',
    ].join("");
    document.body.appendChild(root);

    els.openBtn = document.getElementById("tm-open-btn");
    els.mask = document.getElementById("tm-mask");
    els.panel = document.getElementById("tm-panel");
    els.refreshBtn = document.getElementById("tm-refresh-btn");
    els.createBtn = document.getElementById("tm-create-btn");
    els.closeBtn = document.getElementById("tm-close-btn");
    els.tableTarget = document.getElementById("tm-table-target");
    els.meta = document.getElementById("tm-meta");
    els.taskModal = document.getElementById("tm-task-modal");
    els.taskModalTitle = document.getElementById("tm-task-modal-title");
    els.taskForm = document.getElementById("tm-task-form");
    els.taskModalClose = document.getElementById("tm-task-modal-close");
    els.cancelSubmit = document.getElementById("tm-cancel-submit");
    els.submitBtn = document.getElementById("tm-submit-btn");
    els.runsModal = document.getElementById("tm-runs-modal");
    els.runsTarget = document.getElementById("tm-runs-target");
    els.runsTitle = document.getElementById("tm-runs-title");
    els.runsClose = document.getElementById("tm-runs-close");
    els.logsModal = document.getElementById("tm-logs-modal");
    els.logsTitle = document.getElementById("tm-logs-title");
    els.logsMeta = document.getElementById("tm-logs-meta");
    els.logsTarget = document.getElementById("tm-logs-target");
    els.logsClose = document.getElementById("tm-logs-close");
    els.consoleWrap = document.getElementById("tm-console");
    els.consoleTask = document.getElementById("tm-console-task");
    els.consoleLevel = document.getElementById("tm-console-level");
    els.consoleAutoScroll = document.getElementById("tm-console-autoscroll");
    els.consoleMeta = document.getElementById("tm-console-meta");
    els.consoleOutput = document.getElementById("tm-console-output");
    els.toastWrap = document.getElementById("tm-toast-wrap");
  }

  function setSelectOptions(selectName, rows) {
    const node = els.taskForm ? els.taskForm.elements.namedItem(selectName) : null;
    if (!node) {
      return;
    }
    node.innerHTML = (rows || [])
      .map(function (item) {
        const value = escapeHtml(item.value);
        const label = escapeHtml(item.label || item.value);
        return '<option value="' + value + '">' + label + "</option>";
      })
      .join("");
  }

  async function loadMeta() {
    const results = await Promise.allSettled([
      fetchJson("/api/config/platforms"),
      fetchJson("/api/config/options"),
    ]);

    if (results[0].status === "fulfilled") {
      state.platforms = results[0].value.platforms || [];
      setSelectOptions("platform", state.platforms);
    }
    if (results[1].status === "fulfilled") {
      state.options = results[1].value || state.options;
      setSelectOptions("crawler_type", state.options.crawler_types || []);
      setSelectOptions("login_type", state.options.login_types || []);
      setSelectOptions("save_option", state.options.save_options || []);
    }

    if (results[0].status !== "fulfilled" || results[1].status !== "fulfilled") {
      showToast("配置项加载失败，任务表单可能不完整", "error");
    }
  }

  function statusClass(status) {
    const safe = String(status || "idle").toLowerCase();
    if (safe === "running") return "running";
    if (safe === "success") return "success";
    if (safe === "paused") return "paused";
    if (safe === "killed") return "killed";
    if (safe === "skipped") return "skipped";
    if (safe === "failed") return "failed";
    if (safe === "error") return "error";
    return "idle";
  }

  function runDisabled(task) {
    if (String(task.status) === "running") {
      return true;
    }
    if (task.platform_busy && Number(task.platform_running_task_id) !== Number(task.id)) {
      return true;
    }
    return false;
  }

  function getAutoConsoleTaskId() {
    const running = state.tasks.find(function (task) {
      return String(task.status) === "running";
    });
    if (running) {
      return Number(running.id);
    }
    if (
      state.consoleTaskId &&
      state.tasks.some(function (task) {
        return Number(task.id) === Number(state.consoleTaskId);
      })
    ) {
      return Number(state.consoleTaskId);
    }
    return state.tasks.length ? Number(state.tasks[0].id) : 0;
  }

  function renderConsoleTaskOptions() {
    if (!PAGE_MODE || !els.consoleTask) {
      return;
    }
    const options = state.tasks
      .map(function (task) {
        const running = String(task.status) === "running" ? " [RUNNING]" : "";
        return (
          '<option value="' +
          Number(task.id) +
          '">' +
          escapeHtml(task.name + " (" + task.platform + ")" + running) +
          "</option>"
        );
      })
      .join("");
    els.consoleTask.innerHTML = options;

    const targetTaskId = getAutoConsoleTaskId();
    state.consoleTaskId = targetTaskId;
    if (!targetTaskId) {
      if (els.consoleMeta) {
        els.consoleMeta.textContent = "暂无任务";
      }
      if (els.consoleOutput) {
        els.consoleOutput.textContent = "暂无任务可查看日志";
      }
      return;
    }
    els.consoleTask.value = String(targetTaskId);
  }

  function matchLogLevel(line, level) {
    const text = String(line || "");
    const lower = text.toLowerCase();
    if (level === "info") {
      return lower.includes("info") || text.includes("信息");
    }
    if (level === "warning") {
      return lower.includes("warning") || lower.includes("warn") || text.includes("警告");
    }
    if (level === "error") {
      return lower.includes("error") || text.includes("错误") || text.includes("异常");
    }
    return true;
  }

  async function loadPersistentConsole(silent) {
    if (!PAGE_MODE || !els.consoleOutput || !els.consoleMeta) {
      return;
    }
    const taskId = Number(state.consoleTaskId || 0);
    if (!taskId) {
      els.consoleMeta.textContent = "暂无任务";
      els.consoleOutput.textContent = "暂无任务可查看日志";
      return;
    }

    const task = findTask(taskId);
    const taskName = task ? task.name : "未知任务";
    try {
      const data = await fetchEnvelope("/api/tasks/" + taskId + "/logs?limit=800");
      const rows = (data && data.rows) || [];
      const filteredRows = rows.filter(function (line) {
        return matchLogLevel(line, state.consoleLevel);
      });
      els.consoleMeta.textContent =
        "任务: " +
        taskName +
        " | 状态: " +
        (data && data.running ? "running" : "idle") +
        " | 数据命中: " +
        Number((data && data.data_hit_count) || 0) +
        " | 显示: " +
        filteredRows.length +
        "/" +
        rows.length;
      els.consoleOutput.textContent = filteredRows.length
        ? filteredRows.join("\n")
        : rows.length
          ? "当前筛选条件下暂无日志"
          : "暂无日志";
      if (state.consoleAutoScroll) {
        els.consoleOutput.scrollTop = els.consoleOutput.scrollHeight;
      }
    } catch (error) {
      els.consoleMeta.textContent = "任务: " + taskName + " | 日志加载失败";
      els.consoleOutput.textContent = String(error.message || "日志加载失败");
      if (!silent) {
        showToast("控制台日志加载失败，稍后重试", "error");
      }
    }
  }

  function startConsoleLoop() {
    if (!PAGE_MODE) {
      return;
    }
    if (state.consolePollTimer) {
      window.clearInterval(state.consolePollTimer);
      state.consolePollTimer = null;
    }
    state.consolePollTimer = window.setInterval(function () {
      loadPersistentConsole(true).catch(function () {
        // keep polling; no-op
      });
    }, LOG_POLL_INTERVAL);
  }

  function renderTaskTable() {
    if (!els.tableTarget) {
      return;
    }
    if (!state.tasks.length) {
      els.tableTarget.innerHTML = '<div class="tm-empty">暂无任务，点击“新建任务”开始。</div>';
      if (els.meta) {
        els.meta.textContent = "0 个任务";
      }
      return;
    }

    const rows = state.tasks
      .map(function (task) {
        const busy = !!task.platform_busy;
        const busyOther = busy && Number(task.platform_running_task_id) !== Number(task.id);
        const disabledRun = runDisabled(task);
        const platformCls = "tm-platform-tag" + (busy ? " busy" : "");
        const runBtnText = busyOther ? "平台占用" : task.resume_available ? "续爬执行" : "立即执行";
        const stopDisabled = String(task.status) !== "running";
        const pauseAction = task.is_enabled ? "pause" : "resume";
        const pauseText = task.is_enabled ? "暂停" : "恢复";
        const resumeText = task.resume_available
          ? "可续爬 · " + String(task.resume_summary || "")
          : "无断点";
        return [
          "<tr>",
          '  <td><div class="tm-name">' + escapeHtml(task.name) + '</div><div class="tm-small">' + escapeHtml(task.description || "-") + "</div></td>",
          '  <td><span class="' + platformCls + '">' + escapeHtml(task.platform) + "</span></td>",
          '  <td><span class="tm-status ' + statusClass(task.status) + '">' + escapeHtml(task.status) + "</span></td>",
          "  <td>" + escapeHtml(resumeText) + "</td>",
          "  <td>" + escapeHtml(task.cron_expr || "-") + "</td>",
          "  <td>" + escapeHtml(task.next_run_at_text || "-") + "</td>",
          "  <td>" + escapeHtml(task.last_run_at_text || "-") + "</td>",
          "  <td>" + Number(task.success_count || 0) + " / " + Number(task.fail_count || 0) + '<div class="tm-small">命中数据: ' + Number(task.data_hit_count || 0) + "</div></td>",
          '  <td><div class="tm-ops">',
          '    <button class="tm-btn" data-action="run" data-id="' + Number(task.id) + '"' + (disabledRun ? " disabled" : "") + ">" + runBtnText + "</button>",
          '    <button class="tm-btn warn" data-action="stop" data-id="' + Number(task.id) + '"' + (stopDisabled ? " disabled" : "") + ">停止</button>",
          '    <button class="tm-btn" data-action="' + pauseAction + '" data-id="' + Number(task.id) + '">' + pauseText + "</button>",
          '    <button class="tm-btn" data-action="edit" data-id="' + Number(task.id) + '">编辑</button>',
          '    <button class="tm-btn" data-action="runs" data-id="' + Number(task.id) + '">历史</button>',
          '    <button class="tm-btn" data-action="logs" data-id="' + Number(task.id) + '">日志</button>',
          '    <button class="tm-btn danger" data-action="delete" data-id="' + Number(task.id) + '">删除</button>',
          "  </div></td>",
          "</tr>",
        ].join("");
      })
      .join("");

    els.tableTarget.innerHTML = [
      '<table class="tm-table">',
      "  <thead>",
      "    <tr>",
      "      <th>任务</th>",
      "      <th>平台</th>",
      "      <th>状态</th>",
      "      <th>断点</th>",
      "      <th>Cron</th>",
      "      <th>下次运行</th>",
      "      <th>最近运行</th>",
      "      <th>成功/失败</th>",
      "      <th>操作</th>",
      "    </tr>",
      "  </thead>",
      "  <tbody>",
      rows,
      "  </tbody>",
      "</table>",
    ].join("");

    if (els.meta) {
      const busyCount = state.tasks.filter(function (task) {
        return !!task.platform_busy;
      }).length;
      els.meta.textContent = state.tasks.length + " 个任务，" + busyCount + " 个平台忙";
    }
  }

  async function loadTasks() {
    state.loading = true;
    if (els.meta) {
      els.meta.textContent = "任务加载中...";
    }

    const [taskResult, statusResult] = await Promise.allSettled([
      fetchEnvelope("/api/tasks"),
      fetchEnvelope("/api/tasks/platform-status"),
    ]);

    if (taskResult.status !== "fulfilled") {
      state.tasks = [];
      renderTaskTable();
      renderConsoleTaskOptions();
      await loadPersistentConsole();
      showToast("任务列表加载失败：" + taskResult.reason.message, "error");
      state.loading = false;
      return;
    }

    const tasks = (taskResult.value && taskResult.value.rows) || [];
    const statusRows =
      statusResult.status === "fulfilled" && statusResult.value
        ? statusResult.value.rows || []
        : [];
    const statusMap = {};
    statusRows.forEach(function (item) {
      statusMap[item.platform] = item;
    });

    state.tasks = tasks.map(function (task) {
      const ps = statusMap[task.platform] || {};
      return {
        ...task,
        platform_busy: !!ps.busy || !!task.platform_busy,
        platform_running_task_id: Number(ps.running_task_id || task.platform_running_task_id || 0),
      };
    });
    renderTaskTable();
    renderConsoleTaskOptions();
    await loadPersistentConsole();
    state.loading = false;
  }

  function openTaskModal(task) {
    state.editingTask = task || null;
    if (!els.taskModal || !els.taskForm || !els.taskModalTitle) {
      return;
    }

    const form = els.taskForm;
    const params = task && task.crawler_params ? task.crawler_params : {};
    const isEdit = !!task;
    els.taskModalTitle.textContent = isEdit ? "编辑任务" : "新建任务";
    els.submitBtn.textContent = isEdit ? "更新任务" : "保存任务";

    form.elements.namedItem("name").value = (task && task.name) || "";
    form.elements.namedItem("description").value = (task && task.description) || "";
    form.elements.namedItem("platform").value = (task && task.platform) || (state.platforms[0] && state.platforms[0].value) || "xhs";
    form.elements.namedItem("priority").value = (task && task.priority) || "medium";
    form.elements.namedItem("timeout_seconds").value = Number((task && task.timeout_seconds) || 30);
    form.elements.namedItem("cron_expr").value = (task && task.cron_expr) || "*/10 * * * *";
    form.elements.namedItem("is_enabled").value = String(task ? !!task.is_enabled : true);

    form.elements.namedItem("crawler_type").value = params.crawler_type || "search";
    form.elements.namedItem("login_type").value = params.login_type || "qrcode";
    form.elements.namedItem("save_option").value = params.save_option || "jsonl";
    form.elements.namedItem("keywords").value = params.keywords || "";
    form.elements.namedItem("specified_ids").value = params.specified_ids || "";
    form.elements.namedItem("creator_ids").value = params.creator_ids || "";
    form.elements.namedItem("cookies").value = params.cookies || "";
    form.elements.namedItem("start_page").value = Number(params.start_page || 1);
    form.elements.namedItem("enable_comments").checked = !!params.enable_comments || !isEdit;
    form.elements.namedItem("enable_sub_comments").checked = !!params.enable_sub_comments;
    form.elements.namedItem("headless").checked = !!params.headless;
    form.elements.namedItem("run_now_after_save").checked = false;
    syncCrawlerTypeHint();

    els.taskModal.classList.add("show");
  }

  function closeTaskModal() {
    if (els.taskModal) {
      els.taskModal.classList.remove("show");
    }
    state.editingTask = null;
  }

  function closeRunsModal() {
    if (els.runsModal) {
      els.runsModal.classList.remove("show");
    }
  }

  function closeLogsModal() {
    state.viewingLogsTaskId = 0;
    if (state.logsPollTimer) {
      window.clearInterval(state.logsPollTimer);
      state.logsPollTimer = null;
    }
    if (els.logsModal) {
      els.logsModal.classList.remove("show");
    }
  }

  function syncCrawlerTypeHint() {
    if (!els.taskForm) {
      return;
    }
    const type = String(els.taskForm.elements.namedItem("crawler_type").value || "search");
    const key = document.getElementById("tm-field-keywords");
    const detail = document.getElementById("tm-field-specified");
    const creator = document.getElementById("tm-field-creator");
    if (key) key.style.display = type === "search" ? "" : "none";
    if (detail) detail.style.display = type === "detail" ? "" : "none";
    if (creator) creator.style.display = type === "creator" ? "" : "none";
  }

  function collectPayload() {
    if (!els.taskForm) {
      throw new Error("表单未就绪");
    }
    const form = els.taskForm.elements;
    const name = String(form.namedItem("name").value || "").trim();
    const cronExpr = String(form.namedItem("cron_expr").value || "").trim();
    if (!name) {
      throw new Error("任务名称不能为空");
    }
    if (!cronExpr) {
      throw new Error("Cron 表达式不能为空");
    }

    return {
      name: name,
      description: String(form.namedItem("description").value || "").trim(),
      platform: String(form.namedItem("platform").value || "xhs"),
      crawler_type: String(form.namedItem("crawler_type").value || "search"),
      login_type: String(form.namedItem("login_type").value || "qrcode"),
      save_option: String(form.namedItem("save_option").value || "jsonl"),
      keywords: String(form.namedItem("keywords").value || "").trim(),
      specified_ids: String(form.namedItem("specified_ids").value || "").trim(),
      creator_ids: String(form.namedItem("creator_ids").value || "").trim(),
      cookies: String(form.namedItem("cookies").value || "").trim(),
      start_page: Number(form.namedItem("start_page").value || 1),
      enable_comments: !!form.namedItem("enable_comments").checked,
      enable_sub_comments: !!form.namedItem("enable_sub_comments").checked,
      headless: !!form.namedItem("headless").checked,
      priority: String(form.namedItem("priority").value || "medium"),
      timeout_seconds: Number(form.namedItem("timeout_seconds").value || 30),
      cron_expr: cronExpr,
      is_enabled: String(form.namedItem("is_enabled").value || "true") === "true",
    };
  }

  async function submitTask(event) {
    event.preventDefault();
    let payload;
    try {
      payload = collectPayload();
    } catch (error) {
      showToast(error.message, "error");
      return;
    }

    const editingId = state.editingTask ? Number(state.editingTask.id) : 0;
    const runNowAfterSave = !!els.taskForm.elements.namedItem("run_now_after_save").checked;
    const endpoint = editingId ? "/api/tasks/" + editingId : "/api/tasks";
    const method = editingId ? "PUT" : "POST";
    els.submitBtn.disabled = true;
    try {
      const data = await fetchEnvelope(endpoint, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (runNowAfterSave) {
        const runTaskId = editingId || Number((data && data.id) || 0);
        if (runTaskId > 0) {
          await fetchEnvelope("/api/tasks/" + runTaskId + "/run-now", { method: "POST" });
        }
      }
      closeTaskModal();
      await loadTasks();
      if (runNowAfterSave) {
        showToast("任务已保存并立即执行", "success");
      } else {
        showToast(editingId ? "任务已更新" : "任务已创建", "success");
      }
    } catch (error) {
      showToast(error.message || "提交失败", "error");
    } finally {
      els.submitBtn.disabled = false;
    }
  }

  function findTask(taskId) {
    return state.tasks.find(function (item) {
      return Number(item.id) === Number(taskId);
    });
  }

  async function openRuns(taskId) {
    const task = findTask(taskId);
    if (!task || !els.runsModal || !els.runsTarget || !els.runsTitle) {
      return;
    }
    els.runsTitle.textContent = "运行历史 - " + task.name;
    els.runsTarget.innerHTML = '<div class="tm-empty">加载中...</div>';
    els.runsModal.classList.add("show");
    try {
      const data = await fetchEnvelope("/api/tasks/" + Number(taskId) + "/runs?limit=" + MAX_HISTORY);
      const rows = (data && data.rows) || [];
      if (!rows.length) {
        els.runsTarget.innerHTML = '<div class="tm-empty">暂无运行历史</div>';
        return;
      }
      els.runsTarget.innerHTML = rows
        .map(function (row) {
          return [
            '<div class="tm-run-item">',
            '  <div class="tm-run-top">',
            '    <span class="tm-status ' + statusClass(row.status) + '">' + escapeHtml(row.status) + "</span>",
            '    <span class="tm-chip">' + escapeHtml(row.trigger_type) + "</span>",
            "  </div>",
            '  <div class="tm-run-meta">开始：' + escapeHtml(row.started_at_text || "-") + " / 结束：" + escapeHtml(row.finished_at_text || "-") + "</div>",
            '  <div class="tm-run-meta">PID：' + Number(row.pid || 0) + " / 退出码：" + Number(row.exit_code || 0) + "</div>",
            '  <div class="tm-run-meta">错误：' + escapeHtml(row.error_message || "-") + "</div>",
            "</div>",
          ].join("");
        })
        .join("");
    } catch (error) {
      els.runsTarget.innerHTML = '<div class="tm-empty">运行历史加载失败</div>';
      showToast(error.message || "运行历史加载失败", "error");
    }
  }

  async function loadTaskLogs(taskId) {
    const data = await fetchEnvelope("/api/tasks/" + Number(taskId) + "/logs?limit=500");
    const rows = (data && data.rows) || [];
    if (!els.logsTarget || !els.logsMeta) {
      return;
    }
    els.logsTarget.textContent = rows.join("\n");
    els.logsMeta.textContent =
      "运行中: " + (data && data.running ? "是" : "否") + " | 数据命中: " + Number((data && data.data_hit_count) || 0) + " | 日志行数: " + rows.length;
  }

  async function openLogs(taskId) {
    const task = findTask(taskId);
    if (!task || !els.logsModal || !els.logsTarget || !els.logsTitle) {
      return;
    }
    state.consoleTaskId = Number(taskId);
    if (PAGE_MODE && els.consoleTask) {
      els.consoleTask.value = String(taskId);
      loadPersistentConsole().catch(function () {
        // no-op
      });
    }
    state.viewingLogsTaskId = Number(taskId);
    els.logsTitle.textContent = "运行日志 - " + task.name;
    els.logsTarget.textContent = "";
    if (els.logsMeta) {
      els.logsMeta.textContent = "加载中...";
    }
    els.logsModal.classList.add("show");
    try {
      await loadTaskLogs(taskId);
    } catch (error) {
      showToast(error.message || "日志加载失败", "error");
    }
    if (state.logsPollTimer) {
      window.clearInterval(state.logsPollTimer);
    }
    state.logsPollTimer = window.setInterval(function () {
      if (!state.viewingLogsTaskId) {
        return;
      }
      loadTaskLogs(state.viewingLogsTaskId).catch(function () {
        // keep polling; no-op
      });
    }, LOG_POLL_INTERVAL);
  }

  async function runAction(action, taskId) {
    const id = Number(taskId);
    if (!id) {
      return;
    }
    const task = findTask(id);
    if (!task) {
      return;
    }

    if (action === "edit") {
      openTaskModal(task);
      return;
    }
    if (action === "runs") {
      await openRuns(id);
      return;
    }
    if (action === "logs") {
      await openLogs(id);
      return;
    }
    if (action === "delete") {
      if (!window.confirm("确认删除任务【" + task.name + "】吗？")) {
        return;
      }
      try {
        await fetchEnvelope("/api/tasks/" + id, { method: "DELETE" });
        await loadTasks();
        showToast("任务已删除", "success");
      } catch (error) {
        showToast(error.message || "删除失败", "error");
      }
      return;
    }

    const actionMap = {
      run: { path: "/api/tasks/" + id + "/run-now", text: "任务已启动" },
      stop: { path: "/api/tasks/" + id + "/stop", text: "任务停止请求已发送" },
      pause: { path: "/api/tasks/" + id + "/pause", text: "任务已暂停" },
      resume: { path: "/api/tasks/" + id + "/resume", text: "任务已恢复" },
    };
    const conf = actionMap[action];
    if (!conf) {
      return;
    }
    try {
      await fetchEnvelope(conf.path, { method: "POST" });
      await loadTasks();
      showToast(conf.text, "success");
    } catch (error) {
      showToast(error.message || "操作失败", "error");
    }
  }

  function bindEvents() {
    if (!els.openBtn || !els.mask || !els.panel || !els.tableTarget) {
      console.error("[TaskManager] key dom missing, sidecar degraded");
      return;
    }

    els.openBtn.addEventListener("click", function () {
      if (PAGE_MODE) {
        return;
      }
      setPanelOpen(!state.panelOpen);
      if (state.panelOpen) {
        loadTasks().catch(function (error) {
          showToast(error.message || "刷新失败", "error");
        });
      }
    });
    els.mask.addEventListener("click", function () {
      if (PAGE_MODE) {
        return;
      }
      setPanelOpen(false);
    });
    els.closeBtn.addEventListener("click", function () {
      if (PAGE_MODE) {
        return;
      }
      setPanelOpen(false);
    });
    els.refreshBtn.addEventListener("click", function () {
      loadTasks().catch(function (error) {
        showToast(error.message || "刷新失败", "error");
      });
    });
    els.createBtn.addEventListener("click", function () {
      openTaskModal(null);
    });

    els.tableTarget.addEventListener("click", function (event) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const action = target.dataset.action;
      const taskId = target.dataset.id;
      if (!action || !taskId) {
        return;
      }
      runAction(action, taskId).catch(function (error) {
        showToast(error.message || "操作失败", "error");
      });
    });

    if (PAGE_MODE && els.consoleTask && els.consoleLevel && els.consoleAutoScroll) {
      els.consoleTask.addEventListener("change", function () {
        state.consoleTaskId = Number(els.consoleTask.value || 0);
        loadPersistentConsole().catch(function () {
          // no-op
        });
      });
      els.consoleLevel.addEventListener("change", function () {
        state.consoleLevel = String(els.consoleLevel.value || "info").toLowerCase();
        loadPersistentConsole().catch(function () {
          // no-op
        });
      });
      els.consoleAutoScroll.addEventListener("change", function () {
        state.consoleAutoScroll = !!els.consoleAutoScroll.checked;
        if (state.consoleAutoScroll && els.consoleOutput) {
          els.consoleOutput.scrollTop = els.consoleOutput.scrollHeight;
        }
      });
    }

    els.taskModalClose.addEventListener("click", closeTaskModal);
    els.cancelSubmit.addEventListener("click", closeTaskModal);
    els.taskForm.addEventListener("submit", submitTask);
    els.taskForm.elements.namedItem("crawler_type").addEventListener("change", syncCrawlerTypeHint);

    els.runsClose.addEventListener("click", closeRunsModal);
    els.runsModal.addEventListener("click", function (event) {
      if (event.target === els.runsModal) {
        closeRunsModal();
      }
    });
    els.logsClose.addEventListener("click", closeLogsModal);
    els.logsModal.addEventListener("click", function (event) {
      if (event.target === els.logsModal) {
        closeLogsModal();
      }
    });
    els.taskModal.addEventListener("click", function (event) {
      if (event.target === els.taskModal) {
        closeTaskModal();
      }
    });
  }

  async function loadDashboard() {
    await loadMeta();
    await loadTasks();
  }

  function startRefreshLoop() {
    window.setInterval(function () {
      if (!state.panelOpen && document.visibilityState !== "visible") {
        return;
      }
      loadTasks().catch(function () {
        // noop, errors are shown by loadTasks.
      });
    }, REFRESH_INTERVAL);
  }

  async function init() {
    createLayout();
    bindEvents();
    if (PAGE_MODE) {
      setPanelOpen(true);
    }
    try {
      await loadDashboard();
    } catch (error) {
      showToast(error.message || "任务管理初始化失败", "error");
    }
    startConsoleLoop();
    startRefreshLoop();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
