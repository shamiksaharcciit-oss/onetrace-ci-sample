"""One run of the answering pipeline: read the question, retrieve a passage, answer from it."""
from pathlib import Path

from answering.answer import answer
from answering.retrieve import retrieve

QUESTION_FILE = Path(__file__).resolve().parents[1] / "data" / "question.txt"


def run():
    """Answer the fixture question from the fixture corpus."""
    question = QUESTION_FILE.read_text(encoding="utf-8").strip()
    passage = retrieve(question)
    return answer(question, passage)
