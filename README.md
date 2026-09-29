# onetrace-ci-sample

A small worked example for [onetrace-ci](https://github.com/shamiksaharcciit-oss/onetrace-ci): a
two-stage `retrieve` → `answer` pipeline recorded with `onetrace`, a committed baseline run, and a
GitHub Actions workflow that regenerates a candidate run under five different scenarios and gates
it against that baseline.

## Layout

- `demo.py` — the pipeline itself. Takes an output directory, a run id, and a scenario name.
- `runs/baseline/` — a committed, real `onetrace` run (scenario `unchanged`), already verified.
- `.github/workflows/gate-demo.yml` — `workflow_dispatch`, parameterized by `scenario`.
- `requirements.lock` — pins `onetrace`/`onetrace-verify` by hash, same as `onetrace-ci` itself.
- `answering/`, `tests/`, `ci/` and `.github/workflows/discover-to-gate.yml` — the whole path, from
  discovery to a passing gate (below).

## Scenarios

Run from the Actions tab (`Run workflow`, pick a `scenario`), or locally:

```
pip install --require-hashes -r requirements.lock
python demo.py runs/candidate candidate-run <scenario>
printf 'format: onetrace-ci-plan/0.1\napproved_by: sample-repo-maintainer\n' > onetrace-plan.yaml
onetrace-ci gate --run runs/candidate --baseline runs/baseline \
  --plan onetrace-plan.yaml --out gate-out --review-exit 2
cat gate-out/summary.md
```

| scenario | what changes | gate verdict |
|---|---|---|
| `unchanged` | nothing | PASS (exit 0) |
| `corpus_change` | the retrieved passage's own text differs | REVIEW (exit 2) — `diff` names the first differing stage |
| `instrument_bump` | same output, `retrieve`'s instrument version differs | REVIEW (exit 2) — an instrument/config annotation, `diff` itself still identical |
| `deleted_artifact` | the answer stage's own artifact file is removed after the run | FAIL (exit 1) — `verify` catches the missing artifact, `diff` refuses |
| `missing_approved_by` | the plan carries no `approved_by` | FAIL (exit 1) — a gate against an unapproved plan proves nothing |

`deleted_artifact` and `missing_approved_by` both generate the `unchanged` run underneath and then
alter the artifact or the plan, since the scenario they demonstrate is about the gate's own checks,
not about `demo.py`'s pipeline logic.

## The whole path: from discovery to a passing gate

`answering/` is the same `retrieve` → `answer` pipeline, not yet instrumented, with a fixture test
in `tests/`. `.github/workflows/discover-to-gate.yml` runs the whole path on Python 3.10, 3.11 and
3.12:

1. `onetrace-ci discover` runs the fixture test, unchanged, and drafts a plan in which every field
   that carries meaning is a `DECIDE:` question.
2. `ci/decide.py` answers those questions from `ci/answers.json`. In a real project a person does
   this; here the answers are committed, so the path can run in CI. The stages stay as discovery
   drafted them, and a question left open is refused.
3. `onetrace-ci instrument` turns the plan into a patch, which is applied.
4. The patched pipeline runs once, and that run is proposed as the baseline. It runs again, and
   the gate compares the second run with the baseline: PASS.

onetrace-ci is checked out at one commit and installed from that commit's hash-pinned lock.

## What this does not claim

Same as `onetrace-ci` itself: the gate proves the candidate run's own records are internally
consistent and, where a baseline exists, comparable to it. It does not prove the pipeline's output
is correct.

## License

Copyright 2026 Shamik Saha. Licensed under Apache-2.0; see LICENSE.
