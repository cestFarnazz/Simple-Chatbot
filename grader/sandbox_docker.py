# -*- coding: utf-8 -*-
"""
sandbox_docker.py — runs student code inside a disposable Docker container.

This is the same approach real code-judging platforms use (like the
open-source project Judge0, which powers many educational tools).

Why is this stronger than sandbox.py (the plain subprocess version)?

1) Process-count limit via cgroups, not rlimit:
   In sandbox.py we ran into a real bug: because our container ran as
   the root user, RLIMIT_NPROC (a POSIX limit) had no effect on root,
   and a fork bomb actually crashed the environment.
   Docker uses "cgroups" instead of rlimit — a different, kernel-level
   mechanism that *is enforced even for root*, because its controller
   is kept outside the process, at the host level; the process can't
   escape it with any capability.

2) Network fully disabled (--network none):
   sandbox.py had no way to fully close off network access. Here, a
   single flag turns off all networking for the container.

3) Read-only filesystem, with one controlled exception:
   The entire container filesystem is read-only, except /tmp, which is
   writable via a temporary tmpfs. Code is run from /tmp (not from the
   path where the code is mounted) so exercises that write files (like
   "Reading and Writing Files" in lessons.py) work — this was
   discovered through real testing on another machine: without this
   setting, even a legitimate file write was rejected.

4) Disposable (--rm):
   The entire container, along with any change the student code made
   inside it, is completely removed after execution.

Requirement: Docker must already be installed and running, and the
base image (e.g. python:3.12-slim) must already be pulled:

    docker pull python:3.12-slim

This module deliberately keeps the same interface (ExecutionResult and
function signature) as sandbox.py, so grading.py can switch between the
two backends without changing its own logic.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from grader.sandbox import ExecutionResult, _truncate, _decode  # same class/helpers, for a matching interface

DOCKER_IMAGE = "python:3.12-slim"

DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_MEMORY_MB = 128
DEFAULT_PIDS_LIMIT = 16     # a bit more generous than 1, since the Python interpreter itself sometimes spawns internal threads
DEFAULT_MAX_OUTPUT_CHARS = 20_000


def is_docker_available() -> bool:
    """Checks that the docker command is available and its daemon is running."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def run_code_docker(
    code: str,
    stdin_data: str = "",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    memory_mb: int = DEFAULT_MEMORY_MB,
    pids_limit: int = DEFAULT_PIDS_LIMIT,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> ExecutionResult:
    """
    Runs student code inside a disposable Docker container, with no
    network access, a read-only filesystem, and memory/process-count
    limits.
    """
    if not is_docker_available():
        return ExecutionResult(
            stdout="", stderr="", returncode=None, timed_out=False,
            truncated=False,
            error=(
                "Docker is not installed or its daemon isn't running. To use "
                "this backend, install Docker and run 'docker pull python:3.12-slim'."
            ),
        )

    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="docker_sandbox_")
        code_path = os.path.join(tmp_dir, "submission.py")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        docker_cmd = [
            "docker", "run",
            "--rm",                                   # fully remove the container after it runs
            "--network", "none",                      # no network access at all
            "--memory", f"{memory_mb}m",
            "--memory-swap", f"{memory_mb}m",          # swap set to the same value, i.e. effectively no extra swap
            "--pids-limit", str(pids_limit),           # cgroups (not rlimit) blocks a fork bomb here
            "--cpus", "1",
            "--read-only",                             # container filesystem is read-only
            "--tmpfs", "/tmp:rw,size=16m",              # only a small, temporary /tmp is allowed
            "--cap-drop", "ALL",                        # grant no extra Linux capabilities
            "--security-opt", "no-new-privileges",
            "-v", f"{code_path}:/code/submission.py:ro",  # code is mounted read-only
            "-w", "/tmp",  # run from /tmp (writable), not /code (read-only);
                            # otherwise exercises that write files (like "Reading and Writing Files") would fail
            "-i",                                        # to pass stdin through
            DOCKER_IMAGE,
            "python", "-I", "/code/submission.py",
        ]

        proc = subprocess.run(
            docker_cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        stdout, out_trunc = _truncate(proc.stdout, max_output_chars)
        stderr, err_trunc = _truncate(proc.stderr, max_output_chars)

        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
            timed_out=False,
            truncated=(out_trunc or err_trunc),
        )

    except subprocess.TimeoutExpired as e:
        # Note: because we pass --rm, if docker run itself gets killed, the
        # container may still take a moment to finish being removed by the
        # daemon; this is Docker's default behavior and creates no security
        # issue, since the container had no network and was read-only.
        out, _ = _truncate(_decode(e.stdout), max_output_chars)
        err, _ = _truncate(_decode(e.stderr), max_output_chars)
        return ExecutionResult(
            stdout=out, stderr=err, returncode=None, timed_out=True,
            truncated=False,
            error=f"Code execution took longer than {timeout} seconds and was stopped.",
        )
    except Exception as e:
        return ExecutionResult(
            stdout="", stderr="", returncode=None, timed_out=False,
            truncated=False, error=f"Internal sandbox_docker error: {e}",
        )
    finally:
        if tmp_dir and os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
