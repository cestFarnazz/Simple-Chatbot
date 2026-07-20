"""
progress/db.py — tracking student attempts with SQLite

Design decisions:

1) Why does learner_id exist already, even though the app is currently
   single-user?
   Adding this column costs almost nothing now, but makes a future
   migration possible without a schema change (if multiple people ever use
   one install, or we sync progress). The default value "local" is used
   for the current single user.

2) Why isn't the student's full code stored?
   Storing the full code of every attempt could incidentally include
   sensitive data (if the student pastes something in), and it isn't
   needed for "which exercises are hardest" stats anyway. Only the code's
   length and whether it passed/failed/timed out/error_type are stored. If
   seeing the actual code for debugging is ever needed, that can be added
   later as an opt-in feature with the user's consent.

3) Why WAL mode?
   A single-user PyQt desktop app is usually single-threaded, but WAL
   makes concurrent reads/writes safer, and if the UI later runs on a
   separate QThread (recommended to avoid freezing the UI while the
   sandbox runs), it prevents the database from locking up.

4) Extracting error_type from the traceback:
   Only the exception class name (like ValueError, SyntaxError) is kept,
   not the whole error message — because that's what's useful for
   "which error type is most common in this exercise", without keeping
   message details that could be long or messy.
"""

from __future__ import annotations

import sqlite3
import re
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DEFAULT_LEARNER_ID = "local"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learner_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    timestamp TEXT NOT NULL,       -- ISO 8601 UTC
    passed INTEGER NOT NULL,       -- 0/1
    timed_out INTEGER NOT NULL,    -- 0/1
    error_type TEXT,               -- e.g. 'ValueError', or NULL if there was no error
    code_length INTEGER NOT NULL   -- length of the submitted code, not the code itself
);

CREATE INDEX IF NOT EXISTS idx_attempts_topic ON attempts(topic);
CREATE INDEX IF NOT EXISTS idx_attempts_learner ON attempts(learner_id);
"""


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Creates the tables if they don't exist. Safe to call multiple times."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def _extract_error_type(user_error: str | None) -> str | None:
    """Extracts just the exception class name from a sanitized traceback."""
    if not user_error:
        return None
    # The last line of a traceback is usually of the form 'ExceptionName: message'
    match = re.search(r"^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Warning))\b",
                       user_error.strip().splitlines()[-1] if user_error.strip() else "")
    return match.group(1) if match else None


def record_attempt(
    db_path: str,
    topic: str,
    grade_result,          # grader.grading.GradeResult
    code_length: int,
    learner_id: str = DEFAULT_LEARNER_ID,
) -> None:
    """Records one attempt. Nothing is recorded for auto_gradable=False exercises."""
    if grade_result.not_auto_gradable:
        return  # we don't store statistics that wouldn't mean anything

    error_type = _extract_error_type(grade_result.user_error)

    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO attempts (learner_id, topic, timestamp, passed, timed_out, error_type, code_length)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                learner_id,
                topic,
                datetime.now(timezone.utc).isoformat(),
                1 if grade_result.passed else 0,
                1 if grade_result.timed_out else 0,
                error_type,
                code_length,
            ),
        )


@dataclass
class TopicStats:
    topic: str
    total_attempts: int
    passed_attempts: int
    pass_rate: float
    most_common_error: str | None


def get_topic_stats(db_path: str, learner_id: str = DEFAULT_LEARNER_ID) -> list[TopicStats]:
    """Returns stats for each topic, sorted by the highest number of attempts."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT topic,
                   COUNT(*) AS total,
                   SUM(passed) AS passed_count
            FROM attempts
            WHERE learner_id = ?
            GROUP BY topic
            ORDER BY total DESC
            """,
            (learner_id,),
        ).fetchall()

        stats = []
        for topic, total, passed_count in rows:
            error_row = conn.execute(
                """
                SELECT error_type, COUNT(*) as cnt
                FROM attempts
                WHERE learner_id = ? AND topic = ? AND error_type IS NOT NULL
                GROUP BY error_type
                ORDER BY cnt DESC
                LIMIT 1
                """,
                (learner_id, topic),
            ).fetchone()
            most_common_error = error_row[0] if error_row else None

            stats.append(TopicStats(
                topic=topic,
                total_attempts=total,
                passed_attempts=passed_count or 0,
                pass_rate=(passed_count or 0) / total if total else 0.0,
                most_common_error=most_common_error,
            ))
        return stats


def get_struggling_topics(
    db_path: str,
    learner_id: str = DEFAULT_LEARNER_ID,
    min_attempts: int = 3,
    limit: int = 5,
) -> list[TopicStats]:
    """
    Topics with the lowest pass_rate, only among topics that have had at
    least min_attempts attempts (so a single random failure with 1 attempt
    doesn't wrongly mark a topic as the "hardest").
    """
    all_stats = get_topic_stats(db_path, learner_id)
    eligible = [s for s in all_stats if s.total_attempts >= min_attempts]
    eligible.sort(key=lambda s: s.pass_rate)
    return eligible[:limit]


def get_completed_topics(db_path: str, learner_id: str = DEFAULT_LEARNER_ID) -> set[str]:
    """Topics that have at least one passing attempt."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT topic FROM attempts WHERE learner_id = ? AND passed = 1",
            (learner_id,),
        ).fetchall()
    return {row[0] for row in rows}


