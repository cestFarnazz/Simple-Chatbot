"""
Tests for progress/db.py

Run: python3 -m unittest tests.test_db -v
"""

import sys
import os
import unittest
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from progress.db import (
    init_db, record_attempt, get_topic_stats, get_struggling_topics,
    get_completed_topics, get_current_streak, get_dashboard_stats, _connect,
)
from grader.grading import GradeResult


def _make_result(passed, timed_out=False, user_error=None, not_auto_gradable=False):
    return GradeResult(
        passed=passed,
        user_stdout="",
        expected_stdout="",
        user_error=user_error,
        infra_error=None,
        timed_out=timed_out,
        not_auto_gradable=not_auto_gradable,
    )


def _insert_raw_attempt(db_path, topic, timestamp, passed=True, learner_id="local"):
    """Bypasses record_attempt's automatic 'now' timestamp, so streak tests
    can plant attempts on specific past days."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO attempts (learner_id, topic, timestamp, passed, timed_out, error_type, code_length)
            VALUES (?, ?, ?, ?, 0, NULL, 10)
            """,
            (learner_id, topic, timestamp, 1 if passed else 0),
        )


class TestProgressDB(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)  # init_db must be able to build it from scratch
        init_db(self.db_path)

    def tearDown(self):
        for ext in ("", "-wal", "-shm"):
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_init_db_is_idempotent(self):
        init_db(self.db_path)  # must not error if called again
        init_db(self.db_path)

    def test_record_and_read_back_single_attempt(self):
        record_attempt(self.db_path, "The for Loop", _make_result(passed=True), code_length=42)
        stats = get_topic_stats(self.db_path)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0].topic, "The for Loop")
        self.assertEqual(stats[0].total_attempts, 1)
        self.assertEqual(stats[0].pass_rate, 1.0)

    def test_pass_rate_calculated_correctly(self):
        for _ in range(3):
            record_attempt(self.db_path, "Conditionals", _make_result(passed=True), code_length=10)
        for _ in range(2):
            record_attempt(self.db_path, "Conditionals", _make_result(passed=False), code_length=10)

        stats = get_topic_stats(self.db_path)
        self.assertEqual(stats[0].total_attempts, 5)
        self.assertEqual(stats[0].passed_attempts, 3)
        self.assertAlmostEqual(stats[0].pass_rate, 0.6)

    def test_most_common_error_is_tracked(self):
        record_attempt(self.db_path, "Dictionaries", _make_result(False, user_error="KeyError: 'x'"), code_length=5)
        record_attempt(self.db_path, "Dictionaries", _make_result(False, user_error="KeyError: 'y'"), code_length=5)
        record_attempt(self.db_path, "Dictionaries", _make_result(False, user_error="TypeError: bad"), code_length=5)

        stats = get_topic_stats(self.db_path)
        self.assertEqual(stats[0].most_common_error, "KeyError")

    def test_not_auto_gradable_attempts_are_not_recorded(self):
        record_attempt(self.db_path, "Tkinter", _make_result(False, not_auto_gradable=True), code_length=5)
        stats = get_topic_stats(self.db_path)
        self.assertEqual(len(stats), 0)

    def test_struggling_topics_excludes_low_sample_size(self):
        # only 1 failed attempt — shouldn't be counted as the "hardest"
        record_attempt(self.db_path, "Beginner Topic", _make_result(passed=False), code_length=5)
        # 5 attempts, 4 failed — enough sample size and a low pass_rate
        for i in range(5):
            record_attempt(self.db_path, "Hard Topic", _make_result(passed=(i == 0)), code_length=5)

        struggling = get_struggling_topics(self.db_path, min_attempts=3)
        topics = [s.topic for s in struggling]
        self.assertIn("Hard Topic", topics)
        self.assertNotIn("Beginner Topic", topics)

    def test_learner_isolation(self):
        record_attempt(self.db_path, "Lists", _make_result(True), code_length=5, learner_id="alice")
        record_attempt(self.db_path, "Lists", _make_result(False), code_length=5, learner_id="bob")

        alice_stats = get_topic_stats(self.db_path, learner_id="alice")
        self.assertEqual(alice_stats[0].pass_rate, 1.0)

        bob_stats = get_topic_stats(self.db_path, learner_id="bob")
        self.assertEqual(bob_stats[0].pass_rate, 0.0)

    def test_completed_topics_requires_at_least_one_pass(self):
        record_attempt(self.db_path, "Operators", _make_result(False), code_length=5)
        record_attempt(self.db_path, "Strings", _make_result(True), code_length=5)
        completed = get_completed_topics(self.db_path)
        self.assertNotIn("Operators", completed)
        self.assertIn("Strings", completed)

    def test_streak_is_zero_with_no_attempts(self):
        self.assertEqual(get_current_streak(self.db_path), 0)

    def test_streak_is_one_for_a_single_attempt_today(self):
        now = datetime.now(timezone.utc)
        _insert_raw_attempt(self.db_path, "Recursion", now.isoformat())
        self.assertEqual(get_current_streak(self.db_path), 1)

    def test_streak_counts_consecutive_days_ending_today(self):
        today = datetime.now(timezone.utc)
        for days_ago in (0, 1, 2):
            ts = (today - timedelta(days=days_ago)).isoformat()
            _insert_raw_attempt(self.db_path, "Recursion", ts)
        self.assertEqual(get_current_streak(self.db_path), 3)

    def test_streak_still_counts_if_last_attempt_was_yesterday(self):
        # hasn't practiced yet today, but yesterday's streak shouldn't reset to 0 yet
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        _insert_raw_attempt(self.db_path, "Recursion", yesterday.isoformat())
        self.assertEqual(get_current_streak(self.db_path), 1)

    def test_streak_resets_after_a_gap(self):
        today = datetime.now(timezone.utc)
        _insert_raw_attempt(self.db_path, "Recursion", today.isoformat())
        _insert_raw_attempt(self.db_path, "Recursion", (today - timedelta(days=5)).isoformat())
        # a 5-day gap breaks the streak; only today's attempt should count
        self.assertEqual(get_current_streak(self.db_path), 1)

    def test_streak_is_zero_if_last_attempt_was_two_days_ago(self):
        two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
        _insert_raw_attempt(self.db_path, "Recursion", two_days_ago.isoformat())
        self.assertEqual(get_current_streak(self.db_path), 0)

    def test_dashboard_stats_aggregates_everything_correctly(self):
        mock_lessons = {
            "A": {"level": "Beginner"},
            "B": {"level": "Beginner"},
            "C": {"level": "Intermediate"},
        }
        record_attempt(self.db_path, "A", _make_result(True), code_length=5)
        record_attempt(self.db_path, "A", _make_result(False), code_length=5)
        record_attempt(self.db_path, "B", _make_result(False), code_length=5)

        stats = get_dashboard_stats(self.db_path, mock_lessons)

        self.assertEqual(stats["level_progress"]["Beginner"], (2, 1))  # 2 total, 1 completed (A)
        self.assertEqual(stats["level_progress"]["Intermediate"], (1, 0))
        self.assertEqual(stats["lessons_completed"], 1)
        self.assertEqual(stats["total_lessons"], 3)
        self.assertAlmostEqual(stats["overall_percent"], 1 / 3 * 100)
        self.assertEqual(stats["exercises_solved"], 1)  # only one passing attempt total
        self.assertAlmostEqual(stats["correct_percent"], 1 / 3 * 100)  # 1 passed out of 3 attempts
        self.assertEqual(stats["day_streak"], 1)  # attempts were just recorded "now"


if __name__ == "__main__":
    unittest.main()
