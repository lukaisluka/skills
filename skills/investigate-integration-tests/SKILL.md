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

Investigate integration-test failures on a remote GitLab project and report
evidence-backed conclusions, including UNKNOWN when the evidence runs out.
Use whatever Git-hosting, Kubernetes, code-search, log, and shell capabilities
the host actually has — this skill never names tools. A missing capability is
recorded as Missing Evidence; it never aborts the investigation.

## Hard rules

Cross-phase invariants. Violations are detectable.

1. **Read-only.** No test reruns, no `kubectl exec/delete/edit`, no database
   writes, no label or config changes. Remediation is output as a recommended
   next step, never executed.
2. **Label every claim** as observation, hypothesis, or conclusion. Never
   present an inference as an observation.
3. **Absent evidence is not negative evidence.** Rotated-away logs, missing
   reports, and empty search results are recorded as Missing Evidence — never
   as "no errors found".
4. **Confidence is HIGH / MEDIUM / LOW / UNKNOWN only.** Never numeric
   probabilities.
5. **Use every anchor the user gave.** Fill gaps yourself (step 1.2). Ask the
   user only when blocked on information only they can supply.

## Flow

```
1 ESTABLISH CONTEXT
      ↓
2 GET FAILURE DATA      ──E1: job died before tests ran──► 7 REPORT (job cause)
      ↓
3 CLUSTER               ──E2: single named test──► one cluster of one
      ↓
4 ROUTE EACH CLUSTER    (condition table → paths H / C / R / T)
      ↓
5 HYPOTHESES            (five mandatory fields per hypothesis)
      ↓
6 JUDGMENT POINT        ──fails──► back to 4 with the open question,
      ↓                       or conclude UNKNOWN for that cluster
7 REPORT                (template in references/investigation-report.md)
```

**Early-exit gates fire only on direct evidence, never on a plausible story.**

- **E1 (after step 2):** the job failed before tests ran — image pull error,
  OOMKill, runner failure, manual cancellation. Skip 3–6, investigate the job
  itself, report.
- **E2 (at step 3):** the user asked about one named test. It is a single
  cluster of one; route it directly.

## 1 Establish Context

1.1 List the anchors the user gave: project, MR, pipeline, job, commit, test,
suite, namespace, pod, time range, error text, free description.

1.2 Resolve missing anchors:

| You only have | Resolve via |
| --- | --- |
| MR | its head pipeline |
| Commit | pipelines containing it (usually branch pipelines) |
| Test name | that test across recent pipelines in the time window |
| Time window / symptoms | recent failed pipelines in that window |
| Pod / namespace | the owning project and its recent pipelines |

1.3 Record: project, MR, pipeline, **pipeline type** (MR / branch / nightly),
failed jobs, commit, environment, failure window, services involved.

1.4 Routing prior by pipeline type — MR pipeline: code-change path first;
nightly: runtime and dependency paths first.

1.5 Proceed as soon as the pipeline, job, or failure is located. Missing
context is not a blocker.

## 2 Get Failure Data

2.1 Try sources in this order; stop at the first with case-level detail.
Per-source reading rules:
[references/failure-data-sources.md](references/failure-data-sources.md).

| Order | Source | Yields |
| --- | --- | --- |
| 1 | Pipeline / job test report | per-case status, error, stack, duration |
| 2 | Job artifacts (JUnit XML, Allure, HTML) | the same, from files |
| 3 | Job trace parsing | summary block first, then per-test error blocks |

2.2 Record per failure: error message, exception, stack trace,
setup/fixture vs assertion failure, timeout vs error vs dependency error, and
the **failure window** `[completion − duration, completion]` — report
timestamps are completion times, not occurrence times.

2.3 No source yields case-level data → the blocker itself is a finding:
record what was tried, what would unblock it, and degrade honestly. Do not
guess.

## 3 Cluster

One defect can fail a hundred tests. Cluster before investigating
individuals.

3.1 Aggregate before reading: group by error signature / exception / suite
into counts and distributions. Never paste the full failure list into context
before this step.

3.2 Cluster on: same or similar error message · same exception · same stack
frame · same dependency / endpoint / fixture / setup failure · close failure
windows · same service / runtime error. **Appearing in the same pipeline is
not clustering grounds.**

3.3 One representative per cluster goes to deep investigation; consult the
full list only to check coverage.

3.4 Output the reduction: `N failed tests → A (n₁) · B (n₂) · C (n₃)`.

## 4 Route Each Cluster