def get_current_streak(db_path: str, learner_id: str = DEFAULT_LEARNER_ID) -> int:
    """
    Number of consecutive calendar days (ending today or yesterday) with at
    least one attempt. If the most recent attempt isn't from today or
    yesterday, the streak is considered broken and this returns 0.

    Dates are parsed in Python (via datetime.fromisoformat) rather than with
    SQLite's own date functions, to avoid any ambiguity in how SQLite parses
    the UTC-offset suffix that isoformat() appends (e.g. "+00:00").
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT timestamp FROM attempts WHERE learner_id = ?",
            (learner_id,),
        ).fetchall()
    if not rows:
        return 0

    dates = sorted({datetime.fromisoformat(row[0]).date() for row in rows}, reverse=True)
    today = datetime.now(timezone.utc).date()

    if dates[0] not in (today, today - timedelta(days=1)):
        return 0

    streak = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def get_dashboard_stats(db_path: str, lessons: dict, learner_id: str = DEFAULT_LEARNER_ID) -> dict:
    """
    Aggregates everything the dashboard view needs into one call:
    per-level completion progress, overall completion percentage, total
    exercises solved (every passing attempt, including repeats), the
    overall correct-answer percentage, and the current day streak.

    lessons is passed in (rather than imported here) because "how many
    lessons exist per level" is content, not something the database
    tracks — this keeps progress/db.py from depending on lessons.py.
    """
    completed_topics = get_completed_topics(db_path, learner_id)

    level_progress: dict[str, tuple[int, int]] = {}
    for topic, data in lessons.items():
        level = data["level"]
        total, done = level_progress.get(level, (0, 0))
        total += 1
        if topic in completed_topics:
            done += 1
        level_progress[level] = (total, done)

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), SUM(passed) FROM attempts WHERE learner_id = ?",
            (learner_id,),
        ).fetchone()
    total_attempts = row[0] or 0
    passed_attempts = row[1] or 0

    total_lessons = len(lessons)
    lessons_completed = len(completed_topics)

    return {
        "level_progress": level_progress,  # {level: (total, completed)}
        "lessons_completed": lessons_completed,
        "total_lessons": total_lessons,
        "overall_percent": (lessons_completed / total_lessons * 100) if total_lessons else 0.0,
        "exercises_solved": passed_attempts,
        "correct_percent": (passed_attempts / total_attempts * 100) if total_attempts else 0.0,
        "day_streak": get_current_streak(db_path, learner_id),
    }
