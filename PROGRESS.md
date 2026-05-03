# Project Progress

## Completed Phases

- Phase 0: Repository setup
- Phase 1: Monitoring Engine
- Phase 2: S3 Dashboard

## Current Phase

- LinkedIn Post 5 cost breakdown preparation

## Current Status

- Phase 1 completed
- Phase 2 completed
- S3 dashboard live
- UP and DOWN dashboard states verified
- Recent Failures now working
- Post 6 screenshots are ready

## Completed Task History

- Phase 0 project setup
- Phase 1 Lambda monitoring engine code implemented
- Local test run completed
- Added Phase 1 AWS setup guide to README.
- Connected local project to GitHub and pushed main branch.
- Created DynamoDB table website_checks for Phase 1.
- Created SNS topic uptime-alerts and confirmed email subscription.
- Created IAM role uptime-monitor-lambda-role with Phase 1 permissions.
- Manually invoked Lambda with a working URL and confirmed DynamoDB result was written.
- Manually invoked Lambda with a failure URL and confirmed failure detection, DynamoDB write, and SNS alert email.
- Manually invoked Lambda with a temporary low response threshold and confirmed slow-response failure detection.
- Created EventBridge schedule uptime-check-every-5-min and confirmed automatic Lambda execution.
- Completed Phase 1 monitoring engine validation and automatic EventBridge schedule.
- Added Phase 2 S3 dashboard setup guide to README.
- Built Phase 2 static dashboard files.
- Created S3 dashboard bucket, uploaded dashboard files, enabled status.json write, and confirmed dashboard loads.
- Tested dashboard UP and DOWN states successfully.
- Verified Recent Failures dashboard fix and confirmed Post 6 screenshots are ready.

## Process Notes / Problems Solved

### Phase 0 project setup

- Task name: Phase 0 project setup
- What was done: Created initial repository files and folder structure; created `README.md`, `PRD.md`, `TASKS.md`; created `lambda/`, `dashboard/`, and `docs/` starter files; documented AWS region as `ap-northeast-1`.
- Problem faced: Needed to understand where `PRD.md` and `TASKS.md` should be stored.
- How it was solved, step by step: Checked `TASKS.md` folder structure; confirmed `PRD.md` and `TASKS.md` belong in project root; created project structure based on `TASKS.md`.
- Final result: Phase 0 completed.

### Phase 1 Lambda monitoring engine

- Task name: Phase 1 Lambda monitoring engine
- What was done: Implemented Lambda health-check logic in `lambda/app.py`; added environment variable config; added urllib HTTP check; added response time measurement; added failure handling; added DynamoDB write; added optional S3 `status.json` write; added SNS alert on failure; added simple tests.
- Problem faced: Needed to build only monitoring engine first and avoid dashboard work.
- How it was solved, step by step: Followed PRD/TASKS build order; kept dashboard work out of this task; implemented only Phase 1 Lambda logic.
- Final result: Phase 1 Lambda engine code implemented.

### Local test run

- Task name: Local test run
- What was done: Tried running `python -m pytest lambda/tests`.
- Problem faced: Error: `No module named pytest`.
- How it was solved, step by step: Installed pytest using pip; re-ran `python -m pytest lambda/tests`.
- Final result: 5 tests passed.

### Phase 1 AWS setup guide

- Task name: Added Phase 1 AWS setup guide to README
- What was done: Added beginner-friendly manual AWS setup instructions to `README.md`.
- Problem faced: Needed a clear setup order before creating AWS resources.
- How it was solved, step by step: Used `TASKS.md` as the source of truth; documented the Phase 1 setup order in `README.md`; included resource names, environment variables, schedule, and validation checks.
- Final result: Ready to create AWS resources manually.

### GitHub repository setup and first push

- Task name: GitHub repository setup and first push
- What was done: Created the GitHub repository, fixed the remote URL, and pushed the local project to `main`.
- Problem faced: The remote was first set to the placeholder `YOUR_USERNAME` URL, causing repository not found.
- How it was solved, step by step: Created the real GitHub repo; replaced the wrong `origin` URL with `https://github.com/amanrai00/website-uptime-monitor`; renamed branch to `main`; pushed with `git push -u origin main`.
- Final result: Project files are now stored on GitHub at `https://github.com/amanrai00/website-uptime-monitor`, with local project pushed successfully to `origin/main`.

