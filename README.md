<div align="center">

# Website Uptime Monitor

### Serverless AWS monitoring. Built solo. Running in production.

[![Live Dashboard](https://img.shields.io/badge/🟢_Live_Dashboard-Open-2ea44f?style=for-the-badge)](https://amanrai00-uptime-dashboard.s3.ap-northeast-1.amazonaws.com/index.html)
[![日本語版](https://img.shields.io/badge/日本語版-README.ja.md-red?style=for-the-badge)](README.ja.md)

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=flat&logo=amazon-aws&logoColor=white)
![Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=flat&logo=awslambda&logoColor=white)
![DynamoDB](https://img.shields.io/badge/DynamoDB-4053D6?style=flat&logo=amazondynamodb&logoColor=white)
![S3](https://img.shields.io/badge/Amazon_S3-569A31?style=flat&logo=amazons3&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)

---

**Lambda checks every 5 min → validates content (not just HTTP 200) → DynamoDB stores → S3 dashboard renders → SNS alerts on consecutive failures.**

No EC2. No API Gateway. No idle compute. ~$0/month.

</div>

---

## The Problem This Solves

HTTP 200 ≠ working site. CloudFront error pages, broken deploys, maintenance placeholders all return 200. Basic uptime checks miss them.

This monitor validates **content**, not just **status codes**.

---

## Architecture

<div align="center">

![Architecture](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/architecture.png.PNG)

</div>

```
EventBridge (5 min) ──► Lambda ──┬──► DynamoDB (history)
                                  ├──► S3 status.json ──► Static Dashboard
                                  └──► SNS Email (after N consecutive fails)
```

| Decision | Why |
|---|---|
| **Lambda over EC2** | Schedule-only execution, zero idle compute, zero patching |
| **DynamoDB over RDS** | Append-only timestamped writes, no schema migrations |
| **S3 `status.json` over API Gateway** | One static file, no backend, no cold starts |
| **SNS over custom mail** | AWS handles delivery, zero infra to operate |
| **Consecutive-fail threshold** | Single transient failure ≠ alert. Trust preserved. |

---

## Screenshots

<table>
  <tr>
    <td align="center"><b>Dashboard — Healthy</b></td>
    <td align="center"><b>Dashboard — DOWN State</b></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-up.png" /></td>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-down.png" /></td>
  </tr>
  <tr>
    <td align="center"><b>DynamoDB Check History</b></td>
    <td align="center"><b>SNS Alert Email</b></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dynamodb-results.png" /></td>
    <td><img src="https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/sns-alert-email.png" /></td>
  </tr>
</table>

---

## What I Learned Building This

> **HTTP 200 lies.** Content validation became the most useful feature. Maintenance pages return 200 every time.

> **`status.json` and DynamoDB silently diverged.** Dashboard showed DOWN, `recent_failures` stayed empty. Lambda queried historical records but didn't inject the *current* failed check into the S3 payload. Fix: write current result first → query DynamoDB for older → dedupe by `check_time` → keep latest 5. Bug only surfaces when you actually run the system.

> **IAM least-privilege scope is a thinking exercise.** Forcing each permission to a specific ARN (DynamoDB table, SNS topic, single S3 key) clarified what each service genuinely needs. Discipline carries to production.

> **Alert noise erodes trust faster than missed alerts.** A single transient failure firing email trains operators to ignore alerts. Threshold of 2 = trustworthy.

> **Static S3 beats API Gateway for read-only dashboards.** No cold starts on read. Tradeoff: dashboard freshness = last Lambda run (5 min). Acceptable for this use case.

---

## Failure Detection Logic

Evaluated in order. First match wins.

| # | Rule | Trigger Condition |
|---|---|---|
| 1 | Network error | Connection refused / DNS failure / timeout |
| 2 | Bad status code | HTTP outside 200–299 |
| 3 | Slow response | Time > `RESPONSE_THRESHOLD_MS` |
| 4 | Missing content | `EXPECTED_TEXT` set but absent in body |
| 5 | Forbidden content | `FORBIDDEN_TEXT` set and present in body |
| 6 | Redirect blocked | `redirect_policy=fail_on_redirect` and redirect detected |

---

## Alerting Flow

```
Failure #1  →  Logged to DynamoDB. No email.
Failure #2  →  SNS email fires (URL, reason, status, response time, timestamp)
Recovery    →  consecutive_failure_count resets to 0
```

Default threshold: **2**. Configurable via `ALERT_FAILURE_THRESHOLD`.

---

## Multi-Site Monitoring

One Lambda run → many sites. Each gets its own `site_id` in DynamoDB. One shared table.

Per-site metrics every run:
- Uptime %
- Avg response time
- Incident count (24h / 7d)
- Consecutive failure count
- Alert sent flag
- Redirect policy + detection

---

## Cost

**Near $0/month.**

| Resource | Monthly volume | Free Tier? |
|---|---|---|
| Lambda invocations | ~8,640 | ✅ Well under |
| DynamoDB writes | ~8,640 per site | ✅ On-demand, well under |
| S3 PUT (`status.json`) | ~8,640 (~1KB each) | ✅ Well under |
| SNS email | Only on consecutive fails | ✅ Negligible |

No always-on compute. Schedule-only.

---

## Setup

<details>
<summary><b>Click to expand deployment guide</b></summary>

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
| S3 bucket | globally unique name |

### Environment Variables (Single-Site)

| Variable | Description | Default |
|---|---|---|
| `TARGET_URL` | URL to monitor | required |
| `TIMEOUT_SECONDS` | Request timeout | `10` |
| `RESPONSE_THRESHOLD_MS` | Max acceptable response time | `3000` |
| `SNS_TOPIC_ARN` | ARN for failure alerts | required |
| `DYNAMODB_TABLE` | Table name | `website_checks` |
| `S3_BUCKET` | Dashboard bucket | required |
| `S3_STATUS_KEY` | Status file key | `status.json` |
| `SITE_ID` | Identifier per check | `my-portfolio` |
| `EXPECTED_TEXT` | Must appear in body | optional |
| `FORBIDDEN_TEXT` | Must NOT appear in body | optional |
| `ALERT_FAILURE_THRESHOLD` | Consecutive fails before alert | `2` |
| `RETENTION_DAYS` | DynamoDB TTL | `30` |
| `REDIRECT_POLICY` | `follow` or `fail_on_redirect` | `follow` |

### Multi-Site (`SITES_CONFIG`)

JSON array. Takes priority over single-site vars.

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
    "target_url": "https://example.org"
  }
]
```

### Deploy

```bash
cd lambda
zip -r ../lambda-deploy.zip .

aws lambda update-function-code \
  --function-name website-uptime-check \
  --zip-file fileb://../lambda-deploy.zip

aws s3 sync dashboard/ s3://your-bucket-name/
```

### Validation Tests

- ✅ Healthy URL → `is_success: true`, no SNS
- ✅ Broken URL → `is_success: false`, SNS after 2 fails
- ✅ Low `RESPONSE_THRESHOLD_MS` → slow response detected
- ✅ Mismatched `EXPECTED_TEXT` → content failure on HTTP 200
- ✅ `SITES_CONFIG` multi → separate items per `site_id`

</details>

---

## DynamoDB Schema

<details>
<summary><b>Click to expand</b></summary>

```
website_checks
├── site_id                       (partition key)
├── check_time                    (sort key, ISO 8601)
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

</details>

---

## IAM (Least Privilege)

| Permission | Scope |
|---|---|
| `dynamodb:PutItem` | `website_checks` ARN only |
| `dynamodb:Query` | `website_checks` ARN only |
| `sns:Publish` | `uptime-alerts` ARN only |
| `s3:PutObject` | `<bucket>/status.json` only |
| CloudWatch Logs | Lambda execution logs only |

Core application permissions are scoped to specific resources. DynamoDB, SNS, and S3 access are limited to the required table, topic, and `status.json` object. CloudWatch Logs permissions are limited to Lambda logging.

---

## CloudWatch Logs

![CloudWatch](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/cloudwatch-logs.png)

---

## Known Limitations

- Dashboard reflects last `status.json` write, not live stream. Staleness visible via timestamp.
- No dashboard auth. Acceptable for portfolio, not production.
- No dead-man's switch if Lambda/EventBridge stop silently. CloudWatch alarm on invocation count would catch this.
- Single global alert threshold. Not per-site configurable yet.
- Dashboard chart shows latest response time per site, not historical trend (reads only current `status.json`).

---

## Roadmap

- [ ] CloudWatch alarm for silent Lambda failure (dead-man's switch)
- [ ] Per-site alert threshold configuration
- [ ] Terraform / AWS SAM for IaC deployment

---

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

---

<div align="center">

### Built by [Aman Rai](https://www.linkedin.com/in/amanrai00) · Tokyo

**AWS Certified Cloud Practitioner** · Studying for SAA-C03 · Building toward Cloud Engineering

[LinkedIn](https://www.linkedin.com/in/amanrai00) · [GitHub](https://github.com/amanrai00) · [AWS Badge](https://www.credly.com/badges/095a2b8e-c94f-4af6-b77c-51ec2fa64d56)

</div>
