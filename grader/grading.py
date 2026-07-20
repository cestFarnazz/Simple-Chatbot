"""
grading.py — compares actual execution output, not source text

Design decisions:

1) Why compare output instead of source text?
   Two pieces of code that are logically equivalent can look completely
   different in text (different variable names, different spacing,
   `range(n)` vs. `range(0, n)`). The old grading approach
   (`user_answer == correct_answer`) would wrongly "reject" these. Comparing
   actual stdout solves this, because the criterion becomes "does the
   program do the same thing?" rather than "did it type the exact same
   characters?".

2) The reference answer is also run through the same sandbox — instead of
   hand-writing the expected output ahead of time in lessons.py. This
   prevents "drift": if the reference code in lessons.py is ever edited,
   the expected output automatically stays up to date, and there's no need
   to manually keep two sources (code and output) in sync.

3) Caching the reference output: since the reference code for a topic
   stays constant throughout the program's run, we cache it so that each
   student submission doesn't trigger two sandbox runs (only the student's
   code is executed; the reference output is computed once and kept).

4) Sanitizing the traceback: the path of the temp file the sandbox creates
   (like /tmp/tmpXXXXXX.py) shouldn't be visible in the error shown to the
   user — both for a cleaner message and because exposing the server's
   filesystem path is a small information leak.

5) Choosing the execution backend (plain subprocess or Docker):
   The SANDBOX_BACKEND environment variable lets you switch between the two
   isolation levels without changing the grading logic. The default is the
   plain subprocess (since it needs no Docker installation); for real/
   production use, setting SANDBOX_BACKEND=docker is recommended.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from grader.sandbox import run_code as _run_code_subprocess, ExecutionResult

# Backend selection via the SANDBOX_BACKEND environment variable:
#   "subprocess" (default) → grader/sandbox.py — simple, no external dependency
#   "docker"                → grader/sandbox_docker.py — industry-standard isolation
# This lets you switch between the two backends without changing grading.py's logic.
_BACKEND = os.environ.get("SANDBOX_BACKEND", "subprocess").strip().lower()

if _BACKEND == "docker":
    from grader.sandbox_docker import run_code_docker as _execute_code
else:
    _execute_code = _run_code_subprocess

# Cache of the reference output per topic — since the reference code doesn't change during a run
_reference_output_cache: dict[str, str] = {}


def _apply_masks(text: str, mask_patterns: list[str]) -> str:
    """
    Replaces non-deterministic parts of the output (time, random numbers,
    dates) with a placeholder before comparing. This is needed for
    exercises where even the reference code itself produces different
    output every time (e.g. printing elapsed time in the Decorators
    exercise) — without this masking, such exercises would never be
    auto-gradable, even against their own correct answer.
    """
    if not mask_patterns:
        return text
    result = text
    for pattern in mask_patterns:
        result = re.sub(pattern, "<MASKED>", result)
    return result


@dataclass
class GradeResult:
    passed: bool
    user_stdout: str
    expected_stdout: str
    user_error: str | None      # sanitized traceback, if the student's code errored
    infra_error: str | None      # a sandbox infrastructure error (not the student's fault)
    timed_out: bool
    diff_hint: str | None = field(default=None)  # first point of difference, for feedback
    not_auto_gradable: bool = field(default=False)  # e.g. GUI exercises


def normalize_output(text: str) -> str:
    """
    Conservative normalization: only trailing whitespace on each line and
    trailing blank lines at the end of the output are stripped. Meaningful
    differences (line order, values, upper/lower case) are left untouched —
    since these could be a real bug in the student's code and shouldn't be
    hidden.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _sanitize_traceback(stderr: str, tmp_path: str | None = None) -> str:
    """Removes the sandbox's temp file path from the traceback."""
    # A general pattern for temp paths, even if tmp_path isn't given
    sanitized = re.sub(r'File "[^"]*\.py"', 'File "<submission>"', stderr)
    return sanitized