### Phase 1 DynamoDB table setup

- Task name: Phase 1 DynamoDB table setup
- What was done: Created the `website_checks` table in `ap-northeast-1`.
- Problem faced: Needed the correct key structure before Lambda can store monitoring results.
- How it was solved, step by step: Used the `TASKS.md` DynamoDB data model; created `site_id` as the partition key; created `check_time` as the sort key; used on-demand billing to keep setup simple and cost-friendly.
- Final result: DynamoDB table is ready for Lambda result storage. Table status is Active.

### Phase 1 SNS alert setup

- Task name: Phase 1 SNS alert setup
- What was done: Created SNS topic `uptime-alerts` in `ap-northeast-1` and subscribed an email address.
- Problem faced: Lambda needs an alert destination before failure notifications can work.
- How it was solved, step by step: Created a Standard SNS topic named `uptime-alerts`; added an email subscription; confirmed the subscription from the AWS confirmation email; saved the topic ARN for the Lambda `SNS_TOPIC_ARN` environment variable.
- Final result: SNS email alert destination is ready for Lambda failure alerts. Subscription protocol: Email. Subscription status: Confirmed. Topic ARN: arn:aws:sns:ap-northeast-1:688331456662:uptime-alerts.

### Phase 1 IAM role setup

- Task name: Phase 1 IAM role setup
- What was done: Created the Lambda execution role `uptime-monitor-lambda-role` in `ap-northeast-1` and added inline policy `uptime-monitor-lambda-policy`.
- Problem faced: Lambda needed permission to write DynamoDB results, publish SNS alerts, write logs, and later write `status.json` to S3.
- How it was solved, step by step: Created a Lambda trusted IAM role; added `dynamodb:PutItem` permission for `website_checks`; added `sns:Publish` permission for `uptime-alerts`; added placeholder `s3:PutObject` permission for Phase 2 `status.json`; added CloudWatch Logs permissions for Lambda execution logs.
- Final result: IAM role is ready to attach to the Lambda function.

### Phase 1 Lambda success test

- Task name: Phase 1 Lambda success test
- What was done: Ran `successTest` on Lambda function `website-uptime-check` with `TARGET_URL` set to `https://example.com` and checked the DynamoDB item.
- Problem faced: `S3_BUCKET not configured, skipping dashboard write` appeared in logs, AWS console used Python 3.14 instead of planned Python 3.12, and DynamoDB overview item count initially looked like 0.
- How it was solved, step by step: Confirmed Lambda execution succeeded; confirmed the check returned status code 200; confirmed `is_success` was true and `failure_reason` was null; confirmed the `S3_BUCKET` warning is expected because Phase 2 dashboard is not configured yet; continued with Python 3.14 because x86_64 and handler settings are correct and the code uses compatible standard Python libraries; opened DynamoDB Explore items instead of relying on the overview item count; confirmed the monitoring result item was written to `website_checks`.
- Final result: Lambda success path works and stores monitoring data in DynamoDB. Item: `site_id=my-portfolio`, `check_time=2026-04-29T11:49:56.572513Z`, `url=https://example.com`, `status_code=200`, `response_time_ms=423`, `is_success=true`.

### Phase 1 Lambda failure alert test

- Task name: Phase 1 Lambda failure alert test
- What was done: Changed `TARGET_URL` to `https://httpstat.us/500` and ran Lambda function `website-uptime-check` manually using reused test event `successTest`.
- Problem faced: The URL did not return a clean HTTP 500. It returned a `RemoteDisconnected` network-level failure instead.
- How it was solved, step by step: Confirmed the Lambda execution itself succeeded; confirmed the website check was marked as failed; confirmed `failure_reason` captured the network-level error; confirmed the failed result was written to DynamoDB; confirmed SNS alert email was received; treated this as a valid failure test because network-level failures are part of the MVP failure rules.
- Final result: Failure detection and SNS alerting work. Result: `status_code=null`, `response_time_ms=1639`, `is_success=false`, `failure_reason=RemoteDisconnected: Remote end closed connection without response`. The `S3_BUCKET not configured, skipping dashboard write` warning is expected until Phase 2.

