"""
Tests for the grading module.

Run: python3 -m unittest tests.test_grading -v
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grader.grading import grade_submission, normalize_output, clear_reference_cache


MOCK_LESSONS = {
    "sum_topic": {
        "answer": "total = 0\nfor i in range(1, 6):\n    total += i\nprint(total)",
    },
    "broken_reference": {
        "answer": "print(undefined_variable)",  # deliberately broken, to test the lesson-content error path
    },
    "timing_topic": {
        "answer": "import time\nstart=time.time()\nprint('elapsed:', time.time()-start)",
        "mask_patterns": [r"elapsed: [0-9.eE+-]+"],
    },
    "gui_topic": {
        "answer": "import tkinter\nroot = tkinter.Tk()\nroot.mainloop()",
        "auto_gradable": False,
    },
}


class TestNormalizeOutput(unittest.TestCase):
    def test_strips_trailing_whitespace_per_line(self):
        self.assertEqual(normalize_output("hello   \nworld\t\n"), "hello\nworld")

    def test_strips_trailing_blank_lines(self):
        self.assertEqual(normalize_output("a\nb\n\n\n"), "a\nb")

    def test_preserves_meaningful_blank_lines_in_middle(self):
        self.assertEqual(normalize_output("a\n\nb"), "a\n\nb")


class TestGradeSubmission(unittest.TestCase):
    def setUp(self):
        clear_reference_cache()

    def test_semantically_equivalent_but_textually_different_code_passes(self):
        # this is exactly the scenario the old string-based grading used to reject
        user_code = "s=0\nfor x in range(1,6):s+=x\nprint(s)"
        result = grade_submission("sum_topic", user_code, MOCK_LESSONS)
        self.assertTrue(result.passed)

    def test_wrong_output_fails_with_diff_hint(self):
        user_code = "print(999)"
        result = grade_submission("sum_topic", user_code, MOCK_LESSONS)
        self.assertFalse(result.passed)
        self.assertIsNotNone(result.diff_hint)
        self.assertIn("999", result.diff_hint)

    def test_syntax_error_reported_as_user_error_not_infra_error(self):
        user_code = "def f(:\n  pass"
        result = grade_submission("sum_topic", user_code, MOCK_LESSONS)
        self.assertFalse(result.passed)
        self.assertIsNone(result.infra_error)
        self.assertIn("SyntaxError", result.user_error)

    def test_temp_file_path_not_leaked_in_error(self):
        user_code = "raise ValueError('boom')"
        result = grade_submission("sum_topic", user_code, MOCK_LESSONS)
        self.assertNotIn("/tmp/", result.user_error)
        self.assertNotIn(".py", result.user_error.split("<submission>")[0])

    def test_broken_reference_answer_reported_as_infra_error_not_student_fault(self):
        result = grade_submission("broken_reference", "print(1)", MOCK_LESSONS)
        self.assertFalse(result.passed)
        self.assertIsNotNone(result.infra_error)
        self.assertIn("broken_reference", result.infra_error)

    def test_reference_output_is_cached(self):
        from grader import grading
        grade_submission("sum_topic", "print(15)", MOCK_LESSONS)
        self.assertIn("sum_topic", grading._reference_output_cache)

    def test_masked_nondeterministic_output_still_passes(self):
        # a second run of the reference answer itself; the printed time
        # differs, but with mask_patterns it should still pass
        user_code = "import time\nstart=time.time()\nprint('elapsed:', time.time()-start+0.5)"
        result = grade_submission("timing_topic", user_code, MOCK_LESSONS)
        self.assertTrue(result.passed)

    def test_gui_exercise_is_flagged_not_auto_gradable(self):
        result = grade_submission("gui_topic", "anything", MOCK_LESSONS)
        self.assertTrue(result.not_auto_gradable)
        self.assertFalse(result.passed)
        self.assertIsNone(result.infra_error)  # this isn't a real error, it's a design limitation


class TestRealLessonsIntegration(unittest.TestCase):
    """
    These tests run against the real content of lessons.py — not a mock.
    Extra benefit: if one of lessons.py's answers is ever accidentally
    broken (e.g. while editing content), this test catches it immediately,
    before it reaches a student.
    """

    @classmethod
    def setUpClass(cls):
        from lessons import lessons
        cls.lessons = lessons

    def setUp(self):
        clear_reference_cache()

    def test_every_reference_answer_actually_runs(self):
        failures = []
        for topic in self.lessons:
            result = grade_submission(topic, self.lessons[topic]["answer"], self.lessons)
            if result.infra_error is not None:
                failures.append((topic, result.infra_error))
        self.assertEqual(
            failures, [],
            f"These answers in lessons.py don't run on their own: {failures}"
        )

    def test_submitting_the_exact_reference_answer_always_passes(self):
        # sanity check: if a student submits exactly the reference answer, it should pass
        # (except for auto_gradable=False exercises, which aren't meant to be checked at all)
        failures = []
        for topic in self.lessons:
            if not self.lessons[topic].get("auto_gradable", True):
                continue
            result = grade_submission(topic, self.lessons[topic]["answer"], self.lessons)
            if not result.passed and result.infra_error is None:
                failures.append(topic)
        self.assertEqual(failures, [], f"The reference answer itself wasn't accepted for: {failures}")


if __name__ == "__main__":
    unittest.main()
