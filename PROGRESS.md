# Project Progress

## Completed Phases

- Phase 0: Repository setup
- Phase 1: Monitoring Engine
- Phase 2: S3 Dashboard
- Phase 4: Improvements

## Current Phase

- Phase 5 final portfolio refresh / README update

## Current Status

- Phase 1 completed
- Phase 2 completed
- S3 dashboard live
- UP and DOWN dashboard states verified
- Recent Failures now working
- Post 6 screenshots are ready
- Phase 4 completed

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
- Completed Phase 4B multi-site AWS validation.
- Completed Phase 4C uptime percentage calculation per site.
- Completed Phase 4C uptime percentage AWS validation.
- Completed Phase 4D average response time metric per site.
- Completed Phase 4D average response time AWS validation.
- Completed Phase 4E incident count per site for last 24h and last 7 days.
- Completed Phase 4E incident count AWS validation.
- Completed Phase 4 final checklist review and completion summary.

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

### Phase 3 Lambda content validation AWS test

- Task name: Phase 3 Lambda content validation AWS test
- What was done: Deployed the updated Lambda code to AWS; added `EXPECTED_TEXT=Example Domain`; ran Lambda against `https://example.com`; confirmed the check passed with `is_success=true`, `failure_reason=null`, and `content_check_passed=true`; changed `EXPECTED_TEXT` to `ThisTextShouldNotExist123`; ran Lambda again; confirmed the content validation failure worked with `status_code=200`, `is_success=false`, `failure_reason=Expected text not found: 'ThisTextShouldNotExist123'`, and `content_check_passed=false`.
- Problem faced: Needed to confirm content validation detects broken/missing content even when the website returns HTTP 200.
- How it was solved:
  1. Restored `TARGET_URL` to `https://example.com`.
  2. Set `EXPECTED_TEXT` to text that exists on the page.
  3. Ran Lambda and confirmed content validation passed.
  4. Changed `EXPECTED_TEXT` to text that does not exist on the page.
  5. Ran Lambda and confirmed the check failed because expected content was missing.
  6. Confirmed the failure reason and `content_check_passed=false` in the Lambda output.
- Final result: Phase 3 Lambda content validation works for expected-text pass and expected-text failure cases. `status.json` verification, healthy restore, forbidden-text test, and dashboard UI update are still pending.
- Next step: Confirm `status.json` includes `content_check_passed`, restore `EXPECTED_TEXT=Example Domain`, run Lambda again and confirm healthy state, test `FORBIDDEN_TEXT`, update dashboard UI to display content check result, and update TASKS.md after validation is fully complete.

### Phase 3 forbidden-text validation test and healthy restore

- Task name: Phase 3 forbidden-text validation test and healthy restore
- What was done: Restored healthy content validation with `TARGET_URL=https://example.com` and `EXPECTED_TEXT=Example Domain`; confirmed Lambda returned `is_success=true`, `failure_reason=null`, and `content_check_passed=true`; tested forbidden-text validation by setting `FORBIDDEN_TEXT=Example Domain`; confirmed Lambda failed correctly with `status_code=200`, `is_success=false`, `failure_reason=Forbidden text found: 'Example Domain'`, and `content_check_passed=false`.
- Problem faced: Needed to confirm the monitor can detect forbidden/bad page content even when the website still returns HTTP 200.
- How it was solved:
  1. Kept `TARGET_URL` as `https://example.com`.
  2. Kept `EXPECTED_TEXT` as `Example Domain`.
  3. Added `FORBIDDEN_TEXT` with text that exists on the page.
  4. Ran Lambda and confirmed the check failed because forbidden content was found.
  5. Restored `FORBIDDEN_TEXT` to empty after the test.
  6. Ran Lambda again to confirm the monitor returned to healthy state.
- Final result: Phase 3 Lambda content validation is working for expected text pass, expected text missing failure, and forbidden text found failure. Dashboard UI still needs to be updated to display `content_check_passed`.
- Next step: Update dashboard UI to display Content Check status, verify dashboard shows Passed, Failed, and Not configured states if possible, update TASKS.md after dashboard validation is complete, then prepare Phase 3 completion summary.

### Phase 3 dashboard content check UI implementation

- Task name: Phase 3 dashboard content check UI implementation
- What was done: Updated `dashboard/index.html`; updated `dashboard/app.js`; added a Content Check display field to the dashboard; dashboard now reads `content_check_passed` from `status.json`; displays Passed when `content_check_passed === true`, Failed when `content_check_passed === false`, and Not configured when `content_check_passed` is null, undefined, or missing.
- Problem faced: The dashboard did not have an existing markup target for displaying Phase 3 content validation results.
- How it was solved:
  1. Checked `dashboard/app.js` first.
  2. Confirmed existing targets existed for status, last checked, HTTP status, response time, failure reason, and recent failures.
  3. Added a minimal Content Check target in `dashboard/index.html`.
  4. Updated `dashboard/app.js` to map `content_check_passed` to Passed, Failed, or Not configured.
  5. Kept existing dashboard behavior unchanged.
- Final result: Dashboard code can now display Phase 3 content validation status. S3 upload and live dashboard verification are still pending.
- Next step: Upload updated `dashboard/index.html` and `dashboard/app.js` to S3, confirm dashboard shows Content Check: Passed with current healthy `status.json`, test Failed state using content validation failure, optionally test Not configured state, and update TASKS.md after dashboard validation is complete.

### Phase 3 dashboard content check live verification

- Task name: Phase 3 dashboard content check live verification
- What was done: Uploaded updated `dashboard/index.html` and `dashboard/app.js` to the S3 dashboard bucket; refreshed the live S3 dashboard; confirmed the new Content Check card appears; confirmed browser cache initially showed `--`; opened the dashboard in incognito mode; confirmed Content Check displays `Passed` from `status.json`.
- Problem faced: The dashboard first showed the new Content Check card but displayed `--` because the browser likely cached the old JavaScript.
- How it was solved:
  1. Uploaded the updated dashboard files to S3.
  2. Opened the live dashboard.
  3. Saw the Content Check card but the value stayed as `--`.
  4. Reopened the dashboard in incognito mode to bypass browser cache.
  5. Confirmed the dashboard correctly displayed `Content Check: Passed`.
