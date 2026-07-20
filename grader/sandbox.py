# -*- coding: utf-8 -*-
"""
sandbox.py — runs student code in an isolated subprocess.

⚠️ Honesty about the security level (please read):
This is not a "true security sandbox" on the level of gVisor / Docker+seccomp
/ nsjail / Firejail. Those tools require kernel-level isolation (namespaces,
seccomp, cgroups) that can't be achieved with a plain Python script.

What this module actually provides is a "defense in depth" layer:
  1. Running in a separate subprocess — a crash in student code doesn't
     take down the main app.
  2. A wall-clock timeout (via subprocess.run) — for cases like time.sleep()
     that don't consume CPU but suspend the program forever.
  3. RLIMIT_CPU, separate from the wall-clock timeout — for infinite loops
     that do consume CPU.
  4. RLIMIT_AS (memory cap) — blocks a simple memory bomb.
  5. RLIMIT_NPROC=0 — blocks a fork bomb.
  6. python -I (isolated mode) — no user site-packages, no PYTHONPATH.

⚠️ Critical warning: if this process runs as the root user, RLIMIT_NPROC/
RLIMIT_NOFILE/RLIMIT_CORE have no effect on root (since root is exempt from
these limits), and a fork bomb can get around them. In production this must
run as an unprivileged (non-root) system user; this module warns on import.

⚠️ What this module does *not* make safe: network access, reading/writing
files outside the temp directory, or arbitrary syscalls are not fully
blocked. For that, you need seccomp/gVisor/nsjail, or a container with
networking disabled.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import warnings
from dataclasses import dataclass

IS_UNIX = platform.system() in ("Linux", "Darwin")

if IS_UNIX:
    import resource

_RUNNING_AS_ROOT = IS_UNIX and hasattr(os, "geteuid") and os.geteuid() == 0
if _RUNNING_AS_ROOT:
    warnings.warn(
        "sandbox.py is running as the root user — RLIMIT_NPROC/RLIMIT_NOFILE/"
        "RLIMIT_CORE are ineffective for root and don't count as real "
        "protection. In production, always run this as an unprivileged "
        "system user.",
        RuntimeWarning,
        stacklevel=2,
    )

# --- Default limits ---
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_CPU_SECONDS = 3
DEFAULT_MEMORY_BYTES = 128 * 1024 * 1024  # 128MB
DEFAULT_MAX_OUTPUT_CHARS = 20_000
DEFAULT_MAX_PROCESSES = 1  # itself only, no new children
DEFAULT_MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1MB


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    returncode: int | None
    timed_out: bool
    truncated: bool
    error: str | None = None  # only a sandbox infrastructure error, not a student code error

    @property
    def success(self) -> bool:
        """Ran with no infrastructure error/timeout and exit code zero."""
        return self.error is None and not self.timed_out and self.returncode == 0

    @property
    def likely_oom(self) -> bool:
        """A -9/137 exit code usually means the OOM killer or RLIMIT_AS killed the process."""
        return self.returncode in (-9, 137) or "MemoryError" in (self.stderr or "")


def _apply_resource_limits(cpu_seconds, memory_bytes, max_processes, max_file_size_bytes):
    """Runs in the child, right before exec, via preexec_fn (Unix only)."""
    def limiter():
        for rlimit, value in (
            (resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds)),
            (resource.RLIMIT_AS, (memory_bytes, memory_bytes)),
            (resource.RLIMIT_NPROC, (max_processes, max_processes)),
            (resource.RLIMIT_FSIZE, (max_file_size_bytes, max_file_size_bytes)),
            (resource.RLIMIT_CORE, (0, 0)),
        ):
            try:
                resource.setrlimit(rlimit, value)
            except (ValueError, OSError):
                pass  # some platforms (e.g. macOS) don't support every rlimit
    return limiter


def _truncate(text: str, max_chars: int) -> tuple[str, bool]:
    if text is None:
        return "", False
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n...[output truncated]", True


def run_code(
    code: str,
    stdin_data: str = "",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    cpu_seconds: int = DEFAULT_CPU_SECONDS,
    memory_bytes: int = DEFAULT_MEMORY_BYTES,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> ExecutionResult:
    """
    Runs student code in an isolated subprocess and returns the result.

    Important note: a *student code* error (SyntaxError, ZeroDivisionError,
    etc.) comes back in stderr, not as an exception — this function doesn't
    decide pass/fail, it just executes. Making that decision is the job of
    the grading.py module.
    """
    if not isinstance(code, str) or not code.strip():
        return ExecutionResult(
            stdout="", stderr="", returncode=None, timed_out=False,
            truncated=False, error="The submitted code is empty.",
        )

    if not IS_UNIX:
        warnings.warn(
            "CPU/memory/process-count limits aren't enforced on this "
            "platform; only the wall-clock timeout is active.",
            RuntimeWarning,
        )

    tmp_dir = None
    try:
        # Run the code in a dedicated temp directory, not the main app's cwd.
        # Without this, an exercise like "Reading and Writing Files" in
        # lessons.py that calls open("out.txt", "w") would write the file
        # directly into the project folder (this is exactly what happened
        # during real testing).
        tmp_dir = tempfile.mkdtemp(prefix="sandbox_run_")
        tmp_path = os.path.join(tmp_dir, "submission.py")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Restricted environment: no sensitive env vars (API keys, etc.)
        clean_env = {"PATH": os.environ.get("PATH", ""), "LANG": "en_US.UTF-8"}

        preexec_fn = None
        if IS_UNIX:
            preexec_fn = _apply_resource_limits(
                cpu_seconds, memory_bytes, DEFAULT_MAX_PROCESSES, DEFAULT_MAX_FILE_SIZE_BYTES
            )

        proc = subprocess.run(
            [sys.executable, "-I", tmp_path],  # isolated mode: no site-packages, no PYTHONPATH
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=clean_env,
            cwd=tmp_dir,  # any file the code creates stays here, not in the project folder
            preexec_fn=preexec_fn,
        )

        stdout, out_trunc = _truncate(proc.stdout, max_output_chars)
        stderr, err_trunc = _truncate(proc.stderr, max_output_chars)

        return ExecutionResult(
            stdout=stdout, stderr=stderr, returncode=proc.returncode,
            timed_out=False, truncated=(out_trunc or err_trunc),
        )

    except subprocess.TimeoutExpired as e:
        out, _ = _truncate(_decode(e.stdout), max_output_chars)
        err, _ = _truncate(_decode(e.stderr), max_output_chars)
        return ExecutionResult(
            stdout=out, stderr=err, returncode=None, timed_out=True,
            truncated=False,
            error=f"Code execution took longer than {timeout} seconds and was stopped.",
        )
    except Exception as e:  # sandbox infrastructure error, not a student code error
        return ExecutionResult(
            stdout="", stderr="", returncode=None, timed_out=False,
            truncated=False, error=f"Internal sandbox error: {e}",
        )
    finally:
        if tmp_dir and os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _decode(value) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else value.decode("utf-8", errors="replace")
