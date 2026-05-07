# Website Uptime Monitor

[日本語版はこちら](README.ja.md)

> Serverless AWS monitoring engine that checks uptime, validates content, alerts on failure, and publishes live status to a static dashboard. Zero servers. Near-zero cost.
>
> **[Live Dashboard →](https://amanrai00-uptime-dashboard.s3.ap-northeast-1.amazonaws.com/index.html)**

![Architecture](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/architecture.png.PNG)

-----

## What This Does

Every 5 minutes, a Lambda function wakes up, hits every configured target URL, and makes four decisions per site:

1. Did it respond at all?
1. Did it respond fast enough?
1. Does the page contain the content it should?
1. Does the page contain content it shouldn't?

Results go to DynamoDB. If a site fails consecutively, an SNS email fires. The latest status overwrites a single `status.json` file on S3, which a static dashboard reads on load. No API Gateway. No servers to maintain.

-----

## Dashboard

|Multi-Site Dashboard|DOWN State|
|---|---|
|![UP](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-up.png)|![DOWN](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-down.png)|

|DynamoDB Check History|SNS Alert Email|
|---|---|
|![DynamoDB](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dynamodb-results.png)|![SNS](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/sns-alert-email.png)|

-----

## How It Works

```
EventBridge (every 5 min)
        │
        ▼
   Lambda Function
   ┌──────────────────────────────────────┐
   │  For each configured site:           │
   │  HTTP GET → target URL               │
   │  ✓ Status code 2xx?                  │
   │  ✓ Response time < threshold?        │
   │  ✓ Expected text present?            │
   │  ✓ Forbidden text absent?            │
   │  ✓ Alert threshold reached?          │
   └──────────────────────────────────────┘
        │                   │
        ▼                   ▼
   DynamoDB            S3 status.json ──→ Static Dashboard
   (full history)
        │
        ▼  on consecutive failure threshold only
   SNS Email Alert
```

**Why this stack:**

- **Lambda over EC2:** runs only on schedule, no idle compute, no patching
- **DynamoDB over RDS:** append-only timestamped writes with no schema to maintain
- **S3 `status.json` over API Gateway:** dashboard reads one static file; no backend to operate
- **SNS over custom email:** email alerts after the failure threshold is reached; delivery handled by AWS, zero infrastructure

-----

## Failure Detection

A check fails if any of these are true, evaluated in order:

| Rule | Condition |
|---|---|
| Network error | Connection refused, DNS failure, timeout |
| Bad status code | HTTP response outside 200–299 |
| Slow response | Response time exceeds `RESPONSE_THRESHOLD_MS` |
| Missing content | `EXPECTED_TEXT` set but not found in response body |
| Forbidden content | `FORBIDDEN_TEXT` set and found in response body |
| Redirect blocked | `redirect_policy` set to `fail_on_redirect` and redirect detected |

Content validation is the key addition over basic uptime checks. A maintenance page or broken deployment can still return HTTP 200. Checking for expected text catches what status codes miss.

-----

## Alerting

Alerts use a consecutive-failure threshold before sending SNS. The default threshold is 2.

- First failure: logged and tracked, no alert sent
- Second consecutive failure: SNS email fires with site URL, failure reason, status code, response time, and timestamp
- Recovery: consecutive failure count resets to 0

This reduces alert noise from single transient failures while still catching real outages.

-----

## Multi-Site Monitoring

Multiple sites can be monitored in a single Lambda run using the `SITES_CONFIG` environment variable. Each site gets its own `site_id` in DynamoDB. All results share one table.

Per-site metrics tracked on every run:

- Uptime percentage
- Average response time
- Incident count for last 24h and last 7 days
- Consecutive failure count
- Alert sent status
- Redirect policy and redirect detected

-----

## Cost

Expected cost is **near $0/month** for personal use.

At 5-minute intervals: ~8,640 Lambda executions per month, ~8,640 DynamoDB writes per site, one `status.json` file (~1KB) overwritten each run. For this personal demo workload, the usage is far below typical Free Tier thresholds. SNS email alerts only fire on consecutive failures, keeping that usage minimal.

Cost stays low because: no always-on compute, S3 static dashboard instead of a hosted server, DynamoDB on-demand billing, Lambda runs only on schedule.

-----

## Setup

### Prerequisites

- AWS account
- Python 3.12+
- Region: `ap-northeast-1`

### AWS Resources

| Resource | Name |
|---|---|
| DynamoDB table | `website_checks` |
| SNS topic | `uptime-alerts` |
| IAM role | `uptime-monitor-lambda-role` |
| Lambda function | `website-uptime-check` |
| EventBridge rule | `uptime-check-every-5-min` |
| S3 bucket | globally unique name of your choice |

### Lambda Environment Variables

**Single-site configuration:**

| Variable | Description | Default |
|---|---|---|
| `TARGET_URL` | URL to monitor | required |
| `TIMEOUT_SECONDS` | Request timeout | `10` |
| `RESPONSE_THRESHOLD_MS` | Max acceptable response time (ms) | `3000` |
| `SNS_TOPIC_ARN` | ARN for failure alerts | required |
| `DYNAMODB_TABLE` | Table name | `website_checks` |
| `S3_BUCKET` | Dashboard bucket name | required for dashboard |
| `S3_STATUS_KEY` | Key for status file | `status.json` |
| `SITE_ID` | Identifier stored with each check | `my-portfolio` |
| `EXPECTED_TEXT` | Text that must appear in response body | optional |
| `FORBIDDEN_TEXT` | Text that must not appear in response body | optional |
| `ALERT_FAILURE_THRESHOLD` | Consecutive failures before SNS alert | `2` |
| `RETENTION_DAYS` | DynamoDB TTL retention period in days | `30` |
| `REDIRECT_POLICY` | `follow` or `fail_on_redirect` | `follow` |

**Multi-site configuration:**

Set `SITES_CONFIG` as a JSON array. When present, it takes priority over single-site variables.

```json
[
  {
    "site_id": "main-site",
    "target_url": "https://example.com",
    "timeout_seconds": 10,
    "response_threshold_ms": 3000,
    "expected_text": "Welcome",
    "forbidden_text": "Error",
    "redirect_policy": "follow"
  },
  {
    "site_id": "second-site",
    "target_url": "https://example.org",
    "timeout_seconds": 10,
    "response_threshold_ms": 3000
  }
]
```

### Deploy

```bash
# Package Lambda
cd lambda
zip -r ../lambda-deploy.zip .

# Upload to Lambda
aws lambda update-function-code \
  --function-name website-uptime-check \
  --zip-file fileb://../lambda-deploy.zip

# Upload dashboard to S3
aws s3 sync dashboard/ s3://your-bucket-name/
```

### Validate

Run these manual Lambda tests before relying on the schedule:

- Healthy URL → `is_success: true` in DynamoDB, no SNS alert sent
- Broken URL → `is_success: false` in DynamoDB, SNS email received after 2 consecutive failures
- Low `RESPONSE_THRESHOLD_MS` → slow response detected, `is_success: false`
- Mismatched `EXPECTED_TEXT` → content failure on HTTP 200, `is_success: false`
- `SITES_CONFIG` with multiple sites → separate DynamoDB items per `site_id`

-----

## DynamoDB Schema

```
website_checks
├── site_id                  (partition key)
├── check_time               (sort key, ISO 8601)
├── url
├── status_code
├── response_time_ms
├── is_success
├── failure_reason
├── content_check_passed
├── uptime_percentage
├── uptime_window_checks
├── average_response_time_ms
├── response_time_window_checks
├── incident_count_24h
├── incident_count_7d
├── consecutive_failure_count
├── alert_sent
├── alert_failure_threshold
├── redirect_policy
├── redirect_detected
└── ttl_expires_at
```

-----

## IAM Policy (least privilege)

The Lambda role is granted exactly what it needs:

| Permission | Scope |
|---|---|
| `dynamodb:PutItem` | `website_checks` ARN only |
| `dynamodb:Query` | `website_checks` ARN only |
| `sns:Publish` | `uptime-alerts` ARN only |
| `s3:PutObject` | `<bucket>/status.json` only |
| CloudWatch Logs write | Lambda execution logs |

No broad application permissions. DynamoDB, SNS, and S3 are each scoped to a specific ARN.

-----

## CloudWatch Logs

![CloudWatch](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/cloudwatch-logs.png)

-----

## Known Limitations

- Dashboard reflects the last `status.json` write, not a live stream. Staleness is visible via the last-checked timestamp.
- No dashboard authentication, which is acceptable for a public portfolio demo but not for production.
- If Lambda or EventBridge stops running silently, there is no dead-man's switch. A CloudWatch alarm on invocation count would catch this.
- The consecutive-failure alert threshold is a single global value. It applies to all monitored sites and is not configurable per site.
- The dashboard chart shows the latest response time per site, not a full historical trend, because it reads only the current `status.json` payload.

-----

## Lessons Learned

**HTTP 200 is not enough.** A CloudFront error page, maintenance placeholder, or broken deployment can all return 200. Content validation catches what status codes miss, and that is the real value of Phase 3.

**`status.json` and DynamoDB can silently diverge.** The dashboard showed DOWN, but `recent_failures` stayed empty because Lambda was querying historical DynamoDB records but not injecting the current failed check into the S3 payload. Fix: write the current check result directly into `recent_failures` first, query DynamoDB for older failures, deduplicate by `check_time`, keep the latest 5.

**Static S3 beats API Gateway for a read-only dashboard.** One file, no backend, no cold starts on the read path. The only tradeoff is the 5-minute polling interval. The dashboard is as fresh as the last Lambda run.

**IAM scope matters even in personal projects.** Scoping permissions to specific ARNs forced a clear understanding of what each service actually needs, and that thinking comes up directly in systems design interviews.

**Alert noise is a real problem at scale.** A single transient failure firing an SNS email trains you to ignore alerts. Adding a consecutive-failure threshold before alerting is a small change that makes the system significantly more trustworthy.

-----

## What I'd Build Next

- CloudWatch alarm if Lambda stops executing silently
- Multi-region monitoring for latency comparison across regions
- API Gateway for real-time dashboard data when the 5-minute polling interval is no longer acceptable
- Authenticated page checks for pages behind a login
- Per-site alert threshold configuration instead of one global value
- Public-facing status page separate from the internal dashboard
- Terraform or AWS SAM for infrastructure-as-code deployment

-----

## Project Structure

```
website-uptime-monitor/
├── lambda/
│   ├── app.py
│   ├── requirements.txt
│   └── tests/
│       └── test_app.py
├── dashboard/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── docs/
    ├── architecture.png
    └── screenshots/
```

-----

## Interview Topics

Questions this project is designed to answer:

- Why Lambda over a cron job on EC2?
- Why DynamoDB over RDS for monitoring data?
- Why `status.json` on S3 instead of API Gateway?
- What does the IAM policy allow and why nothing broader?
- How is `response_time_ms` measured and what does it represent?
- What does content validation catch that HTTP status codes miss?
- What happens if Lambda stops running silently?
- How would you extend this to monitor 50 sites?
- Why use a consecutive-failure threshold before alerting?
- How does multi-site monitoring work with a single DynamoDB table?
