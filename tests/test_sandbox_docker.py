# -*- coding: utf-8 -*-
"""
Tests for sandbox_docker.py

⚠️ Important, honest note:
The environment this project was built in (Claude's analysis sandbox)
doesn't have Docker installed itself — since it's a restricted isolated
environment too. So the real code-execution tests don't run here (they're
automatically skipped) and need to be run on your own machine, where
Docker is installed and running, to actually verify them:

    docker pull python:3.12-slim
    python3 -m unittest tests.test_sandbox_docker -v

The last test (fallback message) is always runnable, even without Docker,
since it checks exactly that behavior (a clear error message instead of a
crash).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grader.sandbox_docker import run_code_docker, is_docker_available


@unittest.skipUnless(is_docker_available(), "Docker isn't installed/running — run these tests on your own machine")
class TestDockerSandboxRealExecution(unittest.TestCase):
    def test_simple_print_works(self):
        result = run_code_docker("print('hello from container')")
        self.assertTrue(result.success)
        self.assertIn("hello from container", result.stdout)

    def test_network_is_actually_blocked(self):
        """
        This is exactly what sandbox.py (the plain version) couldn't
        guarantee. If --network none works correctly, this attempt to
        connect to the internet should fail, not succeed.
        """
        code = (
            "import socket\n"
            "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            "s.settimeout(2)\n"
            "try:\n"
            "    s.connect(('8.8.8.8', 53))\n"
            "    print('CONNECTED')\n"
            "except Exception as e:\n"
            "    print('BLOCKED')\n"
        )
        result = run_code_docker(code, timeout=8)
        self.assertIn("BLOCKED", result.stdout)
        self.assertNotIn("CONNECTED", result.stdout)

    def test_readonly_filesystem_blocks_writes(self):
        code = 'open("/etc/should_not_be_writable", "w").write("x")'
        result = run_code_docker(code, timeout=5)
        self.assertFalse(result.success)

    def test_writing_a_file_in_workdir_still_works(self):
        """
        This is exactly the bug that happened once: the "Reading and
        Writing Files" exercise in lessons.py creates a file with
        open("out.txt", "w"). Since we set workdir to /tmp (writable),
        this should work — unlike writes to other paths, which should
        stay blocked.
        """
        code = (
            'with open("out.txt", "w", encoding="utf-8") as f:\n'
            '    f.write("hello")\n'
            'with open("out.txt", "r", encoding="utf-8") as f:\n'
            '    print(f.read())'
        )
        result = run_code_docker(code, timeout=5)
        self.assertTrue(result.success)
        self.assertEqual(result.stdout.strip(), "hello")

    def test_memory_limit_is_enforced(self):
        code = "x = bytearray(500 * 1024 * 1024)"  # attempt to allocate ~500MB
        result = run_code_docker(code, memory_mb=64, timeout=5)
        self.assertFalse(result.success)

    def test_fork_bomb_is_actually_blocked_even_as_root(self):
        """
        This is exactly the scenario that crashed sandbox.py under root.
        Here, since Docker uses cgroups (not rlimit), it should really and
        safely be blocked.
        """
        code = "import os\nfor _ in range(30):\n    os.fork()"
        result = run_code_docker(code, pids_limit=4, timeout=5)
        self.assertFalse(result.success)


class TestDockerUnavailableFallback(unittest.TestCase):
    """This test always runs, since it checks the 'Docker isn't available' behavior."""

    def test_graceful_message_when_docker_missing(self):
        if is_docker_available():
            self.skipTest("Docker is available on this system; this test is for the no-Docker case")
        result = run_code_docker("print('test')")
        self.assertIsNotNone(result.error)
        self.assertIn("Docker", result.error)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