- Final result: Live S3 dashboard now displays Phase 3 content validation status correctly. Passed state is verified. Failed and Not configured dashboard states are still optional to verify.
- Next step: Optionally verify dashboard Failed state using content validation failure, optionally verify Not configured state by removing/emptying content validation environment variables, update TASKS.md Phase 3 checklist after validation is complete, and prepare Phase 3 completion summary.

### Phase 3 dashboard failed state verification and healthy restore

- Task name: Phase 3 dashboard failed state verification and healthy restore
- What was done: Tested dashboard Failed state by setting `TARGET_URL=https://example.com`, `EXPECTED_TEXT=ThisTextShouldNotExist123`, and `FORBIDDEN_TEXT` empty; ran Lambda; confirmed live dashboard showed Status: DOWN, Content Check: Failed, Failure reason: `Expected text not found: 'ThisTextShouldNotExist123'`, and Recent Failures updated.
- Problem faced: Needed to verify that Phase 3 content validation failure is visible on the live dashboard, not only in Lambda output and status.json.
- How it was solved:
  1. Set `EXPECTED_TEXT` to a value missing from the page.
  2. Ran Lambda to generate a content validation failure.
  3. Refreshed the live S3 dashboard.
  4. Confirmed the dashboard displayed DOWN and Content Check: Failed.
  5. Confirmed the failure reason appeared correctly.
  6. Restored healthy settings afterward.
- Final result: Dashboard Passed and Failed states are both verified. Not configured state is optional. Phase 3 is almost complete.
- Next step: Restore and confirm healthy dashboard state if not already done, optionally test Not configured state, update TASKS.md Phase 3 checklist, and prepare Phase 3 completion summary.

### Phase 3 TASKS checklist update

- Task name: Phase 3 TASKS checklist update
- What was done: Updated `TASKS.md`; marked implemented and verified Phase 3 content validation checklist items complete; left Phase 4, Phase 5, Open Design Decisions, README.md, and existing progress history unchanged; did not mark optional Not configured dashboard state.
- Problem faced: Needed to align TASKS.md with the actual Phase 3 work already implemented and verified.
- How it was solved:
  1. Reviewed completed Phase 3 Lambda content validation work.
  2. Reviewed completed AWS validation results.
  3. Reviewed completed dashboard Passed and Failed state verification.
  4. Marked only verified Phase 3 checklist items as complete.
  5. Left optional/unverified items unchanged.
- Final result: TASKS.md now reflects the current Phase 3 implementation and validation status. Phase 3 is ready for final completion review.
- Next step: Review TASKS.md Phase 3 checklist, commit TASKS.md and PROGRESS.md, prepare Phase 3 completion summary, then decide whether to move to Phase 4 or portfolio polish.

### Phase 3 SNS content failure alert verification

- Task name: Phase 3 SNS content failure alert verification
- What was done: Verified the SNS alert after triggering a content validation failure; confirmed the alert included the content failure reason.
- Problem faced: Needed to confirm Phase 3 alert content included the reason for a content validation failure, not only that the Lambda and dashboard showed the failure.
- How it was solved:
  1. Triggered a content validation failure.
  2. Checked the SNS alert generated from that failure.
  3. Confirmed the alert included the content failure reason.
  4. Updated the Phase 3 validation checklist in `TASKS.md`.
- Final result: Phase 3 validation is now fully complete.
- Next step: Commit TASKS.md and PROGRESS.md, prepare Phase 3 completion summary, then decide Phase 4 or portfolio polish.

### Phase 5 screenshot collection

- Task name: Phase 5 screenshot collection
- What was done: Added real screenshots for portfolio documentation: `docs/screenshots/dashboard-up.png`, `docs/screenshots/dashboard-down.png`, `docs/screenshots/dynamodb-results.png`, `docs/screenshots/sns-alert-email.png`, and `docs/screenshots/cloudwatch-logs.png`; updated `TASKS.md` to mark only the Phase 5 screenshot checklist items complete.
- Problem faced: Phase 5 portfolio polish needed proof screenshots tracked without marking unrelated documentation, architecture, setup, cost, limitations, lessons learned, future improvements, or demo recording work as complete.
- How it was solved:
  1. Confirmed the Phase 5 screenshot checklist items that correspond to the added files.
  2. Marked `Add real screenshots to docs/screenshots/` complete.
  3. Marked the dashboard UP, dashboard DOWN, DynamoDB results, SNS alert email, and CloudWatch logs screenshot items complete.
  4. Left the remaining Phase 5 checklist items unchanged.
- Final result: Phase 5 screenshot tracking now reflects the collected documentation screenshots.
- Next step: Create `docs/architecture.png` and add the architecture section to README.

### Phase 5 architecture documentation

- Task name: Phase 5 architecture documentation
- What was done: Created `docs/architecture.png`; added README architecture section with diagram; updated `TASKS.md` architecture checklist.
- Problem faced: Phase 5 architecture documentation needed to show the system flow clearly without marking unrelated README polish tasks complete.
- How it was solved:
  1. Confirmed `docs/architecture.png` exists.
  2. Added an Architecture section to `README.md`.
  3. Included the architecture diagram image.
  4. Documented the EventBridge, Lambda, DynamoDB, S3 dashboard, and SNS alert flow.
  5. Marked only the two Phase 5 architecture checklist items complete in `TASKS.md`.
- Final result: README now includes the architecture diagram and a short explanation of the monitoring flow.
- Next step: Add cost breakdown section to README.

### Phase 5 cost breakdown documentation

- Task name: Phase 5 cost breakdown documentation
- What was done: Added README cost breakdown section; documented estimated monthly usage; documented serverless cost-control choices; updated `TASKS.md` cost breakdown checklist.
- Problem faced: Phase 5 documentation needed to explain why the project stays very low cost without marking unrelated README polish items complete.
- How it was solved:
  1. Added a Cost Breakdown section to `README.md`.
  2. Documented estimated monthly usage for EventBridge, Lambda, DynamoDB, S3, and SNS.
  3. Documented expected personal/demo cost and cost-control choices.
  4. Added cost notes about billing variability and production budget alarms.
  5. Marked only the Phase 5 cost breakdown checklist item complete in `TASKS.md`.
