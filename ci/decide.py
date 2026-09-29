"""Stand in for the person who answers a discovered draft's DECIDE: questions.

    python ci/decide.py DRAFT ANSWERS PLAN

In a real project a person answers the questions in `onetrace-plan.draft.yaml`. Here the answers
are committed, in `ci/answers.json`, so the whole path from discovery to a passing gate can run in
CI. The stages, their order and their functions stay as discovery drafted them. An answer may
answer a question or correct a field the draft holds, never add a stage or a field the draft does
not have. Refused if a question is left open, so no draft reaches `instrument` half decided.
"""
from __future__ import annotations

import json
import sys

from onetrace_ci.plan import find_open_questions, read_document


def _scalar(value) -> str:
    if value is None:
        return "null"
    if value is True or value is False:
        return "true" if value else "false"
    return json.dumps(value, ensure_ascii=False)


def _value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_scalar(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {_scalar(v)}" for k, v in value.items()) + "}"
    return _scalar(value)


def render(plan: dict) -> str:
    lines = ["# Decided from the discovered draft, with the answers in ci/answers.json."]
    for key, value in plan.items():
        if key == "stages":
            lines.append("stages:")
            for stage in value:
                for i, (field, v) in enumerate(stage.items()):
                    lines.append(f"{'  - ' if i == 0 else '    '}{field}: {_value(v)}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            lines += [f"  {field}: {_value(v)}" for field, v in value.items()]
        else:
            lines.append(f"{key}: {_value(value)}")
    return "\n".join(lines) + "\n"


def decide(draft: dict, answers: dict) -> tuple[dict, list[str]]:
    problems = []
    plan = dict(draft)
    for key, answer in answers.items():
        if key == "stages":
            continue
        if key not in draft:
            problems.append(f"{key}: the draft has no such field")
        elif answer is None:
            del plan[key]
        else:
            plan[key] = answer
    drafted = [s["name"] for s in draft["stages"]]
    for name in answers.get("stages", {}):
        if name not in drafted:
            problems.append(f"stages: discovery drafted no stage named {name!r}")
    stages = []
    for stage in draft["stages"]:
        stage = dict(stage)
        for field, answer in answers.get("stages", {}).get(stage["name"], {}).items():
            if field not in stage:
                problems.append(f"stages[{stage['name']}].{field}: the draft has no such field")
            elif answer is None:
                del stage[field]
            else:
                stage[field] = answer
        stages.append(stage)
    plan["stages"] = stages
    return plan, problems


def main(argv: list[str]) -> int:
    draft_path, answers_path, plan_path = argv
    with open(draft_path, encoding="utf-8") as f:
        draft = read_document(f.read(), source=draft_path)
    with open(answers_path, encoding="utf-8") as f:
        answers = json.load(f)
    plan, problems = decide(draft, answers)
    text = render(plan)
    problems += [f"{path}: still an open question" for path, _ in
                 find_open_questions(read_document(text, source=plan_path))]
    if problems:
        print("decide: refused:", *problems, sep="\n  ", file=sys.stderr)
        return 1
    with open(plan_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"decide: wrote {plan_path}; stages as discovered: {[s['name'] for s in plan['stages']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
