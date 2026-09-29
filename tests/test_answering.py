"""The fixture: the answering pipeline answers the fixture question from the fixture corpus.

`onetrace-ci discover` runs this test, unchanged, to see what the pipeline does."""
import unittest

from answering.main import run


class AnsweringTest(unittest.TestCase):
    def test_the_fixture_question_is_answered_from_the_corpus(self):
        result = run()
        self.assertTrue(result["answer"])
        self.assertTrue(result["cited"])


if __name__ == "__main__":
    unittest.main()
