# TASKS.md

## Website Uptime Monitor — Build Checklist

## Aligned to PRD v1.0 | Last Updated: April 2026

-----

## Phase 0 — Repository Setup

- [x] Create GitHub repository: `website-uptime-monitor`
- [x] Add `.gitignore` (Python + Node)
- [x] Add `README.md`
- [x] Add `PRD.md`
- [x] Add `TASKS.md`
- [x] Decide AWS region and document it in README (recommended: `ap-northeast-1`)
- [x] Create folder structure:

```
website-uptime-monitor/
├── README.md
├── PRD.md
├── TASKS.md
├── .gitignore
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

## Phase 1 — Monitoring Engine

> PRD reference: Section 9.1, 9.2, 9.3, 9.4, Section 11, Section 16

### 1.1 IAM Role and Policy

- [x] Create IAM role: `uptime-monitor-lambda-role`
- [x] Attach inline policy with least-privilege permissions only:
  - [x] `dynamodb:PutItem` on `website_checks` table ARN only
  - [x] `sns:Publish` on `uptime-alerts` topic ARN only
  - [x] `s3:PutObject` on dashboard bucket ARN, key `status.json` only — use a placeholder ARN now (`arn:aws:s3:::PLACEHOLDER_BUCKET_NAME/status.json`); update to the real bucket ARN in Phase 2.1 once the bucket is created
  - [x] `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` for CloudWatch
- [ ] Verify no broader permissions are attached (no `*` actions, no `*` resources)

### 1.2 DynamoDB Table

- [x] Create table: `website_checks`
  - Partition key: `site_id` (String)
  - Sort key: `check_time` (String, ISO 8601)
  - Billing mode: On-demand
- [x] Confirm table is active before proceeding
- [ ] Note: `content_check_passed` and `expected_text` fields are reserved for Phase 3; no schema change needed now (DynamoDB is schemaless)

### 1.3 SNS Topic

- [x] Create SNS topic: `uptime-alerts`
- [x] Subscribe your email address to the topic
- [x] Confirm the subscription by clicking the link in the confirmation email
- [x] Note the topic ARN; you will need it as an environment variable

### 1.4 Lambda Function

- [x] Create Lambda function: `website-uptime-check`
  - Runtime: Python 3.12
  - Architecture: x86_64
  - Execution role: `uptime-monitor-lambda-role`
  - Timeout: 30 seconds
  - Memory: 128 MB
- [ ] Write `lambda/app.py` with the following logic:

  **HTTP check (PRD 9.2):**
  - [ ] Send HTTP GET to `TARGET_URL` using `urllib.request` (no extra packages needed)
  - [ ] Record `response_time_ms` as total request duration from start to response received using `time.time()` before and after the request
  - [ ] Capture HTTP status code from response
  - [ ] Read response body (needed for content validation in Phase 3; decode safely with `errors="replace"`)

  **Redirect behaviour (PRD 9.2):**
  - [ ] Confirm `urllib` follows redirects automatically by default
  - [ ] Evaluate the final resolved status code, not the redirect code
  - [ ] Document this behaviour in a code comment

  **Exception handling (PRD 9.2, 14):**
  - [ ] Catch `urllib.error.HTTPError` and record status code and reason
  - [ ] Catch `urllib.error.URLError` and record reason as failure
  - [ ] Catch `socket.timeout` and record as timeout failure
  - [ ] Catch generic `Exception` as fallback with type and message

  **Failure rules (PRD 14):**
  - [ ] Fail if any exception was raised
  - [ ] Fail if status code is outside 200-299
  - [ ] Fail if `response_time_ms` exceeds `RESPONSE_THRESHOLD_MS`
  - [ ] Set `failure_reason` to null if all checks pass; set `is_success = True`

  **DynamoDB write (PRD 9.4):**
  - [ ] Build result dict with all required fields: `site_id`, `check_time`, `url`, `status_code`, `response_time_ms`, `is_success`, `failure_reason`
  - [ ] Write to DynamoDB using `boto3`; skip null values to keep items clean

  **S3 write (PRD 7, 9.5, 13):**
  - [ ] Build `status.json` payload with: `site_id`, `url`, `last_checked`, `status` (UP/DOWN), `status_code`, `response_time_ms`, `is_success`, `failure_reason`, `recent_failures`
  - [ ] For the first MVP version, `recent_failures` can be written as an empty list initially, then expanded to include up to the latest 5 failed checks queried from DynamoDB
  - [ ] Write to S3 with `ContentType: application/json` and `CacheControl: no-cache`
  - [ ] Guard the S3 write with `if os.environ.get("S3_BUCKET"):` — if the variable is not set, skip the write, log a warning (`"S3_BUCKET not configured, skipping dashboard write"`), and continue without raising an exception; the Lambda run must still complete and store the DynamoDB result normally

  **SNS alert (PRD 9.3):**
  - [ ] Publish SNS alert only when `is_success` is False
  - [ ] Alert message must include: site URL, failure reason, status code (or N/A), response time, and timestamp
  - [ ] Alert subject must clearly identify the site and DOWN status
  - [ ] Note in code comments: MVP alerts on every failure; consecutive-failure threshold is a Version 2 improvement
- [ ] Write `lambda/requirements.txt`
  - `boto3` is pre-installed on Lambda; include it for local development only
  - No third-party HTTP libraries needed

### 1.5 Environment Variables

Set all of the following on the Lambda function configuration:

- [x] `TARGET_URL` — full URL to monitor, e.g. `https://example.com`
- [x] `TIMEOUT_SECONDS` — default `10`
- [x] `RESPONSE_THRESHOLD_MS` — default `3000`
- [x] `SNS_TOPIC_ARN` — ARN from step 1.3
- [x] `DYNAMODB_TABLE` — default `website_checks`
- [x] `S3_BUCKET` — optional until Phase 2; set after the dashboard bucket is created
- [x] `S3_STATUS_KEY` — default `status.json`
- [x] `SITE_ID` — short identifier for the site, e.g. `my-portfolio`

