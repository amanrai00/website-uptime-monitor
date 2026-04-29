# Product Requirements Document (PRD)

## Project: Website Uptime Monitor

## Version: 1.0 | Last Updated: April 2026

-----

## 1. Overview

Website Uptime Monitor is a serverless, cloud-native monitoring system built on AWS that verifies whether a website is:

- Available (HTTP reachable)
- Fast enough (response time within threshold)
- Showing expected content (content validation)

The system runs automatically on a schedule, stores all results, alerts the owner on failure, and displays status on a static dashboard hosted on S3.

-----

## 2. Problem

A website can fail in multiple ways that a simple ping cannot detect:

1. The site does not load at all (DNS failure, timeout, connection refused)
1. The site loads but returns an error status (5xx, 4xx)
1. The site loads too slowly (degraded performance)
1. The site loads but critical content is missing or broken

This system addresses all four failure modes with structured monitoring, stored history, and automated alerting.

-----

## 3. Goals

Build a practical, cost-effective monitoring system on AWS that:

- Checks websites automatically on a fixed schedule
- Measures HTTP status, response time, and page content
- Stores all results for history, reporting, and portfolio demonstration
- Sends alerts immediately when a failure condition is detected
- Displays real-time status on a dashboard without requiring a server

-----

## 4. Target Users

**Primary:** Solo developer or small website owner who needs automated monitoring without a paid third-party service.

**Secondary:** Hiring manager or technical interviewer reviewing the project as a cloud/DevOps portfolio piece.

-----

## 5. Success Criteria

The project is successful when:

- Scheduled checks run automatically with no manual action required
- Failed checks trigger an SNS alert to the configured email address
- All check results are stored in DynamoDB and queryable by site and time
- The S3 dashboard shows current status refreshed after every Lambda run
- The system can explain clearly why any given check failed

-----

## 6. Scope

### MVP (Phase 1 + Phase 2)

- Monitor one website every 5 minutes
- Lambda sends HTTP GET and records:
  - Timestamp (ISO 8601)
  - Target URL
  - HTTP status code
  - Response time in milliseconds
  - Pass or fail result
  - Failure reason (if applicable)
- Store every result in DynamoDB
- Send SNS email alert when:
  - Site is unreachable (DNS failure, timeout, connection error)
  - HTTP status is outside the 200-299 range
  - Response time exceeds the configured threshold
- Lambda writes a `status.json` file to S3 after every check
- S3 static dashboard reads `status.json` to display current status

### Out of Scope for MVP

- Multi-region monitoring
- Authenticated page checks
- Screenshots
- SMS, Slack, or PagerDuty integrations
- Advanced analytics or AI root-cause analysis

### Version 2

- Monitor multiple websites
- Calculate uptime percentage
- Show recent incidents list
- Add response time trend chart
- Show average response time and incident count by period

### Version 3

- Content validation: check for expected text presence
- Content validation: check for forbidden text presence
- JSON API response monitoring

-----

## 7. Architecture Decision: Dashboard Data Refresh

**Decision: Option A — Lambda writes `status.json` directly to S3.**

After every health check, Lambda writes a small JSON file (`status.json`) to the S3 dashboard bucket. The static HTML page reads this file on load using a `fetch()` call.

**Why this over API Gateway:**

- No additional AWS service required for MVP
- Zero extra cost
- Simpler to build, deploy, and explain
- Data is always as fresh as the last Lambda run (every 5 minutes)
- Easy to upgrade to API Gateway in Version 2 without changing the dashboard UI

**Tradeoff acknowledged:** The dashboard data is only as fresh as the most recent Lambda execution. For a 5-minute schedule, this is acceptable for MVP.

-----

## 8. Core User Stories

### MVP

- As a website owner, I want to know if my website is down.
- As a website owner, I want to know how long the site takes to respond.
- As a website owner, I want to receive an email alert when the site fails.
- As a website owner, I want to see recent monitoring results in one place.

### Future

- As a website owner, I want to know whether important content is still visible.
- As a website owner, I want to compare uptime across multiple websites.
- As a hiring manager, I want to see clear architecture and real monitoring evidence.

-----

## 9. Functional Requirements

### 9.1 Scheduled Checks

- EventBridge rule triggers Lambda every 5 minutes.
- Default schedule is every 5 minutes. This can be changed by updating the EventBridge rule in AWS when needed.

### 9.2 Health Check Logic

Lambda must:

- Send an HTTP GET to the target URL
- Record status code and response time in milliseconds. `response_time_ms` = total HTTP request duration measured by Lambda from request start until response is received.
- Handle and classify all failure types: timeout, DNS error, connection refused, non-2xx status, slow response
- Write result to DynamoDB
- Write updated `status.json` to S3
- Publish SNS alert if any failure condition is met

**Redirect behaviour:** Python’s `urllib` follows redirects automatically. The final resolved status code is what gets evaluated. A 301 that resolves to a 200 passes. This is the default MVP behaviour. Configurable redirect handling may be added in Version 2.

### 9.3 Alerting

SNS publishes an email alert when:

- Request throws an exception (any network-level error)
- HTTP status code is outside 200-299
- Response time exceeds the configured threshold (default: 3000ms)

Alert message must include: site URL, failure type, status code (if available), response time, and timestamp.

**Alert policy:** MVP sends an SNS notification on every failed check. More advanced rules such as consecutive-failure thresholds to reduce noise may be added in Version 2.

### 9.4 Data Storage

DynamoDB table `website_checks`:

- Partition key: `site_id` (string)
- Sort key: `check_time` (ISO 8601 string)
- Additional fields: `url`, `status_code`, `response_time_ms`, `is_success`, `failure_reason`
- Future fields: `content_check_passed`, `expected_text`

### 9.5 Dashboard

S3 hosts a static `index.html` that:

- Fetches `status.json` from the same S3 bucket on page load
- Displays: current status (UP/DOWN), last checked time, latest response time, latest status code, recent failures list
- Updates automatically on each page refresh (reflects latest Lambda run)

**Dashboard freshness:** The dashboard reflects the latest known check result and updates when the page is refreshed. It is not a live streaming view. Maximum data lag equals the EventBridge interval (default 5 minutes).

### 9.6 Content Validation (Version 3)

- Lambda checks whether expected text is present on the page body
- Lambda checks whether forbidden text is absent from the page body
- Failure reason must specify which rule was violated

-----

## 10. Non-Functional Requirements

- **Cost:** Must stay within AWS Free Tier for typical usage (288 Lambda runs/day at 5-minute intervals)
- **Simplicity:** Code and architecture must be explainable to a technical interviewer in under 5 minutes
- **Maintainability:** Clear folder structure, environment variables for all config, no hardcoded secrets
- **Security:** IAM roles with least-privilege; no credentials in source code; S3 bucket public read limited to dashboard files only

-----

## 11. AWS Architecture

```
EventBridge Schedule (every 5 min)
          |
          v
      Lambda (app.py)
          |
    ______|______________________
    |            |               |
    v            v               v
DynamoDB     SNS Alert     S3 status.json
(all results) (on failure)       |
                                 v
                          S3 index.html (dashboard)
```

-----

## 12. Service Justification

|Service    |Role                        |Why                                           |
|-----------|----------------------------|----------------------------------------------|
|EventBridge|Trigger on schedule         |Native cron-style scheduling, no server needed|
|Lambda     |Run check logic             |Serverless, pay-per-use, no idle cost         |
|DynamoDB   |Store results               |Schemaless, fast writes, cheap at low volume  |
|SNS        |Send alerts                 |Managed pub/sub, email delivery built in      |
|S3         |Host dashboard + status.json|Static hosting, zero server cost              |

-----

## 13. Data Model

### DynamoDB: `website_checks`

|Field                 |Type       |Notes                                                                     |
|----------------------|-----------|--------------------------------------------------------------------------|
|`site_id`             |String (PK)|e.g. `"my-portfolio"`                                                     |
|`check_time`          |String (SK)|ISO 8601 timestamp                                                        |
|`url`                 |String     |Full URL checked                                                          |
|`status_code`         |Number     |HTTP response code                                                        |
|`response_time_ms`    |Number     |Total HTTP request duration from request start to response received, in ms|
|`is_success`          |Boolean    |True if all checks passed                                                 |
|`failure_reason`      |String     |Null if success                                                           |
|`content_check_passed`|Boolean    |Future                                                                    |

### S3: `status.json`

```json
{
  "site_id": "my-portfolio",
  "url": "https://example.com",
  "last_checked": "2026-04-22T10:00:00Z",
  "status": "UP",
  "status_code": 200,
  "response_time_ms": 312,
  "is_success": true,
  "failure_reason": null,
  "recent_failures": []
}
```

`recent_failures` contains up to the latest 5 failed checks, each with `check_time`, `status_code`, `response_time_ms`, and `failure_reason`.