- Final result: README now explains expected cost, Free Tier alignment, and serverless choices that keep the monitor low cost.
- Next step: Add known limitations section to README.

### Phase 5 known limitations documentation

- Task name: Phase 5 known limitations documentation
- What was done: Added README Known Limitations section; documented current single-site scope; documented dashboard freshness limitation; documented alerting and analytics limitations; updated `TASKS.md` known limitations checklist.
- Problem faced: Phase 5 documentation needed to clearly set expectations about current project boundaries without marking unrelated README polish tasks complete.
- How it was solved:
  1. Added a Known Limitations section to `README.md`.
  2. Documented the current single-target monitoring scope.
  3. Documented that the dashboard reflects the latest `status.json` instead of real-time updates.
  4. Documented alerting dependencies, repeated failure emails, public dashboard tradeoff, and analytics limits.
  5. Marked only the known limitations checklist item complete in `TASKS.md`.
- Final result: README now describes the current limitations and future improvement areas for monitoring, alerting, dashboard freshness, security, and analytics.
- Next step: Add lessons learned section to README.

### Phase 5 lessons learned documentation

- Task name: Phase 5 lessons learned documentation
- What was done: Added README Lessons Learned section; documented AWS/serverless design lessons; documented content validation lesson; documented `recent_failures`/`status.json` debugging lesson; updated `TASKS.md` lessons learned checklist.
- Problem faced: Phase 5 documentation needed to explain the engineering takeaways from the project without changing implementation code or marking unrelated checklist items complete.
- How it was solved:
  1. Added a Lessons Learned section to `README.md`.
  2. Documented why Lambda, EventBridge, DynamoDB, S3 `status.json`, IAM least-privilege, and SNS fit this project.
  3. Documented why HTTP 200 alone is not enough and why content validation improves monitoring.
  4. Documented the dashboard freshness and `recent_failures`/`status.json` debugging lessons.
  5. Marked only the lessons learned checklist item complete in `TASKS.md`.
- Final result: README now includes the main design, operations, monitoring, and debugging lessons from the project.
- Next step: Add future improvements section to README.

### Phase 5 future improvements documentation

- Task name: Phase 5 future improvements documentation
- What was done: Added README Future Improvements section; referenced Phase 4 improvement ideas; documented multi-site monitoring, uptime metrics, trend chart, alert threshold, and TTL as future work; updated `TASKS.md` future improvements checklist.
- Problem faced: Phase 5 documentation needed to show a clear roadmap from the current MVP to Phase 4 improvements without marking unrelated portfolio checklist items complete.
- How it was solved:
  1. Added a Future Improvements section to `README.md`.
  2. Listed multi-site monitoring with separate `site_id` values.
  3. Added uptime, response time, incident count, alert threshold, redirect handling, trend chart, dashboard UI, TTL, and CloudWatch alarm improvements.
  4. Marked only the future improvements checklist item complete in `TASKS.md`.
- Final result: README now documents the main future work items that build on the current monitor and align with Phase 4.
- Next step: Review README setup instructions and decide whether they need improvement.

### Phase 5 setup instructions documentation

- Task name: Phase 5 setup instructions documentation
- What was done: Improved README setup instructions; documented AWS resources; documented Lambda environment variables; documented validation checklist; updated `TASKS.md` setup instructions checklist.
- Problem faced: README needed a clear manual setup flow that someone unfamiliar with the project could follow without changing project code or AWS settings.
- How it was solved:
  1. Added a Setup Instructions section to `README.md`.
  2. Listed prerequisites and the AWS region.
  3. Documented required AWS resources.
  4. Documented Lambda environment variables.
  5. Added deployment flow and validation checklist.
  6. Marked only the setup instructions checklist item complete in `TASKS.md`.
- Final result: README now has a clear setup overview covering prerequisites, AWS resources, environment variables, deployment flow, and validation checks.
- Next step: Decide whether to create an optional demo GIF/screen recording or finish Phase 5 polish summary.

### Phase 5 portfolio polish summary

- Task name: Phase 5 portfolio polish summary
- What was done: Summarized Phase 5 polish completed so far: added portfolio screenshots; added architecture diagram; added README Architecture section; added README Cost Breakdown section; added README Known Limitations section; added README Lessons Learned section; added README Future Improvements section; added README Setup Instructions section.
- Problem faced: Phase 5 needed a completion summary that reflects the documentation and screenshot polish already completed while leaving the optional demo GIF/screen recording for later.
- How it was solved:
  1. Reviewed the completed Phase 5 polish work already tracked in `PROGRESS.md`.
  2. Summarized the screenshot, architecture, README documentation, setup, and portfolio polish work.
  3. Kept the demo GIF/screen recording intentionally left for later because screenshots and README are enough for the first portfolio pass.
  4. Left README.md, TASKS.md, PRD.md, Lambda code, dashboard code, screenshots, architecture image, and AWS settings unchanged.
- Final result: Phase 5 portfolio polish is complete for the first portfolio pass, with the optional demo GIF/screen recording deferred.
- Next step: Review final README, then merge phase-5-portfolio-polish into main and push.

### Phase 4 open design decisions resolved

- Task name: Phase 4 open design decisions resolved
- What was done: Updated `TASKS.md` and resolved the Phase 4 open design decisions in both the Phase 4 checklist and Open Design Decisions Tracker.
- Problem faced: Phase 4 should not start with coding until the design decisions are locked.
- How it was solved:
  1. Confirmed redirects will count as success when the final resolved response is 2xx.
  2. Set the alert strategy to use a consecutive-failure threshold, default 2 failures.
  3. Confirmed recent failures will remain latest 5.
  4. Confirmed one shared DynamoDB table, `website_checks`, using `site_id` and `check_time`.
  5. Confirmed Lambda should retry once only for timeout or network-level errors.
  6. Left Phase 4 build items unchecked because implementation has not started yet.
