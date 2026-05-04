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

## Architecture

![Architecture](docs/architecture.png)

EventBridge runs every 5 minutes. Lambda checks the target website and validates HTTP status, response time, expected text, and forbidden text. Results are stored in DynamoDB, and the latest status is written to S3 `status.json`. The static S3 dashboard reads `status.json`. SNS sends an email alert only when the check fails.

## Cost Breakdown

This project is designed to stay very low cost for a small personal monitoring workload.

Estimated monthly usage:

- EventBridge schedule: runs every 5 minutes
- Lambda executions: about 8,640 checks per month
- DynamoDB: one small item written per check, plus small reads for recent failures
- S3: one small `status.json` file plus static dashboard files
- SNS: email alerts only when failures happen

Expected cost for this project:

- Usually $0 or very close to $0 for personal/demo usage
- Main reason: monthly usage is far below typical AWS Free Tier limits for Lambda and EventBridge Scheduler
- DynamoDB and S3 data size are very small
- SNS email alerts are only sent during failures

Cost control choices:

- Serverless design, no always-running EC2 instance
- S3 static dashboard instead of a hosted frontend server
- DynamoDB on-demand table for small and unpredictable usage
- Lambda runs only on schedule, not continuously
- `status.json` is tiny and overwritten each check
- Recent failures are limited to the latest 5 items

Cost notes:

- Actual billing depends on AWS region, account Free Tier eligibility, request volume, stored data size, and alert volume.
- For production use, AWS Budgets and billing alarms should be configured.
- Pricing should always be checked against the official AWS pricing pages.

## Known Limitations

- The monitor currently checks one target website.
- Alerts currently depend on Lambda execution. If Lambda/EventBridge stops running, a separate CloudWatch alarm would be needed.
- The dashboard is not real-time. It reflects the latest `status.json` written by Lambda.
- SNS alerts are sent on failure events, so repeated failures may create repeated emails.
- No authentication is added to the public S3 dashboard because this is a portfolio/demo project.
- Historical analytics are limited. Uptime percentage, trend charts, and incident counts are future improvements.
- The dashboard uses a static `status.json` file instead of an API backend to keep the project simple and low cost.

## Lessons Learned

- Serverless Lambda is a good fit for scheduled uptime monitoring because it runs only when checks are needed and does not require maintaining an always-on server.
- DynamoDB works well for append-only check history because each monitor run can write a small timestamped item with predictable access patterns.
- S3 `status.json` is enough for a simple low-cost dashboard because the dashboard only needs the latest published monitor state.
- EventBridge can replace a traditional cron job by running Lambda on a managed schedule.
- IAM least-privilege matters for portfolio projects because it shows that the system grants only the permissions each service needs.
- SNS provides simple failure notification without building or operating a custom email system.
- HTTP 200 is not always enough for monitoring. Content validation adds stronger monitoring by checking expected and forbidden page text.
- Dashboard freshness should be visible with `last_checked` time so viewers know when the latest check ran.
- Debugging `recent_failures` and `status.json` updates showed the importance of keeping stored history and the published dashboard state in sync.

## Future Improvements

- Monitor multiple websites using separate `site_id` values.
- Add uptime percentage per site.
- Add average response time metric.
- Add incident count for the last 24 hours and last 7 days.
- Add consecutive-failure alert threshold to reduce email noise.
- Add configurable redirect handling.
- Add response time trend chart on the dashboard.
- Improve dashboard UI for multiple sites.
- Add DynamoDB TTL to automatically expire old check records.
- Add CloudWatch alarm if Lambda/EventBridge stops running.

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

## Phase 2 S3 Dashboard Setup

Use AWS region `ap-northeast-1` for all Phase 2 dashboard resources.

Phase 1 intentionally skipped `S3_BUCKET` because the dashboard bucket did not exist yet. In Phase 2, create the S3 bucket first, then add `S3_BUCKET` to the Lambda configuration so Lambda can write `status.json`.

### 1. Create S3 bucket

- Open the AWS Console.
- Go to S3.
- Choose Create bucket.
- Bucket name: `aman-uptime-dashboard`
- If that name is unavailable, use a globally unique variation, such as `aman-uptime-dashboard-<short-random-suffix>`.
- AWS Region: `ap-northeast-1`
- Keep default settings for now unless a later step says to change them.
- Create the bucket.

### 2. Enable static website hosting

- Open the new bucket.
- Go to Properties.
- Find Static website hosting.
- Choose Edit.
- Enable static website hosting.
- Hosting type: Host a static website.
- Index document: `index.html`
- Save changes.
- Copy the bucket website endpoint. You will use it to open the dashboard later.

### 3. Upload dashboard files

- Open the bucket.
- Go to Objects.
- Upload these files from the local `dashboard/` folder:
  - `index.html`
  - `style.css`
  - `app.js`
- Do not upload unrelated files.

### 4. Configure public read access for required dashboard files only

The dashboard must be publicly readable, but only for the required static files and `status.json`.

- Open the bucket.
- Go to Permissions.
- Edit Block public access settings.
- Disable public access blocking only as needed for this static website bucket.
- Save changes and confirm.
- Add a bucket policy that allows public `s3:GetObject` only for:
  - `index.html`
  - `style.css`
  - `app.js`
  - `status.json`

Use your real bucket name in the resource ARNs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadDashboardFilesOnly",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": [
        "arn:aws:s3:::aman-uptime-dashboard/index.html",
        "arn:aws:s3:::aman-uptime-dashboard/style.css",
        "arn:aws:s3:::aman-uptime-dashboard/app.js",
        "arn:aws:s3:::aman-uptime-dashboard/status.json"
      ]
    }
  ]
}
```

If you used a different bucket name, replace `aman-uptime-dashboard` in all four ARNs.

### 5. Update Lambda IAM role S3 permission

In Phase 1, the Lambda role used a placeholder S3 ARN for the future dashboard bucket. Replace that placeholder with the real bucket ARN for `status.json`.

- Go to IAM.
- Open role `uptime-monitor-lambda-role`.
- Open the inline policy for the Lambda permissions.
- Find the `s3:PutObject` statement.
- Replace the placeholder resource with:

```text
arn:aws:s3:::aman-uptime-dashboard/status.json
```

If you used a different bucket name, replace `aman-uptime-dashboard` with your real bucket name.

Keep this permission limited to `status.json` only. Do not grant write access to the whole bucket.

### 6. Add S3_BUCKET environment variable to Lambda

- Go to Lambda.
- Open function `website-uptime-check`.
- Go to Configuration.
- Go to Environment variables.
- Add or update:

|Variable|Value|
|---|---|
|`S3_BUCKET`|`aman-uptime-dashboard`|
|`S3_STATUS_KEY`|`status.json`|

If you used a different bucket name, use that value for `S3_BUCKET`.

### 7. Manually invoke Lambda and confirm status.json is written

- Open the Lambda function `website-uptime-check`.
- Use the existing manual test event.
- Invoke the function.
- Confirm the run succeeds.
- Open the S3 bucket.
- Confirm `status.json` exists in the bucket root.
- Open `status.json` and confirm it contains the latest site status data.

### 8. Open S3 website URL and confirm dashboard loads

- Open the S3 static website endpoint copied from the bucket Properties page.
- Confirm the dashboard page loads.
- Confirm it can read `status.json`.
- Confirm it shows the latest status from the Lambda run.