In Version 2, each monitored site will support its own configuration block containing `site_id`, `target_url`, `timeout_seconds`, `response_threshold_ms`, and optional content rules.

-----

## 14. Failure Rules

### MVP

A check fails if:

- Request raises any exception (timeout, DNS, connection)
- HTTP status code is not in range 200-299
- Response time exceeds threshold (default: 3000ms, configurable via env var)

### Version 3 Addition

A check also fails if:

- Expected text is not found in the response body
- Forbidden text is found in the response body

-----

## 15. Environment Variables

|Variable               |Purpose                                                   |Example                                                                                  |
|-----------------------|----------------------------------------------------------|-----------------------------------------------------------------------------------------|
|`TARGET_URL`           |Website to monitor                                        |`https://example.com`                                                                    |
|`TIMEOUT_SECONDS`      |Request timeout                                           |`10`                                                                                     |
|`RESPONSE_THRESHOLD_MS`|Slow response limit                                       |`3000`                                                                                   |
|`SNS_TOPIC_ARN`        |Alert destination                                         |`arn:aws:sns:...`                                                                        |
|`DYNAMODB_TABLE`       |Results table name                                        |`website_checks`                                                                         |
|`SITE_ID`              |Site identifier used as DynamoDB partition key            |`my-portfolio`                                                                           |
|`S3_BUCKET`            |Dashboard bucket                                          |`my-uptime-dashboard` — optional until Phase 2; set after the dashboard bucket is created|
|`S3_STATUS_KEY`        |Status file path                                          |`status.json`                                                                            |
|`EXPECTED_TEXT`        |Text that must be present in response body (Version 3)    |`Login` — optional; skip content check if not set                                        |
|`FORBIDDEN_TEXT`       |Text that must not be present in response body (Version 3)|`Error` — optional; skip content check if not set                                        |

-----

## 16. Security

- All credentials via IAM role attached to Lambda; no keys in code
- Lambda IAM policy grants only: `dynamodb:PutItem`, `sns:Publish`, `s3:PutObject` on specific resources
- S3 bucket: public read on `index.html`, `style.css`, `app.js`, and `status.json` only; all other objects private
- No VPC required for MVP (monitoring public URLs only)

-----

## 17. Risks and Mitigations

|Risk                           |Mitigation                                                     |
|-------------------------------|---------------------------------------------------------------|
|Alert noise from flapping sites|Add consecutive-failure threshold before alerting (Version 2)  |
|Dashboard stale if Lambda fails|Show last-checked timestamp prominently so staleness is visible|
|200 response but broken content|Addressed in Version 3 content validation                      |
|S3 status.json public read     |Scope bucket policy to specific keys only                      |

-----

## 18. Development Phases

|Phase  |Deliverable                                               |
|-------|----------------------------------------------------------|
|Phase 1|Lambda + DynamoDB + SNS + EventBridge (monitoring engine) |
|Phase 2|S3 dashboard reading status.json (visual layer)           |
|Phase 3|Content validation (smarter checks)                       |
|Phase 4|Multiple sites, uptime %, charts, improved UI             |
|Phase 5|Portfolio polish, README screenshots, architecture diagram|

-----

## 19. Out-of-Scope Enhancements (Future Consideration)

- CloudWatch custom metrics and alarms
- API Gateway for real-time dashboard data
- Terraform or AWS SAM for infrastructure-as-code deployment
- Multi-region monitoring for latency comparison
- CSV export of incident history
- Public-facing status page
- DynamoDB TTL policy to automatically expire old check results and control long-term storage growth

-----

## 20. Open Design Decisions

These questions are unresolved for MVP and should be decided before Version 2 work begins:

- Should redirects count as success, or should the redirect itself be a configurable pass/fail rule?
- Should alerts fire on the first failure or only after 2 or more consecutive failures?
- How many recent failures should appear in `status.json` and on the dashboard? (Current default: 5)
- Should multi-site support use one shared DynamoDB table with `site_id` as partition key, or separate tables per site?
- Should Lambda retry once on timeout before marking a check as failed, or is a single attempt sufficient for MVP?

-----

## 21. Build Order

Do not start with the dashboard.

1. Build and test the monitoring engine (Lambda + DynamoDB + SNS)
1. Verify check results are stored correctly and alerts fire on failure
1. Add the S3 dashboard and status.json write
1. Add content validation
1. Polish for portfolio presentation