- Final result: Phase 4 decisions are now locked and ready for implementation planning.
- Next step: Start Phase 4B by adding multi-site config support in Lambda.

### Phase 4B multi-site Lambda config support

- Task name: Phase 4B multi-site Lambda config support
- What was done: Added Lambda support for `SITES_CONFIG`; kept single-site environment variable fallback; updated S3 `status.json` output to include a `sites` array when multiple sites are checked; added minimal tests for multi-site config parsing and single-site backward compatibility; marked the Phase 4 multi-site Lambda support checklist item complete in `TASKS.md`.
- Problem faced: Lambda needed to support multiple websites from one run without changing the dashboard UI, AWS resource names, DynamoDB table design, alert threshold behavior, or Phase 4 metrics work.
- How it was solved:
  1. Added `SITES_CONFIG` JSON array parsing and validation for per-site `site_id`, `target_url`, timeout, response threshold, expected text, and forbidden text.
  2. Preserved current single-site behavior when `SITES_CONFIG` is missing or empty.
  3. Reused the existing DynamoDB write, recent failures, SNS alert, HTTP redirect, response validation, and content validation paths for each site.
  4. Kept the single-site `status.json` payload shape unchanged, and added a `sites` array only when multiple sites are checked.
  5. Added minimal tests for config parsing and single-site fallback.
  6. Left uptime percentage, average response time, incident count, charts, TTL, dashboard redesign, and alert threshold items untouched.
- Final result: One Lambda invocation can now check multiple configured sites while staying backward compatible with the existing single-site environment configuration.
- Next step: Plan the next Phase 4 item, likely uptime percentage calculation per site.

### Phase 4B multi-site AWS validation

- Task name: Phase 4B multi-site AWS validation
- What was done: Validated the Phase 4B multi-site Lambda behavior in AWS after adding `SITES_CONFIG` to the Lambda environment variables.
- Problem faced: The first Lambda test still returned the old single-site `my-portfolio` result because the updated Phase 4B `app.py` code had not been uploaded to AWS yet.
- How it was solved:
  1. Added `SITES_CONFIG` to the AWS Lambda environment variables.
  2. Ran the first Lambda test and confirmed it still returned single-site `my-portfolio`.
  3. Checked the AWS Lambda code and confirmed `SITES_CONFIG` was not found there.
  4. Created a new Lambda ZIP containing the updated `app.py`.
  5. Uploaded the new ZIP to AWS Lambda.
  6. Ran Lambda again and confirmed the response returned a multi-site `sites` array.
  7. Confirmed the healthy multi-site test passed for `example-main` and `example-second`.
  8. Confirmed DynamoDB stored separate items for `example-main` and `example-second`.
  9. Ran a mixed test and confirmed `example-main` was healthy while `example-failed` returned HTTP 404.
  10. Confirmed an SNS alert email was received for `example-failed` DOWN.
  11. Confirmed DynamoDB stored failed-site records for `example-failed`.
  12. Restored `SITES_CONFIG` back to healthy `example-main` and `example-second`.
  13. Ran Lambda one final time and confirmed both sites were healthy again.
- Final result: Phase 4B multi-site AWS validation is complete. AWS Lambda now runs the updated multi-site code, writes separate DynamoDB records per site, returns a multi-site `sites` array, alerts on a failed site, and is restored to the healthy two-site configuration.
- Next step: Start Phase 4C by adding uptime percentage calculation per site.

### Phase 4C uptime percentage calculation per site

- Task name: Phase 4C uptime percentage calculation per site
- What was done: Added uptime percentage metrics for each monitored site. Each site result now includes `uptime_percentage` and `uptime_window_checks`; the fields are included in the Lambda return output, the S3 `status.json` site payloads, and the DynamoDB result item.
- Problem faced: Uptime had to be calculated per `site_id` only, include the current check result, avoid changing multi-site config, dashboard behavior, recent failures, SNS alerts, or future Phase 4 metrics, and keep DynamoDB writes compatible with numeric percentage values.
- How it was solved:
  1. Added a recent-result query for the current `site_id` only.
  2. Added a small uptime calculator using `successful checks / total checks * 100`.
  3. Included the current check result plus recent stored records in the calculation.
  4. Rounded `uptime_percentage` to 2 decimal places.
  5. Added `uptime_window_checks` to show how many checks were used.
  6. Attached uptime metrics to the result before writing to DynamoDB.
  7. Converted float values to DynamoDB-safe decimals during DynamoDB writes.
  8. Added minimal unit tests for uptime percentage math and same-site filtering.
  9. Marked the Phase 4 uptime percentage checklist item complete in `TASKS.md`.
- Final result: Phase 4C is implemented. Multi-site Lambda output and S3 site payloads now report uptime percentage per site, and DynamoDB can store the current result with the uptime fields.
- Next step: Start Phase 4D by adding average response time metric per site.

### Phase 4C uptime percentage AWS validation

- Task name: Phase 4C uptime percentage AWS validation
- What was done: Deployed the updated Lambda ZIP with Phase 4C uptime percentage code and validated the uptime fields in AWS Lambda, S3 `status.json`, and DynamoDB.
- Problem faced: Needed to confirm the new uptime fields were working in the deployed AWS environment, not only in local code, and that each site received its own uptime calculation.
- How it was solved:
  1. Deployed the updated Lambda ZIP with the Phase 4C uptime percentage code.
  2. Ran Lambda with the healthy multi-site `SITES_CONFIG`.
  3. Confirmed Lambda output included `uptime_percentage` and `uptime_window_checks` for each site.
  4. Confirmed `example-main` returned `uptime_percentage=100` and `uptime_window_checks=11`.
  5. Confirmed `example-second` returned `uptime_percentage=100` and `uptime_window_checks=9`.
  6. Checked S3 `status.json` and confirmed `uptime_percentage` and `uptime_window_checks` appear at the top level and inside the multi-site `sites` array.
  7. Checked the latest DynamoDB item for `example-main` and confirmed `uptime_percentage=100` and `uptime_window_checks=11`.
  8. Checked the latest DynamoDB item for `example-second` and confirmed `uptime_percentage=100` and `uptime_window_checks=9`.
