"""A small two-stage pipeline (retrieve, answer), built with onetrace's own
Recorder -- the same shape as the SDK's own quickstart. Takes a scenario
name so the sample repo's own CI workflow can produce each of the gate's
named proof cases from one script:

    unchanged        -- identical to the committed baseline
    corpus_change     -- the retrieved passage's own text differs
    instrument_bump   -- same output, a different instrument version
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from onetrace.emit import Instrument, Recorder

QUESTION = "What does the warranty cover?"

CORPUS = {
    "unchanged": [
        {"id": "p1", "text": "The warranty covers manufacturing defects for twelve months."},
        {"id": "p2", "text": "Shipping delays are handled by the logistics partner."},
    ],
    "corpus_change": [
        {"id": "p1", "text": "The warranty covers accidental damage for twenty-four months."},
        {"id": "p2", "text": "Shipping delays are handled by the logistics partner."},
    ],
}


def main(out_dir: str, run_id: str, scenario: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    corpus = CORPUS.get(scenario, CORPUS["unchanged"])
    corpus_path = out / "corpus.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")

    retrieve_version = "1.0.1" if scenario == "instrument_bump" else "1.0.0"

    rec = Recorder(out_dir, run_id=run_id, declared_stages=["retrieve", "answer"],
                   manifest=Path(__file__), policy="fail-closed")

    @rec.stage("retrieve", Instrument("word-overlap", "retriever", retrieve_version,
                                      {"top_k": "1"}))
    def retrieve(ctx):
        loaded = json.loads(ctx.read_external(corpus_path, "application/json",
                                              name="corpus", trust_class="operator-authored"))
        q = set(QUESTION.lower().split())
        best = max(loaded, key=lambda p: len(q & set(p["text"].lower().split())))
        ctx.constant("top_k", "1")
        ctx.assertion("candidate_count", str(len(loaded)))
        return ctx.write_json("retrieved.json", best)

    @rec.stage("answer", Instrument("extractive", "answerer", "1.0.0", {"method": "extractive"}))
    def answer(ctx, retrieved_artifact):
        hit = ctx.read_json(retrieved_artifact)
        ctx.constant("method", "extractive")
        ctx.assertion("source", hit["id"])
        return ctx.write_json("answer.json", {"answer": hit["text"], "cited": hit["id"]})

    answer(retrieve())
    rec.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "unchanged")
