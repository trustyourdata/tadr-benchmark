"""Private process identifiers stay within lifecycle management, never artifacts."""

import os
import signal
import subprocess
import sys
import time

import psutil


class ProcessCleanupError(OSError):
    """Private lifecycle failure, mapped to existing infrastructure observations."""


class ProcessTree:
    def __init__(self, process: subprocess.Popen):
        self.process = process
        self.job = None
        self._closed = False
        self._linux = sys.platform == "linux"
        if self._linux:
            # Popen(start_new_session=True) completes setsid before returning.
            # The direct child has not been waited on yet, so even a very short
            # lived leader retains its identity as our unreaped child here.
            self._session = process.pid
            self._leader_created = psutil.Process(process.pid).create_time()
            if os.getsid(process.pid) != self._session or os.getpgid(process.pid) != self._session:
                raise ProcessCleanupError("worker lacks a dedicated execution session")
        if os.name == "nt":
            self._assign_windows_job()

    def _linux_groups(self):
        """Find the launch session even after its leader exits or is reaped.

        A group ID stays reserved while the group exists, including zombies.
        Reject a reused session-leader PID instead of signaling a new session.
        Never use descendant discovery from the departed parent as the boundary.
        """
        try:
            if psutil.Process(self._session).create_time() != self._leader_created:
                raise ProcessCleanupError("worker session identity was reused")
        except psutil.NoSuchProcess:
            pass
        groups = {self._session}
        for pid in psutil.pids():
            try:
                if os.getsid(pid) == self._session:
                    group = os.getpgid(pid)
                    # Recheck membership if the process exited during discovery.
                    if os.getsid(pid) == self._session:
                        groups.add(group)
            except ProcessLookupError:
                continue
        present = set()
        for group in groups:
            try:
                os.killpg(group, 0)
                present.add(group)
            except ProcessLookupError:
                pass
        return present

    def _wait_linux_session(self, sig, timeout):
        deadline = time.monotonic() + timeout
        signaled = set()
        while True:
            # Reap our child, allowing its group to disappear. Other orphaned
            # descendants are reaped by their adopter; zombies are not silently
            # treated as an empty group.
            self.process.poll()
            groups = self._linux_groups()
            if not groups:
                return True
            for group in groups - signaled:
                try:
                    os.killpg(group, sig)
                except ProcessLookupError:
                    pass
                signaled.add(group)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            # This is bounded condition polling, not a delay taken as evidence
            # of cleanup. Every successful return requires empty groups.
            time.sleep(min(0.01, remaining))

    def _close_linux(self):
        if not self._wait_linux_session(signal.SIGTERM, 2):
            if not self._wait_linux_session(signal.SIGKILL, 5):
                raise ProcessCleanupError("worker session termination barrier failed")
        self.process.wait(timeout=0)

    def _assign_windows_job(self):
        import ctypes
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", w.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                        ("process_limit", w.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        api.CreateJobObjectW.restype = w.HANDLE
        api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        api.CloseHandle.argtypes = [w.HANDLE]
        job = api.CreateJobObjectW(None, None)
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not job:
            raise OSError("worker isolation unavailable")
        if not api.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not api.AssignProcessToJobObject(job, int(self.process._handle)):
            api.CloseHandle(job)
            raise OSError("worker job assignment failed")
        self.job, self.api = job, api

    def close(self):
        if self._closed:
            return
        if self._linux:
            try:
                self._close_linux()
            except ProcessCleanupError:
                raise
            except (OSError, psutil.Error, subprocess.SubprocessError):
                raise ProcessCleanupError("worker session cleanup could not be verified") from None
            self._closed = True
            return
        try:
            children = psutil.Process(self.process.pid).children(recursive=True)
        except psutil.Error:
            children = []
        if self.job is not None:
            self.api.CloseHandle(self.job)
            self.job = None
        elif os.name != "nt":
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        # Kill remaining descendants, including ones whose parent exited early.
        if os.name != "nt":
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(children, timeout=3)
        if alive:
            raise ProcessCleanupError("worker descendants did not exit")
        self._closed = True


def spawn(command, **kwargs):
    flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(command, creationflags=flags, start_new_session=os.name != "nt", **kwargs)
    try:
        return process, ProcessTree(process)
    except Exception:
        process.kill()
        process.wait()
        raise