- Final result: Phase 4C AWS validation is complete. Uptime percentage and uptime window count are confirmed in Lambda output, S3 `status.json`, and DynamoDB for both monitored sites.
- Next step: Start Phase 4D by adding average response time metric per site.

### Phase 4D average response time metric per site

- Task name: Phase 4D average response time metric per site
- What was done: Added average response time metrics for each monitored site. Each site result now includes `average_response_time_ms` and `response_time_window_checks`; the fields are included in the Lambda return output, the S3 `status.json` site payloads, and the DynamoDB result item.
- Problem faced: Average response time had to be calculated per `site_id` only, include the current check result, skip records without `response_time_ms`, avoid changing uptime percentage behavior, and avoid touching dashboard, alert, content validation, config, or future Phase 4 work.
- How it was solved:
  1. Reused the existing recent-result query for the current `site_id`.
  2. Added a small average response time calculator using `sum(response_time_ms values) / total checks with response_time_ms`.
  3. Included the current check result plus recent stored records in the calculation.
  4. Filtered records so only the same `site_id` contributes to the metric.
  5. Rounded `average_response_time_ms` to the nearest whole number.
  6. Added `response_time_window_checks` to show how many response-time values were used.
  7. Attached average response time metrics to the result before writing to DynamoDB.
  8. Added minimal unit tests for average response time math and same-site filtering.
  9. Marked the Phase 4 average response time checklist item complete in `TASKS.md`.
- Final result: Phase 4D is implemented. Multi-site Lambda output and S3 site payloads now report average response time per site, and DynamoDB can store the current result with the new response time metric fields.
- Next step: Start Phase 4E by adding incident count per site for last 24h and last 7 days.

### Phase 4D average response time AWS validation

- Task name: Phase 4D average response time AWS validation
- What was done: Deployed the updated Lambda ZIP with Phase 4D average response time code and validated the response time metric fields in AWS Lambda, S3 `status.json`, and DynamoDB.
- Problem faced: Needed to confirm the new average response time fields were working in the deployed AWS environment for both monitored sites, not only in local code.
- How it was solved:
  1. Deployed the updated Lambda ZIP with the Phase 4D average response time code.
  2. Ran Lambda with the healthy multi-site `SITES_CONFIG`.
  3. Confirmed Lambda output included `average_response_time_ms` and `response_time_window_checks` for each site.
  4. Confirmed `example-main` returned `average_response_time_ms=196` and `response_time_window_checks=14`.
  5. Confirmed `example-second` returned `average_response_time_ms=90` and `response_time_window_checks=12`.
  6. Checked S3 `status.json` and confirmed `average_response_time_ms` and `response_time_window_checks` appear at the top level and inside the multi-site `sites` array.
  7. Checked the latest DynamoDB item for `example-main` and confirmed `average_response_time_ms=196` and `response_time_window_checks=14`.
  8. Checked the latest DynamoDB item for `example-second` and confirmed `average_response_time_ms=90` and `response_time_window_checks=12`.
- Final result: Phase 4D AWS validation is complete. Average response time and response time window count are confirmed in Lambda output, S3 `status.json`, and DynamoDB for both monitored sites.
- Next step: Start Phase 4E by adding incident count per site for last 24h and last 7 days.

### Phase 4E incident count per site

- Task name: Phase 4E incident count per site for last 24h and last 7 days
- What was done: Added incident count metrics for each monitored site. Each site result now includes `incident_count_24h` and `incident_count_7d`; the fields are included in the Lambda return output, the S3 `status.json` site payloads, and the DynamoDB result item.
- Problem faced: Incident counts had to use only failed checks for the same `site_id`, include the current failed check, use ISO `check_time` values for 24-hour and 7-day windows, and avoid changing recent failures, uptime percentage, average response time, SNS behavior, dashboard files, or future Phase 4 work.
- How it was solved:
  1. Added an ISO timestamp parser for stored `check_time` values.
  2. Added a small incident count calculator for `incident_count_24h` and `incident_count_7d`.
  3. Used the current check result plus recent stored records from the same `site_id`.
  4. Counted only records where `is_success` is false.
  5. Counted a failed check in the 24-hour window when its `check_time` is inside the last 24 hours.
  6. Counted a failed check in the 7-day window when its `check_time` is inside the last 7 days.
  7. Attached incident metrics to the result before writing to DynamoDB.
  8. Added minimal unit tests for window counting and same-site filtering.
  9. Marked the Phase 4 incident count checklist item complete in `TASKS.md`.
- Final result: Phase 4E is implemented. Multi-site Lambda output and S3 site payloads now report incident counts per site for the last 24 hours and last 7 days, and DynamoDB can store the current result with the new incident count fields.
- Next step: Start Phase 4F by adding the consecutive-failure alert threshold.

### Phase 4E incident count AWS validation

- Task name: Phase 4E incident count AWS validation
- What was done: Deployed the updated Lambda ZIP with Phase 4E incident count code and validated incident count fields in AWS Lambda, S3 `status.json`, and DynamoDB.
- Problem faced: Needed to confirm incident counts worked in AWS for both healthy sites and a mixed failure case, including existing failed records for the failed site.
- How it was solved:
  1. Deployed the updated Lambda ZIP with the Phase 4E incident count code.
  2. Ran Lambda with the healthy multi-site `SITES_CONFIG`.
  3. Confirmed the healthy output included `incident_count_24h` and `incident_count_7d` for `example-main` and `example-second`.
  4. Confirmed `example-main` returned `incident_count_24h=0` and `incident_count_7d=0`.
  5. Confirmed `example-second` returned `incident_count_24h=0` and `incident_count_7d=0`.
  6. Ran a mixed failure test with `example-main` healthy and `example-failed` using `https://example.com/not-found-test`.
  7. Confirmed `example-failed` returned HTTP 404, `is_success=false`, and `failure_reason=HTTP 404: Not Found`.
  8. Confirmed `example-failed` incident counts increased correctly because earlier failed records already existed.
  9. Checked S3 `status.json` and confirmed `incident_count_24h` and `incident_count_7d` appear inside the multi-site `sites` array.
  10. Checked the latest DynamoDB item for `example-failed` and confirmed `incident_count_24h=4` and `incident_count_7d=4`.
  11. Restored `SITES_CONFIG` back to healthy `example-main` and `example-second`.
  12. Ran Lambda one final time and confirmed both sites were healthy again.
