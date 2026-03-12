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
};

const $ = (id) => document.getElementById(id);

function formatNum(value) {
  return Number(value || 0).toLocaleString("zh-CN");
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

function renderOverview(overview) {
  $("today-new-contents").textContent = formatNum(overview.today_new_contents);
  $("total-contents").textContent = formatNum(overview.totals.contents);
  $("total-comments").textContent = formatNum(overview.totals.comments);
  $("total-creators").textContent = formatNum(overview.totals.creators);
}

function renderTrend(trendData) {
  const chart = $("trend-chart");
  const series = trendData.series || [];
  $("trend-period").textContent = `最近 ${trendData.period_days} 天`;

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
      const height = Math.max(4, Math.round((value / maxValue) * 100));
      const dateLabel = item.date.slice(5);
      return `
        <div class="trend-item">
          <div class="trend-value">${formatNum(value)}</div>
          <div class="trend-bar-wrap">
            <div class="trend-bar" style="height:${height}%"></div>
          </div>
          <div class="trend-label">${dateLabel}</div>
        </div>
      `;
    })
    .join("");
}

function renderChannels(channelsData) {
  const container = $("channel-stats");
  const rows = channelsData.rows || [];

  if (rows.length === 0) {
    container.className = "channel-stats empty-state";
    container.innerHTML = "暂无数据";
    return;
  }

  container.className = "channel-stats";
  const maxContent = Math.max(...rows.map((row) => Number(row.content_count || 0)), 1);
  container.innerHTML = rows
    .map((row) => {
      const content = Number(row.content_count || 0);
      const comments = Number(row.comment_count || 0);
      const creators = Number(row.creator_count || 0);
      const ratio = Math.max(2, Math.round((content / maxContent) * 100));
      const name = CHANNEL_LABELS[row.channel] || row.channel;

      return `
        <div class="channel-row">
          <div class="channel-head">
            <span>${name}</span>
            <span>${formatNum(content)}</span>
          </div>
          <div class="channel-track">
            <div class="channel-bar" style="width:${ratio}%"></div>
          </div>
          <div class="channel-meta">
            <span>评论: ${formatNum(comments)}</span>
            <span>创作者: ${formatNum(creators)}</span>
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
          <span>${index + 1}. ${item.keyword}</span>
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
      const channel = CHANNEL_LABELS[item.channel] || item.channel;
      const title = item.title || item.summary || "(无标题)";
      const summary = item.summary && item.summary !== title ? item.summary : "";
      const info = summary
        ? `<div>${title}</div><div class="muted">${summary.slice(0, 48)}</div>`
        : `<div>${title}</div>`;
      const interact = `赞 ${formatNum(item.like_count)} / 评 ${formatNum(item.comment_count)} / 转 ${formatNum(
        item.share_count
      )}`;
      return `
        <tr>
          <td><span class="channel-tag">${channel}</span></td>
          <td>${info}</td>
          <td>${interact}</td>
          <td>${item.collected_at || "-"}</td>
        </tr>
      `;
    })
    .join("");
}

async function loadDashboard() {
  const refreshBtn = $("refresh-btn");
  refreshBtn.disabled = true;
  refreshBtn.textContent = "加载中...";

  try {
    const [overview, channels, trend, keywords, recent] = await Promise.all([
      apiGet(`overview?days=${state.days}`),
      apiGet(`channels?days=${state.days}`),
      apiGet(`trend?days=${state.days}`),
      apiGet(`keywords?days=${state.days}&limit=10`),
      apiGet(`recent?days=${state.days}&limit=50`),
    ]);

    renderOverview(overview);
    renderChannels(channels);
    renderTrend(trend);
    renderKeywords(keywords);
    renderRecent(recent);
  } catch (error) {
    showToast(error.message || "加载失败");
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "刷新";
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
}

function bootstrap() {
  bindEvents();
  loadDashboard();
}

document.addEventListener("DOMContentLoaded", bootstrap);
