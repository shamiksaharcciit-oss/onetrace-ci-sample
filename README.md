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

## The instrumented scenario: from a plan to a passing gate

The `answering/` pipeline shows `onetrace-ci instrument` end to end. Each step is its own commit,
so the history reads as the walkthrough:

1. **An un-instrumented pipeline.** `answering/` (retrieve, then answer), with a fixture question
   and corpus in `data/`, and no onetrace calls at all. It is a small package (`pyproject.toml`),
   so each stage's instrument version is read from its installed metadata.
2. **The plan.** `onetrace-instrument-plan.yaml`: the entry function, the stages in order, the
   files the first stage reads and how far they are trusted, whether each stage can be
   re-derived, the approved boundaries, and how CI installs and runs the pipeline.
3. **The patch.** `instrument.patch`, exactly as
   `onetrace-ci instrument --plan onetrace-instrument-plan.yaml --repo . --out instrument.patch`
   wrote it, so it can be reviewed before it is applied.
4. **The patch, applied.** `git apply instrument.patch` changes `answering/main.py` only (one
   `Recorder` per run, each stage recorded) and adds `.github/workflows/onetrace.yml`.
5. **The baseline.** One run of the instrumented pipeline, proposed with
   `onetrace-ci baseline propose` and committed as `runs/instrumented-baseline/`.

From then on, every push runs `.github/workflows/onetrace.yml`: it installs and runs the pipeline,
then runs the `onetrace-ci gate` against the committed baseline. Unchanged, it passes; change the
corpus and it asks for review at `retrieve`.

**The patch records what the plan names; it does not find stages the plan didn't list.**

## What this does not claim

Same as `onetrace-ci` itself: the gate proves the candidate run's own records are internally
consistent and, where a baseline exists, comparable to it. It does not prove the pipeline's output
is correct.

## License

Copyright 2026 Shamik Saha. Licensed under Apache-2.0; see LICENSE.
