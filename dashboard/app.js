const REFRESH_INTERVAL_MS = 60 * 1000;
let responseTrendChart = null;

const elements = {
  statusBadge: document.getElementById("statusBadge"),
  messagePanel: document.getElementById("messagePanel"),
  siteUrl: document.getElementById("siteUrl"),
  lastChecked: document.getElementById("lastChecked"),
  statusCode: document.getElementById("statusCode"),
  responseTime: document.getElementById("responseTime"),
  contentCheck: document.getElementById("contentCheck"),
  failurePanel: document.getElementById("failurePanel"),
  failureReason: document.getElementById("failureReason"),
  recentFailures: document.getElementById("recentFailures"),
  responseTrendChart: document.getElementById("responseTrendChart"),
  responseTrendEmpty: document.getElementById("responseTrendEmpty"),
  multiSitePanel: document.getElementById("multiSitePanel"),
  siteSummaryNote: document.getElementById("siteSummaryNote"),
  totalSites: document.getElementById("totalSites"),
  upSites: document.getElementById("upSites"),
  downSites: document.getElementById("downSites"),
  siteCards: document.getElementById("siteCards"),
};

async function loadStatus() {
  setLoadingState();

  try {
    const response = await fetch("status.json?t=" + Date.now());

    if (!response.ok) {
      throw new Error(`Unable to load status.json (${response.status})`);
    }

    const data = await response.json();
    renderStatus(data);
  } catch (error) {
    renderError(error);
  }
}

function setLoadingState() {
  elements.messagePanel.className = "message-panel";
  elements.messagePanel.textContent = "Loading latest status...";
}

function renderStatus(data) {
  const isUp = data.is_success === true || data.status === "UP";
  const statusText = isUp ? "UP" : "DOWN";

  elements.statusBadge.className = `status-badge ${isUp ? "status-up" : "status-down"}`;
  elements.statusBadge.textContent = statusText;

  elements.messagePanel.className = `message-panel ${isUp ? "success" : "error"}`;
  elements.messagePanel.textContent = isUp
    ? "Latest check passed."
    : "Latest check failed.";

  renderSiteUrl(data.url);
  elements.lastChecked.textContent = formatDateTime(data.last_checked || data.check_time);
  elements.statusCode.textContent = formatStatusCode(data.status_code);
  renderResponseTime(data.response_time_ms);
  renderContentCheck(data.content_check_passed);
  renderFailureReason(isUp, data.failure_reason);
  renderMultiSitePanel(data);
  renderResponseTrend(data);
  renderRecentFailures(data.recent_failures);
}

function renderSiteUrl(url) {
  if (!url) {
    elements.siteUrl.textContent = "--";
    elements.siteUrl.removeAttribute("href");
    return;
  }

  elements.siteUrl.textContent = url;
  elements.siteUrl.href = url;
}

function renderResponseTime(responseTimeMs) {
  const value = Number(responseTimeMs);

  elements.responseTime.className = "metric-value";

  if (!Number.isFinite(value)) {
    elements.responseTime.textContent = "--";
    return;
  }

  elements.responseTime.textContent = `${Math.round(value)} ms`;

  if (value < 800) {
    elements.responseTime.classList.add("response-fast");
  } else if (value < 2000) {
    elements.responseTime.classList.add("response-medium");
  } else {
    elements.responseTime.classList.add("response-slow");
  }
}

function renderContentCheck(contentCheckPassed) {
  if (contentCheckPassed === true) {
    elements.contentCheck.textContent = "Passed";
  } else if (contentCheckPassed === false) {
    elements.contentCheck.textContent = "Failed";
  } else {
    elements.contentCheck.textContent = "Not configured";
  }
}

function renderFailureReason(isUp, failureReason) {
  if (isUp || !failureReason) {
    elements.failurePanel.classList.add("is-hidden");
    elements.failureReason.textContent = "--";
    return;
  }

  elements.failureReason.textContent = failureReason;
  elements.failurePanel.classList.remove("is-hidden");
}

function renderRecentFailures(recentFailures) {
  elements.recentFailures.replaceChildren();

  if (!Array.isArray(recentFailures) || recentFailures.length === 0) {
    const emptyItem = document.createElement("li");
    emptyItem.className = "empty-state";
    emptyItem.textContent = "No recent failures available.";
    elements.recentFailures.appendChild(emptyItem);
    return;
  }

  recentFailures.slice(0, 5).forEach((failure) => {
    const item = document.createElement("li");
    item.className = "failure-item";

    const time = document.createElement("span");
    time.className = "failure-time";
    time.textContent = formatDateTime(failure.check_time || failure.last_checked);

    const status = document.createElement("span");
    status.className = "failure-meta";
    status.textContent = `HTTP ${formatStatusCode(failure.status_code)}`;

    const responseTime = document.createElement("span");
    responseTime.className = "failure-meta";
    responseTime.textContent = formatResponseTime(failure.response_time_ms);

    const reason = document.createElement("span");
    reason.className = "failure-reason";
    reason.textContent = failure.failure_reason || "No failure reason provided.";

    item.append(time, status, responseTime, reason);
    elements.recentFailures.appendChild(item);
  });
}

function renderMultiSitePanel(data) {
  const sites = Array.isArray(data.sites) ? data.sites : [];

  elements.siteCards.replaceChildren();

  if (!sites.length) {
    elements.multiSitePanel.classList.add("is-hidden");
    return;
  }

  const upCount = sites.filter(isSiteUp).length;
  const downCount = sites.length - upCount;

  elements.totalSites.textContent = sites.length;
  elements.upSites.textContent = upCount;
  elements.downSites.textContent = downCount;
  elements.siteSummaryNote.textContent = `${sites.length} monitored sites`;
  elements.multiSitePanel.classList.remove("is-hidden");

  sites.forEach((site) => {
    elements.siteCards.appendChild(createSiteCard(site));
  });
}