### 1.6 EventBridge Schedule

- [x] Create EventBridge rule: `uptime-check-every-5-min`
  - Schedule expression: `rate(5 minutes)`
  - Target: `website-uptime-check` Lambda function
- [x] Add resource-based policy allowing EventBridge to invoke the Lambda function
- [ ] Note: To change the schedule, update this EventBridge rule in AWS. It is not controlled by an environment variable.

### 1.7 Phase 1 Validation

Run each test in order. Do not proceed to Phase 2 until all pass.

- [x] Manually invoke Lambda with a test event using a working URL
  - [x] Confirm result written to DynamoDB with correct fields
  - If the S3 bucket has already been created, confirm `status.json` is written successfully (check S3 console)
  - [x] Confirm no SNS alert sent (check email)
  - [x] Confirm CloudWatch log shows structured pass result
- [x] Manually invoke Lambda with a broken URL (e.g. `https://httpstat.us/500`)
  - [x] Confirm result written to DynamoDB with `is_success: false`
  - If the S3 bucket has already been created, confirm `status.json` shows `status: DOWN`
  - [x] Confirm SNS alert email received with correct failure details
  - [x] Confirm CloudWatch log shows structured fail result
- [x] Manually invoke Lambda with a slow-response URL (e.g. `https://httpstat.us/200?sleep=5000`)
  - [x] Confirm `response_time_ms` exceeds threshold
  - [x] Confirm check is marked as failed with slow response reason
- [x] Wait for one scheduled EventBridge run (up to 5 minutes) and confirm it fires automatically
  - [x] Check CloudWatch logs for execution triggered by EventBridge (not manual)

-----

## Phase 2 — S3 Dashboard

> PRD reference: Section 7, 9.5, 13

### 2.1 S3 Bucket Setup

- [x] Create S3 bucket: `amanrai00-uptime-dashboard`
- [x] Enable static website hosting on the bucket
  - Index document: `index.html`
- [x] Set bucket policy: public `s3:GetObject` for the dashboard assets required for static hosting (`index.html`, `style.css`, `app.js`, `status.json`)
- [x] Disable “Block all public access” only to the extent required for static hosting
- [x] **Update the IAM role policy** (`uptime-monitor-lambda-role`) — replace the placeholder bucket ARN set in Phase 1.1 with the real ARN: `arn:aws:s3:::amanrai00-uptime-dashboard/status.json`. Verify the policy still grants `s3:PutObject` on that specific key only and nothing broader.
- [x] Update Lambda environment variable `S3_BUCKET` with the bucket name
- [x] Confirm Lambda can write `status.json` (run a manual test invoke after updating the env var)

### 2.2 Dashboard Build

- [x] Create `dashboard/index.html` with:
  - [x] `fetch('status.json?t=' + Date.now())` on page load to prevent browser caching
  - [x] Display status badge: green UP or red DOWN based on `is_success`
  - [x] Display last checked time in human-readable local format
  - [x] Display latest HTTP status code
  - [x] Display latest `response_time_ms` with colour coding (green under 800ms, amber under 2000ms, red above)
  - [x] Display `failure_reason` block if status is DOWN
  - [x] Display `recent_failures` list (up to 5 entries per PRD 13, each with timestamp, status code, response time, reason)
  - [x] Auto-refresh every 60 seconds via `setInterval`
  - [x] Show a clear error state if `status.json` fails to load
  - [x] Show last-checked time prominently so dashboard staleness is always visible (PRD 9.5)
- [x] Create `dashboard/style.css` — clean, minimal, professional styling

### 2.3 Phase 2 Validation

- [x] Open the S3 static website URL in a browser
- [x] Confirm dashboard loads and shows correct UP status
- [x] Force a failure by temporarily setting `TARGET_URL` to a broken URL, wait one cycle, confirm dashboard shows DOWN
  - [x] Confirm forced failure updates `status.json`
  - [x] Confirm dashboard shows DOWN status with failure reason
  - [x] Restore Lambda `TARGET_URL` to working URL after DOWN test
  - [x] Confirm dashboard returns to UP after restore