- Final result: Phase 4E AWS validation is complete. Healthy sites report zero incidents, the failed site reports the expected 24-hour and 7-day incident counts, and the system is restored to the healthy two-site configuration.
- Next step: Start Phase 4F by adding the consecutive-failure alert threshold.

### Phase 4F consecutive-failure alert threshold

- Task name: Phase 4F consecutive-failure alert threshold
- What was done: Added `ALERT_FAILURE_THRESHOLD` with default `2`; calculated `consecutive_failure_count` per `site_id`; added `consecutive_failure_count`, `alert_sent`, and `alert_failure_threshold` to Lambda results, S3 status payloads, and DynamoDB result items; changed SNS publishing to wait until the threshold is reached; added minimal unit tests for consecutive failure counting and alert threshold behavior; marked the Phase 4F checklist item complete in `TASKS.md`.
- Problem faced: Alerts had to be quieter without changing multi-site config, DynamoDB table keys, recent failures, uptime percentage, average response time, incident counts, content validation, dashboard files, or AWS resource names.
- How it was solved:
  1. Read `ALERT_FAILURE_THRESHOLD` from the Lambda environment with a default of `2`.
  2. Added a same-site consecutive failure counter that includes the current failed check and stops when it reaches the latest successful check.
  3. Set successful checks to `consecutive_failure_count=0` and `alert_sent=false`.
  4. Set failed checks to send SNS only when `consecutive_failure_count >= alert_failure_threshold`.
  5. Added the new alert fields before writing DynamoDB and building the S3 status payload.
  6. Added tests for same-site counting, success reset behavior through the count boundary, no alert on the first failure, and alert on the second consecutive failure.
- Final result: Phase 4F is implemented. First failures do not send SNS when `ALERT_FAILURE_THRESHOLD=2`; second consecutive failures for the same `site_id` send SNS and mark `alert_sent=true`.
- Next step: Start Phase 4G by adding configurable redirect handling.

### Phase 4F consecutive-failure alert threshold AWS validation

- Task name: Phase 4F consecutive-failure alert threshold AWS validation
- What was done: Deployed the updated Lambda ZIP with Phase 4F consecutive-failure alert threshold code and validated the threshold behavior in AWS.
- Problem faced: Existing failed records could make alert threshold results unclear, so validation needed a fresh `site_id` with no old failure history.
- How it was solved:
  1. Deployed the updated Lambda ZIP with the Phase 4F consecutive-failure alert threshold code.
  2. Added or confirmed `ALERT_FAILURE_THRESHOLD=2` in the Lambda environment variables.
  3. Used fresh `site_id=threshold-test` to avoid old failure history.
  4. Ran the first failing check and confirmed HTTP 404, `consecutive_failure_count=1`, `alert_failure_threshold=2`, and `alert_sent=false`.
  5. Confirmed no SNS email was expected on the first failure.
  6. Ran the second same-site failing check and confirmed HTTP 404, `consecutive_failure_count=2`, and `alert_sent=true`.
  7. Confirmed the SNS alert email was received on the second consecutive failure.
  8. Ran a healthy reset check for `threshold-test` and confirmed HTTP 200, `is_success=true`, `consecutive_failure_count=0`, and `alert_sent=false`.
  9. Restored `SITES_CONFIG` back to healthy `example-main` and `example-second`.
  10. Ran Lambda one final time and confirmed both sites were healthy with `consecutive_failure_count=0` and `alert_sent=false`.
- Final result: Phase 4F AWS validation is complete. Alert noise is reduced because the first failure does not send SNS when the threshold is 2, while the second consecutive same-site failure does send SNS.
- Next step: Start Phase 4G by adding configurable redirect handling.

### Phase 4G configurable redirect handling

- Task name: Phase 4G configurable redirect handling
- What was done: Added optional `redirect_policy` support for both `SITES_CONFIG` and single-site `REDIRECT_POLICY`; kept the default as `follow`; added `fail_on_redirect` behavior for HTTP 301, 302, 303, 307, and 308 responses; added `redirect_policy` and `redirect_detected` fields to Lambda results, S3 status payloads, and DynamoDB result items; added minimal unit tests for redirect policy parsing and redirect failure behavior; marked the Phase 4G checklist item complete in `TASKS.md`.
- Problem faced: Redirect handling had to become configurable without changing current default `urllib` follow behavior, content validation, uptime percentage, average response time, incident count, consecutive-failure alert threshold, dashboard files, or AWS resource names.
- How it was solved:
  1. Added `redirect_policy` normalization with supported values `follow` and `fail_on_redirect`.
  2. Added `redirect_policy` to normalized per-site config and the single-site fallback environment config.
  3. Kept `follow` using the existing `urllib` redirect behavior.
  4. Added a no-redirect opener for `fail_on_redirect` so redirect responses are returned as failures.
  5. Set redirect failure reason to `Redirect not allowed: HTTP <status_code>`.
  6. Added `redirect_policy` and `redirect_detected` to result output before the existing metrics, DynamoDB write, status payload, and alert threshold flow.
  7. Added minimal tests for per-site redirect policy parsing, single-site `REDIRECT_POLICY`, and `fail_on_redirect` behavior.
- Final result: Phase 4G is implemented. Existing sites still follow redirects by default, and sites can now opt into failing on redirect responses.
- Next step: Start Phase 4H by adding the response time trend chart using Chart.js on the dashboard.

### Phase 4G configurable redirect handling AWS validation

