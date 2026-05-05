# Website Uptime Monitor

[日本語版はこちら](README.ja.md)

> Serverless AWS monitoring engine that checks uptime, validates content, alerts on failure, and publishes live status to a static dashboard. Zero servers. Near-zero cost.

![Architecture](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/architecture.png)

-----

## What This Does

Every 5 minutes, a Lambda function wakes up, hits a target URL, and makes four decisions:

1. Did it respond at all?
1. Did it respond fast enough?
1. Does the page contain the content it should?
1. Does the page contain content it shouldn’t?

Results go to DynamoDB. If something fails, an SNS email fires immediately. The latest status overwrites a single `status.json` file on S3, which a static dashboard reads on load. No API Gateway. No servers to maintain.

-----

## Dashboard

|UP State                                                                                                        |DOWN State                                                                                                          |
|----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
|![UP](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-up.png)|![DOWN](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dashboard-down.png)|

|DynamoDB Check History                                                                                                    |SNS Alert Email                                                                                                     |
|--------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
|![DynamoDB](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/dynamodb-results.png)|![SNS](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/sns-alert-email.png)|

-----

## How It Works

```
EventBridge (every 5 min)
        │
        ▼
   Lambda Function
   ┌──────────────────────────────┐
   │  HTTP GET → target URL       │
   │  ✓ Status code 2xx?          │
   │  ✓ Response time < threshold?│
   │  ✓ Expected text present?    │
   │  ✓ Forbidden text absent?    │
   └──────────────────────────────┘
        │                   │
        ▼                   ▼
   DynamoDB            S3 status.json ──→ Static Dashboard
   (full history)
        │
        ▼  on failure only
   SNS Email Alert
```

**Why this stack:**

- **Lambda over EC2:** runs only on schedule, no idle compute, no patching
- **DynamoDB over RDS:** append-only timestamped writes with no schema to maintain
- **S3 `status.json` over API Gateway:** dashboard reads one static file; no backend to operate
- **SNS over custom email:** email alerts only on failure; delivery handled by AWS, zero infrastructure

-----

## Failure Detection

A check fails if any of these are true, evaluated in order:

|Rule             |Condition                                         |
|-----------------|--------------------------------------------------|
|Network error    |Connection refused, DNS failure, timeout          |
|Bad status code  |HTTP response outside 200–299                     |
|Slow response    |Response time exceeds `RESPONSE_THRESHOLD_MS`     |
|Missing content  |`EXPECTED_TEXT` set but not found in response body|
|Forbidden content|`FORBIDDEN_TEXT` set and found in response body   |

Content validation is the key addition over basic uptime checks. A maintenance page or broken deployment can still return HTTP 200. Checking for expected text catches what status codes miss.

-----

## Cost

Expected cost is **near $0/month** for personal use.

At 5-minute intervals: ~8,640 Lambda executions per month, ~8,640 DynamoDB writes, one `status.json` file (~1KB) overwritten each run. For this personal demo workload, the usage is far below typical Free Tier thresholds. SNS email alerts only fire during actual failures, keeping that usage minimal too.

Cost stays low because: no always-on compute, S3 static dashboard instead of a hosted server, DynamoDB on-demand billing, Lambda runs only on schedule.

-----

## Setup

### Prerequisites

- AWS account
- Python 3.12+
- Region: `ap-northeast-1`

### AWS Resources

|Resource        |Name                               |
|----------------|-----------------------------------|
|DynamoDB table  |`website_checks`                   |
|SNS topic       |`uptime-alerts`                    |
|IAM role        |`uptime-monitor-lambda-role`       |
|Lambda function |`website-uptime-check`             |
|EventBridge rule|`uptime-check-every-5-min`         |
|S3 bucket       |globally unique name of your choice|

### Lambda Environment Variables

