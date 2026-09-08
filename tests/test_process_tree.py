"""Controlled process fixtures; identifiers stay in private pipes and memory."""

import os
import signal
import subprocess
import sys
from types import SimpleNamespace

import psutil
import pytest

from tadr_benchmark.execution import process_tree
from tadr_benchmark.execution.process_tree import ProcessCleanupError, spawn

linux = pytest.mark.skipif(sys.platform != "linux", reason="Linux session cleanup")

CHILD = """
import os, signal, sys
if sys.argv[1] == 'group': os.setpgrp()
if sys.argv[1] == 'ignore': signal.signal(signal.SIGTERM, signal.SIG_IGN)
print('ready', flush=True)
signal.pause()
"""
PARENT = """
import signal, subprocess, sys
child = subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]],
    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
assert child.stdout.readline().strip() == 'ready'
child.stdout.close()
print(child.pid, flush=True)
sys.stdin.readline()
"""


def family(mode="standard"):
    process, tree = spawn([sys.executable, "-c", PARENT, CHILD, mode],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True)
    child = int(process.stdout.readline())
    return process, tree, child


def release_parent(process):
    process.stdin.write("exit\n")
    process.stdin.flush()
    process.wait(timeout=5)


def close_pipes(process):
    process.stdin.close()
    process.stdout.close()


@linux
@pytest.mark.parametrize("repeat", range(50))
def test_early_parent_exit_has_no_descendant_at_return(repeat):
    process, tree, child = family()
    try:
        release_parent(process)
        assert psutil.pid_exists(child)
        tree.close()
        assert not psutil.pid_exists(child)  # No grace sleep after close.
        assert process.returncode == 0
        tree.close()
    finally:
        tree.close()
        close_pipes(process)


@linux
@pytest.mark.parametrize("mode", ["standard", "group", "ignore"])
@pytest.mark.parametrize("parent_exits_first", [False, True])
def test_live_parent_separate_group_and_escalation(mode, parent_exits_first):
    process, tree, child = family(mode)
    try:
        if parent_exits_first:
            release_parent(process)
        tree.close()
        assert process.poll() is not None
        assert not psutil.pid_exists(child)
        tree.close()
    finally:
        tree.close()
        close_pipes(process)


@linux
def test_dead_worker_cleanup_is_idempotent(monkeypatch):
    process, tree = spawn([sys.executable, "-c", "pass"])
    process.wait(timeout=5)
    tree.close()
    monkeypatch.setattr(process_tree.os, "killpg", lambda *args: pytest.fail("closed session signaled again"))
    tree.close()


@linux
def test_descendant_exiting_between_discovery_and_signal(monkeypatch):
    process, tree, child = family()
    real_signal = os.killpg
    raced = []
    def signal_group(group, sig):
        if sig and not raced:
            raced.append(True)
            real_signal(group, signal.SIGKILL)
            raise ProcessLookupError
        return real_signal(group, sig)
    monkeypatch.setattr(process_tree.os, "killpg", signal_group)
    try:
        release_parent(process)
        tree.close()
        assert raced and not psutil.pid_exists(child)
    finally:
        tree.close()
        close_pipes(process)


@linux
def test_unsatisfied_barrier_is_typed_and_retryable(monkeypatch):
    tree = object.__new__(process_tree.ProcessTree)
    tree._linux, tree._closed = True, False
    calls = []
    monkeypatch.setattr(tree, "_wait_linux_session", lambda sig, timeout: calls.append((sig, timeout)) or False)
    with pytest.raises(ProcessCleanupError, match="termination barrier failed"):
        tree.close()
    assert calls == [(signal.SIGTERM, 2), (signal.SIGKILL, 5)]
    assert not tree._closed


@linux
def test_reused_leader_identity_fails_without_signaling(monkeypatch):
    tree = object.__new__(process_tree.ProcessTree)
    tree._session, tree._leader_created = 123, 1.0
    monkeypatch.setattr(process_tree.psutil, "Process", lambda _: SimpleNamespace(create_time=lambda: 2.0))
    monkeypatch.setattr(process_tree.os, "killpg", lambda *args: pytest.fail("reused session signaled"))
    with pytest.raises(ProcessCleanupError, match="identity was reused"):
        tree._linux_groups()


def test_windows_job_cleanup_path_remains_idempotent(monkeypatch):
    assert issubclass(ProcessCleanupError, OSError)
    tree = object.__new__(process_tree.ProcessTree)
    calls = []
    tree._linux, tree._closed, tree.job = False, False, object()
    tree.process = SimpleNamespace(pid=123, wait=lambda **kw: calls.append("wait"))
    tree.api = SimpleNamespace(CloseHandle=lambda _: calls.append("job"))
    child = SimpleNamespace(kill=lambda: calls.append("child"))
    monkeypatch.setattr(process_tree, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(process_tree.psutil, "Process", lambda _: SimpleNamespace(children=lambda **kw: [child]))
    monkeypatch.setattr(process_tree.psutil, "wait_procs", lambda *args, **kw: (calls.append("barrier") or [], []))
    tree.close()
    tree.close()
    assert calls == ["job", "wait", "child", "barrier"]