### Phase 1 Lambda slow-response test

- Task name: Phase 1 Lambda slow-response test
- What was done: Tested slow-response failure logic using `https://example.com` with `RESPONSE_THRESHOLD_MS` temporarily set to `1`.
- Problem faced: The first slow URL test did not prove slow-response failure because `httpstat.us` disconnected and returned a network-level error. A second mistake also created an `InvalidURL` result because `RESPONSE_THRESHOLD_MS` was accidentally typed into `TARGET_URL`.
- How it was solved, step by step: Changed `TARGET_URL` back to `https://example.com`; temporarily lowered `RESPONSE_THRESHOLD_MS` to `1`; fixed the environment variables so `TARGET_URL` and `RESPONSE_THRESHOLD_MS` were separate rows; ran the Lambda test event again; confirmed the website returned HTTP 200; confirmed `response_time_ms` was 410; confirmed Lambda marked the check as failed only because response time exceeded the threshold; confirmed SNS alert email was received; confirmed DynamoDB stored the failed slow-response result; restored `RESPONSE_THRESHOLD_MS` back to `3000`.
- Final result: Slow-response failure detection works. Test result: `status_code=200`, `response_time_ms=410`, `failure_reason=Slow response: 410ms exceeds 1ms threshold`. DynamoDB item count after tests: 5 items. The `S3_BUCKET not configured, skipping dashboard write` warning is expected until Phase 2. Environment restored: `TARGET_URL=https://example.com`, `RESPONSE_THRESHOLD_MS=3000`, `TIMEOUT_SECONDS=10`.

### Phase 1 EventBridge schedule setup

- Task name: Phase 1 EventBridge schedule setup
- What was done: Created an EventBridge trigger in `ap-northeast-1` to invoke `website-uptime-check` every 5 minutes.
- Problem faced: The EventBridge Rules page showed event-pattern setup instead of a simple schedule option, and early scheduled runs still failed because the slow-response threshold test setting had not been cleanly confirmed.
- How it was solved, step by step: Used the Lambda Add trigger flow; selected EventBridge (CloudWatch Events); created rule `uptime-check-every-5-min`; set schedule expression to `rate(5 minutes)`; confirmed the rule state is ENABLED; confirmed Lambda env vars were restored to `TARGET_URL=https://example.com`, `RESPONSE_THRESHOLD_MS=3000`, and `TIMEOUT_SECONDS=10`; ran a manual Lambda test and confirmed success; waited for scheduled runs; confirmed new successful results were written to DynamoDB automatically.
- Final result: Phase 1 monitoring engine now runs automatically every 5 minutes. Event bus: `default`. Manual restore test returned `status_code=200`, `response_time_ms=28`, `is_success=true`, `failure_reason=null`. Automatic DynamoDB results were confirmed at `2026-04-29T13:55:45...`, `2026-04-29T13:59:07...`, and `2026-04-29T14:00:44...`, all successful. Latest visible automatic result had `response_time_ms=27`, `is_success=true`, and empty/null `failure_reason`. SNS alert was not sent for healthy runs. The `S3_BUCKET not configured, skipping dashboard write` warning is expected until Phase 2.

### Phase 1 completion review

- Task name: Phase 1 completion review
- What was done: Reviewed completed Phase 1 AWS resources and validation results.
- Problem faced: Needed to confirm Phase 1 was truly complete before starting dashboard work.
- How it was solved:
  1. Confirmed Lambda success test wrote to DynamoDB.
  2. Confirmed failure test triggered SNS alert and wrote failed item.
  3. Confirmed slow-response test triggered SNS alert and wrote failed item.
  4. Confirmed EventBridge rule is enabled with rate(5 minutes).
  5. Confirmed automatic scheduled runs are writing successful results to DynamoDB.
- Final result: Phase 1 is complete and the project is ready for Phase 2.

### Phase 2 S3 dashboard setup guide

- Task name: Phase 2 S3 dashboard setup guide
- What was done: Added setup guide for S3 static hosting and Lambda status.json write.
- Problem faced: Needed a clear order before creating the S3 dashboard resources.
- How it was solved: Documented the manual S3 setup flow in README based on PRD.md and TASKS.md.
- Final result: Ready to create S3 dashboard resources manually.

