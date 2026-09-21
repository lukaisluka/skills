# Failure Data Sources

How to obtain structured failure data before reasoning about causes, and how
to degrade honestly when a source is unavailable.

## Priority chain

Try sources in order; stop as soon as you have test-case-level failure detail.

1. **Pipeline / job test report** — GitLab's JUnit report integration (the
   "Test" tab on a pipeline or job). Provides per-suite and per-case status,
   failure message, stack trace, and duration. This is the cheapest path to
   structured data; check for it first.
2. **Job artifacts** — JUnit XML files (`junit*.xml`, `test-results/`),
   Allure results, HTML reports. Browse artifacts for a report file before
   falling back to raw logs.
3. **Job trace parsing** — the job's raw log. Last resort; see heuristics
   below.

## Reading a test report

- Failed vs error vs skipped mean different things: a case that *errored*
  never completed (setup crash, unhandled exception); a *failed* case completed
  with a wrong assertion. Record which.
- The report's per-case time is a **duration**, and any timestamp on it is a
  **completion** time, not the moment the error occurred. The failure happened
  somewhere inside `[completion − duration, completion]`. Use that interval —
  not a point — when correlating with runtime events.
- Suite-level rollups tell you scale; individual cases tell you cause. Pull
  both, but only pull representative cases into full detail.

## Reading artifacts

- Identify the report format from filenames: JUnit XML (`<testsuite>` /
  `<testcase>` with `<failure message>` / `<error>` children), Allure
  (`allure-results/` JSON per case), custom HTML summaries.
- JUnit XML `classname` + `name` identify the test; `time` is duration;
  `system-out` / `system-err` often carry captured logs close to the failure.

## Job-trace parsing heuristics

When no report exists:

- Most frameworks print a **summary block** near the end (failed-test list
  with counts) and per-test error blocks above it. Find the summary first —
  it gives you the failure list cheaply — then locate the error detail for
  representatives only.
- Recognize your framework's markers as you encounter them (pytest's
  `FAILED`/`ERROR` summary, jest's `✕` lines, Go's `--- FAIL`, Surefire's
  `Failures:` section). Do not assume one format.
- Watch for **job-level failure before any test ran**: image pull errors,
  OOMKill, container startup crash, runner infrastructure errors, missing
  dependencies at boot. If the job never reached the test phase, there is no
  test failure to analyze — investigate the job itself and say so.
- Trace lines are usually prefixed with runner timestamps; those come from
  the CI runner's clock, which is not synchronized with the cluster. When
  correlating with Kubernetes events, keep both timestamps and note the
  skew.

## Log retention and alternatives

- Pod restarts wipe `kubectl logs` history. If the container restarted in
  place, previous-instance logs may still be reachable; if the pod was
  replaced, they are gone — fall back to events, centralized logging, or
  artifacts shipped by the job.
- GitLab caps job trace size; long jobs may have truncated tails. If the tail
  is missing, the archived trace or artifacts may hold the full version.
- When citing a log, note where it came from and its retention limits. If the
  failure window's logs are no longer retrievable, record **Missing Evidence**
  — never infer "no errors" from absent logs.

## Time-precision rules

- Allow minute-scale slack when aligning test failures with runtime events.
  The report timestamp is a completion time; the actual error may precede it
  by the test's duration (which for timeouts is the whole timeout budget).
- CI runner, application pods, and the Kubernetes API server run on different
  clocks. Correlating "10:31:05 in the job log" with "10:31:07 in pod events"
  is fine; treating a 40-second gap as exclusion evidence is not.

## Data-unavailable protocol

When a source in the priority chain is unavailable:

1. Record what was tried and why it failed (no test report uploaded, artifacts
   expired, logs rotated).
2. Degrade to the next source and note the reduced precision.
3. If all sources fail, report the blocker and what would unblock it (e.g.
   "enable JUnit report on job X", "check centralized logging for window Y").
   Guessing from memory of "similar past failures" is not a substitute.

## Context discipline

Whatever the source: aggregate before you read. Collapse the failure list to
signatures and counts first; pull full detail for representatives only. The
full list is for coverage checks, not for wholesale pasting into context.
