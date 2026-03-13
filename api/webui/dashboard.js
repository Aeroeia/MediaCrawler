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
  commentGroupsRows: [],
  detailCache: new Map(),
};

const $ = (id) => document.getElementById(id);

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

function renderOverview(overview) {
  const totals = overview.totals || {};
  const totalContents = Number(totals.contents || 0);
  const totalComments = Number(totals.comments || 0);
  const totalCreators = Number(totals.creators || 0);
  const totalCrawled = Number(totals.crawled || totalContents + totalComments);

  const todayNewContents = Number(overview.today_new_contents || 0);
  const todayNewComments = Number(overview.today_new_comments || 0);
  const todayNewCrawled = Number(overview.today_new_crawled || todayNewContents + todayNewComments);

  $("total-crawled").textContent = formatNum(totalCrawled);
  $("today-new-crawled").textContent = formatNum(todayNewCrawled);
  $("total-contents").textContent = formatNum(totalContents);
  $("total-comments").textContent = formatNum(totalComments);
  $("total-creators").textContent = formatNum(totalCreators);
}

function renderTrend(trendData) {
  const chart = $("trend-chart");
  const series = trendData.series || [];
  $("trend-period").textContent = `最近 ${trendData.period_days || state.days} 天`;

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
  const container = $("site-classification");
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
  const container = $("keyword-list");
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

function renderRecent(recentData) {
  const tbody = $("recent-table-body");
  const rows = recentData.rows || [];
  $("recent-count").textContent = `${rows.length} 条`;

  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">暂无数据</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((item) => {
      const channel = getChannelName(item.channel);
      const title = item.title || item.summary || "(无标题)";
      const safeTitle = String(title);
      const summary = item.summary && item.summary !== title ? item.summary : "";
      const info = summary
        ? `<div class="content-title" title="${escapeHtml(safeTitle)}">${escapeHtml(truncateText(safeTitle, 90))}</div><div class="content-summary">${escapeHtml(truncateText(summary, 96))}</div>`
        : `<div class="content-title" title="${escapeHtml(safeTitle)}">${escapeHtml(truncateText(safeTitle, 90))}</div>`;
      const interact = `赞 ${formatNum(item.like_count)} / 评 ${formatNum(item.comment_count)} / 转 ${formatNum(
        item.share_count
      )}`;
      return `
        <tr>
          <td><span class="site-tag">${escapeHtml(channel)}</span></td>
          <td>${info}</td>
          <td>${interact}</td>
          <td>${escapeHtml(item.collected_at || "-")}</td>
        </tr>
      `;
    })
    .join("");
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

function renderCommentGroups(groupData) {
  const tbody = $("comment-group-body");
  const rows = groupData.rows || [];
  state.commentGroupsRows = rows;
  $("comment-group-count").textContent = `${rows.length} 个帖子`;

  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">暂无数据</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((row) => {
      const key = buildGroupKey(row.channel, row.content_id);
      const opened = state.openGroupKey === key;
      const detailState = state.detailCache.get(key);
      const actionText = opened ? "收起" : "展开";
      const title = String(row.title || "(无标题)");
      const details = opened
        ? `
          <tr class="detail-row">
            <td colspan="6">${renderDetailContent(detailState)}</td>
          </tr>
        `
        : "";

      return `
        <tr class="group-row ${opened ? "opened" : ""}">
          <td><span class="site-tag">${escapeHtml(getChannelName(row.channel))}</span></td>
          <td class="mono">${escapeHtml(row.content_id)}</td>
          <td><span class="row-title" title="${escapeHtml(title)}">${escapeHtml(truncateText(title, 96))}</span></td>
          <td>${formatNum(row.comment_count)}</td>
          <td>${escapeHtml(row.latest_comment_at || "-")}</td>
          <td>
            <button
              class="toggle-btn"
              type="button"
              data-channel="${escapeHtml(row.channel)}"
              data-content-id="${escapeHtml(row.content_id)}"
            >
              ${actionText}
            </button>
          </td>
        </tr>
        ${details}
      `;
    })
    .join("");
}

async function toggleCommentGroup(channel, contentId) {
  const key = buildGroupKey(channel, contentId);
  if (state.openGroupKey === key) {
    state.openGroupKey = "";
    renderCommentGroups({ rows: state.commentGroupsRows });
    return;
  }

  state.openGroupKey = key;
  if (!state.detailCache.has(key)) {
    state.detailCache.set(key, { loading: true, error: "", rows: [] });
    renderCommentGroups({ rows: state.commentGroupsRows });

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

  renderCommentGroups({ rows: state.commentGroupsRows });
}

async function loadDashboard() {
  const refreshBtn = $("refresh-btn");
  refreshBtn.disabled = true;
  refreshBtn.textContent = "加载中...";
  state.openGroupKey = "";
  state.detailCache.clear();

  try {
    const [overview, channels, trend, keywords, recent, commentGroups] = await Promise.all([
      apiGet(`overview?days=${state.days}`),
      apiGet(`channels?days=${state.days}`),
      apiGet(`trend?days=${state.days}`),
      apiGet(`keywords?days=${state.days}&limit=10`),
      apiGet(`recent?days=${state.days}&limit=50`),
      apiGet(`comment-groups?days=${state.days}&limit=20`),
    ]);

    renderOverview(overview);
    renderSiteClassification(channels);
    renderTrend(trend);
    renderKeywords(keywords);
    renderRecent(recent);
    renderCommentGroups(commentGroups);
  } catch (error) {
    showToast(error.message || "加载失败");
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "刷新数据";
  }
}

function bindEvents() {
  $("days-select").addEventListener("change", (event) => {
    state.days = Number(event.target.value) || 7;
    loadDashboard();
  });

  $("refresh-btn").addEventListener("click", () => {
    loadDashboard();
  });

  $("comment-group-body").addEventListener("click", (event) => {
    const button = event.target.closest(".toggle-btn");
    if (!button) return;
    const channel = button.dataset.channel || "";
    const contentId = button.dataset.contentId || "";
    toggleCommentGroup(channel, contentId);
  });
}

function bootstrap() {
  bindEvents();
  loadDashboard();
}

document.addEventListener("DOMContentLoaded", bootstrap);