### Phase 2 static dashboard build

- Task name: Phase 2 static dashboard build
- What was done: Created static dashboard files that read status.json from S3.
- Problem faced: Needed a simple dashboard that works without API Gateway or a backend server.
- How it was solved: Used static HTML, CSS, and JavaScript with fetch('status.json?t=' + Date.now()).
- Final result: Dashboard files are ready to upload to S3.

### Phase 2 S3 dashboard setup and verification

- Task name: Phase 2 S3 dashboard setup and verification
- What was done: Created S3 dashboard bucket, enabled static hosting, uploaded dashboard files, updated bucket policy, updated Lambda IAM permission, added S3_BUCKET, ran Lambda, confirmed status.json, and opened dashboard.
- Problem faced: Bucket policy could not be saved at first because Block Public Access was still enabled.
- How it was solved:
  1. Disabled Block Public Access for this dashboard bucket.
  2. Added a bucket policy limited to index.html, style.css, app.js, and status.json.
  3. Replaced placeholder S3 IAM resource with arn:aws:s3:::amanrai00-uptime-dashboard/status.json.
  4. Added S3_BUCKET=amanrai00-uptime-dashboard to Lambda.
  5. Ran Lambda manually.
  6. Confirmed status.json appeared in S3.
  7. Opened the static website endpoint and confirmed dashboard shows UP.
- Final result: Static S3 dashboard is live and reading status.json successfully.

### Phase 2 dashboard UP/DOWN validation

- Task name: Phase 2 dashboard UP/DOWN validation
- What was done: Forced a failure URL, ran Lambda, confirmed dashboard showed DOWN, then restored the working URL and confirmed dashboard returned to UP.
- Problem faced: Needed to confirm the dashboard reflects status.json changes, not only the initial UP state.
- How it was solved:
  1. Temporarily changed TARGET_URL to a broken URL.
  2. Ran Lambda manually.
  3. Confirmed status.json updated.
  4. Refreshed the dashboard and confirmed DOWN state.
  5. Restored TARGET_URL to https://example.com.
  6. Ran Lambda again.
  7. Refreshed the dashboard and confirmed UP state.
- Final result: Dashboard correctly reflects both UP and DOWN states.

### Phase 2 Recent Failures dashboard fix

- Task name: Phase 2 Recent Failures dashboard fix
- What was done: Updated Lambda status payload generation so the S3 dashboard receives recent failed checks from DynamoDB.
- Problem faced: The dashboard showed DOWN, but Recent Failures stayed empty and displayed "No recent failures available."
- How it was solved:
  1. Identified that status.json was writing `recent_failures` as an empty list or not collecting failed checks from DynamoDB.
  2. Kept the existing health check, DynamoDB PutItem, SNS alert, and S3 status.json write flow.
  3. Added a DynamoDB Query on `website_checks` for the current `SITE_ID` using `ScanIndexForward=False`.
  4. Limited the query to the latest 50 records.
  5. Filtered those records in Python for checks where `is_success` is false.
  6. Kept the latest 5 failed checks.
  7. Wrote each failure into `recent_failures` with `check_time`, `status_code`, `response_time_ms`, and `failure_reason`.
  8. Noted that the Lambda role needs `dynamodb:Query` on `website_checks` if that permission is not already added.
- Final result: Lambda now writes recent failed checks into `recent_failures` in status.json so the dashboard can show Recent Failures during DOWN states.
- Next step: Add IAM permission if not already added, deploy/update Lambda, run a failure test, confirm status.json contains `recent_failures`, refresh dashboard, take updated DOWN screenshot, then restore `TARGET_URL` to the healthy URL.

### Recent Failures empty list final fix

