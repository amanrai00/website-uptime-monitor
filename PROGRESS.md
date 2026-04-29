# Project Progress

## Completed Phases

- Phase 0: Repository setup

## Current Phase

- Phase 1: Monitoring Engine

## Current Status

- Lambda code completed
- Local tests passed
- AWS setup not completed yet

## Completed Task History

- Phase 0 project setup
- Phase 1 Lambda monitoring engine code implemented
- Local test run completed
- Added Phase 1 AWS setup guide to README.

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

## Ongoing Rule

After every future project task, update `PROGRESS.md` with task completed, problems faced, solution steps, final result, and next step.

## Next Step

Create AWS resources manually in `ap-northeast-1` and configure Lambda environment variables.