- Task name: Phase 4G configurable redirect handling AWS validation
- What was done: Deployed the updated Lambda ZIP with Phase 4G configurable redirect handling code and validated both redirect policies in AWS.
- Problem faced: Needed to prove the default missing `redirect_policy` behavior still follows redirects while `fail_on_redirect` fails on redirect responses, without confusing the result with old site history or the existing alert threshold behavior.
- How it was solved:
  1. Deployed the updated Lambda ZIP with the Phase 4G configurable redirect handling code.
  2. Tested default missing `redirect_policy` using `redirect-follow-test`.
  3. Confirmed `redirect-follow-test` used `redirect_policy=follow`, `redirect_detected=true`, final `status_code=200`, `is_success=true`, and `failure_reason=null`.
  4. Tested `redirect_policy=fail_on_redirect` using `redirect-fail-test`.
  5. Confirmed `redirect-fail-test` returned `status_code=302`, `is_success=false`, `redirect_detected=true`, and `failure_reason=Redirect not allowed: HTTP 302`.
  6. Confirmed that because `ALERT_FAILURE_THRESHOLD=2`, the first redirect failure returned `consecutive_failure_count=1` and `alert_sent=false`.
  7. Restored `SITES_CONFIG` back to healthy `example-main` and `example-second`.
  8. Ran Lambda one final time and confirmed both sites were healthy with `redirect_policy=follow`, `redirect_detected=false`, `consecutive_failure_count=0`, and `alert_sent=false`.
- Final result: Phase 4G AWS validation is complete. Default redirect-follow behavior remains unchanged, and `fail_on_redirect` correctly marks redirect responses as failed without sending a first-failure SNS alert under the threshold setting.
- Next step: Start Phase 4H by adding the response time trend chart using Chart.js on the dashboard.

### Phase 4H response time trend chart

- Task name: Phase 4H response time trend chart using Chart.js on the dashboard
- What was done: Added Chart.js from a CDN to the dashboard; added one response time trend chart section; plotted latest `response_time_ms` values from existing `status.json` data; supported multi-site payloads with one point per site and single-site payloads with one point; added a clean empty state when no usable response time data is available; marked the Phase 4H checklist item complete in `TASKS.md`.
- Problem faced: The chart needed to use only the current `status.json` shape, preserve the existing dashboard layout and UP/DOWN cards, and avoid adding DynamoDB/API fetching or changing backend payload generation.
- How it was solved:
  1. Added the Chart.js CDN script before `app.js` in `dashboard/index.html`.
  2. Added a compact chart section with a canvas and empty-state text.
  3. Added dashboard JavaScript to read `data.sites` when present or fall back to the single-site payload.
  4. Filtered out sites without numeric `response_time_ms` values and showed the empty state if no points remain.
  5. Created or updated one Chart.js line chart using site IDs as labels and response times as values.
  6. Added minimal CSS for the chart card while keeping the existing dashboard theme and layout.
- Final result: Phase 4H is implemented. The dashboard now shows an MVP response time trend chart based on the latest response time data already present in `status.json`.
- Next step: Start Phase 4I by improving the dashboard UI for multiple sites.

### Phase 4H response time trend chart live validation

- Task name: Phase 4H response time trend chart live validation
- What was done: Uploaded the updated `dashboard/index.html`, `dashboard/app.js`, and `dashboard/style.css` to S3 and validated the live dashboard.
- Problem faced: Needed to confirm the Chart.js section worked on the live S3 dashboard without breaking existing status, content check, recent failures, or layout behavior.
- How it was solved:
  1. Uploaded the updated dashboard files to S3.
  2. Opened the live S3 dashboard.
  3. Confirmed the Response Time Trend chart appears.
  4. Confirmed the chart uses existing `status.json` data.
  5. Confirmed the chart shows one point for `example-main` and one point for `example-second`.
  6. Confirmed the existing UP status display still works.
  7. Confirmed Content Check still displays correctly.
  8. Confirmed Recent Failures still displays correctly.
  9. Confirmed the dashboard layout is not broken.
- Final result: Phase 4H live validation is complete. The dashboard now shows the MVP response time chart from `status.json`; this is latest response time per site, not a historical trend, because the dashboard only reads `status.json`.
- Next step: Start Phase 4I by improving the dashboard UI for multiple sites.

### Phase 4I multiple-site dashboard UI

- Task name: Phase 4I improve dashboard UI for multiple sites
- What was done: Added a multi-site dashboard section that appears when `status.json` contains a `sites` array; added overall site totals for total, UP, and DOWN sites; added one readable card per monitored site with the key monitoring fields; kept single-site dashboard behavior, Response Time Trend chart, and Recent Failures working; marked the Phase 4I checklist item complete in `TASKS.md`.
- Problem faced: The dashboard needed to show multi-site data clearly without changing the backend `status.json` structure, removing the existing main status cards, breaking the chart, or redesigning the full dashboard.
- How it was solved:
  1. Added a hidden multi-site section in `dashboard/index.html`.
  2. Added summary cards for total sites, UP sites, and DOWN sites.
  3. Added JavaScript that detects `data.sites` and renders the multi-site panel only for multi-site payloads.
  4. Added one site card per item in `sites`, including status, URL, HTTP status, response time, content check, uptime, average response time, incident counts, consecutive failures, alert sent, redirect policy, and redirect detected.
  5. Displayed `failure_reason` only on failed site cards.
  6. Preserved the single-site view by hiding the multi-site panel when `sites` is missing.
  7. Added minimal responsive CSS for the summary and site cards while keeping the current cream/green dashboard theme.
- Final result: Phase 4I is implemented. The dashboard now clearly supports multiple monitored sites using the existing `status.json` `sites` array, while remaining backward-compatible with single-site payloads.
- Next step: Start Phase 4J by adding a DynamoDB TTL attribute to expire old records.

### Phase 4I multi-site dashboard UI live validation