def _get_reference_output(topic: str, lessons: dict) -> tuple[str | None, str | None]:
    """
    Returns the reference output (cached). If the reference code itself
    errors, this is an internal content bug in the lesson (not the
    student's fault) and must be reported separately so it isn't confused
    with a student error.
    """
    if topic in _reference_output_cache:
        return _reference_output_cache[topic], None

    reference_code = lessons[topic]["answer"]
    mask_patterns = lessons[topic].get("mask_patterns", [])
    result: ExecutionResult = _execute_code(reference_code)

    if not result.success:
        error_msg = (
            f"Internal error: the reference answer for topic \"{topic}\" "
            f"doesn't run or errors out itself. This needs to be fixed in "
            f"lessons.py. Details: {result.error or result.stderr}"
        )
        return None, error_msg

    normalized = _apply_masks(normalize_output(result.stdout), mask_patterns)
    _reference_output_cache[topic] = normalized
    return normalized, None


def grade_submission(topic: str, user_code: str, lessons: dict) -> GradeResult:
    """
    Runs the student's code and compares its output against the reference
    code's output. Never raises an exception — every error case comes back
    in a GradeResult.
    """
    if not lessons[topic].get("auto_gradable", True):
        # e.g. Tkinter exercises: they open a graphical window and never
        # produce comparable stdout (mainloop blocks forever). Running them
        # would just be a wasted 5-second timeout.
        return GradeResult(
            passed=False,
            user_stdout="",
            expected_stdout="",
            user_error=None,
            infra_error=None,
            timed_out=False,
            not_auto_gradable=True,
        )

    mask_patterns = lessons[topic].get("mask_patterns", [])
    expected_stdout, ref_error = _get_reference_output(topic, lessons)

    if ref_error is not None:
        return GradeResult(
            passed=False,
            user_stdout="",
            expected_stdout="",
            user_error=None,
            infra_error=ref_error,
            timed_out=False,
        )

    user_result = _execute_code(user_code)

    if user_result.timed_out:
        return GradeResult(
            passed=False,
            user_stdout=user_result.stdout,
            expected_stdout=expected_stdout,
            user_error=None,
            infra_error=user_result.error,
            timed_out=True,
        )

    if user_result.error is not None:
        # a sandbox infrastructure error, not the student's fault
        return GradeResult(
            passed=False,
            user_stdout="",
            expected_stdout=expected_stdout,
            user_error=None,
            infra_error=user_result.error,
            timed_out=False,
        )

    if user_result.returncode != 0:
        # student error: the code ran but crashed (SyntaxError, Exception, ...)
        return GradeResult(
            passed=False,
            user_stdout=normalize_output(user_result.stdout),
            expected_stdout=expected_stdout,
            user_error=_sanitize_traceback(user_result.stderr),
            infra_error=None,
            timed_out=False,
        )

    user_stdout_normalized = _apply_masks(normalize_output(user_result.stdout), mask_patterns)
    passed = user_stdout_normalized == expected_stdout

    diff_hint = None
    if not passed:
        diff_hint = _first_diff_hint(user_stdout_normalized, expected_stdout)

    return GradeResult(
        passed=passed,
        user_stdout=user_stdout_normalized,
        expected_stdout=expected_stdout,
        user_error=None,
        infra_error=None,
        timed_out=False,
        diff_hint=diff_hint,
    )


def _first_diff_hint(actual: str, expected: str) -> str:
    """Identifies the first differing line, for simple feedback."""
    actual_lines = actual.split("\n")
    expected_lines = expected.split("\n")

    for i, (a, e) in enumerate(zip(actual_lines, expected_lines), start=1):
        if a != e:
            return f"Line {i}: your output was \"{a}\" but the expected output was \"{e}\"."

    if len(actual_lines) != len(expected_lines):
        return (
            f"The number of output lines differs: yours has {len(actual_lines)} lines, "
            f"the expected has {len(expected_lines)} lines."
        )
    return "The outputs don't match."


def clear_reference_cache():
    """For tests, or when lessons.py changes during a hot-reload."""
    _reference_output_cache.clear()