Cheapest decisive signal first. Run only the paths whose condition fires. A
cluster whose cause is already established by direct evidence runs no further
paths.

| IF (observable) | THEN route to |
| --- | --- |
| Same test, same commit passed in another pipeline or retry | Not a regression → quick discriminators in [failure-classification.md](references/failure-classification.md) |
| Failures cross suites/services and align with an infra event window | R Runtime |
| Error signature names a dependency (refused / reset / timeout to X) | R Runtime, dependency first |
| One test fails deterministically only in this MR's pipeline | C Code change |
| Failure references specific records / IDs or depends on execution order | T Test (data / state) |
| Deployed version or config differs from the pipeline's commit | R Runtime (version / config) |
| Nothing fires | H first, then per the pipeline-type prior (1.4) |

Each path fixes the question and the exit condition. How you search is free.

**H — Historical (API-only, cheapest)**
Question: has this failure been seen before, and does the same code pass
elsewhere?
- H1: same test on same commit elsewhere — passed ⇒ record "not a
  regression" and route per the discriminators; failed further back in
  history ⇒ the problem predates this change.
- H2: search previous pipelines, MRs, and issues for the error signature.
Exit: history stated with pointers, or "no history found" recorded.

**C — Code change**
Question: can this diff explain **this exact observed error** through a named
execution path (diff → path → error)?
Exit: the named path, or "no plausible path" recorded as evidence against
regression. A file modified in the MR is a lead until the path is named —
never a cause by itself. How to read and search the code is free (a local
checkout, if present, is an accelerator, never a requirement).

**R — Runtime**
Question: is there a runtime event inside the failure window with a reliable
time-and-cause link to the failures?
Exit: event + window correlation + causal mechanism, or "no correlation"
recorded. Gotchas: pod restarts wipe `kubectl logs` → Missing Evidence, fall
back to events / centralized logs / artifacts; allow minute-scale slack when
aligning windows (a 40-second mismatch proves nothing); CI-runner and cluster
clocks are not synchronized.

**T — Test**
Question: is the failure consistent with a defect in the test itself —
assertion, fixture, assumption, test data, timing dependence?
Exit: the specific defect named, or "not consistent with a test defect".

## 5 Hypotheses

Per cluster, at most a few main hypotheses. All five fields are mandatory —
a field you cannot fill means the hypothesis is too vague: rewrite it before
proceeding.

```
Hypothesis:           <proposed cause>
Supporting evidence:  <observations, labeled as such>
Missing evidence:     <what is not yet known>
Contradiction risk:   <what could refute it>
Disproof observation: <one observation that would differ if this were false>
```

## 6 Judgment Point: Validate

The weighing is judgment; the outputs are mandatory. Freedom lives here and
only here.

- [ ] The disproof observation from step 5 is **named and actually checked**.
      If none can be named, confidence for that cluster is capped at LOW.
- [ ] Counter-evidence was actively searched — state where you looked;
      "none found" without a search does not count.
- [ ] Alternatives were compared — state why the main hypothesis wins.
- [ ] Time overlap is distinguished from causation — name the mechanism, not
      just the window overlap.

All pass → classify per
[failure-classification.md](references/failure-classification.md) and set
confidence by its HIGH / MEDIUM / LOW definitions. Any fail → back to step 4
with the open question, or conclude UNKNOWN for that cluster.

## 7 Report

Produce the report per
[references/investigation-report.md](references/investigation-report.md):
summary header, one section per cluster, UNKNOWN layout wherever the root
cause is not established. Next steps must name targets, time windows, and
test names — never "check the logs". Write in the user's language.

## Follow-up investigations

Maintain this state and update it at every phase boundary:

```
INVESTIGATION STATE
Context:     <project, pipeline/MR, commit, environment, failure window>
Clusters:    <id, signature, count, representative>
Hypotheses:  <id, cluster, status: active|confirmed|refuted, key evidence>
Ruled out:   <what, on what evidence>
Open items:  <missing evidence, next checks>
```

A follow-up question ("why do you think it's not MR !832?") re-anchors on
this state first, then gathers only the new evidence it demands — it never
restarts the investigation. Conclusions may change on new evidence; state
what changed and why.

## References

- [failure-data-sources.md](references/failure-data-sources.md) — per-source
  reading rules: test reports, artifacts, trace parsing, log retention, time
  precision
- [failure-classification.md](references/failure-classification.md) —
  category definitions and quick discriminators
- [investigation-report.md](references/investigation-report.md) — report
  templates, evidence-citation norms, next-step writing rules
