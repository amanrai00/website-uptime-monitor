# Website Uptime Monitor

Website Uptime Monitor is a serverless AWS project for checking whether a website is reachable, responding within a threshold, and eventually showing expected content. It stores check results, sends alerts on failures, and publishes current status to a static dashboard.

## AWS Region

This project uses `ap-northeast-1`.

## Folder Structure

```text
website-uptime-monitor/
|-- README.md
|-- PRD.md
|-- TASKS.md
|-- .gitignore
|-- lambda/
|   |-- app.py
|   |-- requirements.txt
|   `-- tests/
|       `-- test_app.py
|-- dashboard/
|   |-- index.html
|   |-- style.css
|   `-- app.js
`-- docs/
    |-- architecture.png
    `-- screenshots/
```

## Build Order

1. Build the monitoring engine with Lambda, DynamoDB, SNS, and EventBridge.
2. Verify check results are stored and alerts fire on failures.
3. Add the S3 dashboard and `status.json` update flow.
4. Add content validation.
5. Polish documentation, screenshots, and architecture assets for portfolio presentation.

## Phase 1 AWS Setup

Use AWS region `ap-northeast-1` for all Phase 1 resources.

### 1. Create DynamoDB table

- Table name: `website_checks`
- Partition key: `site_id` as String
- Sort key: `check_time` as String
- Billing mode: On-demand
- Wait until the table status is Active before moving on.

### 2. Create SNS topic and confirm email subscription

- Topic name: `uptime-alerts`
- Add an email subscription.
- Open the confirmation email from AWS and confirm the subscription.
- Save the SNS topic ARN for `SNS_TOPIC_ARN`.

### 3. Create IAM role and least-privilege policy

- Role name: `uptime-monitor-lambda-role`
- Trusted service: Lambda
- Add only the permissions needed for Phase 1:
  - `dynamodb:PutItem` for the `website_checks` table
  - `sns:Publish` for the `uptime-alerts` topic
  - CloudWatch Logs permissions for Lambda logs
  - `s3:PutObject` for the future dashboard `status.json` object only
- Do not use broad `*` actions or broad `*` resources.

### 4. Create Lambda function

- Function name: `website-uptime-check`
- Runtime: Python 3.12
- Architecture: x86_64
- Execution role: `uptime-monitor-lambda-role`
- Timeout: 30 seconds
- Memory: 128 MB

Upload or paste the code from `lambda/app.py`.

### 5. Configure Lambda environment variables

Set these environment variables on `website-uptime-check`:

|Variable|Value|
|---|---|
|`TARGET_URL`|Full website URL to monitor, such as `https://example.com`|
|`TIMEOUT_SECONDS`|`10`|
|`RESPONSE_THRESHOLD_MS`|`3000`|
|`SNS_TOPIC_ARN`|ARN for `uptime-alerts`|
|`DYNAMODB_TABLE`|`website_checks`|
|`SITE_ID`|Short site name, such as `my-portfolio`|
|`S3_BUCKET`|Optional until Phase 2|
|`S3_STATUS_KEY`|`status.json`|

`S3_BUCKET` can stay empty until the Phase 2 dashboard bucket exists. `S3_STATUS_KEY` can be `status.json`.

### 6. Create EventBridge schedule

- Rule name: `uptime-check-every-5-min`
- Schedule expression: `rate(5 minutes)`
- Target: Lambda function `website-uptime-check`
- Allow EventBridge to invoke the Lambda function when prompted.

### 7. Run manual validation checks

Run these checks from the Lambda test page before relying on the schedule:

- Test with a working URL and confirm a successful result is written to DynamoDB.
- Test with an HTTP failure URL, such as `https://httpstat.us/500`, and confirm the result is failed and an SNS email is sent.
- Test with a slow-response URL, such as `https://httpstat.us/200?sleep=5000`, and confirm the result fails when response time exceeds `RESPONSE_THRESHOLD_MS`.