- Task name: Phase 4I multi-site dashboard UI live validation
- What was done: Uploaded the updated `dashboard/index.html`, `dashboard/app.js`, and `dashboard/style.css` to S3 and validated the live multi-site dashboard UI.
- Problem faced: Needed to confirm the new multi-site section worked on the live S3 dashboard without breaking the chart, recent failures, existing theme, or layout.
- How it was solved:
  1. Uploaded the updated dashboard files to S3.
  2. Opened the live S3 dashboard.
  3. Confirmed the multi-site dashboard section appears.
  4. Confirmed summary cards show total sites 2, UP sites 2, and DOWN sites 0.
  5. Confirmed a per-site card appears for `example-main`.
  6. Confirmed a per-site card appears for `example-second`.
  7. Confirmed site cards show key metrics including HTTP status, response time, content check, uptime, average response, incident counts, consecutive failures, alert sent, redirect policy, and redirect seen.
  8. Confirmed the Response Time Trend chart still works.
  9. Confirmed the Recent Failures section still works.
  10. Confirmed the dashboard theme and layout remain clean.
- Final result: Phase 4I live validation is complete. The live S3 dashboard now clearly presents the two healthy monitored sites and their per-site metrics without breaking the existing chart or failure history sections.
- Next step: Start Phase 4J by adding a DynamoDB TTL attribute to expire old records.

### Phase 4J DynamoDB TTL attribute

- Task name: Phase 4J DynamoDB TTL attribute to expire old records
- What was done: Added `RETENTION_DAYS` with default `30`; added `ttl_expires_at` to each new check result; included `ttl_expires_at` in the DynamoDB item, Lambda return output, and S3 `status.json` site payload; added minimal unit tests for TTL timestamp calculation and invalid `RETENTION_DAYS` fallback; marked the Phase 4J checklist item complete in `TASKS.md`.
- Problem faced: TTL needed to be added to new records only without changing DynamoDB table keys, enabling TTL from code, changing existing records, or affecting content validation, recent failures, metrics, alert threshold, redirect handling, dashboard files, or AWS resources.
- How it was solved:
  1. Added a safe positive-integer parser for environment values.
  2. Read `RETENTION_DAYS` from the Lambda environment and fell back to `30` when missing, empty, invalid, or non-positive.
  3. Calculated `ttl_expires_at` from the current `check_time` plus the retention period.
  4. Stored `ttl_expires_at` on the result before the existing DynamoDB write and status payload build.
  5. Reused the existing DynamoDB write flow so the TTL attribute is included cleanly in new current result items.
  6. Added focused tests for retention fallback and deterministic TTL epoch calculation.
- Final result: Phase 4J is implemented. New check records now carry a Unix epoch `ttl_expires_at` value that can be used when DynamoDB TTL is enabled manually.
- Next step: Phase 4J AWS validation: deploy Lambda, set or confirm `RETENTION_DAYS`, run Lambda, confirm `ttl_expires_at` appears in DynamoDB, then enable TTL manually on the DynamoDB table using `ttl_expires_at`.

### Phase 4J DynamoDB TTL AWS validation

- Task name: Phase 4J DynamoDB TTL AWS validation
- What was done: Deployed the updated Lambda ZIP with Phase 4J TTL code, validated `ttl_expires_at` in Lambda output and DynamoDB, and manually enabled DynamoDB TTL.
- Problem faced: Needed to confirm the TTL attribute was present on new records in AWS and then enable DynamoDB TTL manually without changing code or AWS resource names from Lambda.
- How it was solved:
  1. Deployed the updated Lambda ZIP with the Phase 4J TTL code.
  2. Added or confirmed `RETENTION_DAYS=30` in the Lambda environment variables.
  3. Ran Lambda with the healthy multi-site `SITES_CONFIG`.
  4. Confirmed Lambda output included `ttl_expires_at` for `example-main` and `example-second`.
  5. Confirmed the `ttl_expires_at` value was `1780675263` in Lambda output.
  6. Checked the latest DynamoDB item for `example-main` and confirmed `ttl_expires_at=1780675263`.
  7. Checked the latest DynamoDB item for `example-second` and confirmed `ttl_expires_at=1780675263`.
  8. Manually enabled DynamoDB TTL on table `website_checks` using `ttl_expires_at` as the TTL attribute.
  9. Confirmed in the AWS console that TTL status is On.
  10. Confirmed in the AWS console that the TTL attribute is `ttl_expires_at`.
- Final result: Phase 4J AWS validation is complete. New records include the TTL attribute, and DynamoDB TTL is enabled on `website_checks`; expired item deletion is not immediate and AWS may remove expired items later.
- Next step: Review Phase 4 checklist and decide whether to close Phase 4 or add a final Phase 4 summary.

### Phase 4 final checklist review and completion summary

- Task name: Phase 4 final checklist review and completion summary
- What was done: Reviewed the Phase 4 checklist against completed work already recorded in `PROGRESS.md`.
- Problem faced: Needed to confirm Phase 4 could be closed based only on recorded implementation and validation notes.
- How it was solved:
  1. Confirmed multi-site monitoring was implemented and validated in AWS.
  2. Confirmed uptime percentage per site was implemented and validated in AWS.
  3. Confirmed average response time per site was implemented and validated in AWS.
  4. Confirmed incident counts per site for the last 24 hours and last 7 days were implemented and validated in AWS.
  5. Confirmed consecutive-failure alert threshold was implemented and validated in AWS.
  6. Confirmed configurable redirect handling was implemented and validated in AWS.
  7. Confirmed the Chart.js response time chart was implemented and live-validated on the S3 dashboard.
  8. Confirmed the multi-site dashboard UI was implemented and live-validated on the S3 dashboard.
  9. Confirmed the DynamoDB TTL attribute was implemented, validated in AWS, and enabled on `website_checks`.
- Final result: Phase 4 is complete. All listed Phase 4 improvement items are checked in `TASKS.md` and have matching recorded implementation or validation notes in `PROGRESS.md`.
- Next step: Start Phase 5 final portfolio refresh / README update.

## Ongoing Rule

After every future project task, update `PROGRESS.md` with task completed, problems faced, solution steps, final result, and next step.

## Next Step

- Start Phase 5 final portfolio refresh / README update.
