# Investigation Report

Output norms for the final report and for follow-up answers. Write in the
user's language; keep the structure below.

## Evidence citation norms

- Every evidence bullet carries a **source pointer**: pipeline/job id, MR diff
  file, pod and event name, log line excerpt — enough for an engineer to find
  it again.
- Attach timestamps when available, and name the clock they come from (CI
  runner vs cluster).
- Mark each item as **direct evidence** (the thing itself was observed) or
  **inference** (concluded from other observations). Never present an
  inference as an observation.

## Full report template

```markdown
## Summary

Project:
MR:                    (or "none")
Pipeline:
Pipeline type:         MR / branch / nightly
Failed jobs:
Failed tests:          <total count>
Failure clusters:      <count and one-line signatures>

## Cluster 1: <short signature>

Affected tests:        <count; representative names; full list on request>

Observed failure:      <the error as seen, quoted — observation, not explanation>

Classification:        <category from failure-classification.md>

Likely cause:          <one or two sentences>

Supporting evidence:
- <source pointer + timestamp — direct/inference>
- ...

Contradicting evidence / open risks:
- ...                                   (state "none found" if actively searched)

Confidence:            HIGH / MEDIUM / LOW

Recommended next step: <concretely executable action>

## Cluster 2
...
```

If the root cause of a cluster is not established, replace its
Classification/Likely cause block with the UNKNOWN layout:

```markdown
Conclusion: UNKNOWN

What is known:
- ...

What has been ruled out:
- <what> — <on what evidence>

Most likely remaining hypotheses:
- <hypothesis> — <what evidence would confirm or refute it>

Recommended next evidence:
- ...
```

## Confidence scale

- **HIGH** — direct evidence exists, or multiple independent lines of
  evidence agree, and no credible counter-evidence was found.
- **MEDIUM** — evidence is strongly consistent with the explanation, but a
  key verification is still missing.
- **LOW** — limited signals; the conclusion is essentially a hypothesis
  pending validation.
- **UNKNOWN** — evidence is insufficient. Legal and sometimes the right
  answer.

Never attach pseudo-precise probabilities (87%, 92%). They cannot be
calibrated and mislead the reader.

## Recommended next-step rules

A next step is written for an engineer who will execute it without redoing
the investigation. It names targets, time windows, and comparison points.

Bad:  "Check the logs."
Bad:  "Investigate the Redis issue."
Good: "Compare the `order-engine` logs between 10:31:10–10:31:20 with the
       Redis pod restart event at 10:31:12, then rerun the cancel-order test
       group and check whether failures follow the restart."
Good: "Run pipeline's test report for the parent commit (pipeline 18344) and
       confirm whether `test_cancel_order` passed there; if it did, rerun
       this pipeline's job to test for flakiness."

Typical next steps: rerun one test case or one cluster, pull logs for a named
time window, verify a named dependency's health, diff a specific code path,
compare against a named successful pipeline, fix a suspected fixture.

## Follow-up answers

When the user challenges or extends a conclusion ("why do you think it's not
MR !832?"):

1. Re-anchor on the Investigation State; restate the hypothesis being
   challenged.
2. Present the evidence that led to its current status, separating direct
   evidence from inference.
3. Gather any *new* evidence the question specifically demands — do not
   restate the old report as an answer.
4. If the conclusion changes, say what changed and why. Updating a
   conclusion on new evidence is correct behavior, not inconsistency.