function createSiteCard(site) {
  const isUp = isSiteUp(site);
  const card = document.createElement("article");
  card.className = "site-card";

  const header = document.createElement("div");
  header.className = "site-card-header";

  const titleGroup = document.createElement("div");

  const title = document.createElement("h3");
  title.textContent = site.site_id || "Site";

  const url = document.createElement("a");
  url.className = "site-card-url";
  url.textContent = site.url || "--";
  if (site.url) {
    url.href = site.url;
    url.target = "_blank";
    url.rel = "noreferrer";
  }

  titleGroup.append(title, url);

  const badge = document.createElement("span");
  badge.className = `status-badge site-status ${isUp ? "status-up" : "status-down"}`;
  badge.textContent = isUp ? "UP" : "DOWN";

  header.append(titleGroup, badge);
  card.appendChild(header);

  const details = document.createElement("dl");
  details.className = "site-detail-grid";

  [
    ["HTTP", formatStatusCode(site.status_code)],
    ["Response", formatResponseTime(site.response_time_ms)],
    ["Content", formatContentCheck(site.content_check_passed)],
    ["Uptime", formatPercent(site.uptime_percentage)],
    ["Average", formatResponseTime(site.average_response_time_ms)],
    ["Incidents 24h", formatNumber(site.incident_count_24h)],
    ["Incidents 7d", formatNumber(site.incident_count_7d)],
    ["Consecutive", formatNumber(site.consecutive_failure_count)],
    ["Alert Sent", formatBoolean(site.alert_sent)],
    ["Redirect Policy", site.redirect_policy || "follow"],
    ["Redirect Seen", formatBoolean(site.redirect_detected)],
  ].forEach(([label, value]) => {
    details.appendChild(createSiteDetail(label, value));
  });

  card.appendChild(details);

  if (!isUp && site.failure_reason) {
    const reason = document.createElement("p");
    reason.className = "site-failure-reason";
    reason.textContent = site.failure_reason;
    card.appendChild(reason);
  }

  return card;
}

function createSiteDetail(label, value) {
  const item = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");

  term.textContent = label;
  description.textContent = value;
  item.append(term, description);

  return item;
}

function renderResponseTrend(data) {
  const chartData = getResponseTrendData(data);

  if (!chartData.labels.length || typeof Chart === "undefined") {
    if (responseTrendChart) {
      responseTrendChart.destroy();
      responseTrendChart = null;
    }
    elements.responseTrendChart.classList.add("is-hidden");
    elements.responseTrendEmpty.classList.remove("is-hidden");
    return;
  }

  elements.responseTrendEmpty.classList.add("is-hidden");
  elements.responseTrendChart.classList.remove("is-hidden");

  if (responseTrendChart) {
    responseTrendChart.data.labels = chartData.labels;
    responseTrendChart.data.datasets[0].data = chartData.values;
    responseTrendChart.update();
    return;
  }

  responseTrendChart = new Chart(elements.responseTrendChart, {
    type: "line",
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: "Response time (ms)",
          data: chartData.values,
          borderColor: "#235a82",
          backgroundColor: "rgba(35, 90, 130, 0.14)",
          pointBackgroundColor: "#235a82",
          pointBorderColor: "#fbfcf8",
          pointRadius: 5,
          pointHoverRadius: 6,
          tension: 0.28,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.parsed.y} ms`,
          },
        },
      },
      scales: {
        x: {
          grid: {
            display: false,
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `${value} ms`,
          },
        },
      },
    },
  });
}

function getResponseTrendData(data) {
  const sites = Array.isArray(data.sites) ? data.sites : [data];
  const points = sites
    .map((site) => ({
      label: site.site_id || site.url || "Site",
      value: Number(site.response_time_ms),
    }))
    .filter((point) => Number.isFinite(point.value));

  return {
    labels: points.map((point) => point.label),
    values: points.map((point) => Math.round(point.value)),
  };
}

function renderError(error) {
  elements.statusBadge.className = "status-badge status-loading";
  elements.statusBadge.textContent = "Error";
  elements.messagePanel.className = "message-panel error";
  elements.messagePanel.textContent = `${error.message}. Confirm status.json exists in the same S3 bucket and is publicly readable.`;
  renderMultiSitePanel({});
  renderResponseTrend({});
}

function isSiteUp(site) {
  return site.is_success === true || site.status === "UP";
}

function formatDateTime(value) {
  if (!value) {
    return "--";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

function formatStatusCode(statusCode) {
  return statusCode === null || statusCode === undefined ? "N/A" : String(statusCode);
}

function formatResponseTime(responseTimeMs) {
  const value = Number(responseTimeMs);
  return Number.isFinite(value) ? `${Math.round(value)} ms` : "N/A";
}

function formatContentCheck(contentCheckPassed) {
  if (contentCheckPassed === true) {
    return "Passed";
  }
  if (contentCheckPassed === false) {
    return "Failed";
  }
  return "Not configured";
}

function formatPercent(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${number.toFixed(2)}%` : "N/A";
}

function formatNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number)) : "N/A";
}

function formatBoolean(value) {
  if (value === true) {
    return "Yes";
  }
  if (value === false) {
    return "No";
  }
  return "N/A";
}

loadStatus();
setInterval(loadStatus, REFRESH_INTERVAL_MS);
