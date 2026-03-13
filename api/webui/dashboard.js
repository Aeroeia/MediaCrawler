const CHANNEL_LABELS = {
  xhs: "小红书",
  dy: "抖音",
  ks: "快手",
  bili: "B站",
  wb: "微博",
  tieba: "贴吧",
  zhihu: "知乎",
};

const state = {
  days: 7,
  openGroupKey: "",
  mergedRows: [],
  detailCache: new Map(),
};

const $ = (id) => document.getElementById(id);
const OVERVIEW_FALLBACK = {
  totals: { contents: 0, comments: 0, creators: 0, crawled: 0 },
  today_new_contents: 0,
  today_new_comments: 0,
  today_new_crawled: 0,
};

function getElementOrWarn(id) {
  const el = $(id);
  if (!el) {
    console.error(`[dashboard] Missing DOM element: #${id}`);
  }
  return el;
}

function safeSetText(id, text) {
  const el = getElementOrWarn(id);
  if (el) {
    el.textContent = text;
  }
}

function formatNum(value) {
  const num = Number(value || 0);
  if (Number.isNaN(num)) return "0";
  return num.toLocaleString("zh-CN");
}

function escapeHtml(input) {
  return String(input ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function truncateText(input, maxLen = 80) {
  const text = String(input ?? "");
  if (text.length <= maxLen) return text;
  return `${text.slice(0, maxLen)}...`;
}

function showToast(message) {
  const toast = $("toast");
  if (!toast) {
    console.error(`[dashboard] Toast unavailable: ${message}`);
    return;
  }
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2600);
}

async function apiGet(path) {
  const response = await fetch(`/api/dashboard/${path}`, {
    headers: { Accept: "application/json" },
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = { success: false, message: "接口返回非 JSON 数据" };
  }

  if (!response.ok || !payload.success) {
    const message = payload && payload.message ? payload.message : `请求失败: ${path}`;
    throw new Error(message);
  }
  return payload.data;
}

function buildGroupKey(channel, contentId) {
  return `${channel}::${contentId}`;
}

function getChannelName(channel) {
  return CHANNEL_LABELS[channel] || channel;
}

function parseCollectedTs(collectedAt) {
  const text = String(collectedAt || "").trim();
  if (!text) return 0;
  const ts = Date.parse(`${text.replace(" ", "T")}+08:00`);
  return Number.isNaN(ts) ? 0 : ts;
}

function renderOverview(overview) {
  if (!overview) {
    console.error("[dashboard] renderOverview received empty payload");
    return;
  }
  const totals = overview.totals || {};
  const totalContents = Number(totals.contents || 0);
  const totalComments = Number(totals.comments || 0);
  const totalCreators = Number(totals.creators || 0);
  const totalCrawled = Number(totals.crawled || totalContents + totalComments);

  const todayNewContents = Number(overview.today_new_contents || 0);
  const todayNewComments = Number(overview.today_new_comments || 0);
  const todayNewCrawled = Number(overview.today_new_crawled || todayNewContents + todayNewComments);

  safeSetText("total-crawled", formatNum(totalCrawled));
  safeSetText("today-new-crawled", formatNum(todayNewCrawled));
  safeSetText("total-contents", formatNum(totalContents));
  safeSetText("total-comments", formatNum(totalComments));
  safeSetText("total-creators", formatNum(totalCreators));
}

function renderTrend(trendData) {
  trendData = trendData || { period_days: state.days, series: [] };
  const chart = getElementOrWarn("trend-chart");
  const period = getElementOrWarn("trend-period");
  if (!chart || !period) return;
  const series = trendData.series || [];
  period.textContent = `最近 ${trendData.period_days || state.days} 天`;

  if (series.length === 0) {
    chart.className = "trend-chart empty-state";
    chart.innerHTML = "暂无数据";
    return;
  }

  chart.className = "trend-chart";
  const maxValue = Math.max(...series.map((item) => Number(item.total || 0)), 1);

  chart.innerHTML = series
    .map((item) => {
      const value = Number(item.total || 0);
      const height = Math.max(6, Math.round((value / maxValue) * 100));
      const dateLabel = escapeHtml(String(item.date || "").slice(5));
      return `
        <div class="trend-item">
          <div class="trend-num">${formatNum(value)}</div>
          <div class="trend-bar-wrap">
            <div class="trend-bar" style="height:${height}%"></div>
          </div>
          <div class="trend-date">${dateLabel}</div>
        </div>
      `;
    })
    .join("");
}

function renderSiteClassification(channelsData) {
  channelsData = channelsData || { rows: [] };
  const container = getElementOrWarn("site-classification");
  if (!container) return;
  const rows = (channelsData.rows || []).map((row) => {
    const contentCount = Number(row.content_count || 0);
    const commentCount = Number(row.comment_count || 0);
    const creatorCount = Number(row.creator_count || 0);
    const crawledCount = Number(row.crawled_count || contentCount + commentCount);
    return {
      channel: row.channel,
      contentCount,
      commentCount,
      creatorCount,
      crawledCount,
    };
  });

  if (rows.length === 0) {
    container.className = "site-list empty-state";
    container.innerHTML = "暂无数据";
    return;
  }

  rows.sort((a, b) => b.crawledCount - a.crawledCount);
  const maxCrawled = Math.max(...rows.map((row) => row.crawledCount), 1);
  const totalCrawled = rows.reduce((sum, row) => sum + row.crawledCount, 0) || 1;

  container.className = "site-list";
  container.innerHTML = rows
    .map((row) => {
      const ratio = Math.max(3, Math.round((row.crawledCount / maxCrawled) * 100));
      const share = ((row.crawledCount / totalCrawled) * 100).toFixed(1);
      return `
        <div class="site-row">
          <div class="site-head">
            <span class="site-name">${escapeHtml(getChannelName(row.channel))}</span>
            <span class="site-count">${formatNum(row.crawledCount)}</span>
          </div>
          <div class="site-track">
            <div class="site-fill" style="width:${ratio}%"></div>
          </div>
          <div class="site-meta">
            <span>帖子 ${formatNum(row.contentCount)}</span>
            <span>评论 ${formatNum(row.commentCount)}</span>
            <span>创作者 ${formatNum(row.creatorCount)}</span>
            <span>占比 ${share}%</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderKeywords(keywordData) {
  keywordData = keywordData || { rows: [] };
  const container = getElementOrWarn("keyword-list");
  if (!container) return;
  const rows = keywordData.rows || [];

  if (rows.length === 0) {
    container.className = "keyword-list empty-state";
    container.innerHTML = "暂无关键词数据";
    return;
  }

  container.className = "keyword-list";
  container.innerHTML = rows
    .map(
      (item, index) => `
        <div class="keyword-item">
          <span>${index + 1}. ${escapeHtml(item.keyword)}</span>
          <b>${formatNum(item.count)}</b>
        </div>
      `
    )
    .join("");
}

function mergeRecentAndCommentGroups(recentData, groupData) {
  recentData = recentData || { rows: [] };
  groupData = groupData || { rows: [] };
  const groupMap = new Map();
  (groupData.rows || []).forEach((item) => {
    const channel = String(item.channel || "");
    const contentId = String(item.content_id || "");
    const key = buildGroupKey(channel, contentId);
    groupMap.set(key, {
      commentCount: Number(item.comment_count || 0),
      latestCommentAt: String(item.latest_comment_at || "-"),
    });
  });

  const mergedRows = (recentData.rows || []).map((item, index) => {
    const channel = String(item.channel || "");
    const contentId = String(item.content_id || "");
    const key = buildGroupKey(channel, contentId);
    const group = groupMap.get(key);
    const title = String(item.title || item.summary || "(无标题)");
    const summary = item.summary && item.summary !== title ? String(item.summary) : "";
    return {
      key,
      rowIndex: index,
      channel,
      contentId,
      title,
      summary,
      collectedAt: String(item.collected_at || "-"),
      collectedTs: parseCollectedTs(item.collected_at),
      likeCount: Number(item.like_count || 0),
      interactCommentCount: Number(item.comment_count || 0),
      shareCount: Number(item.share_count || 0),
      capturedCommentCount: group ? group.commentCount : 0,
      latestCommentAt: group ? group.latestCommentAt : "-",
    };
  });

  mergedRows.sort((a, b) => b.collectedTs - a.collectedTs || a.rowIndex - b.rowIndex);
  return mergedRows;
}

function renderDetailContent(detailState) {
  if (!detailState || detailState.loading) {
    return `<div class="detail-state">正在加载评论明细...</div>`;
  }
  if (detailState.error) {
    return `<div class="detail-state error">${escapeHtml(detailState.error)}</div>`;
  }
  const rows = detailState.rows || [];
  if (rows.length === 0) {
    return `<div class="detail-state">该帖子暂无评论明细</div>`;
  }
  return `
    <div class="detail-table-wrap">
      <table class="detail-table">
        <thead>
          <tr>
            <th>评论 ID</th>
            <th>用户</th>
            <th>评论内容</th>
            <th>点赞</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (item) => `
                <tr>
                  <td>${escapeHtml(item.comment_id || "-")}</td>
                  <td>${escapeHtml(item.user_name || "-")}</td>
                  <td>${escapeHtml(item.content || "-")}</td>
                  <td>${formatNum(item.like_count)}</td>
                  <td>${escapeHtml(item.collected_at || "-")}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderMergedRows(rows) {
  rows = rows || [];
  const tbody = getElementOrWarn("merged-table-body");
  const mergedCount = getElementOrWarn("merged-count");
  if (!tbody) return;
  state.mergedRows = rows;
  if (mergedCount) {
    mergedCount.textContent = `${rows.length} 个帖子`;
  }

  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">暂无数据</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((row) => {
      const key = row.key;
      const opened = state.openGroupKey === key;
      const detailState = state.detailCache.get(key);
      const canExpand = row.capturedCommentCount > 0;
      const actionText = opened ? "收起" : "展开";
      const safeTitle = String(row.title || "(无标题)");
      const summaryHtml = row.summary
        ? `<div class="content-summary">${escapeHtml(truncateText(row.summary, 96))}</div>`
        : "";
      const actionNode = canExpand
        ? `
          <button
            class="toggle-btn"
            type="button"
            data-channel="${escapeHtml(row.channel)}"
            data-content-id="${escapeHtml(row.contentId)}"
          >
            ${actionText}
          </button>
        `
        : `<button class="toggle-btn action-disabled" type="button" disabled>无评论</button>`;
      const details = opened
        ? `
          <tr class="detail-row">
            <td colspan="8">${renderDetailContent(detailState)}</td>
          </tr>
        `
        : "";
      const interact = `赞 ${formatNum(row.likeCount)} / 评 ${formatNum(row.interactCommentCount)} / 转 ${formatNum(
        row.shareCount
      )}`;

      return `
        <tr class="group-row ${opened ? "opened" : ""}">
          <td><span class="site-tag">${escapeHtml(getChannelName(row.channel))}</span></td>
          <td class="mono">${escapeHtml(row.contentId)}</td>
          <td>
            <div class="content-title" title="${escapeHtml(safeTitle)}">${escapeHtml(truncateText(safeTitle, 90))}</div>
            ${summaryHtml}
          </td>
          <td class="mono">${escapeHtml(row.collectedAt)}</td>
          <td class="mono">${formatNum(row.capturedCommentCount)}</td>
          <td class="mono">${escapeHtml(row.latestCommentAt)}</td>
          <td class="mono">${interact}</td>
          <td>${actionNode}</td>
        </tr>
        ${details}
      `;
    })
    .join("");
}

async function toggleCommentGroup(channel, contentId) {
  const key = buildGroupKey(channel, contentId);
  const currentRow = state.mergedRows.find((item) => item.key === key);
  if (!currentRow || currentRow.capturedCommentCount <= 0) {
    return;
  }

  if (state.openGroupKey === key) {
    state.openGroupKey = "";
    renderMergedRows(state.mergedRows);
    return;
  }

  state.openGroupKey = key;
  if (!state.detailCache.has(key)) {
    state.detailCache.set(key, { loading: true, error: "", rows: [] });
    renderMergedRows(state.mergedRows);

    try {
      const detailData = await apiGet(
        `comment-group-detail?days=${state.days}&channel=${encodeURIComponent(channel)}&content_id=${encodeURIComponent(
          contentId
        )}&limit=50`
      );
      state.detailCache.set(key, { loading: false, error: "", rows: detailData.rows || [] });
    } catch (error) {
      state.detailCache.set(key, { loading: false, error: error.message || "明细加载失败", rows: [] });
      showToast(error.message || "评论明细加载失败");
    }
  }

  renderMergedRows(state.mergedRows);
}

async function loadDashboard() {
  const refreshBtn = $("refresh-btn");
  if (refreshBtn) {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "加载中...";
  }
  state.openGroupKey = "";
  state.detailCache.clear();

  try {
    const entries = [
      {
        key: "overview",
        label: "总览",
        promise: apiGet(`overview?days=${state.days}`),
        fallback: OVERVIEW_FALLBACK,
      },
      {
        key: "channels",
        label: "网站分类",
        promise: apiGet(`channels?days=${state.days}`),
        fallback: { period_days: state.days, rows: [] },
      },
      {
        key: "trend",
        label: "趋势",
        promise: apiGet(`trend?days=${state.days}`),
        fallback: { period_days: state.days, series: [] },
      },
      {
        key: "keywords",
        label: "关键词",
        promise: apiGet(`keywords?days=${state.days}&limit=10`),
        fallback: { period_days: state.days, limit: 10, rows: [] },
      },
      {
        key: "recent",
        label: "最近帖子",
        promise: apiGet(`recent?days=${state.days}&limit=50`),
        fallback: { period_days: state.days, limit: 50, rows: [] },
      },
      {
        key: "commentGroups",
        label: "评论归属",
        promise: apiGet(`comment-groups?days=${state.days}&limit=100`),
        fallback: { period_days: state.days, limit: 100, rows: [] },
      },
    ];
    const settled = await Promise.allSettled(entries.map((item) => item.promise));
    const data = {};
    const failedModules = [];

    settled.forEach((result, idx) => {
      const entry = entries[idx];
      if (result.status === "fulfilled") {
        data[entry.key] = result.value;
      } else {
        data[entry.key] = entry.fallback;
        failedModules.push(entry.label);
        console.error(`[dashboard] ${entry.label} 加载失败`, result.reason);
      }
    });
    const mergedRows = mergeRecentAndCommentGroups(data.recent, data.commentGroups);

    renderOverview(data.overview || OVERVIEW_FALLBACK);
    renderSiteClassification(data.channels);
    renderTrend(data.trend);
    renderKeywords(data.keywords);
    renderMergedRows(mergedRows);
    if (failedModules.length > 0) {
      showToast(`${failedModules.join("、")}加载失败，其他模块已显示`);
    }
  } catch (error) {
    console.error("[dashboard] loadDashboard fatal error", error);
    showToast(error.message || "加载失败");
  } finally {
    if (refreshBtn) {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "刷新数据";
    }
  }
}

function bindEvents() {
  const daysSelect = $("days-select");
  if (daysSelect) {
    daysSelect.addEventListener("change", (event) => {
      state.days = Number(event.target.value) || 7;
      loadDashboard();
    });
  } else {
    console.error("[dashboard] Missing #days-select; change filter disabled");
  }

  const refreshBtn = $("refresh-btn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadDashboard();
    });
  } else {
    console.error("[dashboard] Missing #refresh-btn; manual refresh disabled");
  }

  const mergedTableBody = $("merged-table-body");
  if (mergedTableBody) {
    mergedTableBody.addEventListener("click", (event) => {
      const button = event.target.closest(".toggle-btn");
      if (!button || button.disabled) return;
      const channel = button.dataset.channel || "";
      const contentId = button.dataset.contentId || "";
      toggleCommentGroup(channel, contentId);
    });
  } else {
    console.error("[dashboard] Missing #merged-table-body; comment detail interaction disabled");
  }
}

function bootstrap() {
  const currentScript = Array.from(document.scripts).find((item) => item.src.includes("/static/dashboard.js"));
  console.info("[dashboard] bootstrap", {
    path: window.location.pathname,
    script: currentScript ? currentScript.src : "unknown",
  });
  bindEvents();
  loadDashboard();
}

document.addEventListener("DOMContentLoaded", bootstrap);
