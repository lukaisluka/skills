# Failure Classification

Classification is per cluster, not per pipeline: different clusters in one
investigation may land in different categories, and one cluster carries a
primary classification plus optional secondary notes. Every classification
cites evidence — a category without evidence is a guess.

## Categories

### Application Regression

New code change breaks behavior the tests correctly expect.

- Typical evidence: failures appear with a specific commit/MR and reproduce
  across runs of the same commit; the diff touches an execution path that
  plausibly explains the exact error; parent commit or other pipelines on the
  same code pass.
- Key discriminator: can the diff's execution path explain the *specific*
  observed error, not just the same general area?
- Common confusion: a **Test Defect** exposed for the first time by unrelated
  changes. Resolve by checking whether the old behavior was actually intended
  (MR description, linked issue, spec).

### Test Defect

The test itself is wrong: bad assertion, stale expectation, fragile fixture,
invalid assumption.

- Typical evidence: the assertion contradicts current *intended* behavior
  (often because behavior changed deliberately without updating the test);
  fixture violates documented preconditions; test misuses an API.
- Key discriminator: which side is wrong relative to intended behavior — the
  code or the test? Intended behavior lives in the MR description, issue,
  spec, or maintainers' statements, not in the test itself.
- Common confusion: Application Regression. Same failure surface, opposite
  fix.

### Flaky Test

The test is nondeterministic: identical code passes and fails.

- Typical evidence: same test on the same commit both passes and fails across
  pipelines or retries; failure times scatter; classic patterns — sleeps and
  timing assumptions, ordering dependence, shared mutable state, concurrency,
  time-of-day or random-data dependence.
- Key discriminator: the pass/fail flip **on identical code**. That single
  check is the first historical query to run.
- Common confusion: an intermittent **Environment Issue** masquerading as
  flakiness. If the environment hiccups, affected tests also flip. Check
  whether *other, unrelated* tests degraded in the same windows; if yes,
  suspect the environment, not the test.

### Environment / Infrastructure Issue

The test environment itself is broken: platform-level fault affecting
whatever ran in the window.

- Typical evidence: pod restarts, crash loops, OOM kills, node or storage
  problems, service outages in the failure window; many unrelated tests
  across suites/services fail in the same window; failures align in time with
  infrastructure events.
- Key discriminator: failures cross service and suite boundaries and time-
  correlate with an infra event.
- Common confusion: Dependency Failure. A broken dependency hosted inside the
  test environment blurs the line; classify by the failing layer (see below).

### Dependency Failure

A specific external system the tests rely on misbehaves: database, cache,
message broker, third-party API, identity provider.

- Typical evidence: connection refused / reset / timeout errors with the
  dependency's name; dependency-specific exceptions (auth failures, protocol
  errors); the dependency's own pods/logs show anomalies in the window.
- Key discriminator: the failing layer is a specific dependency, not the
  platform. If half the platform is down, that is an Environment Issue; if
  one broker is rejecting connections while everything else is healthy, that
  is a Dependency Failure.

### Test Data / State Issue

Corrupt, missing, or colliding test data or leftover state.

- Typical evidence: failures reference specific records or IDs; assertions
  fail on data shape/content rather than behavior; reruns on clean data pass;
  unique-constraint or not-found errors on seeded entities; failures depend
  on execution order or on residue from an earlier run.
- Key discriminator: the code and environment are healthy; the *data* the
  test found (or left behind) is the anomaly.
- Common confusion: Flaky Test (state collisions look nondeterministic).
  Resolve by checking whether the flip correlates with a specific data
  condition rather than timing.

### Configuration / Version Mismatch

Deployed config or version differs from what the code expects: image skew,
wrong env vars, feature flags, replica/config drift between environments.

- Typical evidence: deployed image/version does not match the pipeline's
  commit; the same test passes in one environment and fails in another;
  deployment or config-change events near the failure window; errors that
  only make sense if an old/new code path is active.
- Key discriminator: a *difference between environments or deploys* explains
  the failure that neither the code nor the environment alone does.
- Common confusion: Dependency Failure and Environment Issue. Ask "what
  exactly is deployed in the test environment right now, and does it match
  what this pipeline assumed?"

### Unknown

A legitimate result when the evidence is insufficient. Always pair it with:
what is known, what has been ruled out, the most likely remaining hypotheses,
and the next evidence that would settle it. An honest UNKNOWN with a sharp
next step is more valuable than a confident wrong answer.

## Quick discriminators

- Same commit, different outcome → not an Application Regression; branch to
  Flaky / Environment / Dependency / Data.
- Only this MR's pipeline fails, deterministically → look at the diff first.
- Many unrelated suites fail together → shared cause: environment,
  dependency, or platform.
- Failure moves with a specific record/ID → Test Data / State.
- Failure moves with a specific deploy/config change → Configuration /
  Version Mismatch.
