const REFRESH_INTERVAL_MS = 60 * 1000;

const elements = {
  statusBadge: document.getElementById("statusBadge"),
  messagePanel: document.getElementById("messagePanel"),
  siteUrl: document.getElementById("siteUrl"),
  lastChecked: document.getElementById("lastChecked"),
  statusCode: document.getElementById("statusCode"),
  responseTime: document.getElementById("responseTime"),
  failurePanel: document.getElementById("failurePanel"),
  failureReason: document.getElementById("failureReason"),
  recentFailures: document.getElementById("recentFailures"),
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
  renderFailureReason(isUp, data.failure_reason);
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

function renderError(error) {
  elements.statusBadge.className = "status-badge status-loading";
  elements.statusBadge.textContent = "Error";
  elements.messagePanel.className = "message-panel error";
  elements.messagePanel.textContent = `${error.message}. Confirm status.json exists in the same S3 bucket and is publicly readable.`;
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

loadStatus();
setInterval(loadStatus, REFRESH_INTERVAL_MS);
