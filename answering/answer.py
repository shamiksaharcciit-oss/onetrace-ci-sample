"""Answer extractively: the retrieved passage is the answer, and it is cited."""


def answer(question, passage):
    return {"answer": passage["text"], "cited": passage["id"], "question": question}
