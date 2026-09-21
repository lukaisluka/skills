---
name: investigate-integration-tests
description: >
  Investigate integration test failures end-to-end. Use when the user asks why
  a CI pipeline, merge request, job, or test case failed, wants failed tests
  clustered by root cause, suspects flaky tests or test-environment / dependency
  problems, or continues an ongoing investigation. Combines GitLab pipelines,
  MRs, jobs, test reports, logs, and Kubernetes runtime evidence into
  evidence-backed conclusions.
---

# Integration Test Investigation

Investigate integration-test failures on remote GitLab projects: understand
what failed, cluster related failures, gather evidence across code, runtime,
and history, form and validate hypotheses, and report conclusions with explicit
confidence — including UNKNOWN when the evidence runs out.

This skill is a methodology, not a tool chain. It never names a specific tool.
Use whatever Git-hosting, Kubernetes, log, and code-search capabilities the
host agent already has.

## Operating principles

1. **Read-only.** Investigation must not mutate the world: no test reruns, no
   `kubectl exec/delete/edit`, no database writes, no label flips. Remediation
   is proposed as next steps, never executed.
2. **Observe before explaining.** Establish what actually failed (jobs, tests,
   errors, timestamps) before looking for causes. Never jump from "the pipeline
   is red" to a root cause.
3. **Separate observation, hypothesis, and conclusion.** State each as such.
   A suspicious log line is an observation; what it implies is a hypothesis
   until validated.
4. **One defect can fail a hundred tests.** Never assume each failed test is
   an independent defect; look for the shared failure first.
5. **Seek disconfirming evidence.** Before declaring a root cause, actively
   look for evidence that contradicts it. Correlation in time is not causation.
6. **UNKNOWN is a valid result.** Report what is known, what is ruled out, and
   what evidence would settle it. Never manufacture certainty.
7. **Remote-first.** Work against the remote GitLab project through available
   capabilities. A local checkout is an optional accelerator (full-text search,
   git history, cross-file navigation), never a precondition.
8. **Don't re-ask what you already know.** Use every anchor the user provided
   and fill gaps yourself. Ask the user only when the investigation is truly
   blocked on information only they have.
9. **Adaptive depth.** Choose investigation paths based on evidence, not rote.
   Do not mechanically walk every path — but do not stop at the first
   suspicious signal either; ask whether the evidence on the table actually
   supports a root cause.

## Capabilities

Discover what is available in this host and proceed with what exists: Git
hosting (pipelines, jobs, MRs, commits, diffs, repository files), Kubernetes
(workload status, events, logs), code search (local checkout or remote),
shell, centralized logging. A missing capability becomes a Missing Evidence
item in the report, not an abort.

## Workflow

```
Establish Context → Inspect Failures → Cluster Failures →
Investigate → Form Hypotheses → Validate Hypotheses → Report
```

The phases are a protocol, not a script: move forward as soon as you have
enough to proceed, and revisit an earlier phase when new evidence demands it.

### 1. Establish Context

Confirm what this investigation is anchored to: project, MR (if any),
pipeline, failed jobs, commit, test suite, environment/namespace, approximate
failure time, relevant services, and pipeline type (MR pipeline / branch
pipeline / scheduled nightly — MR pipelines prioritize the MR's changes;
nightly pipelines prioritize environment drift and dependency changes).

Anchor resolution heuristics:

- MR only → its head pipeline
- Commit only → pipelines containing that commit (usually branch pipelines)
- Test name only → search that test across recent pipelines in the relevant
  time window
- Time window or symptoms only → recent failed pipelines in that window
- Pod / namespace only → map back to the project and its recent pipelines

Missing context must not block the investigation. Proceed as soon as you can
locate the pipeline, job, or failure.

### 2. Inspect Failures

Get structured failure data before reasoning about causes. Follow the priority
chain and per-source reading rules in
[references/failure-data-sources.md](references/failure-data-sources.md):
test report → job artifacts → job-trace parsing.

Record per failure: error message, exception, stack trace, failure timestamp,
setup/fixture vs assertion failure, timeout vs error vs dependency failure.
Distinguish test-level failures from job-level failures — if the job died
before running tests (image pull, OOMKill, runner error), there is no test
failure to analyze; investigate the job itself.

If structured data is unavailable, say so explicitly and degrade honestly. A
data-access blocker is itself a finding, not a reason to guess.