|Variable               |Description                               |Default               |
|-----------------------|------------------------------------------|----------------------|
|`TARGET_URL`           |URL to monitor                            |required              |
|`TIMEOUT_SECONDS`      |Request timeout                           |`10`                  |
|`RESPONSE_THRESHOLD_MS`|Max acceptable response time (ms)         |`3000`                |
|`SNS_TOPIC_ARN`        |ARN for failure alerts                    |required              |
|`DYNAMODB_TABLE`       |Table name                                |`website_checks`      |
|`S3_BUCKET`            |Dashboard bucket name                     |required for dashboard|
|`S3_STATUS_KEY`        |Key for status file                       |`status.json`         |
|`SITE_ID`              |Identifier stored with each check         |`my-portfolio`        |
|`EXPECTED_TEXT`        |Text that must appear in response body    |optional              |
|`FORBIDDEN_TEXT`       |Text that must not appear in response body|optional              |

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
- Broken URL → `is_success: false` in DynamoDB, SNS email received
- Low `RESPONSE_THRESHOLD_MS` → slow response detected, SNS email received
- Mismatched `EXPECTED_TEXT` → content failure on HTTP 200, `is_success: false`

-----

## DynamoDB Schema

```
website_checks
├── site_id              (partition key)
├── check_time           (sort key, ISO 8601)
├── url
├── status_code
├── response_time_ms
├── is_success
├── failure_reason
└── content_check_passed
```

-----

## IAM Policy (least privilege)

The Lambda role is granted exactly what it needs:

|Permission           |Scope                      |
|---------------------|---------------------------|
|`dynamodb:PutItem`   |`website_checks` ARN only  |
|`dynamodb:Query`     |`website_checks` ARN only  |
|`sns:Publish`        |`uptime-alerts` ARN only   |
|`s3:PutObject`       |`<bucket>/status.json` only|
|CloudWatch Logs write|Lambda execution logs      |

No broad application permissions. DynamoDB, SNS, and S3 are each scoped to a specific ARN.

-----

## CloudWatch Logs

![CloudWatch](https://raw.githubusercontent.com/amanrai00/website-uptime-monitor/main/docs/screenshots/cloudwatch-logs.png)

-----

## Known Limitations

- Monitors one target URL. Multi-site support is the natural next step, with each site getting its own `site_id`.
- Dashboard reflects the last `status.json` write, not a live stream. Staleness is visible via the last-checked timestamp.
- Alerts fire on every failure. A consecutive-failure threshold to reduce noise is a planned improvement.
- No dashboard authentication, which is acceptable for a public portfolio demo but not for production.
- If Lambda or EventBridge stops running silently, there is no dead-man’s switch. A CloudWatch alarm on invocation count would catch this.

-----

## Lessons Learned

**HTTP 200 is not enough.** A CloudFront error page, maintenance placeholder, or broken deployment can all return 200. Content validation catches what status codes miss, and that is the real value of Phase 3.

**`status.json` and DynamoDB can silently diverge.** The dashboard showed DOWN, but `recent_failures` stayed empty because the Lambda was querying historical DynamoDB records but not injecting the current failed check into the S3 payload. Fix: write the current check result directly into `recent_failures` first, query DynamoDB for older failures, deduplicate by `check_time`, keep the latest 5.

**Static S3 beats API Gateway for a read-only dashboard.** One file, no backend, no cold starts on the read path. The only tradeoff is the 5-minute polling interval. The dashboard is as fresh as the last Lambda run.

**IAM scope matters even in personal projects.** Scoping permissions to specific ARNs forced a clear understanding of what each service actually needs, and that thinking comes up directly in systems design interviews.

-----

## What I’d Build Next

- Multi-site monitoring with per-site `site_id` routing
- Uptime percentage and incident count metrics per site
- Response time trend chart on the dashboard (Chart.js)
- Consecutive-failure alert threshold to reduce email noise
- DynamoDB TTL to auto-expire old records
- CloudWatch alarm if Lambda stops executing

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