- [x] Confirm `recent_failures` list populates after failures occur
- [x] Confirm last-checked time updates after each Lambda execution
- [x] Confirm auto-refresh works after 60 seconds without manual reload

-----

## Phase 3 — Content Validation

> PRD reference: Section 9.6, 14 (Version 3 Addition)

- [x] Add environment variables to Lambda:
  - [x] `EXPECTED_TEXT` — text that must be present in the response body (optional; skip check if empty)
  - [x] `FORBIDDEN_TEXT` — text that must not be present in the response body (optional; skip check if empty)
- [x] Update `app.py` to read response body and apply content rules after status and response time checks pass
- [x] Fail check if `EXPECTED_TEXT` is set and not found in body; set failure reason: `Expected text not found: '<text>'`
- [x] Fail check if `FORBIDDEN_TEXT` is set and found in body; set failure reason: `Forbidden text found: '<text>'`
- [x] Add `content_check_passed` field to DynamoDB result and `status.json`
- [x] Include content failure reason in SNS alert message
- [x] Update dashboard to show content check result (pass / fail / not configured)

### Phase 3 Validation

- [x] Set `EXPECTED_TEXT` to a string present on the page and confirm check passes
- [x] Set `EXPECTED_TEXT` to a string not on the page and confirm check fails with correct reason
- [x] Set `FORBIDDEN_TEXT` to a string on the page and confirm check fails with correct reason
- [x] Confirm `content_check_passed` field appears in DynamoDB
- [x] Confirm SNS alert includes content failure reason

-----

## Phase 4 — Improvements

> PRD reference: Section 6 (Version 2), Section 20 (Open Design Decisions)

Before starting Phase 4, resolve the open design decisions from PRD Section 20:

- [ ] Decide: should redirects count as success or be a configurable rule?
- [ ] Decide: should alerts fire on first failure or after N consecutive failures?
- [ ] Decide: how many recent failures to show (PRD default is 5)?
- [ ] Decide: one shared DynamoDB table with `site_id` as partition key, or separate tables per site?
- [ ] Decide: should Lambda retry once on timeout before marking a check failed?

Then build:

- [ ] Support monitoring multiple websites (list of site configs, each with own `site_id`, `target_url`, thresholds)
- [ ] Calculate and store uptime percentage per site
- [ ] Add average response time metric per site
- [ ] Add incident count per site (last 24h and last 7 days)
- [ ] Add consecutive-failure threshold before alerting (reduce noise)
- [ ] Add configurable redirect handling
- [ ] Add response time trend chart using Chart.js on dashboard
- [ ] Improve dashboard UI for multiple sites
- [ ] Add DynamoDB TTL attribute to expire old records (PRD Section 19)

-----

## Phase 5 — Portfolio Polish

> PRD reference: Section 18 (Phase 5), Section 10 (Non-Functional Requirements)

- [x] Create `docs/architecture.png` — clean architecture diagram matching PRD Section 11
- [x] Add architecture section to README with diagram image
- [x] Add real screenshots to `docs/screenshots/`:
  - [x] Dashboard in UP state
  - [x] Dashboard in DOWN state with failure reason visible
  - [x] DynamoDB table showing stored check results
  - [x] SNS alert email received in inbox
  - [x] CloudWatch logs showing structured Lambda output
- [ ] Write clear setup instructions in README (step-by-step, someone unfamiliar with the project can follow)
- [x] Add cost breakdown section to README (PRD Section 10 — must stay within Free Tier)
- [x] Add known limitations section to README
- [x] Add lessons learned section
- [ ] Add future improvements section referencing Phase 4 items
- [ ] Record a short demo GIF or screen recording of the full flow

-----

## Open Design Decisions Tracker

> From PRD Section 20 — resolve before starting Phase 4

|Decision                                                            |Status        |Resolution       |
|--------------------------------------------------------------------|--------------|-----------------|
|Should redirects count as success in MVP?                           |Open          |                 |
|Should alerts fire on first failure or after N consecutive failures?|Open          |                 |
|How many recent failures on dashboard?                              |Defaulted to 5|Confirm or change|
|One shared DynamoDB table or separate tables per site?              |Open          |                 |
|Should Lambda retry once on timeout before failing?                 |Open          |                 |

-----

## Interview Talking Points — Prepare Before Any Interview

- Why serverless Lambda over a cron job on EC2 for this use case
- Why DynamoDB over RDS for append-only time-series monitoring data
- Why `status.json` on S3 instead of API Gateway for the dashboard (PRD Section 7)
- What the IAM policy allows and why nothing broader was granted (PRD Section 16)
- How `response_time_ms` is measured and what it represents (PRD Section 9.2)
- How redirect handling works in Python `urllib` and what the current behaviour is
- What failure rules are applied and in what order
- What happens if Lambda itself stops executing silently (answer: CloudWatch alarm is a future improvement)
- How the system would extend to multi-region monitoring
- What content validation adds that pure uptime monitoring misses
- What the open design decisions are and how you would resolve each one
