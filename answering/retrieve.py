"""Retrieve the passage that shares the most words with the question."""
import json
from pathlib import Path

CORPUS_FILE = Path(__file__).resolve().parents[1] / "data" / "corpus.json"


def retrieve(question):
    corpus = json.loads(CORPUS_FILE.read_text(encoding="utf-8"))
    words = set(question.lower().split())
    return max(corpus, key=lambda p: len(words & set(p["text"].lower().split())))
