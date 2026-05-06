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
  const sites = Array.isArray(data.sites) ? data.sites : [];
  const isMultiSite = sites.length > 0;
  const isUp = data.is_success === true || data.status === "UP";

  elements.statusBadge.className = `status-badge ${isUp ? "status-up" : "status-down"}`;
  elements.statusBadge.textContent = isUp ? "UP" : "DOWN";

  elements.messagePanel.className = `message-panel ${isUp ? "success" : "error"}`;
  elements.messagePanel.textContent = isUp
    ? "All sites are up."
    : "One or more sites are down.";

  if (isMultiSite) {
    renderTopCardsMultiSite(data, sites);
  } else {
    renderTopCardsSingleSite(data);
  }

  renderFailureReason(isMultiSite || isUp, data.failure_reason);
  renderMultiSitePanel(data);
  renderResponseTrend(data);
  renderRecentFailures(data, sites);
}

function renderTopCardsSingleSite(data) {
  const siteUrlCard = elements.siteUrl.closest("article");
  if (siteUrlCard) siteUrlCard.querySelector(".metric-label").textContent = "Site URL";
  elements.siteUrl.className = "metric-value link-value";
  renderSiteUrl(data.url);

  elements.lastChecked.textContent = formatDateTime(data.checked_at || data.last_checked || data.check_time);

  const statusCodeCard = elements.statusCode.closest("article");
  if (statusCodeCard) statusCodeCard.querySelector(".metric-label").textContent = "HTTP Status";
  elements.statusCode.className = "metric-value";
  elements.statusCode.textContent = formatStatusCode(data.status_code);

  const responseCard = elements.responseTime.closest("article");
  if (responseCard) responseCard.querySelector(".metric-label").textContent = "Response Time";
  renderResponseTime(data.response_time_ms);

  const contentCard = elements.contentCheck.closest("article");
  if (contentCard) contentCard.querySelector(".metric-label").textContent = "Content Check";
  renderContentCheck(data.content_check_passed);
}

function renderTopCardsMultiSite(data, sites) {
  const upCount = sites.filter(isSiteUp).length;
  const downCount = sites.length - upCount;
  const checkedAt = formatDateTime(data.checked_at || data.last_checked || data.check_time);

  // Card 1 (wide): repurpose as "Monitored Sites" overview
  const siteUrlCard = elements.siteUrl.closest("article");
  if (siteUrlCard) {
    siteUrlCard.querySelector(".metric-label").textContent = "Monitored Sites";
    elements.siteUrl.textContent = `${sites.length} site${sites.length !== 1 ? "s" : ""} tracked`;
    elements.siteUrl.removeAttribute("href");
    elements.siteUrl.className = "metric-value";
  }

  elements.lastChecked.textContent = checkedAt;

  // Card 3: UP count
  const statusCodeCard = elements.statusCode.closest("article");
  if (statusCodeCard) statusCodeCard.querySelector(".metric-label").textContent = "UP";
  elements.statusCode.textContent = upCount;
  elements.statusCode.className = "metric-value response-fast";

  // Card 4: DOWN count
  const responseCard = elements.responseTime.closest("article");
  if (responseCard) responseCard.querySelector(".metric-label").textContent = "DOWN";
  elements.responseTime.className = "metric-value" + (downCount > 0 ? " response-slow" : " response-fast");
  elements.responseTime.textContent = downCount;

  // Card 5: overall uptime across all sites
  const contentCard = elements.contentCheck.closest("article");
  if (contentCard) contentCard.querySelector(".metric-label").textContent = "Avg Uptime";
  const uptimes = sites.map((s) => Number(s.uptime_percentage)).filter(Number.isFinite);
  elements.contentCheck.textContent = uptimes.length
    ? `${(uptimes.reduce((a, b) => a + b, 0) / uptimes.length).toFixed(1)}%`
    : "--";
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

function renderRecentFailures(data, sites) {
  elements.recentFailures.replaceChildren();

  let failures;

  if (sites.length > 0) {
    failures = [];
    sites.forEach((site) => {
      if (Array.isArray(site.recent_failures) && site.recent_failures.length > 0) {
        site.recent_failures.forEach((f) => {
          failures.push({ ...f, _site_id: site.site_id || site.url, _url: site.url });
        });
      } else if (!isSiteUp(site)) {
        failures.push({
          _site_id: site.site_id || site.url,
          _url: site.url,
          check_time: data.checked_at || data.last_checked || data.check_time,
          status_code: site.status_code,
          response_time_ms: site.response_time_ms,
          failure_reason: site.failure_reason,
        });
      }
    });
  } else {
    failures = Array.isArray(data.recent_failures) ? data.recent_failures : [];
  }

  if (failures.length === 0) {
    const emptyItem = document.createElement("li");
    emptyItem.className = "empty-state";
    emptyItem.textContent = "No recent failures available.";
    elements.recentFailures.appendChild(emptyItem);
    return;
  }

  failures.slice(0, 10).forEach((failure) => {
    const item = document.createElement("li");
    item.className = "failure-item";

    const time = document.createElement("span");
    time.className = "failure-time";

    const siteLabel = failure._site_id ? `[${failure._site_id}] ` : "";
    const timeStr = formatDateTime(failure.check_time || failure.last_checked || failure.checked_at);
    time.textContent = siteLabel + timeStr;

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
    ["Incidents 24h", formatNumber(site.incidents_24h ?? site.incident_count_24h)],
    ["Incidents 7d", formatNumber(site.incidents_7d ?? site.incident_count_7d)],
    ["Consecutive", formatNumber(site.consecutive_failures ?? site.consecutive_failure_count)],
    ["Alert Sent", formatBoolean(site.alert_sent)],
    ["Redirect Policy", site.redirect_policy || "follow"],
    ["Redirect Seen", formatBoolean(site.redirect_seen ?? site.redirect_detected)],
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

  const barValueLabelsPlugin = {
    id: "barValueLabels",
    afterDatasetsDraw(chart) {
      const { ctx, data } = chart;
      ctx.save();
      ctx.font = "bold 12px Inter, ui-sans-serif, system-ui, sans-serif";
      ctx.fillStyle = "oklch(41% 0.17 151)";
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";
      data.datasets.forEach((dataset, datasetIndex) => {
        const meta = chart.getDatasetMeta(datasetIndex);
        meta.data.forEach((bar, index) => {
          const value = dataset.data[index];
          if (value != null) {
            ctx.fillText(`${value} ms`, bar.x, bar.y - 4);
          }
        });
      });
      ctx.restore();
    },
  };

  responseTrendChart = new Chart(elements.responseTrendChart, {
    type: "bar",
    plugins: [barValueLabelsPlugin],
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: "Response time (ms)",
          data: chartData.values,
          borderColor: "#159947",
          backgroundColor: "rgba(21, 153, 71, 0.78)",
          borderRadius: 6,
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { top: 24 },
      },
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
          grid: {
            color: "rgba(24, 99, 67, 0.12)",
          },
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
  renderRecentFailures({}, []);
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
