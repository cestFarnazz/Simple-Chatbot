# -*- coding: utf-8 -*-
"""
Unit tests for grader/sandbox.py

Run: python3 -m unittest tests.test_sandbox -v
(no pytest needed — everything works with standard unittest)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grader.sandbox import run_code, IS_UNIX


class TestNormalExecution(unittest.TestCase):
    def test_simple_print_works(self):
        result = run_code("print('hello')")
        self.assertTrue(result.success)
        self.assertEqual(result.stdout.strip(), "hello")

    def test_stdin_is_passed_through(self):
        result = run_code("name = input(); print(f'Hi {name}')", stdin_data="Sara\n")
        self.assertTrue(result.success)
        self.assertIn("Hi Sara", result.stdout)

    def test_syntax_error_is_captured_not_raised(self):
        """A student code error must not raise an exception; it must come back in stderr."""
        result = run_code("print('unterminated")
        self.assertFalse(result.success)
        self.assertIsNone(result.error)  # not an infrastructure error, a student code error
        self.assertIn("SyntaxError", result.stderr)

    def test_runtime_error_is_captured(self):
        result = run_code("1 / 0")
        self.assertFalse(result.success)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ZeroDivisionError", result.stderr)

    def test_empty_code_returns_error_without_crashing(self):
        result = run_code("")
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)


class TestTimeout(unittest.TestCase):
    def test_infinite_loop_times_out(self):
        result = run_code("while True: pass", timeout=2, cpu_seconds=1)
        self.assertTrue(result.timed_out or result.returncode != 0)

    def test_sleep_hits_wallclock_timeout_not_cpu_limit(self):
        """
        time.sleep() doesn't actually consume CPU, so RLIMIT_CPU doesn't
        catch it; this is exactly the scenario that needs a separate
        wall-clock timeout.
        """
        result = run_code("import time; time.sleep(10)", timeout=2, cpu_seconds=5)
        self.assertTrue(result.timed_out)


class TestOutputAndEnv(unittest.TestCase):
    def test_large_output_is_truncated(self):
        code = "for i in range(1_000_000):\n    print('x' * 100)"
        result = run_code(code, max_output_chars=1000, timeout=5)
        self.assertTrue(result.truncated)
        self.assertLessEqual(len(result.stdout), 1000 + len("\n...[output truncated]"))

    def test_sensitive_env_vars_not_leaked(self):
        """Main app environment variables (like an API key) must not be passed to student code."""
        os.environ["FAKE_SECRET_FOR_TEST"] = "should-not-leak"
        try:
            result = run_code("import os; print(os.environ.get('FAKE_SECRET_FOR_TEST'))")
            self.assertTrue(result.success)
            self.assertNotIn("should-not-leak", result.stdout)
        finally:
            del os.environ["FAKE_SECRET_FOR_TEST"]


class TestFilesystemIsolation(unittest.TestCase):
    def test_student_code_cannot_write_into_project_directory(self):
        """
        The real scenario that happened: the "Reading and Writing Files"
        exercise in lessons.py creates a file with open("out.txt", "w").
        Before cwd was set to a temp directory, this file was created
        directly in the project folder.
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        marker_path = os.path.join(project_root, "should_not_exist.txt")
        if os.path.exists(marker_path):
            os.remove(marker_path)

        code = 'with open("should_not_exist.txt", "w") as f:\n    f.write("leak")'
        run_code(code, timeout=3)

        self.assertFalse(
            os.path.exists(marker_path),
            "Student code was able to create a file directly in the project folder!",
        )


@unittest.skipUnless(IS_UNIX, "resource limits are only enforced on Unix")
class TestResourceLimitsUnixOnly(unittest.TestCase):
    def test_memory_bomb_is_blocked(self):
        # unlike RLIMIT_NPROC, RLIMIT_AS is enforced for root too
        code = "x = bytearray(10 ** 9)"
        result = run_code(code, memory_bytes=64 * 1024 * 1024, timeout=5)
        self.assertFalse(result.success)

    def test_nproc_limit_is_configured(self):
        """
        The NPROC limit is now computed dynamically (current baseline for
        this user + a fixed headroom), not a hardcoded number — so we just
        check it's a sane positive value, not a specific constant.
        """
        code = "import resource; soft, _ = resource.getrlimit(resource.RLIMIT_NPROC); print(soft)"
        result = run_code(code, timeout=3)
        self.assertTrue(result.success)
        self.assertGreater(int(result.stdout.strip()), 10)

    def test_threading_module_is_not_blocked_by_process_limit(self):
        """
        Regression test for a real bug: RLIMIT_NPROC=1 (the original value)
        silently broke any exercise using the threading module, because on
        Linux RLIMIT_NPROC also counts threads, not just forked processes.
        This only showed up once the sandbox ran as a non-root user (on
        GitHub Actions) — under root, in this project's own analysis
        environment, the limit had no effect, so the bug stayed hidden.
        """
        code = (
            "import threading\n"
            "def job():\n"
            "    pass\n"
            "t1 = threading.Thread(target=job)\n"
            "t2 = threading.Thread(target=job)\n"
            "t1.start(); t2.start()\n"
            "t1.join(); t2.join()\n"
            "print('ok')\n"
        )
        result = run_code(code, timeout=5)
        self.assertTrue(result.success, msg=f"stderr was: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "ok")


if __name__ == "__main__":
    unittest.main()