### 3. Cluster Failures

Guard the context window: never paste the full failure list before clustering.
Pre-aggregate by error signature / exception / suite into counts and
distributions; pick one representative failure per cluster for deep
investigation; page through the full list only to check coverage.

Clustering dimensions: same or similar error message, same exception, same
stack frame, same dependency, endpoint, fixture, or setup failure, close
failure timestamps, same service, same runtime error. Appearing in the same
pipeline is **not** a clustering reason by itself.

The goal is to turn "100 failed tests" into "Cluster A — 72, Cluster B — 21,
Cluster C — 7" and investigate representatives, not every test.

### 4. Investigate

Four directions. Choose by evidence, not by rote.

**Test investigation** — test implementation, fixtures, setup and cleanup,
test assumptions, test data, assertions, timing dependencies. Question: is the
failure consistent with a defect in the test itself?

**Code-change investigation** — MR/commit diff, changed modules, touched
execution paths, configuration and dependency changes. Question: *can* this
change explain the observed failure? A file being modified in the MR is a
lead, not a verdict.

**Runtime investigation** — workload and pod status, restarts, events,
application and dependency logs, deployment status, version mismatches,
resource anomalies — scoped to the failure time window. Look for a reliable
time-and-cause link between failure and runtime event. Respect the
log-retention and time-precision rules in
[references/failure-data-sources.md](references/failure-data-sources.md):
test-report timestamps are completion times; allow minute-scale slack; if
logs have rotated away, record Missing Evidence rather than concluding "no
errors found".

**Historical investigation** — first action, cheapest and most decisive: *did
the same test on the same commit pass in another pipeline or in a retry?*
Passing → strong evidence against a code regression (points to flaky /
environment / dependency). Failing further back in history → the problem
predates this change. Then: previous pipelines, historical failures, related
MRs and issues, known problems.

### 5. Form Hypotheses

For each cluster, form at most a few main hypotheses. Each hypothesis states:
proposed cause, supporting evidence, missing evidence, potential
contradiction, and what evidence would disprove it. Distinguish the cluster's
*observed failure* from *why it failed* — the hypothesis is only the latter.

### 6. Validate Hypotheses

Before naming a root cause: (1) gather supporting evidence, (2) actively look
for counter-evidence, (3) compare against alternative hypotheses, (4) separate
correlation from causation, (5) judge whether the evidence suffices. Declaring
a root cause off a single suspicious log line is forbidden. If validation
fails or evidence is insufficient, keep the uncertainty explicit.

Classify each cluster using the definitions and discriminators in
[references/failure-classification.md](references/failure-classification.md):
Application Regression / Test Defect / Flaky Test / Environment or
Infrastructure Issue / Dependency Failure / Test Data or State Issue /
Configuration or Version Mismatch / Unknown. Assign confidence HIGH / MEDIUM /
LOW — never pseudo-precise percentages.

### 7. Report

Produce the report per
[references/investigation-report.md](references/investigation-report.md):
summary header, one section per cluster (observed failure, classification,
likely cause, supporting and contradicting evidence, confidence, recommended
next step) — or the UNKNOWN layout when the root cause is not established.
Write the report in the user's language. Next steps must be concretely
actionable (targets, time windows, test names), never "check the logs".

## Follow-up investigations

This skill supports continuing an investigation, not just emitting one
report. Maintain a compact **Investigation State** as the conversation
progresses:

```
INVESTIGATION STATE
Context:     <project, pipeline/MR, commit, environment, failure window>
Clusters:    <id, signature, count, representative test>
Hypotheses:  <id, cluster, status: active|confirmed|refuted, key evidence>
Ruled out:   <what was ruled out, on what evidence>
Open items:  <missing evidence, suggested next checks>
```

Update it as evidence lands. When the user asks a follow-up ("why do you think
it's not MR !832?"), first re-anchor on this state, then gather the specific
new evidence the question demands — do not restart the investigation.
Conclusions are allowed to change as evidence arrives; state explicitly what
changed and why.

## References

- [failure-data-sources.md](references/failure-data-sources.md) — where
  failure data comes from, in what order, and how to read each source
- [failure-classification.md](references/failure-classification.md) — category
  definitions and how to tell the confusable ones apart
- [investigation-report.md](references/investigation-report.md) — report
  templates, evidence-citation norms, next-step writing rules