- Task name: Recent Failures empty list final fix
- What was done: Updated Lambda recent failure collection so the current failed check is included directly in status.json when the latest run fails.
- Problem faced: status.json updated DOWN correctly with `status_code=404` and `failure_reason=HTTP 404: Not Found`, but `recent_failures` stayed empty.
- How it was solved:
  1. Cause found after debugging: the dashboard status payload depended only on failed records returned from the DynamoDB query, so status.json could still write `recent_failures` as an empty list even when the current check was DOWN.
  2. Kept the current health check logic, DynamoDB PutItem logic, SNS alert logic, S3 status.json write behavior, and environment variable names.
  3. Updated recent failure collection to query DynamoDB for latest records by the same `SITE_ID`.
  4. Filtered queried records where `is_success` is false.
  5. Added the current failed check directly when `is_success` is false and the same `check_time` was not already present.
  6. Removed duplicates by `check_time`.
  7. Sorted failures newest first and kept the latest 5.
  8. Added CloudWatch print logs for query start, DynamoDB records returned, failed records found, whether the current failure was added manually, final recent failure count, and query errors.
- Final result: Current failed checks are now written into `recent_failures` immediately, DynamoDB query fills older failures, duplicates are removed, and the latest 5 failures are written to status.json.
- Next step: Deploy Lambda, run failure test, confirm `recent_failures` has at least 1 item, refresh dashboard, take updated DOWN screenshot, restore `TARGET_URL` to healthy URL.

### Recent Failures dashboard fix verification

- Task name: Recent Failures dashboard fix verification
- What was done: Uploaded the updated Lambda ZIP from VS Code to AWS Lambda, ran the failure test again, confirmed status.json now contains `recent_failures`, refreshed the dashboard, confirmed Recent Failures appears on the DOWN dashboard, restored `TARGET_URL` back to `https://example.com`, ran Lambda again, and confirmed the dashboard returned to UP.
- Problem faced: The dashboard showed DOWN correctly, but Recent Failures was empty because status.json had `"recent_failures": []`.
- How it was solved:
  1. Updated `lambda/app.py` so the current failed check is included directly in `recent_failures`.
  2. Kept DynamoDB Query for older failures.
  3. Added dedupe by `check_time`.
  4. Kept latest 5 failures.
  5. Added `dynamodb:Query` permission to the Lambda IAM policy.
  6. Created `lambda-deploy.zip` from VS Code.
  7. Uploaded the ZIP to AWS Lambda.
  8. Ran a failure test with `https://example.com/not-found-test`.
  9. Confirmed status.json contains 5 `recent_failures`.
  10. Refreshed the dashboard and confirmed Recent Failures displays correctly.
  11. Restored `TARGET_URL` to `https://example.com`.
  12. Ran Lambda again and confirmed UP state.
- Final result: Recent Failures is now fully working. The dashboard correctly shows UP, DOWN, failure reason, and recent failure history. Both Post 6 screenshots are ready.
- Next step: Prepare LinkedIn Post 5 cost breakdown first, then use the UP and DOWN screenshots for Post 6 dashboard live.

### Phase 3 Lambda content validation implementation

- Task name: Phase 3 Lambda content validation implementation
- What was done: Updated `lambda/app.py`; added optional `EXPECTED_TEXT` and `FORBIDDEN_TEXT`; safely decodes HTTP response body; fails when expected text is missing; fails when forbidden text is found; adds `content_check_passed` to DynamoDB result and `status.json`.
- Problem faced: Phase 3 needed smarter monitoring beyond HTTP status and response time.
- How it was solved:
  1. Read optional content validation environment variables.
  2. Decoded response body safely.
  3. Applied expected-text and forbidden-text rules.
  4. Reused existing `failure_reason` flow.
  5. Added `content_check_passed` to stored result and dashboard payload.
  6. Kept existing DynamoDB, SNS, S3, and recent failures logic unchanged.
- Final result: Lambda code now supports Phase 3 content validation, but AWS deployment and validation are still pending.
- Next step: Deploy updated Lambda, set `EXPECTED_TEXT` / `FORBIDDEN_TEXT` test values, run content validation tests, confirm DynamoDB and `status.json` include `content_check_passed`, then update dashboard UI to display content check result.

## Ongoing Rule

After every future project task, update `PROGRESS.md` with task completed, problems faced, solution steps, final result, and next step.

## Next Step

- Deploy updated Lambda.
- Set `EXPECTED_TEXT` / `FORBIDDEN_TEXT` test values.
- Run content validation tests.
- Confirm DynamoDB and `status.json` include `content_check_passed`.
- Then update dashboard UI to display content check result.
